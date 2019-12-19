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

"""MTT event handler integration tests."""
import logging
import uuid

from absl.testing import absltest

from multitest_transport.integration_test import integration_util


class EventHandlerIntegrationTest(integration_util.DockerContainerTest):
  """Tests that execution events get correctly handled."""

  def setUp(self):
    super(EventHandlerIntegrationTest, self).setUp()
    # Schedule test run
    self.run_target = str(uuid.uuid4())
    self.test_run_id = self.container.ScheduleTestRun(self.run_target)['id']
    self.container.WaitForState(self.test_run_id, 'QUEUED')
    # Lease task and start test run
    self.task = self.container.LeaseTask(
        integration_util.DeviceInfo(self.run_target))
    self.container.SubmitCommandEvent(self.task, 'InvocationStarted')
    self.container.WaitForState(self.test_run_id, 'RUNNING')

  def testFatalError(self):
    """Test that fatal errors should stop run and set state to ERROR."""
    self.container.SubmitCommandEvent(self.task, 'ConfigurationError')
    self.container.WaitForState(self.test_run_id, 'ERROR')

  def testError(self):
    """Test that non-fatal errors should trigger an automatic retry."""
    self.container.SubmitCommandEvent(self.task, 'ExecuteFailed')
    self.container.WaitForState(self.test_run_id, 'QUEUED')  # Back to QUEUED
    # Retry attempt can be leased
    retry = self.container.LeaseTask(
        integration_util.DeviceInfo(self.run_target))
    self.assertIsNotNone(retry)
    self.assertNotEqual(self.task['attempt_id'], retry['attempt_id'])

  def testCompleted_success(self):
    """Test that run can be notified of successful completion."""
    self.container.SubmitCommandEvent(
        self.task,
        'InvocationCompleted',
        data={
            'total_test_count': 2,
            'failed_test_count': 0,
        })
    self.container.WaitForState(self.test_run_id, 'COMPLETED')
    # Test run will contain result information
    test_run = self.container.GetTestRun(self.test_run_id)
    self.assertEqual('2', test_run['total_test_count'])
    self.assertEqual('0', test_run['failed_test_count'])

  def testCompleted_failure(self):
    """Test that failed tests will trigger an automatic retry."""
    self.container.SubmitCommandEvent(
        self.task,
        'InvocationCompleted',
        data={
            'total_test_count': 2,
            'failed_test_count': 1,
        })
    self.container.WaitForState(self.test_run_id, 'QUEUED')  # Back to QUEUED
    # Retry attempt can be leased
    retry = self.container.LeaseTask(
        integration_util.DeviceInfo(self.run_target))
    self.assertIsNotNone(retry)
    self.assertNotEqual(self.task['attempt_id'], retry['attempt_id'])
    # Test run will contain result information
    test_run = self.container.GetTestRun(self.test_run_id)
    self.assertEqual('2', test_run['total_test_count'])
    self.assertEqual('1', test_run['failed_test_count'])


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  absltest.main()
