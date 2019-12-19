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

MTT relies on cron jobs but dev_appserver does not run them automatically.
This module parses cron.yaml and triggers cron jobs as configured there.
"""

import datetime
import json
import logging
import os
import pickle

import pytz
from six.moves import urllib
import webapp2
import yaml

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api.modules import modules
from google.appengine.cron import groctimespecification

CRON_YAML_PATH = 'cron.yaml'
CRON_KICKER_QUEUE = 'cron-kicker-queue'
CRON_JOB_DEADLINE_SECONDS = 300


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


def _IsDevelopmentServer():
  """Returns whether an app is running in development server."""
  return os.environ.get('SERVER_SOFTWARE', 'Development').startswith(
      'Development')


def Init():
  """Initialize the module."""
  logging.info('Init')
  taskqueue.Queue(name=CRON_KICKER_QUEUE).purge()
  if not _IsDevelopmentServer():
    logging.info('cron_kicker only runs in development server.')
    return

  logging.debug('loading %s...', CRON_YAML_PATH)
  with open(CRON_YAML_PATH) as f:
    data = yaml.load(f)
  cron_jobs = [
      CronJob(
          url=d['url'], schedule=d['schedule'],
          target=d.get('target', 'default'), next_run_time=None)
      for d in data['cron']
  ]
  logging.info('cron jobs = %s', cron_jobs)
  for cron_job in cron_jobs:
    ScheduleNextKick(cron_job)


def Kick(cron_job):
  """Check a cron job to see whether it needs to run.

  Also schedule the next check.

  Args:
    cron_job: a CronJob object.
  """
  now = _GetCurrentTime()
  if not cron_job.next_run_time or now < cron_job.next_run_time:
    logging.warn(
        'cron job %s is not yet to run: next_run_time=%s',
        cron_job.url, cron_job.next_run_time)
    return
  hostname = modules.get_hostname(module=cron_job.target)
  url = 'http://%s%s' % (hostname, cron_job.url)
  logging.info('Kicking a cron job: %s', url)
  urlfetch.set_default_fetch_deadline(CRON_JOB_DEADLINE_SECONDS)
  urllib.request.urlopen(url)
  cron_job.next_run_time = None


def ScheduleNextKick(cron_job):
  """Schedule a next kick for a cron job.

  Args:
    cron_job: a CronJob object.
  """
  now = _GetCurrentTime()
  schedule = groctimespecification.GrocTimeSpecification(cron_job.schedule)
  cron_job.next_run_time = schedule.GetMatches(now, 1)[0]
  task = taskqueue.Task(
      payload=pickle.dumps(cron_job),
      eta=pytz.UTC.localize(cron_job.next_run_time))
  task.add(queue_name=CRON_KICKER_QUEUE)


class TaskHandler(webapp2.RequestHandler):
  """A web request handler to handle tasks from the cron kicker queue."""

  def post(self):
    """Process a request message."""
    cron_job = pickle.loads(self.request.body)
    Kick(cron_job)
    ScheduleNextKick(cron_job)

APP = webapp2.WSGIApplication([
    ('/.*', TaskHandler),
], debug=True)
