# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module to kick cron jobs in local mode.

This module parses cron.yaml and triggers cron jobs as configured there.
"""

import datetime
import json
import logging
import os
import pickle

import flask
import pytz
from six.moves import urllib
import yaml

# TODO: remove this dependency.
from multitest_transport.core.cron import groctimespecification
from multitest_transport.util import env
from tradefed_cluster import common
from tradefed_cluster.services import app_manager
from tradefed_cluster.services import task_scheduler

CRON_YAML_PATH = 'cron.yaml'
CRON_KICKER_QUEUE = 'cron-kicker-queue'
CRON_JOB_DEADLINE_SECONDS = 300

APP = flask.Flask(__name__)


class CronJob(object):
  """A class representing a cron job entry."""

  def __init__(self, url, schedule, target, next_run_time):
    self.url = url
    self.schedule = schedule
    self.target = target
    self.next_run_time = next_run_time

  def __repr__(self):
    return json.dumps(self.__dict__)

  def __eq__(self, other):
    if isinstance(self, other.__class__):
      return self.__dict__ == other.__dict__
    return False


def _GetCurrentTime():
  return datetime.datetime.utcnow()


def _IsRunningInGAE():
  """Returns true if running in Google App Engine."""
  server_software = os.environ.get('SERVER_SOFTWARE', '')
  return server_software.startswith('Google App Engine/')


def Init():
  """Initialize the module."""
  logging.info('Init')
  if _IsRunningInGAE():
    logging.info('cron_kicker disabled on Google App Engine')
    return

  logging.debug('loading %s...', CRON_YAML_PATH)
  with open(CRON_YAML_PATH) as f:
    data = yaml.safe_load(f)
  cron_jobs = []
  for d in data['cron']:
    cron_jobs.append(
        CronJob(
            url=d['url'],
            schedule=d['schedule'],
            target=d.get('target', 'default'),
            next_run_time=None))
  logging.info('cron jobs = %s', cron_jobs)
  for cron_job in cron_jobs:
    ScheduleNextKick(cron_job, _GetCurrentTime())


def Kick(cron_job):
  """Check a cron job to see whether it needs to run.

  Also schedule the next check.

  Args:
    cron_job: a CronJob object.
  """
  now = _GetCurrentTime()
  if not cron_job.next_run_time or now < cron_job.next_run_time:
    logging.warning(
        'cron job %s is not yet to run: next_run_time=%s',
        cron_job.url, cron_job.next_run_time)
    return
  hostname = app_manager.GetInfo(cron_job.target).hostname
  hostname = hostname.replace(env.HOSTNAME, 'localhost')
  url = 'http://%s%s' % (hostname, cron_job.url)
  logging.info('Kicking a cron job: %s', url)
  urllib.request.urlopen(url)
  cron_job.next_run_time = None


def ScheduleNextKick(cron_job, next_run_time=None):
  """Schedule a next kick for a cron job.

  Args:
    cron_job: a CronJob object.
    next_run_time: an optional next run time.
  """
  if not next_run_time:
    now = _GetCurrentTime()
    schedule = groctimespecification.GrocTimeSpecification(cron_job.schedule)
    next_run_time = schedule.GetMatches(now, 1)[0]
  cron_job.next_run_time = next_run_time
  # TODO: consider switching to json since picke is insecure.
  task_scheduler.AddTask(
      queue_name=CRON_KICKER_QUEUE,
      payload=pickle.dumps(cron_job, protocol=2),
      eta=pytz.UTC.localize(cron_job.next_run_time))


@APP.route('/', methods=['POST'])
# This matchs all path start with '/'.
@APP.route('/<path:fake>', methods=['POST'])
def TaskHandler(fake=None):
  """A web request handler to handle tasks from the cron kicker queue."""
  del fake
  cron_job = pickle.loads(flask.request.get_data())
  Kick(cron_job)
  ScheduleNextKick(cron_job)
  return common.HTTP_OK
