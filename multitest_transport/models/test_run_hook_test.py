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

"""Unit tests for test_run_hook."""
from unittest import mock

from absl.testing import absltest
from google.oauth2 import credentials as authorized_user
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.api_messages import CommandState
from tradefed_cluster.command_task_api import CommandTask

from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.plugins import base as plugins
from multitest_transport.util import analytics
from multitest_transport.util import oauth2_util
from multitest_transport.util import tfc_client


class SimpleHook(plugins.TestRunHook):
  """Simple test run hook."""
  name = 'simple'


class OAuth2Hook(plugins.TestRunHook):
  """Test run hook with OAuth2 configuration."""
  name = 'oauth2'
  oauth2_config = oauth2_util.OAuth2Config('id', 'secret', ['scope'])


class TestRunHookTest(testbed_dependent_test.TestbedDependentTest):

  @mock.patch.object(test_run_hook, '_ExecuteHook')
  @mock.patch.object(test_run_hook, '_GetLatestAttempt')
  def testExecuteHooks(self, mock_get_latest_attempt, mock_execute_hook):
    """Tests that relevant actions can be found and executed."""
    before_action = ndb_models.TestRunAction(
        name='Before', hook_class_name='simple',
        phases=[ndb_models.TestRunPhase.BEFORE_RUN])
    after_action = ndb_models.TestRunAction(
        name='After', hook_class_name='simple',
        phases=[ndb_models.TestRunPhase.AFTER_RUN])
    # Create test run with two actions and an attempt
    test_run = ndb_models.TestRun(
        test_run_actions=[before_action, after_action])
    test_run.put()
    attempt = mock.MagicMock()
    mock_get_latest_attempt.return_value = attempt
    # Execute after run hooks and verify
    test_run_hook.ExecuteHooks(test_run.key.id(),
                               ndb_models.TestRunPhase.AFTER_RUN,
                               attempt_id='attempt_id')
    mock_get_latest_attempt.assert_called_once_with(test_run, 'attempt_id')
    hook_context = plugins.TestRunHookContext(
        test_run=test_run, latest_attempt=attempt,
        phase=ndb_models.TestRunPhase.AFTER_RUN)
    mock_execute_hook.assert_called_once_with(after_action, hook_context)

  def testApplyOptionsFromDeviceActions(self):
    """Tests that device actions can be found and executed."""
    device_action = ndb_models.DeviceAction(
        name='unit test',
        tradefed_options=[
            ndb_models.NameMultiValuePair(
                name='device-type', values=['LOCAL_VIRTUAL_DEVICE'])
        ])
    test_run = ndb_models.TestRun(before_device_actions=[device_action])
    test_run.put()
    task = mock.MagicMock(extra_options={})
    test_run_hook._ApplyOptionsFromDeviceActions(test_run.key.id(), task)
    self.assertEqual(task.extra_options,
                     {'device-type': ['LOCAL_VIRTUAL_DEVICE']})

  @mock.patch.object(test_run_hook, '_ExecuteHook')
  def testExecuteHooks_notFound(self, mock_execute_hook):
    """Tests that no hooks are executed if run not found."""
    test_run_hook.ExecuteHooks('unknown', ndb_models.TestRunPhase.AFTER_RUN)
    mock_execute_hook.assert_not_called()

  def testGetLatestAttempt_noRequest(self):
    """Tests that no attempt is returned without a TFC request ID."""
    test_run = ndb_models.TestRun()
    self.assertIsNone(test_run_hook._GetLatestAttempt(test_run, None))

  @mock.patch.object(tfc_client, 'GetAttempt')
  def testGetLatestAttempt_attemptId(self, mock_get_attempt):
    """Tests that the attempt is fetched directly if an ID is provided."""
    test_run = ndb_models.TestRun(request_id='request_id')
    attempt = mock.MagicMock()
    mock_get_attempt.return_value = attempt
    self.assertEqual(attempt,
                     test_run_hook._GetLatestAttempt(test_run, 'attempt_id'))
    mock_get_attempt.assert_called_once_with('request_id', 'attempt_id')

  @mock.patch.object(tfc_client, 'GetRequest')
  def testGetLatestAttempt(self, mock_get_request):
    """Tests that the latest finished attempt is fetched if no ID specified."""
    test_run = ndb_models.TestRun(request_id='request_id')
    # Three attempts found and the third is still running
    first_attempt = mock.MagicMock(state=CommandState.COMPLETED)
    second_attempt = mock.MagicMock(state=CommandState.COMPLETED)
    third_attempt = mock.MagicMock(state=CommandState.RUNNING)
    request = mock.MagicMock(
        command_attempts=[first_attempt, second_attempt, third_attempt])
    mock_get_request.return_value = request
    # Should return the second attempt (latest attempt in final state)
    self.assertEqual(second_attempt,
                     test_run_hook._GetLatestAttempt(test_run, None))

  @mock.patch.object(SimpleHook, 'Execute')
  @mock.patch.object(analytics, 'Log')
  @mock.patch.object(SimpleHook, '__init__')
  def testExecuteHook(self, mock_init, mock_log, mock_execute):
    """Tests that a hook can be constructed and executed."""
    mock_init.return_value = None
    hook_context = mock.MagicMock()
    credentials = authorized_user.Credentials(None)
    action = ndb_models.TestRunAction(
        name='Test', hook_class_name='simple',
        options=[ndb_models.NameValuePair(name='ham', value='eggs')],
        credentials=credentials,
    )
    test_run_hook._ExecuteHook(action, hook_context)
    mock_init.assert_called_with(_credentials=credentials, ham='eggs')
    mock_log.assert_called()
    mock_execute.assert_called_with(hook_context)

  @mock.patch.object(SimpleHook, 'Execute')
  @mock.patch.object(analytics, 'Log')
  @mock.patch.object(SimpleHook, '__init__')
  def testExecuteHook_withContextVariables(
      self, mock_init, mock_log, mock_execute):
    """Tests that a hook can be constructed and executed."""
    test = ndb_models.Test(name='test', command='command')
    test.put()
    test_run = ndb_models.TestRun(
        test=test,
        test_run_config=ndb_models.TestRunConfig(
            test_key=test.key, cluster='cluster'),
        test_resources=[
            ndb_models.TestResourceObj(
                name='device_image',
                url='mtt:///android_ci/branch/target/build_id/image.zip',
                test_resource_type=ndb_models.TestResourceType.DEVICE_IMAGE)
        ])
    test_run.put()
    mock_init.return_value = None
    hook_context = mock.MagicMock()
    hook_context.test_run = test_run
    credentials = authorized_user.Credentials(None)
    action = ndb_models.TestRunAction(
        name='Test', hook_class_name='simple',
        options=[
            ndb_models.NameValuePair(name='ham', value='eggs'),
            ndb_models.NameValuePair(
                name='test_run_id', value='${MTT_TEST_RUN_ID}'),
            ndb_models.NameValuePair(
                name='device_image_url', value='${MTT_DEVICE_IMAGE_URL}'),
            ndb_models.NameValuePair(
                name='device_image_branch', value='${MTT_DEVICE_IMAGE_BRANCH}'),
            ndb_models.NameValuePair(
                name='device_image_target', value='${MTT_DEVICE_IMAGE_TARGET}'),
            ndb_models.NameValuePair(
                name='device_image_build_id',
                value='${MTT_DEVICE_IMAGE_BUILD_ID}'),
        ],
        credentials=credentials,
    )

    test_run_hook._ExecuteHook(action, hook_context)

    mock_init.assert_called_with(
        _credentials=credentials,
        ham='eggs',
        test_run_id=str(test_run.key.id()),
        device_image_url='mtt:///android_ci/branch/target/build_id/image.zip',
        device_image_branch='branch',
        device_image_target='target',
        device_image_build_id='build_id')
    mock_log.assert_called()
    mock_execute.assert_called_with(hook_context)

  def testGetOAuth2Config_notFound(self):
    """Tests that no OAuth2 config is returned if hook class not found."""
    action = ndb_models.TestRunAction(name='Test', hook_class_name='unknown')
    self.assertIsNone(test_run_hook.GetOAuth2Config(action))

  def testGetOAuth2Config_noConfig(self):
    """Tests that no OAuth2 config is returned if class doesn't have any."""
    action = ndb_models.TestRunAction(name='Test', hook_class_name='simple')
    self.assertIsNone(test_run_hook.GetOAuth2Config(action))

  def testGetOAuth2Config(self):
    """Tests that a hook's OAuth2 config can be retrieved."""
    action = ndb_models.TestRunAction(name='Test', hook_class_name='oauth2')
    self.assertEqual(OAuth2Hook.oauth2_config,
                     test_run_hook.GetOAuth2Config(action))

  def testGetAuthorizationState_notApplicable(self):
    """Tests detecting hooks not requiring authorization."""
    action = ndb_models.TestRunAction(name='Test', hook_class_name='simple')
    self.assertEqual(ndb_models.AuthorizationState.NOT_APPLICABLE,
                     test_run_hook.GetAuthorizationState(action))

  def testGetAuthorizationState_unauthorized(self):
    """Tests detecting hooks requiring authorization and without credentials."""
    action = ndb_models.TestRunAction(name='Test', hook_class_name='oauth2')
    self.assertEqual(ndb_models.AuthorizationState.UNAUTHORIZED,
                     test_run_hook.GetAuthorizationState(action))

  def testGetAuthorizationState_authorized(self):
    """Tests detecting hooks requiring authorization and with credentials."""
    action = ndb_models.TestRunAction(
        name='Test', hook_class_name='oauth2',
        credentials=authorized_user.Credentials(None),
    )
    self.assertEqual(ndb_models.AuthorizationState.AUTHORIZED,
                     test_run_hook.GetAuthorizationState(action))

  @mock.patch.object(test_run_hook.TfcTaskInterceptor, 'UpdateCommandTask')
  @mock.patch.object(test_run_hook, 'ExecuteHooks')
  @mock.patch.object(test_run_hook, '_ApplyOptionsFromDeviceActions')
  def testTfcTaskInterceptor(self, mock_apply_options, mock_execute_hooks,
                             mock_update_task):
    """Tests that TFC tasks can be intercepted and passed to run hooks."""
    test_run = ndb_models.TestRun(request_id='request_id')
    test_run.put()
    unknown_task = CommandTask(request_id='unknown')  # Unknown request ID
    expected_task = CommandTask(request_id='request_id')

    # Verify that the right hooks are executed and task updates applied
    plugin = test_run_hook.TfcTaskInterceptor()
    converted_task = plugin.ConvertCommandTask(expected_task)
    plugin.OnCommandTasksLease([unknown_task, expected_task])
    mock_apply_options.assert_called_once_with(
        test_run.key.id(), converted_task)
    mock_execute_hooks.assert_called_once_with(
        test_run.key.id(),
        ndb_models.TestRunPhase.BEFORE_ATTEMPT,
        task=converted_task)
    mock_update_task.assert_called_once_with(expected_task, converted_task)


if __name__ == '__main__':
  absltest.main()
