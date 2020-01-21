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

"""MTT config objects and utilities for serializing/deserializing them."""
import json
from protorpc import protojson
from protorpc.messages import Message
from protorpc.messages import MessageField
import yaml

from multitest_transport.models import messages
from multitest_transport.models import ndb_models

NAMESPACE_SEPARATOR = '::'


def Encode(config_set):
  """Serializes MTT configuration.

  Args:
    config_set: MTT configuration set
  Returns:
    Configuration set serialized as a YAML string
  """
  msg = messages.Convert(config_set, _ConfigSetMessage)
  return _JsonToYaml(protojson.encode_message(msg))


def Decode(str_or_list):
  """Deserializes MTT configuration from multiple sources.

  Args:
    str_or_list: one or more configuration sets in YAML format
  Returns:
    MTT configuration set
  """
  if not isinstance(str_or_list, list): str_or_list = [str_or_list]
  data = {}
  for string in str_or_list:
    _MergeConfigs(data, yaml.safe_load(string))
  msg = protojson.decode_message(_ConfigSetMessage, json.dumps(data))

  # If url is provided, add it as a namespace to the id to dedupe objects from
  # different configs with the same id and identify which config set each
  # belongs to.
  info = msg.info
  if info:
    for obj in msg.tests + msg.device_actions + msg.build_channels:
      obj.id = _AddNamespaceToId(info.url, obj.id)
  return messages.Convert(msg, ConfigSet)


def _AddNamespaceToId(namespace, obj_id):
  return NAMESPACE_SEPARATOR.join([namespace, obj_id])


def Load(config_set):
  """Load MTT configuration into the DB.

  Args:
    config_set: MTT configuration set
  """
  if config_set.node_config:
    _Load(config_set.node_config)

  objs = (config_set.build_channels + config_set.device_actions +
          config_set.test_run_hooks + config_set.tests)
  for obj in objs:
    _Load(obj)


def _JsonToYaml(string):
  """Converts a JSON string to YAML."""
  obj = json.loads(string)
  return yaml.safe_dump(obj, default_flow_style=False)


def _MergeConfigs(a, b):
  """Performs a deep merge on two config dicts."""
  if isinstance(a, dict) and isinstance(b, dict):
    # merging two dicts: recursively merge
    for key in b:
      a[key] = _MergeConfigs(a[key], b[key]) if key in a else b[key]
    return a
  if isinstance(a, list) and isinstance(b, list):
    # merging two lists: merge elements with same ID and concatenate the rest
    return _MergeLists(a, b)
  # type mismatch, primitives, or None: overwrite existing
  return b


def _MergeLists(a, b):
  """Perform a deep merge on two lists, merging elements with the same ID."""
  result = []
  elements = {}
  for element in a + b:
    if not isinstance(element, dict) or 'id' not in element:
      # no ID to merge with, append element to results
      result.append(element)
      continue
    id_ = element['id']
    if id_ in elements:
      # another element with same ID found, merge the two elements
      elements[id_] = _MergeConfigs(elements[id_], element)
    else:
      # first element with this ID, append
      elements[id_] = element
      result.append(element)
  return result


def _Load(obj):
  """Upsert a model instance."""
  existing = obj.key.get()
  if existing:
    # existing data found, update with new values
    properties = dir(obj.__class__)
    values = dict(
        (k, v) for k, v in obj.to_dict().items() if v and k in properties)
    existing.populate(**values)
    existing.put()
  else:
    # no existing data, create using new values
    obj.put()


# Modify YAML serializer's treatment of unicode strings.
def _RepresentUnicode(self, data):
  return self.represent_str(data.encode('utf-8'))
yaml.add_representer(unicode, _RepresentUnicode)


class ConfigSet(object):
  """MTT configuration set object."""

  def __init__(self, node_config=None, build_channels=None, device_actions=None,
               test_run_hooks=None, tests=None, info=None):
    self.node_config = node_config
    self.build_channels = build_channels or []
    self.device_actions = device_actions or []
    self.test_run_hooks = test_run_hooks or []
    self.tests = tests or []
    self.info = info
    # TODO: add support for test plans

  def __eq__(self, other):
    return (isinstance(other, ConfigSet) and
            self.node_config == other.node_config and
            self.build_channels == other.build_channels and
            self.device_actions == other.device_actions and
            self.test_run_hooks == other.test_run_hooks and
            self.tests == other.tests and
            self.info == other.info)

  def __ne__(self, other):
    return not self.__eq__(other)


class _ConfigSetMessage(Message):
  """MTT configuration set message."""
  node_config = MessageField(messages.NodeConfig, 1)
  build_channels = MessageField(messages.BuildChannelConfig, 2, repeated=True)
  device_actions = MessageField(messages.DeviceAction, 3, repeated=True)
  test_run_hooks = MessageField(messages.TestRunHookConfig, 4, repeated=True)
  tests = MessageField(messages.Test, 5, repeated=True)
  info = MessageField(messages.ConfigSetInfo, 6)


@messages.Converter(ConfigSet, _ConfigSetMessage)
def _ConfigSetConverter(obj):
  return _ConfigSetMessage(
      node_config=messages.Convert(obj.node_config, messages.NodeConfig),
      build_channels=messages.Convert(obj.build_channels,
                                      messages.BuildChannelConfig),
      device_actions=messages.Convert(obj.device_actions,
                                      messages.DeviceAction),
      test_run_hooks=messages.Convert(obj.test_run_hooks,
                                      messages.TestRunHookConfig),
      tests=messages.Convert(obj.tests, messages.Test),
      info=messages.Convert(obj.info, messages.ConfigSetInfo))


@messages.Converter(_ConfigSetMessage, ConfigSet)
def _ConfigSetMessageConverter(msg):
  return ConfigSet(
      node_config=messages.Convert(msg.node_config, ndb_models.NodeConfig),
      build_channels=messages.Convert(msg.build_channels,
                                      ndb_models.BuildChannelConfig),
      device_actions=messages.Convert(msg.device_actions,
                                      ndb_models.DeviceAction),
      test_run_hooks=messages.Convert(msg.test_run_hooks,
                                      ndb_models.TestRunHookConfig),
      tests=messages.Convert(msg.tests, ndb_models.Test),
      info=messages.Convert(msg.info, ndb_models.ConfigSetInfo))
