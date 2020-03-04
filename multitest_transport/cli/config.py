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

"""Utility classes for configuration management."""
from __future__ import print_function

import base64
import collections
import logging
import os.path

import six
from six.moves import configparser

GLOBAL_CONFIG_PATH = os.path.expanduser('~/.config/mtt/mtt.ini')


class ConfigField(object):
  """A config field."""

  _MAX_DISPLAY_LENGTH = 50

  def __init__(
      self, name, prompt=None, value_type=None, default=None, choices=None,
      encode=False):
    """A constructor.

    Args:
      name: a name.
      prompt: a string to display when prompting.
      value_type: a supported value type.
      default: a default value.
      choices: a list of possible values.
      encode: whether to encode a value when saving.
    """
    self._name = name
    self._prompt = prompt or name
    self._type = value_type or str
    self._default = default
    self._choices = choices
    self._encode = encode
    self._value = self._default

  @property
  def value(self):
    return self._value

  def Prompt(self):
    """Prompt a user to enter a value for the field."""
    # Normalize whitespace characters to make it pretty.
    value = ' '.join(str(self._value).split())
    if self._MAX_DISPLAY_LENGTH < len(value):
      value = value[0:self._MAX_DISPLAY_LENGTH] + '...'
    s = '%s [%s]: ' % (self._prompt, value)
    while True:
      try:
        new_value = six.moves.input(s)
        if not new_value:
          logging.info(
              'no new value entered; keeping the current value %s', self._value)
          break
        if new_value.startswith('@'):
          filename = new_value[1:]
          with open(filename) as f:
            new_value = f.read()
        new_value = self._type(new_value)
        if new_value == 'None':
          new_value = None
        if self._choices and new_value not in self._choices:
          raise ValueError('%s is not in %s' % (new_value, self._choices))
        self._value = new_value
        break
      except (IOError, TypeError) as e:
        logging.error('Invalid value: %s', e)

  def Load(self, parser, section):
    """Load a value from a config parser.

    Args:
      parser: a ConfigParser object.
      section: a config section.
    """
    try:
      value = parser.get(section, self._name)
      if value and self._encode:
        value = base64.b64decode(value)
      self._value = value or None
    except (configparser.NoSectionError, configparser.NoOptionError):
      pass

  def Save(self, parser, section):
    """Save a value to a config parser.

    Args:
      parser: a ConfigParser object.
      section: a config section.
    """
    if not parser.has_section(section):
      parser.add_section(section)
    value = self._value
    if value and self._encode:
      value = base64.b64encode(value)
    parser.set(section, self._name, value or '')


class Config(object):
  """A class to manage app configurations."""

  _DEFAULT_SECTION = 'general'
  # Set an empty dict avoid errors from __init__.
  _field_map = {}

  def __init__(self, filename, section=None, field_map=None):
    self._filename = filename
    self._section = section or self._DEFAULT_SECTION
    self._field_map = field_map or collections.OrderedDict()

  def __getattr__(self, name):
    if name not in self._field_map:
      raise AttributeError
    return self._field_map[name].value

  def __setattr__(self, name, value):
    if name in self._field_map:
      self._field_map[name].value = value
      return
    super(Config, self).__setattr__(name, value)

  @property
  def field_map(self):
    return self._field_map

  def DefineField(self, name, *args, **kwargs):
    """Add a field."""
    field = ConfigField(name, *args, **kwargs)
    self._field_map[name] = field

  def Prompt(self):
    """Prompt a user to change configuration values."""
    for field in self._field_map.values():
      field.Prompt()

  def Load(self):
    """Load field values from a config file."""
    if not os.path.exists(self._filename):
      logging.warning('config file does not exist: %s', self._filename)
    parser = configparser.SafeConfigParser()
    parser.read(self._filename)
    for field in self._field_map.values():
      field.Load(parser, self._section)

  def Save(self):
    """Save field values to a config file."""
    parser = configparser.SafeConfigParser()
    for field in self._field_map.values():
      field.Save(parser, self._section)
    dirname = os.path.dirname(self._filename)
    if not os.path.exists(dirname):
      os.makedirs(dirname)
    with open(self._filename, 'w') as f:
      parser.write(f)


config = Config(GLOBAL_CONFIG_PATH)
# The default value for this field is chosen dynamically in cli.
config.DefineField('docker_image', prompt='Docker image')
config.DefineField('service_account_json_key_path',
                   prompt='The service account json key to use')
config.DefineField('custom_adb_path',
                   prompt='Path to custom ADB tool')
config.Load()
