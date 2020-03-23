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

"""A test run manager module."""
import datetime
import logging

from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.util import tfc_client


class TestRunNotFoundError(Exception):
  pass


def SetTestRunState(test_run_id, state, update_time=None, error_reason=None):
  """Update a test run's state.

  Args:
    test_run_id: test run ID
    state: new test run state
    update_time: update timestamp, defaults to current time
    error_reason: error message, only used for ERROR state
  Raises:
    TestRunNotFoundError: if a given test run does not exist.
  """
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    raise TestRunNotFoundError('Test run %s does not exist' % test_run_id)

  if test_run.IsFinal():
    logging.warn('Test run %s already in final state (state=%s)',
                 test_run_id, test_run.state)
    return

  if not update_time:
    update_time = datetime.datetime.utcnow()

  if test_run.request_id and state == ndb_models.TestRunState.CANCELED:
    # Need to cancel an associated TFC request and wait.
    tfc_client.CancelRequest(test_run.request_id)
    event_log.Warn(test_run, 'Test run canceled')

  if state == ndb_models.TestRunState.ERROR:
    test_run.error_reason = error_reason
    event_log.Error(test_run, 'Test run failed: %s' % error_reason)
  test_run.state = state
  test_run.update_time = update_time
  test_run.put()
