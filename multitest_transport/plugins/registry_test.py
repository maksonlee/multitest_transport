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

"""Unit tests for registry."""
from absl.testing import absltest
import six

from multitest_transport.plugins.registry import PluginRegistry


class RegistryTest(absltest.TestCase):

  def setUp(self):
    super(RegistryTest, self).setUp()
    self.registry = PluginRegistry()
    self.assertEmpty(self.registry.ListPluginNames())

  def testRegisterPlugin(self):
    # Register a mock plugin explicitly
    class MockPlugin(object):        name = 'mock'
    self.registry.RegisterPlugin(MockPlugin)
    # Verify that it is in the registry
    self.assertEqual(self.registry.ListPluginNames(), ['mock'])
    self.assertEqual(self.registry.GetPluginClass('mock'), MockPlugin)

  def testRegisterPlugin_noName(self):
    # Register a mock plugin with no name explicitly
    class MockPlugin(object):        pass
    self.registry.RegisterPlugin(MockPlugin)
    self.assertEmpty(self.registry.ListPluginNames())  # Not registered

  def testRegisterPlugin_abstract(self):
    # Register an abstract mock plugin explicitly
    class AbstractMockPlugin(object):        name = 'mock'
    self.registry.RegisterPlugin(AbstractMockPlugin)
    self.assertEmpty(self.registry.ListPluginNames())  # Not registered

  def testMetaclass(self):
    # Register a mock plugin using the registry metaclass
    class MockPlugin(six.with_metaclass(self.registry.GetMetaclass(), object)):        name = 'metaclass'
    # Verify that it is in the registry
    self.assertEqual(self.registry.ListPluginNames(), ['metaclass'])
    self.assertEqual(self.registry.GetPluginClass('metaclass'), MockPlugin)


if __name__ == '__main__':
  absltest.main()
