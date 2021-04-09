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

from tradefed_cluster.util import ndb_shim as ndb

from multitest_transport.models import ndb_models
from multitest_transport.models import sql_models
from multitest_transport.util import file_util
from multitest_transport.util import xts_result


def StoreTestResults(test_run_id, attempt_id, test_results_url):
  """Parses and stores test results for a test run and attempt."""
  start_time = time.time()
  with file_util.OpenFile(test_results_url) as test_results_stream:
    try:
      test_results = xts_result.TestResults(test_results_stream)
    except Exception:        logging.exception('Failed to parse test results')
      return

    # Update test run summary
    def _UpdateSummaryTxn():
      summary = test_results.summary
      if not summary:
        return
      test_run = ndb_models.TestRun.get_by_id(test_run_id)
      if not test_run:
        return
      test_run.total_test_count = summary.passed + summary.failed
      test_run.failed_test_count = summary.failed
      test_run.failed_test_run_count = (
          summary.modules_total - summary.modules_done)
      test_run.put()
    ndb.transaction(_UpdateSummaryTxn)

    # Store test results in DB
    try:
      sql_models.InsertTestResults(test_run_id, attempt_id, test_results)
    except Exception:        logging.exception('Failed to store test results')
  logging.info('Stored test results from %s (took %.1fs)',
               attempt_id, time.time() - start_time)
