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

"""MTT test scheduler integration tests."""
import logging
import uuid

from absl.testing import absltest

from multitest_transport.integration_test import integration_util


class TestSchedulerIntegrationTest(integration_util.DockerContainerTest):
  """Tests that test run requests get correctly converted into tasks."""

  def testScheduleRun(self):
    device_serial = str(uuid.uuid4())
    # Schedule test run
    test_run_id = self.container.ScheduleTestRun(device_serial)['id']
    self.container.WaitForState(test_run_id, 'QUEUED')
    # Should be able to lease with matching run target
    task = self.container.LeaseTask(integration_util.DeviceInfo(device_serial))
    self.assertIsNotNone(task)
    self.assertEqual([device_serial], task['device_serials'])
    self.assertEqual(
        'util/timewaster --invocation-data mtt=1', task['command_line'])

  def testScheduleRun_extraArgs(self):
    device_serial = str(uuid.uuid4())
    # Schedule test run
    test_run = self.container.ScheduleTestRun(
        device_serial, extra_args='extra_args')
    test_run_id = test_run['id']
    self.container.WaitForState(test_run_id, 'QUEUED')
    # Task should have extra command line arguments
    task = self.container.LeaseTask(integration_util.DeviceInfo(device_serial))
    self.assertEqual(
        'util/timewaster extra_args --invocation-data mtt=1',
        task['command_line'])

  def testCancelRun(self):
    device_serial = str(uuid.uuid4())
    # Schedule test run and cancel it
    test_run_id = self.container.ScheduleTestRun(device_serial)['id']
    self.container.WaitForState(test_run_id, 'QUEUED')
    self.container.CancelTestRun(test_run_id)
    # Can't lease with matching run target, task was cancelled
    task = self.container.LeaseTask(integration_util.DeviceInfo(device_serial))
    self.assertIsNone(task)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  absltest.main()
