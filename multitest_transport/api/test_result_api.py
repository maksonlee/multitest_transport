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

"""Test results APIs."""
# Non-standard docstrings are used to generate the API documentation.
import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.models import sql_models
from multitest_transport.util import sql_util
from multitest_transport.util import tfc_client


@base.MTT_API.api_class(resource_name='test_result', path='test_results')
class TestResultApi(remote.Service):
  """Test results API handler."""

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          attempt_id=messages.StringField(1),
          test_run_id=messages.StringField(2),
          max_results=messages.IntegerField(
              3, default=base.DEFAULT_MAX_RESULTS),
          page_token=messages.StringField(4)),
      mtt_messages.TestModuleResultList,
      path='modules', http_method='GET', name='list_modules')
  def ListTestModuleResults(self, request):
    """Fetches a page of test module results, in descending failure count order.

    Parameters:
      attempt_id: Test run attempt ID
      test_run_id: Test run ID (used if attempt_id not provided)
      max_results: Maximum number of modules to return
      page_token: Token for pagination
    """
    if request.attempt_id:
      # Use attempt_id directly if provided
      attempt_id = request.attempt_id
    elif request.test_run_id:
      # Determine attempt_id from test_run_id (latest finished attempt)
      test_run_id = request.test_run_id
      test_run = ndb_models.TestRun.get_by_id(test_run_id)
      if not test_run:
        raise endpoints.NotFoundException('Test run %s not found' % test_run_id)
      if not test_run.request_id:
        return mtt_messages.TestModuleResultList(
            attempt_info='Test run %s not started' % test_run_id)
      latest_attempt = tfc_client.GetLatestFinishedAttempt(test_run.request_id)
      if not latest_attempt:
        return mtt_messages.TestModuleResultList(
            attempt_info='Test run %s has no completed attempts' % test_run_id)
      attempt_id = latest_attempt.attempt_id
    else:
      # Invalid request (test_run_id and attempt_id not provided)
      raise endpoints.BadRequestException('Test run ID or attempt ID required')

    with sql_models.db.Session() as session:
      # Initialize query (ordered by failed test counts)
      query = session.query(sql_models.TestModuleResult)
      query = query.order_by(sql_models.TestModuleResult.failed_tests.desc(),
                             sql_models.TestModuleResult.id)
      query = query.filter_by(attempt_id=attempt_id)
      # Apply page token (<last failed test count>:<last id>)
      if request.page_token:
        max_failed_tests, min_id = request.page_token.split(':', 1)
        query = query.filter(sql_util.OR(
            sql_models.TestModuleResult.failed_tests < max_failed_tests,
            sql_util.AND(
                sql_models.TestModuleResult.failed_tests == max_failed_tests,
                sql_models.TestModuleResult.id > min_id)))
      # Fetch at most N + 1 results
      if request.max_results and request.max_results > 0:
        query = query.limit(request.max_results + 1)
      modules = query.all()

    # Generate next page token and response
    next_page_token = None
    if request.max_results and 0 < request.max_results < len(modules):
      modules = modules[:-1]
      last_module = modules[-1]
      next_page_token = '%d:%s' % (last_module.failed_tests, last_module.id)
    results = mtt_messages.ConvertList(modules, mtt_messages.TestModuleResult)
    return mtt_messages.TestModuleResultList(
        results=results,
        next_page_token=next_page_token,
        attempt_info='Test results from attempt %s' % attempt_id)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          module_id=messages.StringField(1, required=True),
          max_results=messages.IntegerField(
              2, default=base.DEFAULT_MAX_RESULTS),
          page_token=messages.StringField(3)),
      mtt_messages.TestCaseResultList,
      path='modules/{module_id}/test_cases',
      http_method='GET', name='list_test_cases')
  def ListTestCaseResults(self, request):
    """Fetches a page of test case results.

    Parameters:
      module_id: Test module ID
      max_results: Maximum number of test results to return
      page_token: Token for pagination
    """
    with sql_models.db.Session() as session:
      # Find parent module
      module = session.query(sql_models.TestModuleResult).get(request.module_id)
      if not module:
        raise endpoints.NotFoundException(
            'Module %s not found' % request.module_id)
      # Initialize query (ordered by insertion order)
      query = session.query(sql_models.TestCaseResult)
      query = query.order_by(sql_models.TestCaseResult.id).with_parent(module)
      # Apply page token (<last id>)
      if request.page_token:
        query = query.filter(
            sql_models.TestCaseResult.id > int(request.page_token))
      # Fetch at most N + 1 results
      if request.max_results and request.max_results > 0:
        query = query.limit(request.max_results + 1)
      test_cases = query.all()

    # Generate next page token and response
    next_page_token = None
    if request.max_results and 0 < request.max_results < len(test_cases):
      test_cases = test_cases[:-1]
      next_page_token = str(test_cases[-1].id)
    results = mtt_messages.ConvertList(test_cases, mtt_messages.TestCaseResult)
    return mtt_messages.TestCaseResultList(
        results=results, next_page_token=next_page_token)
