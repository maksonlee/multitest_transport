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

"""A module to kick test plans."""

import datetime
import json
import logging
import croniter
import pytz
import webapp2

from google.appengine.api import taskqueue
from multitest_transport.models import build
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_kicker

TEST_PLAN_KICKER_QUEUE = 'test-plan-kicker-queue'
MAX_NEXT_RUN_DELAY_SECONDS = 5 * 60


def _GetCurrentTime():
  """Returns the current time in UTC.

  Returns:
    a datetime.datetime object.
  """
  return datetime.datetime.utcnow()


def ScheduleCronKick(test_plan_id, next_run_time=None):
  """Schedule a next cron kick for a test plan.

  Args:
    test_plan_id: a test plan ID.
    next_run_time: next run time. It would be calculated based on cron_exp if
        not given.
  """
  test_plan = messages.ConvertToKey(ndb_models.TestPlan, test_plan_id).get()
  if not test_plan:
    logging.warn('test plan %s does not exist', test_plan_id)
    return
  test_plan_status = ndb_models.TestPlanStatus.query(
      ancestor=test_plan.key).get()
  if not test_plan_status:
    test_plan_status = ndb_models.TestPlanStatus(parent=test_plan.key)

  if test_plan.cron_exp:
    now = _GetCurrentTime()
    if next_run_time:
      test_plan_status.next_run_time = next_run_time
    else:
      cron = croniter.croniter(test_plan.cron_exp, now)
      test_plan_status.next_run_time = cron.get_next(datetime.datetime)
    payload = json.dumps({
        'test_plan_id': test_plan_id,
        'is_cron': True
    })
    task = taskqueue.Task(
        payload=payload, eta=pytz.UTC.localize(test_plan_status.next_run_time))
    task.add(queue_name=TEST_PLAN_KICKER_QUEUE)
    test_plan_status.next_run_task_name = task.name
    logging.info(
        'Scheduled the next kick task %s (eta=%s)', task.name, task.eta)
  else:
    logging.warn(
        'Cannot schedule next kick for test plan %s: cron_exp is None.',
        test_plan_id)
    test_plan_status.next_run_time = None
    test_plan_status.next_run_task_name = None
  test_plan_status.put()


def KickTestPlan(test_plan_id, is_cron=False, task_name=None):
  """Kicks a test plan.

  Args:
    test_plan_id: a test plan ID.
    is_cron: whether a kick is triggered by cron or not.
    task_name: a task name.
  Raises:
    NoBuildError: if any of build channels doesn't return any builds.
  """
  logging.info('Kicking test plan %s', test_plan_id)
  test_plan = messages.ConvertToKey(ndb_models.TestPlan, test_plan_id).get()
  if not test_plan:
    logging.warn('test plan %s does not exist', test_plan_id)
    return
  test_plan_status = ndb_models.TestPlanStatus.query(
      ancestor=test_plan.key).get()
  if not test_plan_status:
    test_plan_status = ndb_models.TestPlanStatus(parent=test_plan.key)

  if is_cron:
    if test_plan_status.next_run_task_name != task_name:
      logging.warn(
          'unexpected cron task name: %s != %s; ignoring',
          task_name, test_plan_status.next_run_task_name)
      return
    test_plan_status.next_run_task_name = None

  test_resource_objs = build.FindTestResources(test_plan.test_resource_pipes)

  test_output_upload_configs = test_plan.test_output_upload_configs

  # Schedule all tests
  test_runs = []
  try:
    for config in test_plan.test_run_configs:
      # Test plan's before device actions run before those of a test run config.
      config.before_device_action_keys = (
          test_plan.before_device_action_keys +
          config.before_device_action_keys)
      test_run = test_kicker.CreateTestRun(
          labels=test_plan.labels,
          test_plan_key=test_plan.key,
          test_run_config=config,
          test_resources=test_resource_objs,
          test_output_upload_configs=test_output_upload_configs)
      test_runs.append(test_run)
  except Exception:
    # TODO: cancel test runs if a test plan fails to be executed.
    raise

  # Add a task for the next run.
  now = _GetCurrentTime()
  test_plan_status.last_run_time = now
  if test_plan_status.next_run_task_name == task_name:
    test_plan_status.next_run_task_name = None
  test_plan_status.put()

  if is_cron and test_plan.cron_exp:
    ScheduleCronKick(test_plan_id)


def CheckTestPlanNextRuns():
  """Check next runs of test plans to reschedule non-executed ones."""
  now = _GetCurrentTime()
  cutoff_time = now - datetime.timedelta(
      seconds=MAX_NEXT_RUN_DELAY_SECONDS)
  query = ndb_models.TestPlanStatus.query(
      ndb_models.TestPlanStatus.next_run_time < cutoff_time)
  for status in query:
    if not status.next_run_time:
      continue
    test_plan_id = status.key.parent().id()
    logging.info(
        'test plan %s did not run until %s (next_run_time=%s); rescheduling',
        test_plan_id, now, status.next_run_time)
    ScheduleCronKick(test_plan_id, next_run_time=now)


class TaskHandler(webapp2.RequestHandler):
  """A web request handler to handle tasks from the test kicker queue."""

  def post(self):
    """Process a request message."""
    payload = json.loads(self.request.body)
    test_plan_id = payload['test_plan_id']
    is_cron = payload.get('is_cron', False)
    KickTestPlan(
        test_plan_id, is_cron,
        task_name=self.request.headers.get('X-AppEngine-TaskName'))


APP = webapp2.WSGIApplication([
    ('.*', TaskHandler),
], debug=True)
