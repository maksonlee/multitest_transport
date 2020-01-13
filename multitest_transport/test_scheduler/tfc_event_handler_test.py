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

"""Unit tests for tfc_event_handler module."""

import datetime

import mock
from tradefed_cluster import api_messages
from tradefed_cluster import common

from google.appengine.ext import deferred
from google.appengine.ext import testbed
from absl.testing import absltest

from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.test_scheduler import test_output_uploader
from multitest_transport.test_scheduler import tfc_event_handler
from multitest_transport.util import analytics
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client
from multitest_transport.util import webhook_util


class TfcEventHandlerTest(absltest.TestCase):

  def setUp(self):
    super(TfcEventHandlerTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.mock_test = ndb_models.Test(
        name='test', command='command', result_file='result_file')
    self.mock_test.put()
    self.mock_test_plan = ndb_models.TestPlan(name='plan')
    self.mock_test_plan.put()
    self.mock_test_run = ndb_models.TestRun(
        test_plan_key=self.mock_test_plan.key,
        test_run_config=ndb_models.TestRunConfig(
            test_key=self.mock_test.key, run_target='run_target'),
        test=self.mock_test,
        request_id='request_id',
        state=ndb_models.TestRunState.UNKNOWN)
    self.mock_test_run.put()

  def tearDown(self):
    super(TfcEventHandlerTest, self).tearDown()
    self.testbed.deactivate()

  def CreateMockRequestEvent(self, timedelta, state=None):
    """Create a dummy TFC request change event."""
    return api_messages.RequestEventMessage(
        type=common.ObjectEventType.REQUEST_STATE_CHANGED,
        request_id=self.mock_test_run.request_id,
        new_state=state or ndb_models.TestRunState.UNKNOWN,
        event_time=self.mock_test_run.update_time + timedelta)

  def CreateMockCommandAttemptEvent(self, timedelta, state=None, serials=None):
    """Create a dummy TFC command attempt change event."""
    return api_messages.CommandAttemptEventMessage(
        type=common.ObjectEventType.COMMAND_ATTEMPT_STATE_CHANGED,
        attempt=api_messages.CommandAttemptMessage(
            request_id=self.mock_test_run.request_id,
            device_serials=serials or [],
            state=state or common.CommandState.UNKNOWN),
        event_time=self.mock_test_run.update_time + timedelta)

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  def testProcessRequestEvent(self, mock_after_test):
    # state changed to RUNNING one hour after last update
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=1), state=api_messages.RequestState.RUNNING)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated, but post-run actions not executed
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.RUNNING, self.mock_test_run.state)
    mock_after_test.assert_not_called()

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  def testProcessRequestEvent_skipOldEvent(self, mock_after_test):
    # state changed one hour BEFORE last update
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=-1), state=api_messages.RequestState.RUNNING)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information not updated and post-run actions not executed
    self.assertNotEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.UNKNOWN, self.mock_test_run.state)
    mock_after_test.assert_not_called()

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  def testProcessRequestEvent_completed(self, mock_after_test):
    # state changed to COMPLETED from UNKNOWN
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=1), state=api_messages.RequestState.COMPLETED)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated and post-run actions executed
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.COMPLETED,
                     self.mock_test_run.state)
    mock_after_test.assert_called_with(self.mock_test_run)

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  def testProcessRequestEvent_alreadyFinal(self, mock_after_test):
    # test run state already final and post-run handlers already executed
    self.mock_test_run.state = ndb_models.TestRunState.ERROR
    self.mock_test_run.is_finalized = True
    self.mock_test_run.put()

    # state changed to COMPLETED
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=1), state=api_messages.RequestState.COMPLETED)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated, but state preserved and post-run skipped
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.ERROR, self.mock_test_run.state)
    mock_after_test.assert_not_called()

  @mock.patch.object(tfc_client, 'GetDeviceInfo')
  def testProcessCommandAttemptEvent(self, mock_get_device):
    # attempt changed one hour after last update
    mock_event = self.CreateMockCommandAttemptEvent(
        datetime.timedelta(hours=1), serials=['SERIAL'])
    # device information with build ID retrieved
    mock_get_device.return_value = api_messages.DeviceInfo(
        device_serial='SERIAL', build_id='TEST')

    tfc_event_handler.ProcessCommandAttemptEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    expected_device = ndb_models.TestDeviceInfo(
        device_serial='SERIAL', build_id='TEST')
    self.assertEqual(self.mock_test_run.test_devices, [expected_device])

  @mock.patch.object(tfc_client, 'GetDeviceInfo')
  def testProcessCommandAttemptEvent_skipOldEvent(self, mock_get_device):
    # attempt changed one hour BEFORE last update
    mock_event = self.CreateMockCommandAttemptEvent(
        datetime.timedelta(hours=-1), serials=['SERIAL'])

    tfc_event_handler.ProcessCommandAttemptEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information not updated
    self.assertNotEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(self.mock_test_run.test_devices, [])
    mock_get_device.assert_not_called()

  @mock.patch.object(file_util, 'GetXtsTestResultSummary')
  def testProcessCommandAttemptEvent_summary(self, mock_get_summary):
    # COMPLETED attempt, will attempt to update test result counts
    mock_event = self.CreateMockCommandAttemptEvent(
        datetime.timedelta(hours=1), state=common.CommandState.COMPLETED)
    mock_get_summary.return_value = file_util.XtsTestResultSummary(
        passed=12, failed=34, modules_done=56, modules_total=78)

    tfc_event_handler.ProcessCommandAttemptEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(12 + 34, self.mock_test_run.total_test_count)
    self.assertEqual(34, self.mock_test_run.failed_test_count)
    self.assertEqual(78 - 56, self.mock_test_run.failed_test_run_count)

  @mock.patch.object(deferred, 'defer')
  @mock.patch.object(tfc_client, 'GetTestContext')
  @mock.patch.object(tfc_client, 'GetRequest')
  def testAfterTestRunHandler(self, mock_get_request, mock_get_test_context,
                              mock_defer):
    # configure mock TFC request
    request_id = self.mock_test_run.request_id
    mock_request = api_messages.RequestMessage(id=request_id)
    mock_request.commands.append(api_messages.CommandMessage(id='bar'))
    mock_get_request.return_value = mock_request

    # configure mock TFC test context
    mock_test_context = api_messages.TestContext(
        command_line='command_line',
        env_vars=[api_messages.KeyValuePair(key='key', value='value')],
        test_resources=[
            api_messages.TestResource(url='url', name='name', path='path')
        ])
    mock_get_test_context.return_value = mock_test_context
    expected_test_context = ndb_models.TestContextObj(
        command_line='command_line',
        env_vars=[ndb_models.NameValuePair(name='key', value='value')],
        test_resources=[
            ndb_models.TestResourceObj(url='url', name='name')
        ])

    # add a webhook to invoke
    mock_webhook = ndb_models.Webhook(url='url')
    self.mock_test_run.after_webhooks.append(mock_webhook)

    # add output upload URL
    mock_upload_config = ndb_models.TestOutputUploadConfig(url='url')
    self.mock_test_run.test_output_upload_configs = [mock_upload_config]

    tfc_event_handler._AfterTestRunHandler(self.mock_test_run)

    # test run updated, webhooks invoked, output uploaded, and metrics tracked
    mock_get_request.assert_called_with(request_id)
    mock_get_test_context.assert_called_with(request_id, 'bar')
    self.assertEqual(expected_test_context,
                     self.mock_test_run.next_test_context)
    mock_defer.assert_has_calls([
        mock.call(tfc_event_handler._InvokeWebhooks,
                  self.mock_test_run.key.id(), _transactional=True),
        mock.call(test_run_hook.ExecuteHooks, self.mock_test_run.key.id(),
                  ndb_models.TestRunPhase.AFTER_RUN, _transactional=True),
        mock.call(test_output_uploader.ScheduleUploadJobs,
                  self.mock_test_run.key.id(), _transactional=True),
        mock.call(tfc_event_handler._TrackTestRun,
                  self.mock_test_run.key.id(), _transactional=True),
    ])

  @mock.patch.object(webhook_util, 'InvokeWebhook')
  def testInvokeWebhooks(self, mock_invoke):
    # add a webhook to invoke
    mock_webhook = ndb_models.Webhook(url='url')
    self.mock_test_run.after_webhooks.append(mock_webhook)

    tfc_event_handler._InvokeWebhooks(self.mock_test_run.key.id())
    mock_invoke.assert_called_with(mock_webhook,
                                   context=self.mock_test_run.GetContext())

  @mock.patch.object(analytics, 'Log')
  @mock.patch.object(tfc_client, 'GetRequest')
  @mock.patch.object(tfc_event_handler, '_GetCurrentTime')
  def testTrackTestRun(self, mock_time, mock_get_request, mock_log):
    # mock current time
    now = datetime.datetime.now()
    mock_time.return_value = now

    # configure mock TFC request with 1 attempt and 2 devices
    request_id = self.mock_test_run.request_id
    mock_request = api_messages.RequestMessage(id=request_id)
    mock_request.command_attempts.append(
        api_messages.CommandAttemptMessage(device_serials=['1', '2']))
    mock_get_request.return_value = mock_request

    # update mock test run
    self.mock_test_run.test_package_info = ndb_models.TestPackageInfo(
        name='name', version='version')
    self.mock_test_run.state = ndb_models.TestRunState.COMPLETED
    self.mock_test_run.create_time = now - datetime.timedelta(seconds=123)
    self.mock_test_run.failed_test_run_count = 1
    self.mock_test_run.total_test_count = 2
    self.mock_test_run.failed_test_count = 3

    # check that right data was logged
    tfc_event_handler._TrackTestRun(self.mock_test_run.key.id())
    mock_log.assert_called_with(analytics.TEST_RUN_CATEGORY,
                                analytics.END_ACTION,
                                test_name='name',
                                test_version='version',
                                state=ndb_models.TestRunState.COMPLETED,
                                is_rerun=False,
                                duration_seconds=123,
                                device_count=2,
                                attempt_count=1,
                                failed_module_count=1,
                                test_count=2,
                                failed_test_count=3)


if __name__ == '__main__':
  absltest.main()
