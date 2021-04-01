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

"""Tests for test_result_api."""
from absl.testing import absltest
import mock
from protorpc import protojson

from tradefed_cluster.api_messages import CommandState

from multitest_transport.api import api_test_util
from multitest_transport.api import test_result_api
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.models import sql_models
from multitest_transport.util import tfc_client
from multitest_transport.util import xts_result


class TestResultApiTest(api_test_util.TestCase):

  def setUp(self):
    super(TestResultApiTest, self).setUp(test_result_api.TestResultApi)
    sql_models.db.uri = 'sqlite:///:memory:'
    sql_models.db.CreateTables()
    # Create two modules with two test cases
    with sql_models.db.Session() as session:
      session.add_all([
          sql_models.TestModuleResult(
              id='module_1', attempt_id='attempt_1', name='module_2',
              passed_tests=0, failed_tests=0, total_tests=0),
          sql_models.TestModuleResult(
              id='module_2', attempt_id='attempt_1', name='module_1',
              passed_tests=1, failed_tests=1, total_tests=2,
              test_cases=[
                  sql_models.TestCaseResult(
                      name='test_case_1', status=xts_result.TestStatus.PASS),
                  sql_models.TestCaseResult(
                      name='test_case_2', status=xts_result.TestStatus.PASS),
              ]),
      ])

  def tearDown(self):
    sql_models.db.DropTables()
    super(TestResultApiTest, self).tearDown()

  def testListTestModuleResults(self):
    """Tests that module results can be fetched."""
    path = 'modules?attempt_id=attempt_1'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    result_list = protojson.decode_message(
        messages.TestModuleResultList, response.body)
    # Both modules returned, ordered by failure counts, with no next page
    self.assertLen(result_list.results, 2)
    module_ids = [r.id for r in result_list.results]
    self.assertEqual(['module_2', 'module_1'], module_ids)
    self.assertIsNone(result_list.next_page_token)

  def testListTestModuleResults_pagination(self):
    """Tests that module results can be fetched with pagination."""
    path = 'modules?attempt_id=attempt_1&max_results=1'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    first_page = protojson.decode_message(
        messages.TestModuleResultList, response.body)
    # First page has one result and a page token
    self.assertLen(first_page.results, 1)
    self.assertEqual('module_2', first_page.results[0].id)
    self.assertEqual('1:module_2', first_page.next_page_token)

    path = 'modules?attempt_id=attempt_1&max_results=1&page_token=1:module_2'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    second_page = protojson.decode_message(
        messages.TestModuleResultList, response.body)
    # Second page has one result and no page token
    self.assertLen(second_page.results, 1)
    self.assertEqual('module_1', second_page.results[0].id)
    self.assertIsNone(second_page.next_page_token)

  @mock.patch.object(tfc_client, 'GetRequest')
  def testListTestModuleResults_testRunId(self, mock_get_request):
    """Tests that module results can be fetched using a test run ID."""
    # Create test run with three attempts (latest is still RUNNING)
    ndb_models.TestRun(id='test_run_id', request_id='request_id').put()
    first_attempt = mock.MagicMock(
        attempt_id='INVALID', state=CommandState.COMPLETED)
    second_attempt = mock.MagicMock(
        attempt_id='attempt_1', state=CommandState.COMPLETED)
    third_attempt = mock.MagicMock(
        attempt_id='INVALID', state=CommandState.RUNNING)
    request = mock.MagicMock(
        command_attempts=[first_attempt, second_attempt, third_attempt])
    mock_get_request.return_value = request

    # Results are fetched for the latest completed attempt
    path = 'modules?test_run_id=test_run_id'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    result_list = protojson.decode_message(
        messages.TestModuleResultList, response.body)
    self.assertLen(result_list.results, 2)
    module_ids = [r.id for r in result_list.results]
    self.assertEqual(['module_2', 'module_1'], module_ids)
    self.assertIsNone(result_list.next_page_token)

  def testListTestModuleResults_testRunNotFound(self):
    """Tests that an error is returned if the test run is not found."""
    path = 'modules?test_run_id=UNKNOWN'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path,
                            expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testListTestModuleResults_missingAttemptId(self):
    """Tests that an error is returned if no attempt ID provided."""
    response = self.app.get('/_ah/api/mtt/v1/test_results/modules',
                            expect_errors=True)
    self.assertEqual('400 Bad Request', response.status)

  def testListTestCaseResults(self):
    """Tests that test case results can be fetched."""
    path = 'modules/module_2/test_cases'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    result_list = protojson.decode_message(
        messages.TestCaseResultList, response.body)
    # Both test cases returned, ordered by ID, with no next page
    self.assertLen(result_list.results, 2)
    test_case_names = [r.name for r in result_list.results]
    self.assertEqual(['test_case_1', 'test_case_2'], test_case_names)
    self.assertIsNone(result_list.next_page_token)

  def testListTestCaseResults_pagination(self):
    """Tests that test case results can be fetched with pagination."""
    path = 'modules/module_2/test_cases?max_results=1'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    first_page = protojson.decode_message(
        messages.TestCaseResultList, response.body)
    # First page has one result and a page token
    self.assertLen(first_page.results, 1)
    self.assertEqual('test_case_1', first_page.results[0].name)
    self.assertEqual('1', first_page.next_page_token)

    path = 'modules/module_2/test_cases?max_results=1&page_token=1'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path)
    self.assertEqual('200 OK', response.status)
    second_page = protojson.decode_message(
        messages.TestCaseResultList, response.body)
    # Second page has one result and no page token
    self.assertLen(second_page.results, 1)
    self.assertEqual('test_case_2', second_page.results[0].name)
    self.assertIsNone(second_page.next_page_token)

  def testListTestCaseResults_moduleNotFound(self):
    """Tests that an error is returned if the module is not found."""
    path = 'modules/UNKNOWN/test_cases'
    response = self.app.get('/_ah/api/mtt/v1/test_results/' + path,
                            expect_errors=True)
    self.assertEqual('404 Not Found', response.status)


if __name__ == '__main__':
  absltest.main()
