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

"""Tests for config_set_helper."""
from absl.testing import absltest
import mock
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.util import ndb_shim as ndb

from multitest_transport.models import build
from multitest_transport.models import config_encoder
from multitest_transport.models import config_set_helper
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.util import errors


class ConfigSetHelperTest(testbed_dependent_test.TestbedDependentTest):

  def _CreateConfigSetInfo(self, name='Test Config',
                           url='some.url/some.bucket', hash_value='123'):
    info = ndb_models.ConfigSetInfo(name=name, url=url, hash=hash_value)
    info.key = ndb.Key(ndb_models.ConfigSetInfo, url)
    return info

  def _CreateConfigSetInfoMessage(self, info, status):
    message = messages.Convert(info, messages.ConfigSetInfo)
    message.status = status
    return message

  def _CreateImportedConfig(self):
    imported_config = self._CreateConfigSetInfo(name='Imported Config',
                                                url='import/config.yaml',
                                                hash_value='12345')
    imported_config.put()
    return imported_config

  def _CreateNonImportedConfig(self):
    return self._CreateConfigSetInfo(name='Non-Imported Config',
                                     url='dont/import/config.yaml',
                                     hash_value='67890')

  def _CreateUpdatableConfig(self):
    name = 'Updatable Config'
    url = 'updatable/config.yaml'
    old_config = self._CreateConfigSetInfo(name=name, url=url,
                                           hash_value='34567')
    old_config.put()
    new_config = self._CreateConfigSetInfo(name=name, url=url,
                                           hash_value='98765')
    return old_config, new_config

  def _CreateMockTest(self, test_id='test.id', namespace='', name='Test 1'):
    if namespace:
      test_id = config_encoder._AddNamespaceToId(namespace, test_id)
    test = ndb_models.Test(name=name, command='command')
    test.key = ndb.Key(ndb_models.Test, test_id)
    test.put()
    return test

  def _CreateMockDeviceAction(self, action_id='action.id', namespace='',
                              name='Device Action 1'):
    if namespace:
      action_id = config_encoder._AddNamespaceToId(namespace, action_id)
    action = ndb_models.DeviceAction(name=name)
    action.key = ndb.Key(ndb_models.DeviceAction, action_id)
    action.put()
    return action

  def _CreateMockTestRunAction(self, action_id='action.id', namespace='',
                               name='Test Run Action 1'):
    if namespace:
      action_id = config_encoder._AddNamespaceToId(namespace, action_id)
    action = ndb_models.TestRunAction(name=name, hook_class_name='hook class')
    action.key = ndb.Key(ndb_models.TestRunAction, action_id)
    action.put()
    return action

  @mock.patch.object(config_set_helper, 'ReadRemoteFile')
  @mock.patch.object(build, 'GetBuildChannel')
  def testGetRemoteConfigSetInfos(
      self, mock_get_build_channel, mock_read_remote_file):
    mock_build_items = [
        build.BuildItem(name='foo.yaml', path='foo.yaml', is_file=True),
        build.BuildItem(name='bar.yaml', path='bar.yaml', is_file=True),
    ]
    mock_build_channel = mock.MagicMock()
    mock_get_build_channel.return_value = mock_build_channel
    mock_build_channel.ListBuildItems.return_value = (mock_build_items, None)
    mock_read_remote_file.side_effect = [
        'info:\n'
        '- name: FOO\n'
        '  description: FOO_DESCRIPTION\n'
        '  url: FOO_URL\n',
        'info:\n'
        '- name: BAR\n'
        '  description: BAR_DESCRIPTION\n'
        '  url: BAR_URL\n'
    ]

    infos = config_set_helper.GetRemoteConfigSetInfos()

    mock_get_build_channel.assert_called_with('google_cloud_storage')
    mock_build_channel.ListBuildItems.assert_called()
    mock_read_remote_file.assert_has_calls(
        [
            mock.call('%s/%s' % (config_set_helper.CONFIG_SET_URL, 'foo.yaml')),
            mock.call('%s/%s' % (config_set_helper.CONFIG_SET_URL, 'bar.yaml'))
        ])
    self.assertLen(infos, 2)
    self.assertEqual('FOO', infos[0].name)
    self.assertEqual('FOO_DESCRIPTION', infos[0].description)
    self.assertEqual('FOO_URL', infos[0].url)
    self.assertIsNotNone(infos[0].hash)
    self.assertEqual('BAR', infos[1].name)
    self.assertEqual('BAR_DESCRIPTION', infos[1].description)
    self.assertEqual('BAR_URL', infos[1].url)
    self.assertIsNotNone(infos[1].hash)

  @mock.patch.object(config_set_helper, '_GetAuthorizedBuildChannel')
  def testGetRemoteConfigSetInfos_buildChannelNotAuthorized(
      self, mock_get_authorized_build_channel):
    mock_build_channel = mock.MagicMock()
    mock_build_channel.auth_state = ndb_models.AuthorizationState.UNAUTHORIZED
    mock_get_authorized_build_channel.return_value = (mock_build_channel, None)
    # Return an empty list if the build channel is not authorized
    infos = config_set_helper.GetRemoteConfigSetInfos()
    self.assertEmpty(infos)

  @mock.patch.object(build, 'GetBuildChannel')
  def testGetRemoteConfigSetInfos_noPermissionForBuildChannel(
      self, mock_get_build_channel):
    error = errors.FilePermissionError('test error')
    mock_build_channel = mock.MagicMock()
    mock_build_channel.ListBuildItems.side_effect = error
    mock_get_build_channel.return_value = mock_build_channel
    # Failing to list build items will return an empty list
    infos = config_set_helper.GetRemoteConfigSetInfos()
    self.assertEmpty(infos)

  def testUpdateConfigSetInfos(self):
    imported_config = self._CreateImportedConfig()
    nonimported_config = self._CreateNonImportedConfig()
    updatable_config_old, updatable_config_new = self._CreateUpdatableConfig()

    imported_message = self._CreateConfigSetInfoMessage(
        imported_config, ndb_models.ConfigSetStatus.IMPORTED)
    nonimported_message = self._CreateConfigSetInfoMessage(
        nonimported_config, ndb_models.ConfigSetStatus.NOT_IMPORTED)
    updatable_message_old = self._CreateConfigSetInfoMessage(
        updatable_config_old, ndb_models.ConfigSetStatus.IMPORTED)
    updatable_message_new = self._CreateConfigSetInfoMessage(
        updatable_config_new, ndb_models.ConfigSetStatus.UPDATABLE)
    updatable_message_combined = self._CreateConfigSetInfoMessage(
        updatable_config_old, ndb_models.ConfigSetStatus.UPDATABLE)

    imported_messages = [imported_message, updatable_message_old]
    remote_messages = [nonimported_message, updatable_message_new]

    updated_messages = config_set_helper.UpdateConfigSetInfos(imported_messages,
                                                              remote_messages)
    self.assertLen(updated_messages, 3)
    self.assertEqual(nonimported_message, updated_messages[0])
    self.assertEqual(imported_message, updated_messages[1])
    self.assertEqual(updatable_message_combined, updated_messages[2])

  @mock.patch.object(config_set_helper, 'GetRemoteConfigSetInfo')
  def testGetLatestVersion_noUpdates(self, mock_get_remote_config_set_info):
    imported_config = self._CreateImportedConfig()
    imported_message = self._CreateConfigSetInfoMessage(
        imported_config, ndb_models.ConfigSetStatus.IMPORTED)

    mock_get_remote_config_set_info.return_value = imported_config

    updated_message = config_set_helper.GetLatestVersion(imported_config)

    self.assertEqual(imported_message, updated_message)

  @mock.patch.object(config_set_helper, 'GetRemoteConfigSetInfo')
  def testGetLatestVersion_updatable(self, mock_get_remote_config_set_info):
    updatable_config_old, updatable_config_new = self._CreateUpdatableConfig()
    updatable_message_combined = self._CreateConfigSetInfoMessage(
        updatable_config_old, ndb_models.ConfigSetStatus.UPDATABLE)

    mock_get_remote_config_set_info.return_value = updatable_config_new

    updated_message = config_set_helper.GetLatestVersion(updatable_config_old)

    self.assertEqual(updated_message, updatable_message_combined)

  def testDeleteConfigSetInfo(self):
    config = self._CreateImportedConfig()
    namespaced_test = self._CreateMockTest('test.1', config.url)
    default_test = self._CreateMockTest('test.2')
    namespaced_device_action = self._CreateMockDeviceAction('device.action.1',
                                                            config.url)
    default_device_action = self._CreateMockDeviceAction('device.action.2')
    namespaced_test_run_action = self._CreateMockTestRunAction('run.action.1',
                                                               config.url)
    default_test_run_action = self._CreateMockTestRunAction('run.action.2')

    config_set_helper.Delete(config.url)
    self.assertIsNone(config.key.get())
    self.assertIsNone(namespaced_test.key.get())
    self.assertIsNotNone(default_test.key.get())
    self.assertIsNone(namespaced_device_action.key.get())
    self.assertIsNotNone(default_device_action.key.get())
    self.assertIsNone(namespaced_test_run_action.key.get())
    self.assertIsNotNone(default_test_run_action.key.get())

if __name__ == '__main__':
  absltest.main()
