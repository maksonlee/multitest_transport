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

"""Tests for config_set_api."""

from absl.testing import absltest

from google.appengine.ext import testbed

from multitest_transport.models import config_set_helper
from multitest_transport.models import messages
from multitest_transport.models import ndb_models


class ConfigSetHelperTest(absltest.TestCase):

  def setUp(self):
    super(ConfigSetHelperTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  def tearDown(self):
    self.testbed.deactivate()
    super(ConfigSetHelperTest, self).tearDown()

  def _CreateConfigSetInfo(self, name='Test Config',
                           url='some.url/some.bucket', hash_value='123'):
    return ndb_models.ConfigSetInfo(name=name, url=url, hash=hash_value)

  def _CreateConfigSetInfoMessage(self, info, imported, update_available):
    message = messages.Convert(info, messages.ConfigSetInfo)
    message.imported = imported
    message.update_available = update_available
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

  def testUpdateConfigSetInfos(self):
    imported_config = self._CreateImportedConfig()
    nonimported_config = self._CreateNonImportedConfig()
    updatable_config_old, updatable_config_new = self._CreateUpdatableConfig()

    imported_message = self._CreateConfigSetInfoMessage(imported_config,
                                                        True, False)
    nonimported_message = self._CreateConfigSetInfoMessage(nonimported_config,
                                                           False, False)
    updatable_message_old = self._CreateConfigSetInfoMessage(
        updatable_config_old, True, False)
    updatable_message_new = self._CreateConfigSetInfoMessage(
        updatable_config_new, True, True)
    updatable_message_combined = self._CreateConfigSetInfoMessage(
        updatable_config_old, True, True)

    imported_messages = [imported_message, updatable_message_old]
    remote_messages = [nonimported_message, updatable_message_new]

    updated_messages = config_set_helper.UpdateConfigSetInfos(imported_messages,
                                                              remote_messages)
    self.assertLen(updated_messages, 3)
    self.assertEqual(nonimported_message, updated_messages[0])
    self.assertEqual(imported_message, updated_messages[1])
    self.assertEqual(updatable_message_combined, updated_messages[2])


if __name__ == '__main__':
  absltest.main()
