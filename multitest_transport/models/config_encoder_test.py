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

"""Unit tests for config."""

from absl.testing import absltest

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from multitest_transport.models import config_encoder
from multitest_transport.models import ndb_models


class ConfigTest(absltest.TestCase):

  def setUp(self):
    super(ConfigTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  def CreateNodeConfig(self, env_vars=None):
    return ndb_models.NodeConfig(
        id=ndb_models.NODE_CONFIG_ID,
        env_vars=ndb_models.NameValuePair.FromDict(env_vars or {}))

  def CreateBuildChannel(self, key=None, name=None, options=None):
    return ndb_models.BuildChannelConfig(
        id=key, name=name, provider_name=name,
        options=ndb_models.NameValuePair.FromDict(options or {}))

  def CreateTestRunHook(
      self, key=None, name=None, hook_class_name=None, options=None):
    return ndb_models.TestRunHookConfig(
        id=key, name=name, hook_class_name=hook_class_name,
        options=ndb_models.NameValuePair.FromDict(options or {}))

  def testEncode_nodeConfig(self):
    """Tests serializing a node config (single object)."""
    node_config = self.CreateNodeConfig(env_vars={'variable': 'value'})

    expected =\
"""node_config:
  env_vars:
  - name: variable
    value: value
"""
    actual = config_encoder.Encode(
        config_encoder.ConfigSet(node_config=node_config))
    self.assertEqual(expected, actual)

  def testDecode_nodeConfig(self):
    """Tests deserializing a node config (single object)."""
    node_config = self.CreateNodeConfig(env_vars={'hello': 'world'})
    expected = config_encoder.ConfigSet(node_config=node_config)

    string =\
"""node_config:
  env_vars:
  - name: hello
    value: world
"""
    actual = config_encoder.Decode(string)
    self.assertEqual(expected, actual)

  def testEncode_buildChannels(self):
    """Tests serializing build channels (list of objects)."""
    foo = self.CreateBuildChannel(key='foo', name='Foo')
    bar = self.CreateBuildChannel(key='bar', name='Bar',
                                  options={'option': 'value'})

    expected =\
"""build_channels:
- id: foo
  name: Foo
  provider_name: Foo
- id: bar
  name: Bar
  options:
  - name: option
    value: value
  provider_name: Bar
"""
    actual = config_encoder.Encode(
        config_encoder.ConfigSet(build_channels=[foo, bar]))
    self.assertEqual(expected, actual)

  def testDecode_buildChannels(self):
    """Tests deserializing build channels (list of objects)."""
    foo = self.CreateBuildChannel(key='foo', name='Foo')
    bar = self.CreateBuildChannel(key='bar', name='Bar',
                                  options={'option': 'value'})
    expected = config_encoder.ConfigSet(build_channels=[foo, bar])

    string = \
"""build_channels:
- id: foo
  name: Foo
  provider_name: Foo
- id: bar
  name: Bar
  options:
  - name: option
    value: value
  provider_name: Bar
"""
    actual = config_encoder.Decode(string)
    self.assertEqual(expected, actual)

  def testEncode_multipleObjects(self):
    """Tests serializing multiple objects."""
    build_channel = self.CreateBuildChannel(key='foo', name='Foo',
                                            options={'option': 'value'})
    test_run_hook = self.CreateTestRunHook(key='bar', name='Bar',
                                           hook_class_name='Web',
                                           options={'url': 'www.google.com'})
    expected = \
"""build_channels:
- id: foo
  name: Foo
  options:
  - name: option
    value: value
  provider_name: Foo
test_run_hooks:
- hook_class_name: Web
  id: bar
  name: Bar
  options:
  - name: url
    value: www.google.com
"""

    config_set = config_encoder.ConfigSet(
        build_channels=[build_channel], test_run_hooks=[test_run_hook])
    actual = config_encoder.Encode(config_set)
    self.assertEqual(expected, actual)

  def testDecode_multipleStrings(self):
    """Tests deserializing a merged configuration."""
    build_channel = self.CreateBuildChannel(key='foo', name='Foo',
                                            options={'option': 'value'})
    expected = config_encoder.ConfigSet(build_channels=[build_channel])

    strings = [
        """build_channels:
        - id: foo
          name: Foo
          provider_name: Foo
        """,
        """build_channels:
        - id: foo
          options:
          - name: option
            value: value
        """]
    actual = config_encoder.Decode(strings)
    self.assertEqual(expected, actual)

  def testLoad(self):
    # add an existing build channel
    self.CreateBuildChannel(key='foo', name='Foo').put()

    # load configuration
    node_config = self.CreateNodeConfig()
    build_channel = self.CreateBuildChannel(key='foo',
                                            options={'option': 'value'})
    config_set = config_encoder.ConfigSet(node_config=node_config,
                                          build_channels=[build_channel])
    config_encoder.Load(config_set)

    # new stored config added
    stored_node_config = ndb.Key(ndb_models.NodeConfig, 1).get()
    self.assertIsNotNone(stored_node_config)

    # updated existing build channel
    stored_build_channel = ndb.Key(ndb_models.BuildChannelConfig, 'foo').get()
    self.assertIsNotNone(stored_build_channel)
    self.assertEqual('Foo', stored_build_channel.name)  # preserved
    self.assertEqual('option', stored_build_channel.options[0].name)
    self.assertEqual('value', stored_build_channel.options[0].value)

  def testMergeConfigs(self):
    """Tests merging simple configuration objects."""
    a = {
        'a': True,
        'dict': {'a': 1},
        'list': [1, 2],
    }
    b = {
        'b': False,
        'dict': {'a': 2, 'b': 1},
        'list': [3, 4],
    }

    expected = {
        'a': True,
        'b': False,  # added key
        'dict': {
            'a': 2,  # nested value overwritten
            'b': 1,  # added nested key
        },
        'list': [1, 2, 3, 4],  # concatenated
    }
    actual = config_encoder._MergeConfigs(a, b)
    self.assertEqual(expected, actual)

  def testMergeLists(self):
    """Tests merging lists whose elements share IDs."""
    a = [{'id': 1, 'val': '1'}, {'id': 2, 'val': '2'}]
    b = [{'id': 2, 'val': '3'}, {'val': '4'}, {'id': 3, 'val': '5'}]

    expected = [{'id': 1, 'val': '1'},
                {'id': 2, 'val': '3'},  # merged entry with existing ID
                {'val': '4'},  # added entry with no ID to merge on
                {'id': 3, 'val': '5'}]  # added entry with new ID

    actual = config_encoder._MergeConfigs(a, b)
    self.assertEqual(expected, actual)

if __name__ == '__main__':
  absltest.main()
