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
from unittest import mock

from absl.testing import absltest
from tradefed_cluster import api_messages
from tradefed_cluster import common
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.services import task_scheduler
from tradefed_cluster.util import ndb_shim as ndb


from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.test_scheduler import tfc_event_handler
from multitest_transport.test_scheduler import test_result_handler
from multitest_transport.util import analytics
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client


class TfcEventHandlerTest(testbed_dependent_test.TestbedDependentTest):

  def setUp(self):
    super(TfcEventHandlerTest, self).setUp()
    self.mock_test = ndb_models.Test(
        name='test', command='command', result_file='result_file')
    self.mock_test.put()
    self.mock_test_plan = ndb_models.TestPlan(name='plan')
    self.mock_test_plan.put()
    self.mock_test_run = ndb_models.TestRun(
        test_plan_key=self.mock_test_plan.key,
        test_run_config=ndb_models.TestRunConfig(
            test_key=self.mock_test.key,
            run_target='run_target',
            cluster='cluster',
            command='mock test run command',
            retry_command='mock test run retry command'),
        test=self.mock_test,
        request_id='request_id',
        state=ndb_models.TestRunState.UNKNOWN)
    self.mock_test_run.put()

  def CreateMockRequestEvent(self, timedelta, state=None):
    """Create a placeholder TFC request change event."""
    return api_messages.RequestEventMessage(
        type=common.ObjectEventType.REQUEST_STATE_CHANGED,
        request_id=self.mock_test_run.request_id,
        new_state=state or ndb_models.TestRunState.UNKNOWN,
        event_time=self.mock_test_run.update_time + timedelta)

  def CreateMockCommandAttemptEvent(self, timedelta, state=None, serials=None):
    """Create a placeholder TFC command attempt change event."""
    return api_messages.CommandAttemptEventMessage(
        type=common.ObjectEventType.COMMAND_ATTEMPT_STATE_CHANGED,
        attempt=api_messages.CommandAttemptMessage(
            attempt_id='attempt_id',
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
    self.mock_test_run.request_event_time = datetime.datetime.utcnow()
    self.mock_test_run.put()
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=-1), state=api_messages.RequestState.RUNNING)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information not updated and post-run actions not executed
    self.assertNotEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.UNKNOWN, self.mock_test_run.state)
    mock_after_test.assert_not_called()

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  @mock.patch.object(test_result_handler, 'UpdateTestRunSummary')
  def testProcessRequestEvent_completed(
      self, mock_update_summary, mock_after_test):
    # state changed to COMPLETED from UNKNOWN
    mock_event = self.CreateMockRequestEvent(
        datetime.timedelta(hours=1), state=api_messages.RequestState.COMPLETED)

    tfc_event_handler.ProcessRequestEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information updated and post-run actions executed
    self.assertEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(ndb_models.TestRunState.COMPLETED,
                     self.mock_test_run.state)
    mock_update_summary.assert_called_once_with(self.mock_test_run.key.id())
    mock_after_test.assert_called_with(self.mock_test_run)

  @mock.patch.object(tfc_event_handler, '_AfterTestRunHandler')
  @mock.patch.object(test_result_handler, 'UpdateTestRunSummary')
  def testProcessRequestEvent_alreadyFinal(
      self, mock_update_summary, mock_after_test):
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
    mock_update_summary.assert_called_once_with(self.mock_test_run.key.id())
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
    self.assertEqual([d.to_dict() for d in self.mock_test_run.test_devices],
                     [expected_device.to_dict()])

  @mock.patch.object(tfc_client, 'GetDeviceInfo')
  def testProcessCommandAttemptEvent_skipOldEvent(self, mock_get_device):
    # attempt changed one hour BEFORE last update
    self.mock_test_run.attempt_event_time = datetime.datetime.utcnow()
    self.mock_test_run.put()
    mock_event = self.CreateMockCommandAttemptEvent(
        datetime.timedelta(hours=-1), serials=['SERIAL'])

    tfc_event_handler.ProcessCommandAttemptEvent(mock_event)
    self.mock_test_run = self.mock_test_run.key.get()

    # test run information not updated
    self.assertNotEqual(mock_event.event_time, self.mock_test_run.update_time)
    self.assertEqual(self.mock_test_run.test_devices, [])
    mock_get_device.assert_not_called()

  @mock.patch.object(task_scheduler, 'AddCallableTask')
  @mock.patch.object(file_util, 'GetResultUrl')
  def testProcessCommandAttemptEvent_final(self, mock_get_result_url,
                                           mock_add_task):
    # COMPLETED attempt, will attempt to store test results
    mock_event = self.CreateMockCommandAttemptEvent(
        datetime.timedelta(hours=1), state=common.CommandState.COMPLETED)
    mock_get_result_url.return_value = 'test_results_url'

    tfc_event_handler.ProcessCommandAttemptEvent(mock_event)

    # test results stored and after attempt hooks executed
    mock_add_task.assert_has_calls([
        mock.call(test_result_handler.StoreTestResults,
                  self.mock_test_run.key.id(), 'attempt_id', 'test_results_url',
                  _transactional=True),
        mock.call(test_run_hook.ExecuteHooks, self.mock_test_run.key.id(),
                  ndb_models.TestRunPhase.AFTER_ATTEMPT,
                  attempt_id='attempt_id', _transactional=True),
    ])

  @mock.patch.object(task_scheduler, 'AddCallableTask')
  @mock.patch.object(tfc_client, 'GetTestContext')
  @mock.patch.object(tfc_client, 'GetRequest')
  def testAfterTestRunHandler(self, mock_get_request, mock_get_test_context,
                              mock_add_task):
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
            api_messages.TestResource(
                url='url', name='name', path='path', decompress=True,
                decompress_dir='dir',
                params=api_messages.TestResourceParameters(
                    decompress_files=['file'])),
            api_messages.TestResource(url='url2', name='name2', path='path2')
        ])
    mock_get_test_context.return_value = mock_test_context
    expected_test_context = ndb_models.TestContextObj(
        command_line='command_line',
        env_vars=[ndb_models.NameValuePair(name='key', value='value')],
        test_resources=[
            ndb_models.TestResourceObj(
                url='url', name='name', decompress=True, decompress_dir='dir',
                params=ndb_models.TestResourceParameters(
                    decompress_files=['file'])),
            ndb_models.TestResourceObj(url='url2', name='name2')
        ])

    tfc_event_handler._AfterTestRunHandler(self.mock_test_run)

    # test run updated, run hooks invoked, output uploaded, and metrics tracked
    mock_get_request.assert_called_with(request_id)
    mock_get_test_context.assert_called_with(request_id, 'bar')
    self.assertEqual(expected_test_context,
                     self.mock_test_run.next_test_context)
    mock_add_task.assert_has_calls([
        mock.call(test_run_hook.ExecuteHooks, self.mock_test_run.key.id(),
                  ndb_models.TestRunPhase.AFTER_RUN, _transactional=True),
        mock.call(tfc_event_handler._TrackTestRun,
                  self.mock_test_run.key.id(), _transactional=True),
    ])

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
        api_messages.CommandAttemptMessage(
            device_serials=['1', '2'], start_time=now, end_time=now,
            state=common.CommandState.COMPLETED))
    mock_get_request.return_value = mock_request

    # update mock test run
    self.mock_test_run.test_package_info = ndb_models.TestPackageInfo(
        name='name', version='version')
    self.mock_test_run.state = ndb_models.TestRunState.COMPLETED
    self.mock_test_run.create_time = now - datetime.timedelta(seconds=123)
    self.mock_test_run.failed_test_run_count = 1
    self.mock_test_run.total_test_count = 2
    self.mock_test_run.failed_test_count = 3
    self.mock_test_run.put()

    # check that right data was logged
    tfc_event_handler._TrackTestRun(self.mock_test_run.key.id())
    mock_log.assert_called_with(analytics.TEST_RUN_CATEGORY,
                                analytics.END_ACTION,
                                test_name='name',
                                test_version='version',
                                state='COMPLETED',
                                is_rerun=False,
                                duration_seconds=123,
                                device_count=2,
                                attempt_count=1,
                                failed_module_count=1,
                                test_count=2,
                                failed_test_count=3)

  @mock.patch.object(analytics, 'Log')
  @mock.patch.object(tfc_event_handler, '_GetCurrentTime')
  def testTrackTestInvocation(self, mock_time, mock_log):
    # mock current time
    now = datetime.datetime.now()
    mock_time.return_value = now

    # configure mock TFC request with 2 attempts
    request_id = self.mock_test_run.request_id
    mock_request = api_messages.RequestMessage(id=request_id,
                                               command_line='command')
    mock_request.command_attempts.append(
        api_messages.CommandAttemptMessage(
            state=common.CommandState.COMPLETED,
            device_serials=['1', '2'],
            start_time=now - datetime.timedelta(seconds=400),
            end_time=now-datetime.timedelta(seconds=300),
            total_test_count=60, failed_test_run_count=50,
            failed_test_count=40))
    mock_request.command_attempts.append(
        api_messages.CommandAttemptMessage(
            state=common.CommandState.COMPLETED,
            device_serials=['2'],
            start_time=now - datetime.timedelta(seconds=200),
            end_time=now - datetime.timedelta(seconds=100),
            total_test_count=3, failed_test_run_count=2, failed_test_count=1))

    # set test id
    self.mock_test.key = ndb.Key(ndb_models.Test, 'some.test.id')
    self.mock_test.put()
    self.mock_test_run.test_run_config.test_key = self.mock_test.key

    # update mock test run
    self.mock_test_run.test_package_info = ndb_models.TestPackageInfo(
        name='name', version='version')
    self.mock_test_run.state = ndb_models.TestRunState.COMPLETED
    self.mock_test_run.create_time = now - datetime.timedelta(seconds=1000)
    self.mock_test_run.failed_test_count = 1
    self.mock_test_run.sequence_id = 'abc-def-ghi'

    # check that right data was logged
    tfc_event_handler._TrackTestInvocations(mock_request, self.mock_test_run)
    mock_log.assert_called_with(
        analytics.INVOCATION_CATEGORY,
        analytics.END_ACTION,
        command='command',
        test_run_command='mock test run command',
        test_run_retry_command='mock test run retry command',
        test_id='some.test.id',
        test_name='name',
        test_version='version',
        state='COMPLETED',
        failed_test_count_threshold='10',
        duration_seconds=100,
        elapsed_time_seconds=900,
        device_count=1,
        test_count=3,
        failed_module_count=2,
        failed_test_count=1,
        prev_total_test_count=60,
        prev_failed_module_count=50,
        prev_failed_test_count=40,
        missing_previous_run=False,
        is_sequence_run=True)

  @mock.patch.object(analytics, 'Log')
  @mock.patch.object(tfc_event_handler, '_GetCurrentTime')
  def testTrackTestInvocation_manualRetry(self, mock_time, mock_log):
    # mock current time
    now = datetime.datetime.now()
    mock_time.return_value = now

    # configure mock TFC request with 1 attempt
    request_id = self.mock_test_run.request_id
    mock_request = api_messages.RequestMessage(id=request_id,
                                               command_line='command')
    mock_request.command_attempts.append(
        api_messages.CommandAttemptMessage(
            state=common.CommandState.COMPLETED,
            device_serials=['2'],
            start_time=now - datetime.timedelta(seconds=200),
            end_time=now - datetime.timedelta(seconds=100),
            total_test_count=3, failed_test_run_count=2, failed_test_count=1))

    # create previous test runs
    first_test_run = ndb_models.TestRun(
        test_run_config=ndb_models.TestRunConfig(
            test_key=self.mock_test.key, run_target='run_target',
            cluster='cluster'),
        test=self.mock_test,
        request_id='request_id1',
        state=ndb_models.TestRunState.UNKNOWN,
        create_time=now - datetime.timedelta(seconds=5000),
        total_test_count=100,
        failed_test_run_count=90,
        failed_test_count=80,
        prev_test_context=ndb_models.TestContextObj())
    first_test_run.put()
    second_test_run = ndb_models.TestRun(
        test_run_config=ndb_models.TestRunConfig(
            test_key=self.mock_test.key, run_target='run_target',
            cluster='cluster'),
        test=self.mock_test,
        request_id='request_id2',
        state=ndb_models.TestRunState.UNKNOWN,
        create_time=now - datetime.timedelta(seconds=2000),
        total_test_count=10,
        failed_test_run_count=9,
        failed_test_count=8,
        prev_test_run_key=first_test_run.key)
    second_test_run.put()

    # update mock test run
    self.mock_test_run.test_package_info = ndb_models.TestPackageInfo(
        name='name', version='version')
    self.mock_test_run.state = ndb_models.TestRunState.COMPLETED
    self.mock_test_run.create_time = now - datetime.timedelta(seconds=1000)
    self.mock_test_run.failed_test_count = 1
    self.mock_test_run.prev_test_run_key = second_test_run.key

    # check that right data was logged
    tfc_event_handler._TrackTestInvocations(mock_request, self.mock_test_run)
    mock_log.assert_called_with(
        analytics.INVOCATION_CATEGORY,
        analytics.END_ACTION,
        command='command',
        test_run_command='mock test run command',
        test_run_retry_command='mock test run retry command',
        test_id=tfc_event_handler.LOCAL_ID_TAG,
        test_name='name',
        test_version='version',
        state='COMPLETED',
        failed_test_count_threshold=None,
        duration_seconds=100,
        elapsed_time_seconds=4900,
        device_count=1,
        test_count=3,
        failed_module_count=2,
        failed_test_count=1,
        prev_total_test_count=10,
        prev_failed_module_count=9,
        prev_failed_test_count=8,
        missing_previous_run=True,
        is_sequence_run=False)


if __name__ == '__main__':
  absltest.main()
