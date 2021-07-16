# Copyright 2021 Google LLC
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

"""Unit tests for test_result_handler."""
from absl.testing import absltest
import mock
from tradefed_cluster import api_messages
from tradefed_cluster import testbed_dependent_test

from multitest_transport.models import ndb_models
from multitest_transport.models import sql_models
from multitest_transport.test_scheduler import test_result_handler
from multitest_transport.util import tfc_client
from multitest_transport.util import xts_result


class TestResultHandlerTest(testbed_dependent_test.TestbedDependentTest):

  def setUp(self):
    super(TestResultHandlerTest, self).setUp()
    self.test_run = ndb_models.TestRun(
        id='test_run_id', request_id='request_id')
    self.test_run.put()

  @mock.patch.object(tfc_client, 'GetLatestFinishedAttempts')
  @mock.patch.object(sql_models, 'GetTestModuleResults')
  @mock.patch.object(sql_models, 'InsertTestResults')
  @mock.patch.object(xts_result, 'TestResults')
  def testStoreTestResults(
      self, mock_results_ctor, mock_insert, mock_get, mock_get_attempts):
    test_results = mock.MagicMock(
        summary=xts_result.Summary(
            passed=12, failed=34, modules_done=56, modules_total=78))
    mock_results_ctor.return_value = test_results
    mock_get_attempts.return_value = [
        api_messages.CommandAttemptMessage(attempt_id='attempt_id')
    ]
    mock_get.return_value = [
        sql_models.TestModuleResult(              id='%d' % i,
            test_run_id='test_run_id',
            attempt_id='attempt_id',
            name='module %d' % i,
            complete=True,
            duration_ms=0,
            passed_tests=1,
            failed_tests=2,
            total_tests=3,
            error_message=None if i < 50 else 'error_message')
        for i in range(100)
    ]

    test_result_handler.StoreTestResults(
        'test_run_id', 'attempt_id', 'test_results_url')

    # Results inserted into DB
    mock_insert.assert_called_with('test_run_id', 'attempt_id', test_results)
    mock_get_attempts.assert_called_with('request_id')
    mock_get.assert_called_with(['attempt_id'])
    # Test run summary updated
    self.test_run = self.test_run.key.get()
    self.assertEqual(300, self.test_run.total_test_count)
    self.assertEqual(200, self.test_run.failed_test_count)
    self.assertEqual(50, self.test_run.failed_test_run_count)

if __name__ == '__main__':
  absltest.main()
