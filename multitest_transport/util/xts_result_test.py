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

"""Tests for xts_result."""
import os

from absl.testing import absltest

from multitest_transport.util import xts_result

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


class XtsResultTest(absltest.TestCase):

  def testSummary(self):
    with open(os.path.join(TEST_DATA_DIR, 'test_result.xml')) as xml_stream:
      test_results = xts_result.TestResults(xml_stream)
      self.assertEqual(
          test_results.summary,
          xts_result.Summary(
              passed=12, failed=34, modules_done=56, modules_total=78))

  def testModules(self):
    with open(os.path.join(TEST_DATA_DIR, 'test_result.xml')) as xml_stream:
      modules = list(xts_result.TestResults(xml_stream))
      self.assertEqual(
          modules[0],
          xts_result.Module(
              name='abi SimpleModule',
              duration_ms=123,
              test_cases=[
                  xts_result.TestCase(
                      name='Passing#test',
                      status=xts_result.TestStatus.PASS,
                  )
              ],
          ))
      self.assertEqual(
          modules[1],
          xts_result.Module(
              name='abi ComplexModule',
              duration_ms=456,
              test_cases=[
                  xts_result.TestCase(
                      name='Failing#test',
                      status=xts_result.TestStatus.FAIL,
                      error_message='Failure message',
                      stack_trace='Failure stacktrace'),
                  xts_result.TestCase(
                      name='Skipped#ignored',
                      status=xts_result.TestStatus.IGNORED,
                  ),
                  xts_result.TestCase(
                      name='Skipped#assumption',
                      status=xts_result.TestStatus.ASSUMPTION_FAILURE,
                      error_message='Assumption failure message',
                      stack_trace='Assumption failure stacktrace'),
              ],
          ))
      self.assertEqual(
          modules[2],
          xts_result.Module(
              name='abi IncompleteModule',
              duration_ms=789,
              error_message='Incomplete module message',
          ))


if __name__ == '__main__':
  absltest.main()
