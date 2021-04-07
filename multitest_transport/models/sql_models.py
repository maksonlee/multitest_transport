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

"""SQL-based model classes (for the test results DB)."""
import uuid

import sqlalchemy as sa

from multitest_transport.util import env
from multitest_transport.util import sql_util
from multitest_transport.util import xts_result

# Default number of test result rows to insert at a time
RESULTS_BATCH_SIZE = 100000

# Database manager singleton
db = sql_util.Database(uri=env.SQL_DATABASE_URI)


class TestModuleResult(db.Model):
  """Test module containing multiple test case results."""
  __tablename__ = 'test_module_result'
  __table_args__ = (
      {'mysql_row_format': 'compressed'},
  )

  id = sa.Column(sa.String(36), primary_key=True)
  attempt_id = sa.Column(sa.String(36), nullable=False, index=True)
  name = sa.Column(sa.String(255), nullable=False)
  duration_ms = sa.Column(sa.Integer, nullable=False)
  complete = sa.Column(sa.Boolean, nullable=False)
  test_cases = sa.orm.relationship(
      'TestCaseResult', backref='module', lazy=True)
  passed_tests = sa.Column(sa.Integer, nullable=False)
  failed_tests = sa.Column(sa.Integer, nullable=False)
  total_tests = sa.Column(sa.Integer, nullable=False)
  error_message = sa.Column(sa.Text)


class TestCaseResult(db.Model):
  """Test case with result and debugging information."""
  __tablename__ = 'test_case_result'
  __table_args__ = (
      {'mysql_row_format': 'compressed'},
  )

  id = sa.Column(sa.Integer, primary_key=True)
  module_id = sa.Column(
      sa.String(36), sa.ForeignKey('test_module_result.id'), nullable=False)
  name = sa.Column(sa.String(255), nullable=False)
  status = sa.Column(sql_util.IntEnum(xts_result.TestStatus), nullable=False)
  error_message = sa.Column(sa.Text)
  stack_trace = sa.Column(sa.Text)


def InsertTestResults(attempt_id, test_results, batch_size=RESULTS_BATCH_SIZE):
  """Efficiently inserts large test results into the database.

  Extracts raw test case data and executes batch inserts with pre-populated IDs.
  This is significantly (10x) faster than using the ORM and letting the database
  auto-generate IDs.

  Args:
    attempt_id: attempt ID to inject in modules
    test_results: xts_result.TestResults
    batch_size: number of test cases to insert at a time
  """
  with db.Session() as session:
    test_case_data = []
    # Iterate over modules, convert to entities with pre-populated IDs
    for module in test_results:
      module_entity = TestModuleResult(
          id=str(uuid.uuid4()),
          attempt_id=attempt_id,
          name=module.name,
          complete=module.complete,
          duration_ms=module.duration_ms,
          passed_tests=0,
          failed_tests=0,
          total_tests=0,
          error_message=module.error_message)
      session.add(module_entity)

      # Iterate over test cases, convert to dicts, and set module ID
      for test_case in module.test_cases:
        test_case_data.append(dict(
            module_id=module_entity.id,
            name=test_case.name,
            status=test_case.status,
            error_message=test_case.error_message,
            stack_trace=test_case.stack_trace,
        ))
        # Track test case statistics
        module_entity.total_tests += 1
        if test_case.status == xts_result.TestStatus.PASS:
          module_entity.passed_tests += 1
        elif test_case.status == xts_result.TestStatus.FAIL:
          module_entity.failed_tests += 1
        # Bulk insert raw test case data in batches to reduce memory usage
        if len(test_case_data) >= batch_size:
          session.commit()  # Persist modules (ensure foreign keys are valid)
          session.bulk_insert_mappings(TestCaseResult, test_case_data)
          test_case_data = []

      # Ensure test case statistics will be updated if necessary
      session.add(module_entity)

    # Persist any remaining modules and test cases
    session.commit()
    session.bulk_insert_mappings(TestCaseResult, test_case_data)
