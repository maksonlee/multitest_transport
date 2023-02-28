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

"""Handles storing test result information."""
import logging
import time

from tradefed_cluster.services import task_scheduler
from tradefed_cluster.util import ndb_shim as ndb


from multitest_transport.models import ndb_models
from multitest_transport.models import sql_models
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client
from multitest_transport.util import xts_result


def StoreTestResults(test_run_id, attempt_id, test_results_url):
  """Parses and stores test results for a test run and attempt."""
  start_time = time.time()
  try:
    with file_util.OpenFile(test_results_url) as test_results_stream:
      test_results = xts_result.TestResults(test_results_stream)

      # Store test results in DB
      sql_models.InsertTestResults(test_run_id, attempt_id, test_results)
      logging.info('Stored test results from %s (took %.1fs)',
                   attempt_id, time.time() - start_time)
  except FileNotFoundError:
    logging.warning('Test result file not found: %s', test_results_url)
  task_scheduler.AddCallableTask(UpdateTestRunSummary, test_run_id)


@ndb.transactional()
def UpdateTestRunSummary(test_run_id):
  """Update test run numbers."""
  logging.info('Updating summary for test run %s', test_run_id)
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  test_run.total_test_count = 0
  test_run.failed_test_count = 0
  test_run.failed_test_run_count = 0
  attempts = tfc_client.GetLatestFinishedAttempts(test_run.request_id)
  modules = sql_models.GetTestModuleResults(
      [attempt.attempt_id for attempt in attempts])
  for module in modules:
    test_run.total_test_count += module.total_tests
    test_run.failed_test_count += module.failed_tests
    if module.error_message:
      test_run.failed_test_run_count += 1
  test_run.put()
