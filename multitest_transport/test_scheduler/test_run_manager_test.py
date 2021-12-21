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

"""Unit tests for test_run_manager module."""
from unittest import mock

from absl.testing import absltest
from tradefed_cluster import testbed_dependent_test

from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_run_manager
from multitest_transport.util import tfc_client


class TestRunManagerTest(testbed_dependent_test.TestbedDependentTest):
  """Unit tests for test_run_manager module."""

  def _CreateTestRun(self, state):
    """Creates a placeholder test run."""
    test_run = ndb_models.TestRun(state=state)
    test_run.put()
    return test_run

  def testSetTestRunState(self):
    # can modify non-final test run state
    test_run = self._CreateTestRun(state=ndb_models.TestRunState.RUNNING)

    test_run_manager.SetTestRunState(test_run_id=test_run.key.id(),
                                     state=ndb_models.TestRunState.ERROR,
                                     error_reason='reason')
    test_run = test_run.key.get()
    self.assertEqual(ndb_models.TestRunState.ERROR, test_run.state)
    self.assertEqual('reason', test_run.error_reason)

  def testSetTestRunState_notFound(self):
    # trying to modify unknown test run throws error
    with self.assertRaises(test_run_manager.TestRunNotFoundError):
      test_run_manager.SetTestRunState(test_run_id=666,
                                       state=ndb_models.TestRunState.ERROR)

  def testSetTestRunState_finalState(self):
    # final test run state is immutable
    test_run = self._CreateTestRun(state=ndb_models.TestRunState.COMPLETED)

    test_run_manager.SetTestRunState(test_run_id=test_run.key.id(),
                                     state=ndb_models.TestRunState.ERROR)
    test_run = test_run.key.get()
    self.assertEqual(ndb_models.TestRunState.COMPLETED, test_run.state)

  @mock.patch.object(tfc_client, 'CancelRequest')
  def testSetTestRunState_cancel(self, mock_cancel_request):
    # switching to CANCELED state will also cancel the TFC request
    test_run = self._CreateTestRun(state=ndb_models.TestRunState.RUNNING)
    test_run.request_id = 'request_id'
    test_run.put()

    test_run_manager.SetTestRunState(test_run_id=test_run.key.id(),
                                     state=ndb_models.TestRunState.CANCELED)
    test_run = test_run.key.get()
    mock_cancel_request.assert_called_with(test_run.request_id)
    self.assertEqual(ndb_models.TestRunState.CANCELED, test_run.state)

if __name__ == '__main__':
  absltest.main()
