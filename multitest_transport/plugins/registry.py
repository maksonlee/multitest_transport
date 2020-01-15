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

"""Plugin implementation registry."""
import logging


class PluginRegistry(object):
  """Holds a reference to all the plugin implementations."""

  def __init__(self):
    self._plugins_by_name = {}

  def RegisterPlugin(self, cls):
    """Registers a plugin class using its name."""
    name = getattr(cls, 'name', None)
    if not name:
      return  # Ignore classes without names.
    assert name not in self._plugins_by_name, (
        'Plugin \'%s\' already registered' % name)
    logging.info('Registering plugin \'%s\' (%s)', name, cls)
    self._plugins_by_name[name] = cls

  def GetPluginClass(self, name):
    """Retrieves a plugin class by name (property or class name)."""
    return self._plugins_by_name.get(name)

  def ListPluginNames(self):
    """Lists all registered plugin names."""
    return self._plugins_by_name.keys()

  def GetMetaclass(self):
    """Generates a metaclass to automatically registers subclasses."""
    class Metaclass(type):        def __init__(cls, name, parents, attributes):          self.RegisterPlugin(cls)
        type.__init__(cls, name, parents, attributes)
    return Metaclass
