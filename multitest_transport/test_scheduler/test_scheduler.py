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

"""A test scheduler module."""

import datetime
import logging



import webapp2

from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_kicker
from multitest_transport.test_scheduler import test_plan_kicker
from multitest_transport.test_scheduler import test_run_manager

_PENDING_TEST_RUN_TTL = 86400


def CheckPendingTestRuns():
  """Check test runs to decide if requeue/cancel according timeout parameter."""
  pending_test_runs = (
      ndb_models.TestRun.query().order(
          -ndb_models.TestRun.create_time, ndb_models.TestRun.key)
      .filter(ndb_models.TestRun.state == ndb_models.TestRunState.PENDING))
  for test_run in pending_test_runs:
    pending_start_time = datetime.datetime.utcnow() - datetime.timedelta(
        seconds=_PENDING_TEST_RUN_TTL)
    if  pending_start_time > test_run.create_time:
      test_run_manager.SetTestRunState(
          test_run_id=test_run.key.id(),
          state=ndb_models.TestRunState.CANCELED)
      continue
    logging.info('requeue the test run %s', test_run.key.id())
    test_kicker.EnqueueTestRun(test_run.key.id())


def ScheduleTestPlanCronJob(test_plan_id):
  """Schedules a cron job for a test plan.

  If the test plan is not for cron, no cron job will be scheduled.

  Args:
    test_plan_id: a test plan ID.
  """
  test_plan_kicker.ScheduleCronKick(test_plan_id)


class CronHandler(webapp2.RequestHandler):
  """A cron handler for periodic schedule checks."""

  def get(self):
    """Check test plan schedule."""
    test_plan_kicker.CheckTestPlanNextRuns()


APP = webapp2.WSGIApplication([
    ('/test_scheduler/cron', CronHandler),
], debug=True)
