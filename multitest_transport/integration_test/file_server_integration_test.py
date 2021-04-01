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

"""MTT file server integration tests."""
import logging
import os
import uuid

from absl.testing import absltest
import requests

from multitest_transport.integration_test import integration_util

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


class FileServerIntegrationTest(integration_util.DockerContainerTest):
  """"Tests that MTT can access files using the file server."""

  def setUp(self):
    super(FileServerIntegrationTest, self).setUp()
    # Upload test resource to local file store
    test_resource_file = os.path.join(TEST_DATA_DIR, 'android-cts.zip')
    self.container.UploadFile(test_resource_file,
                              'local_file_store/android-cts.zip')
    # Schedule test run with test resource
    self.device_serial = str(uuid.uuid4())
    self.test_run_id = self.container.ScheduleTestRun(
        self.device_serial,
        test_id='android.cts.9_0.arm',
        test_resource_objs=[{
            'name': 'android-cts.zip',
            'url': 'file:///data/local_file_store/android-cts.zip',
        }])['id']
    # Lease task, allowing additional time for resource download
    self.container.WaitForState(self.test_run_id, 'QUEUED', timeout=60)
    self.task = self.container.LeaseTask(
        integration_util.DeviceInfo(self.device_serial))

  def testStreamLogs(self):
    """Tests that logs can be read using the file server."""
    # Write to log file
    log_file = os.path.join(TEST_DATA_DIR, 'stdout.txt')
    self.container.CopyFile(
        log_file, '/data/tmp/%s/logs/stdout.txt' % self.task['attempt_id'])
    # Verify that log file can be read
    response = requests.get(
        '%s/test_runs/%s/output' %
        (self.container.mtt_api_url, self.test_run_id),
        params={
            'attempt_id': self.task['attempt_id'],
            'path': 'logs/stdout.txt'
        })
    response.raise_for_status()
    output = response.json()
    self.assertEqual('0', output['offset'])
    self.assertEqual('19', output['length'])
    self.assertEqual(['hello\n', 'world\n', 'goodbye'], output['lines'])

  def testTestPackageInfo(self):
    """Tests that test package information is parsed after download."""
    test_run = self.container.GetTestRun(self.test_run_id)
    test_package = test_run['test_package_info']
    self.assertEqual('1234567', test_package['build_number'])
    self.assertEqual('CTS', test_package['name'])
    self.assertEqual('10.0', test_package['version'])

  def testTestResult(self):
    """Tests that the test result file can be parsed on completion."""
    # Write test results file
    result_file = os.path.join(TEST_DATA_DIR, 'test_result.xml')
    output_file = (
        '/data/app_default_bucket/test_runs/%s/output/%s/%s/test_result.xml' %
        (self.test_run_id, self.task['command_id'], self.task['attempt_id']))
    self.container.CopyFile(result_file, output_file)
    # Verify that test results were parsed on completion
    self.container.SubmitCommandEvent(self.task, 'InvocationCompleted')
    self.container.WaitForState(self.test_run_id, 'COMPLETED')
    test_run = self.container.GetTestRun(self.test_run_id)
    self.assertEqual('34', test_run['failed_test_count'])
    self.assertEqual('22', test_run['failed_test_run_count'])
    self.assertEqual('46', test_run['total_test_count'])


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  absltest.main()
