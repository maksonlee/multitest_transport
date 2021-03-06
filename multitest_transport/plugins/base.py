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

"""Base classes for MTT plugins."""

import collections
import logging
import re

import attr
import enum
import six

from multitest_transport.plugins.registry import PluginRegistry

BUILD_PROVIDER_REGISTRY = PluginRegistry()
TEST_RUN_HOOK_REGISTRY = PluginRegistry()

OptionDef = collections.namedtuple(
    'OptionDef', ['name', 'value_type', 'choices', 'default'])

BuildItem = collections.namedtuple('BuildItem', [
    'name', 'path', 'is_file', 'size', 'timestamp', 'description'
])
BuildItem.__new__.__defaults__ = (False, None, None, None, None)

# A URL pattern that can be handled by a build provider.
UrlPattern = collections.namedtuple(
    'UrlPattern',
    ['url', 'path'])


class AuthorizationMethod(enum.Enum):
  """Authorization methods."""
  OAUTH2_AUTHORIZATION_CODE = 1
  OAUTH2_SERVICE_ACCOUNT = 2


class BuildItemType(enum.Enum):
  """Build item types."""
  FILE = 1
  DIRECTORY = 2


class BuildProviderOptions(object):
  """A class to store parsed build provider options."""

  def __init__(self, option_def_map):
    self._option_def_map = option_def_map
    # Fill default values
    for name, option_def in six.iteritems(self._option_def_map):
      self.__dict__[name] = option_def.default

  def Update(self, **kwargs):
    """Updates options values.

    Args:
      **kwargs: option name/value pairs to update.
    Raises:
      ValueError: if an option is not defined.
    """
    for name, value in six.iteritems(kwargs):
      option_def = self._option_def_map.get(name)
      if not option_def:
        logging.warning('Unsupported option name %s; ignoring', name)
        continue
      self.__dict__[name] = option_def.value_type(value)


class BuildProvider(
    six.with_metaclass(BUILD_PROVIDER_REGISTRY.GetMetaclass(), object)):
  """A base class for a build provider."""

  name = None
  auth_methods = []
  oauth2_config = None
  url_patterns = []

  def __init__(self):
    """ctor."""
    self._option_def_map = collections.OrderedDict()
    self._options = None
    self._credentials = None

  def AddOptionDef(self, name, value_type=str, choices=None, default=None):
    """Adds a new option definition.

    Option definitions are used to validate user-provided options and render UI.

    Args:
      name: a name.
      value_type: a value type.
      choices: a list of possible values (optional).
      default: a default value (optional).
    Raises:
      ValueError: if an option is already defined.
    """
    if name in self._option_def_map:
      raise ValueError('option %s is already defined' % name)
    self._option_def_map[name] = OptionDef(name, value_type, choices, default)

  def GetOptionDefs(self):
    return self._option_def_map.values()

  def GetOptions(self):
    if not self._options:
      self._options = BuildProviderOptions(self._option_def_map)
    return self._options

  def UpdateOptions(self, **kwargs):
    """Update build provider options.

    Args:
      **kwargs: name value pairs to be updated.
    """
    options = self.GetOptions()
    options.Update(**kwargs)

  def GetCredentials(self):
    """Returns stored credentials.

    Returns:
      a google.auth.credentials.Credentials object.
    """
    return self._credentials

  def UpdateCredentials(self, credentials):
    """Updates stored credentials for a provider.

    Args:
      credentials: a google.auth.credentials.Credentials object.
    """
    self._credentials = credentials

  def GetOAuth2Config(self):
    """Returns OAuth2Config object.

    This must be implemented by a child build provider. If it returns None,
    MTT will assume a provider doesn't need OAuth2.

    Returns:
      a OAuth2Config object or None if a provider doesn't need OAuth2.
    """
    return None

  def ListBuildItems(self, path=None, page_token=None, item_type=None):
    """List build items in a given path.

    Args:
      path: a path within a build channel.
      page_token: an optional page token.
      item_type: a type of build items to list. Returns all types if None.
    Returns:
      (a list of BuildItem object, a next page token)
    """
    raise NotImplementedError('ListBuildItems() is not implemented.')

  def GetBuildItem(self, path):
    """Get a build item.

    Args:
      path: a build item path.
    Returns:
      a BuildItem object. None if the build item does not exist.
    """
    raise NotImplementedError('GetBuildItem() is not implemented.')

  def DeleteBuildItem(self, path):
    """Delete a build item.

    Args:
      path: a build item path.
    """
    raise NotImplementedError('DeleteBuildItem() is not implemented.')

  def DownloadFile(self, path, offset=0):
    """Download a build file.

    Args:
      path: a build file path
      offset: byte offset to read from
    Yields:
      content: chunk of data read
      offset: current position in file
      total_size: total number of bytes in file
    """
    raise NotImplementedError('DownloadFile() is not implemented.')

  def FindBuildItemPath(self, url):
    """Find a build item by a URL.

    If a URL matches any known URL patterns, it will return a corresponding
    build item path. If there is no match, it will return None.

    Args:
      url: a URL.
    Returns:
      a build item path if a URL belongs to this build channel. None otherwise.
    """
    for url_pattern in self.url_patterns:
      m = re.match(url_pattern.url, url)
      if not m:
        continue
      path = url_pattern.path.format(**m.groupdict())
      return path
    return None


def GetBuildProviderClass(name):
  """Retrieves a registered build provider class by its name."""
  return BUILD_PROVIDER_REGISTRY.GetPluginClass(name)


def ListBuildProviderNames():
  """Lists all registered build provider names."""
  return BUILD_PROVIDER_REGISTRY.ListPluginNames()


@attr.s(frozen=True)
class TestRunHookContext(object):
  """Test run hook execution context.

  Attributes:
    test_run: test run being executed
    phase: current execution phase
    latest_attempt: optional latest finished attempt
    next_task: optional next task to be executed
  """
  test_run = attr.ib()
  phase = attr.ib()
  latest_attempt = attr.ib(default=None)
  next_task = attr.ib(default=None)


@attr.s
class TestRunTask(object):
  """Mutable test run attempt not yet sent to the runner."""
  task_id = attr.ib()  # task ID
  command_line = attr.ib()  # command line to execute
  device_serials = attr.ib()  # list of device serials
  extra_options = attr.ib()  # dict of extra options to pass to runner


class TestRunHook(
    six.with_metaclass(TEST_RUN_HOOK_REGISTRY.GetMetaclass(), object)):
  """Base class for all test run hooks."""

  def Execute(self, context):
    """Execute the hook.

    Args:
      context: test run hook execution context.
    """
    raise NotImplementedError()


def GetTestRunHookClass(name):
  """Retrieve a run hook class by its name."""
  return TEST_RUN_HOOK_REGISTRY.GetPluginClass(name)
