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

"""API messages."""

import collections
import logging

from protorpc import message_types
from protorpc import messages
import pytz
from tradefed_cluster import api_messages
from tradefed_cluster import common

from google.appengine.ext import ndb

from multitest_transport.plugins import base as plugins
from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.util import env
from multitest_transport.util import file_util

_DEFAULT_CLUSTER = 'default'
_TEST_RUN_CANCEL_REASON_MAP = {
    common.CancelReason.QUEUE_TIMEOUT: 'Queue timeout',
    common.CancelReason.REQUEST_API: 'User requested',
    common.CancelReason.COMMAND_ALREADY_CANCELED: 'Command already canceled',
    common.CancelReason.REQUEST_ALREADY_CANCELED: 'Request already canceled',
    common.CancelReason.COMMAND_NOT_EXECUTABLE: 'Invalid command',
    common.CancelReason.INVALID_REQUEST: 'Invalid request',
}

_convert_func_map = {}


def Converter(from_cls, to_cls):
  """A decorator to register a message converter.

  Args:
    from_cls: a class to convert from.
    to_cls: a class to convert to.
  Returns:
    a decorator function.
  """
  def Decorator(func):
    _convert_func_map[(from_cls, to_cls)] = func
    return func
  return Decorator


def _ConvertObject(obj, to_cls, from_cls):
  """Converts an object to a given class.

  Args:
    obj: an object.
    to_cls: a class to convert to.
    from_cls: a class to convert from (optional).
  Returns:
    a converted object.
  Raises:
    ValueError: if there's no registered converter function.
  """
  if obj is None:
    return None
  from_cls = from_cls or type(obj)
  func = _convert_func_map.get((from_cls, to_cls))
  if not func:
    raise ValueError('no convert function for %s -> %s' % (from_cls, to_cls))
  return func(obj)


def Convert(obj_or_list, to_cls, from_cls=None):
  """Converts an object or a list objects to a given class.

  Args:
    obj_or_list: an object or a list of objects.
    to_cls: a class to convert to.
    from_cls: a class to convert from (optional).
  Returns:
    a converted object or a list of conveted objects.
  """
  if isinstance(obj_or_list, collections.Iterable):
    return [_ConvertObject(obj, to_cls, from_cls) for obj in obj_or_list]
  return _ConvertObject(obj_or_list, to_cls, from_cls)


def ConvertToKey(model_cls, id_):
  """Convert to a ndb.Key object.

  Args:
    model_cls: a model class.
    id_: an object ID.
  Returns:
    a ndb.Key object.
  """
  if id_ is None:
    return None
  try:
    id_ = int(id_)
  except ValueError:
    pass
  return ndb.Key(model_cls, id_)


def _AddTimezone(datetime, timezone=pytz.UTC):
  """Adds timezone to an NDB datetime (which doesn't store timezone)."""
  if datetime:
    return datetime.replace(tzinfo=timezone)  

class AuthorizationInfo(messages.Message):
  """OAuth2 authorization information.

  Attributes:
    url: an authorization url.
    is_manual: a boolean value which tell us to start automatic or manual
      copy/paste flow
  """
  url = messages.StringField(1, required=True)
  is_manual = messages.BooleanField(2, required=True)


class SimpleMessage(messages.Message):
  """Simple string message."""
  value = messages.StringField(1, required=True)


class NameValuePair(messages.Message):
  """A generic name-value pair to store an option.

  Attributes:
    name: a name.
    value: a value.
  """
  name = messages.StringField(1, required=True)
  value = messages.StringField(2)


class NameMultiValuePair(messages.Message):
  """A generic name-multi value pair to store an option.

  Attributes:
    name: a name.
    values: a value.
  """
  name = messages.StringField(1, required=True)
  values = messages.StringField(2, repeated=True)


def ConvertNameValuePairs(pairs, to_cls):
  """Convert message and NDB model name-value(s) pairs."""
  is_multi = to_cls in (NameMultiValuePair, ndb_models.NameMultiValuePair)
  d = collections.OrderedDict()
  for pair in pairs:
    if pair.name in d:
      logging.warn('Duplicate key %s in %s', pair.name, pairs)
    if is_multi:
      d[pair.name] = to_cls(name=pair.name, values=pair.values)
    else:
      d[pair.name] = to_cls(name=pair.name, value=pair.value)
  return d.values()


class FileSegment(messages.Message):
  """Partial file content."""
  offset = messages.IntegerField(1)
  length = messages.IntegerField(2)
  lines = messages.StringField(3, repeated=True)


@Converter(file_util.FileSegment, FileSegment)
def _FileSegmentConverter(obj):
  lines = [unicode(line, encoding='utf-8', errors='ignore')
           for line in obj.lines]
  return FileSegment(offset=obj.offset, length=obj.length, lines=lines)


class TestResourceDef(messages.Message):
  """A test resource definition for a test."""
  name = messages.StringField(1, required=True)
  default_download_url = messages.StringField(2)
  test_resource_type = messages.EnumField(ndb_models.TestResourceType, 3)


@Converter(ndb_models.TestResourceDef, TestResourceDef)
def _TestResourceDefConverter(obj):
  return TestResourceDef(
      name=obj.name, default_download_url=obj.default_download_url,
      test_resource_type=obj.test_resource_type)


@Converter(TestResourceDef, ndb_models.TestResourceDef)
def _TestResourceDefMessageConverter(msg):
  return ndb_models.TestResourceDef(
      name=msg.name, default_download_url=msg.default_download_url,
      test_resource_type=msg.test_resource_type)


class Test(messages.Message):
  """A test."""
  id = messages.StringField(1)
  name = messages.StringField(2, required=True)
  test_resource_defs = messages.MessageField(TestResourceDef, 3, repeated=True)
  command = messages.StringField(4)
  env_vars = messages.MessageField(NameValuePair, 5, repeated=True)
  output_file_patterns = messages.StringField(6, repeated=True)
  result_file = messages.StringField(7)
  setup_scripts = messages.StringField(8, repeated=True)
  jvm_options = messages.StringField(9, repeated=True)
  java_properties = messages.MessageField(NameValuePair, 10, repeated=True)
  context_file_dir = messages.StringField(11)
  context_file_pattern = messages.StringField(12)
  retry_command_line = messages.StringField(13)
  runner_sharding_args = messages.StringField(14)


@Converter(ndb_models.Test, Test)
def _TestConverter(obj):
  return Test(
      id=str(obj.key.id()) if obj.key else None,
      name=obj.name,
      test_resource_defs=Convert(obj.test_resource_defs, TestResourceDef),
      command=obj.command,
      env_vars=ConvertNameValuePairs(obj.env_vars, NameValuePair),
      output_file_patterns=obj.output_file_patterns,
      result_file=obj.result_file,
      setup_scripts=obj.setup_scripts,
      jvm_options=obj.jvm_options,
      java_properties=ConvertNameValuePairs(obj.java_properties, NameValuePair),
      context_file_dir=obj.context_file_dir,
      context_file_pattern=obj.context_file_pattern,
      retry_command_line=obj.retry_command_line,
      runner_sharding_args=obj.runner_sharding_args)


@Converter(Test, ndb_models.Test)
def _TestMessageConverter(msg):
  return ndb_models.Test(
      key=ConvertToKey(ndb_models.Test, msg.id),
      name=msg.name,
      test_resource_defs=Convert(msg.test_resource_defs,
                                 ndb_models.TestResourceDef),
      command=msg.command,
      env_vars=ConvertNameValuePairs(msg.env_vars, ndb_models.NameValuePair),
      setup_scripts=msg.setup_scripts,
      output_file_patterns=msg.output_file_patterns,
      result_file=msg.result_file,
      jvm_options=msg.jvm_options,
      java_properties=ConvertNameValuePairs(
          msg.java_properties, ndb_models.NameValuePair),
      context_file_dir=msg.context_file_dir,
      context_file_pattern=msg.context_file_pattern,
      retry_command_line=msg.retry_command_line,
      runner_sharding_args=msg.runner_sharding_args)


class TestList(messages.Message):
  """A list of tests."""
  tests = messages.MessageField(Test, 1, repeated=True)


class BuildChannelConfig(messages.Message):
  """A build channel configuration."""
  id = messages.StringField(1, required=True)
  name = messages.StringField(2, required=True)
  provider_name = messages.StringField(3, required=True)
  options = messages.MessageField(NameValuePair, 4, repeated=True)


@Converter(ndb_models.BuildChannelConfig, BuildChannelConfig)
def _BuildChannelConfigConverter(obj):
  return BuildChannelConfig(
      id=str(obj.key.id()) if obj.key else None,
      name=obj.name,
      provider_name=obj.provider_name,
      options=ConvertNameValuePairs(obj.options, NameValuePair))


@Converter(BuildChannelConfig, ndb_models.BuildChannelConfig)
def _BuildChannelConfigMessageConverter(msg):
  return ndb_models.BuildChannelConfig(
      key=ConvertToKey(ndb_models.BuildChannelConfig, msg.id),
      name=msg.name,
      provider_name=msg.provider_name,
      options=ConvertNameValuePairs(msg.options, ndb_models.NameValuePair))


class BuildChannel(messages.Message):
  """A build channel, which combines channel config and provider properties."""
  id = messages.StringField(1, required=True)
  name = messages.StringField(2, required=True)
  provider_name = messages.StringField(3, required=True)
  auth_state = messages.EnumField(
      ndb_models.BuildChannelAuthState, 4, required=True)
  need_auth = messages.BooleanField(5, required=True)


@Converter(build.BuildChannel, BuildChannel)
def _BuildChannelConverter(obj):
  authorizable = True if obj.oauth2_config else False
  return BuildChannel(
      id=str(obj.id),
      name=obj.name,
      provider_name=obj.provider_name,
      auth_state=obj.auth_state,
      need_auth=authorizable)


class BuildChannelList(messages.Message):
  """A list of build channels."""
  build_channels = messages.MessageField(BuildChannel, 1, repeated=True)


class OptionDef(messages.Message):
  """A build channel provider option definition."""
  name = messages.StringField(1, required=True)
  value_type = messages.StringField(2, required=True)
  choices = messages.StringField(3, repeated=True)
  default = messages.StringField(4)


@Converter(plugins.OptionDef, OptionDef)
def _OptionDefConverter(obj):
  return OptionDef(
      name=obj.name,
      value_type=obj.value_type.__name__,
      choices=obj.choices or [],
      default=obj.default)


class BuildChannelProvider(messages.Message):
  """Information about a build channel provider."""
  name = messages.StringField(1, required=True)
  option_defs = messages.MessageField(OptionDef, 2, repeated=True)


class BuildChannelProviderList(messages.Message):
  """A list of build channel providers."""
  build_channel_providers = messages.MessageField(
      BuildChannelProvider, 1, repeated=True)


class BuildItem(messages.Message):
  """A build item."""
  name = messages.StringField(1)
  path = messages.StringField(2)
  is_file = messages.BooleanField(3)
  size = messages.IntegerField(4)
  timestamp = message_types.DateTimeField(5)
  origin_url = messages.StringField(6)
  description = messages.StringField(7)


class BuildItemList(messages.Message):
  """A list of build items."""
  build_items = messages.MessageField(BuildItem, 1, repeated=True)
  next_page_token = messages.StringField(2)


class TradefedConfigObject(messages.Message):
  class_name = messages.StringField(1, required=True)
  option_values = messages.MessageField(NameMultiValuePair, 2, repeated=True)


@Converter(ndb_models.TradefedConfigObject, TradefedConfigObject)
def _TradefedConfigObjectConverter(obj):
  return TradefedConfigObject(
      class_name=obj.class_name,
      option_values=ConvertNameValuePairs(
          obj.option_values, NameMultiValuePair))


@Converter(TradefedConfigObject, ndb_models.TradefedConfigObject)
def _TradefedConfigObjectMessageConverter(msg):
  return ndb_models.TradefedConfigObject(
      class_name=msg.class_name,
      option_values=ConvertNameValuePairs(
          msg.option_values, ndb_models.NameMultiValuePair))


class ConfigSetInfo(messages.Message):
  """Metadata for a config set."""
  url = messages.StringField(1, required=True)
  hash = messages.StringField(2)
  name = messages.StringField(3, required=True)
  description = messages.StringField(4)
  last_update_time = messages.StringField(5)
  status = messages.EnumField(ndb_models.ConfigSetStatus, 6)


@Converter(ndb_models.ConfigSetInfo, ConfigSetInfo)
def _ConfigSetInfoConverter(obj):
  return ConfigSetInfo(
      url=obj.url,
      hash=obj.hash,
      name=obj.name,
      description=obj.description,
      last_update_time=obj.last_update_time,
  )


@Converter(ConfigSetInfo, ndb_models.ConfigSetInfo)
def _ConfigSetInfoMessageConverter(msg):
  return ndb_models.ConfigSetInfo(
      key=ConvertToKey(ndb_models.ConfigSetInfo, msg.url),
      url=msg.url,
      hash=msg.hash,
      name=msg.name,
      description=msg.description,
      last_update_time=msg.last_update_time,
  )


class ConfigSetInfoList(messages.Message):
  config_set_infos = messages.MessageField(ConfigSetInfo, 1, repeated=True)


@Converter(ndb_models.ConfigSetInfoList, ConfigSetInfoList)
def _ConfigSetInfoListConverter(obj):
  return ConfigSetInfoList(
      config_set_infos=Convert(obj.config_set_infos, ConfigSetInfo))


@Converter(ConfigSetInfoList, ndb_models.ConfigSetInfoList)
def _ConfigSetInfoListMessageConverter(msg):
  return ndb_models.ConfigSetInfoList(
      config_set_infos=Convert(msg.config_set_infos,
                               ndb_models.ConfigSetInfo))


class DeviceAction(messages.Message):
  """A device action."""
  id = messages.StringField(1)
  name = messages.StringField(2, required=True)
  description = messages.StringField(3)
  test_resource_defs = messages.MessageField(TestResourceDef, 4, repeated=True)
  tradefed_target_preparers = messages.MessageField(
      TradefedConfigObject, 5, repeated=True)


@Converter(ndb_models.DeviceAction, DeviceAction)
def _DeviceActionConverter(obj):
  return DeviceAction(
      id=str(obj.key.id()) if obj.key else None,
      name=obj.name,
      description=obj.description,
      test_resource_defs=Convert(obj.test_resource_defs, TestResourceDef),
      tradefed_target_preparers=Convert(
          obj.tradefed_target_preparers, TradefedConfigObject))


@Converter(DeviceAction, ndb_models.DeviceAction)
def _DeviceActionMessageConverter(msg):
  return ndb_models.DeviceAction(
      key=ConvertToKey(ndb_models.DeviceAction, msg.id),
      name=msg.name,
      description=msg.description,
      test_resource_defs=Convert(
          msg.test_resource_defs, ndb_models.TestResourceDef),
      tradefed_target_preparers=Convert(
          msg.tradefed_target_preparers, ndb_models.TradefedConfigObject))


class DeviceActionList(messages.Message):
  """A list of device actions."""
  device_actions = messages.MessageField(DeviceAction, 1, repeated=True)
  next_page_token = messages.StringField(2)


class TestRunAction(messages.Message):
  """A test run action."""
  id = messages.StringField(1)
  name = messages.StringField(2, required=True)
  description = messages.StringField(3)
  hook_class_name = messages.StringField(4, required=True)
  phases = messages.EnumField(ndb_models.TestRunPhase, 5, repeated=True)
  options = messages.MessageField(NameValuePair, 6, repeated=True)
  tradefed_result_reporters = messages.MessageField(
      TradefedConfigObject, 7, repeated=True)
  authorization_state = messages.EnumField(ndb_models.AuthorizationState, 8)


@Converter(ndb_models.TestRunAction, TestRunAction)
def _TestRunActionConverter(obj):
  return TestRunAction(
      id=str(obj.key.id()) if obj.key else None,
      name=obj.name,
      description=obj.description,
      hook_class_name=obj.hook_class_name,
      phases=obj.phases,
      options=ConvertNameValuePairs(obj.options, NameValuePair),
      tradefed_result_reporters=Convert(
          obj.tradefed_result_reporters, TradefedConfigObject))


@Converter(TestRunAction, ndb_models.TestRunAction)
def _TestRunActionMessageConverter(msg):
  return ndb_models.TestRunAction(
      key=ConvertToKey(ndb_models.TestRunAction, msg.id),
      name=msg.name,
      description=msg.description,
      hook_class_name=msg.hook_class_name,
      phases=msg.phases,
      options=ConvertNameValuePairs(msg.options, ndb_models.NameValuePair),
      tradefed_result_reporters=Convert(
          msg.tradefed_result_reporters, ndb_models.TradefedConfigObject))


class TestRunActionList(messages.Message):
  """A list of test run actions."""
  actions = messages.MessageField(TestRunAction, 1, repeated=True)


class TestRunActionRef(messages.Message):
  """A test run action reference."""
  action_id = messages.StringField(1)
  options = messages.MessageField(NameValuePair, 2, repeated=True)


@Converter(ndb_models.TestRunActionRef, TestRunActionRef)
def _TestRunActionRefConverter(obj):
  return TestRunActionRef(
      action_id=str(obj.action_key.id()) if obj.action_key else None,
      options=ConvertNameValuePairs(obj.options, NameValuePair))


@Converter(TestRunActionRef, ndb_models.TestRunActionRef)
def _TestRunActionRefMessageConverter(msg):
  return ndb_models.TestRunActionRef(
      action_key=ConvertToKey(ndb_models.TestRunAction, msg.action_id),
      options=ConvertNameValuePairs(msg.options, ndb_models.NameValuePair))


class TestRunConfig(messages.Message):
  """A test run config."""
  test_id = messages.StringField(1, required=True)
  cluster = messages.StringField(2, required=True, default=_DEFAULT_CLUSTER)
  command = messages.StringField(3, required=True, default='')
  retry_command = messages.StringField(4, required=True, default='')
  run_target = messages.StringField(5, required=True)
  run_count = messages.IntegerField(6, required=True, default=1)
  shard_count = messages.IntegerField(7, required=True, default=1)
  sharding_mode = messages.EnumField(ndb_models.ShardingMode, 8)
  extra_args = messages.StringField(9)  # TODO: Deprecated
  retry_extra_args = messages.StringField(10)  # TODO: Deprecated
  max_retry_on_test_failures = messages.IntegerField(11)
  queue_timeout_seconds = messages.IntegerField(
      12, required=True, default=env.DEFAULT_QUEUE_TIMEOUT_SECONDS)
  output_idle_timeout_seconds = messages.IntegerField(
      13, default=env.DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS)
  before_device_action_ids = messages.StringField(14, repeated=True)
  test_run_action_refs = messages.MessageField(
      TestRunActionRef, 15, repeated=True)


@Converter(ndb_models.TestRunConfig, TestRunConfig)
def _TestRunConfigConverter(obj):
  """Converts test run configs."""
  if not obj.command or not obj.retry_command:
    test = obj.test_key.get()
    if not obj.command:
      obj.command = test.command
      if obj.extra_args:
        obj.command += ' %s' % obj.extra_args
    if not obj.retry_command:
      obj.retry_command = test.retry_command_line
      if obj.retry_extra_args:
        obj.retry_command += ' %s' % obj.retry_extra_args
  return TestRunConfig(
      test_id=str(obj.test_key.id()) if obj.test_key else None,
      cluster=obj.cluster,
      command=obj.command,
      retry_command=obj.retry_command,
      run_target=obj.run_target,
      run_count=obj.run_count,
      shard_count=obj.shard_count,
      sharding_mode=obj.sharding_mode,
      max_retry_on_test_failures=obj.max_retry_on_test_failures,
      queue_timeout_seconds=obj.queue_timeout_seconds,
      output_idle_timeout_seconds=obj.output_idle_timeout_seconds,
      before_device_action_ids=[
          str(key.id()) for key in obj.before_device_action_keys
      ],
      test_run_action_refs=Convert(
          obj.test_run_action_refs, TestRunActionRef))


@Converter(TestRunConfig, ndb_models.TestRunConfig)
def _TestRunConfigMessageConverter(msg):
  return ndb_models.TestRunConfig(
      test_key=ConvertToKey(ndb_models.Test, msg.test_id),
      cluster=msg.cluster,
      command=msg.command,
      retry_command=msg.retry_command,
      run_target=msg.run_target,
      run_count=msg.run_count,
      shard_count=msg.shard_count,
      extra_args=msg.extra_args,  # TODO: Deprecated
      retry_extra_args=msg.retry_extra_args,  # TODO: Deprecated
      max_retry_on_test_failures=msg.max_retry_on_test_failures,
      queue_timeout_seconds=msg.queue_timeout_seconds,
      output_idle_timeout_seconds=msg.output_idle_timeout_seconds,
      before_device_action_keys=[
          ConvertToKey(ndb_models.DeviceAction, device_action_id)
          for device_action_id in msg.before_device_action_ids
      ],
      test_run_action_refs=Convert(
          msg.test_run_action_refs, ndb_models.TestRunActionRef))


class TestResourcePipe(messages.Message):
  """A test resource pipe for a test plan."""
  name = messages.StringField(1, required=True)
  url = messages.StringField(2)
  test_resource_type = messages.EnumField(ndb_models.TestResourceType, 3)


@Converter(ndb_models.TestResourcePipe, TestResourcePipe)
def _TestResourcePipeConverter(obj):
  return TestResourcePipe(
      name=obj.name,
      url=obj.url,
      test_resource_type=obj.test_resource_type)


@Converter(TestResourcePipe, ndb_models.TestResourcePipe)
def _TestResourcePipeMessageConverter(msg):
  return ndb_models.TestResourcePipe(
      name=msg.name,
      url=msg.url,
      test_resource_type=msg.test_resource_type)


class TestPlan(messages.Message):
  """A test plan."""
  id = messages.StringField(1)
  name = messages.StringField(2, required=True)
  labels = messages.StringField(3, repeated=True)
  cron_exp = messages.StringField(4)
  test_run_configs = messages.MessageField(TestRunConfig, 5, repeated=True)
  test_resource_pipes = messages.MessageField(
      TestResourcePipe, 6, repeated=True)
  before_device_action_ids = messages.StringField(7, repeated=True)
  last_run_time = message_types.DateTimeField(8)
  next_run_time = message_types.DateTimeField(9)


@Converter(ndb_models.TestPlan, TestPlan)
def _TestPlanConverter(obj):
  status = None
  if obj.key.id():
    status = ndb_models.TestPlanStatus.query(ancestor=obj.key).get()
  return TestPlan(
      id=str(obj.key.id()),
      name=obj.name,
      labels=obj.labels,
      cron_exp=obj.cron_exp,
      test_run_configs=Convert(obj.test_run_configs, TestRunConfig),
      test_resource_pipes=Convert(obj.test_resource_pipes, TestResourcePipe),
      before_device_action_ids=[
          str(key.id()) for key in obj.before_device_action_keys
      ],
      last_run_time=_AddTimezone(status.last_run_time) if status else None,
      next_run_time=_AddTimezone(status.next_run_time) if status else None,
  )


@Converter(TestPlan, ndb_models.TestPlan)
def _TestPlanMessageConverter(msg):
  return ndb_models.TestPlan(
      key=ConvertToKey(ndb_models.TestPlan, getattr(msg, 'id')),
      name=msg.name,
      labels=msg.labels,
      cron_exp=msg.cron_exp,
      test_run_configs=Convert(msg.test_run_configs, ndb_models.TestRunConfig),
      test_resource_pipes=Convert(
          msg.test_resource_pipes, ndb_models.TestResourcePipe),
      before_device_action_keys=[
          ConvertToKey(ndb_models.DeviceAction, device_action_id)
          for device_action_id in msg.before_device_action_ids
      ])


class TestPlanList(messages.Message):
  """A list of test plans."""
  test_plans = messages.MessageField(TestPlan, 1, repeated=True)


class TestResourceObj(messages.Message):
  """A test resource object for a test."""
  name = messages.StringField(1)
  url = messages.StringField(2)
  cache_url = messages.StringField(3)
  test_resource_type = messages.EnumField(ndb_models.TestResourceType, 4)


@Converter(ndb_models.TestResourceObj, TestResourceObj)
def _TestResourceObjConverter(obj):
  return TestResourceObj(
      name=obj.name, url=obj.url, cache_url=obj.cache_url,
      test_resource_type=obj.test_resource_type)


class TestContextObj(messages.Message):
  """A test context object."""
  command_line = messages.StringField(1)
  env_vars = messages.MessageField(NameValuePair, 2, repeated=True)
  test_resources = messages.MessageField(TestResourceObj, 3, repeated=True)


@Converter(ndb_models.TestContextObj, TestContextObj)
def _TestContextObjConverter(obj):
  return TestContextObj(
      command_line=obj.command_line,
      env_vars=ConvertNameValuePairs(obj.env_vars, NameValuePair),
      test_resources=Convert(obj.test_resources, TestResourceObj))


class TestPackageInfo(messages.Message):
  """A test package info."""
  build_number = messages.StringField(1)
  target_architecture = messages.StringField(2)
  name = messages.StringField(3)
  fullname = messages.StringField(4)
  version = messages.StringField(5)


@Converter(ndb_models.TestPackageInfo, TestPackageInfo)
def _TestPackageInfoConverter(obj):
  return TestPackageInfo(
      build_number=obj.build_number,
      target_architecture=obj.target_architecture,
      name=obj.name,
      fullname=obj.fullname,
      version=obj.version)


class TestDeviceInfo(messages.Message):
  """A test device info."""
  device_serial = messages.StringField(1)
  hostname = messages.StringField(2)
  run_target = messages.StringField(3)
  build_id = messages.StringField(4)
  product = messages.StringField(5)
  sdk_version = messages.StringField(7)


@Converter(ndb_models.TestDeviceInfo, TestDeviceInfo)
def _TestDeviceInfoConverter(obj):
  return TestDeviceInfo(
      device_serial=obj.device_serial,
      hostname=obj.hostname,
      run_target=obj.run_target,
      build_id=obj.build_id,
      product=obj.product,
      sdk_version=obj.sdk_version)


class TestRun(messages.Message):
  """A test run."""
  id = messages.StringField(1)
  prev_test_run_id = messages.StringField(2)
  user = messages.StringField(3)
  labels = messages.StringField(4, repeated=True)
  test_plan = messages.MessageField(TestPlan, 5)
  test = messages.MessageField(Test, 6)
  test_run_config = messages.MessageField(TestRunConfig, 7)
  test_resources = messages.MessageField(TestResourceObj, 8, repeated=True)
  state = messages.EnumField(ndb_models.TestRunState, 9)
  state_info = messages.StringField(10)
  output_url = messages.StringField(11)
  prev_test_context = messages.MessageField(TestContextObj, 12)
  next_test_context = messages.MessageField(TestContextObj, 13)

  request_id = messages.StringField(14)
  total_test_count = messages.IntegerField(15)
  failed_test_count = messages.IntegerField(16)
  failed_test_run_count = messages.IntegerField(17)

  create_time = message_types.DateTimeField(18)
  update_time = message_types.DateTimeField(19)

  before_device_actions = messages.MessageField(DeviceAction, 20, repeated=True)
  test_run_actions = messages.MessageField(TestRunAction, 21, repeated=True)

  test_devices = messages.MessageField(TestDeviceInfo, 22, repeated=True)
  test_package_info = messages.MessageField(TestPackageInfo, 23)


@Converter(ndb_models.TestRun, TestRun)
def _TestRunConverter(obj):
  """Converts a ndb_models.TestRun object to a message."""
  # TestRun.test stores a snapshot copy of a test at test run creation time.
  test_msg = Convert(obj.test, Test)
  test_run_config_msg = Convert(obj.test_run_config, TestRunConfig)
  # Grab a valid test id from test_run_config since a snapshot copy is missing
  # a key.
  test_msg.id = test_run_config_msg.test_id

  return TestRun(
      id=str(obj.key.id()),
      prev_test_run_id=(str(obj.prev_test_run_key.id())
                        if obj.prev_test_run_key else None),
      user=obj.user,
      labels=obj.labels,
      test_plan=(
          Convert(obj.test_plan_key.get(), TestPlan)
          if obj.test_plan_key else None),
      test=test_msg,
      test_run_config=test_run_config_msg,
      test_resources=Convert(obj.test_resources, TestResourceObj),
      state=obj.state,
      state_info=_GetTestRunStateInfo(obj),
      output_url=file_util.GetStorageUrl(obj.output_storage, obj.output_path),
      prev_test_context=Convert(obj.prev_test_context, TestContextObj),
      next_test_context=Convert(obj.next_test_context, TestContextObj),
      request_id=obj.request_id,
      total_test_count=obj.total_test_count,
      failed_test_count=obj.failed_test_count,
      failed_test_run_count=obj.failed_test_run_count,
      create_time=_AddTimezone(obj.create_time),
      update_time=_AddTimezone(obj.update_time),
      before_device_actions=Convert(obj.before_device_actions, DeviceAction),
      test_run_actions=Convert(obj.test_run_actions, TestRunAction),
      test_devices=Convert(obj.test_devices, TestDeviceInfo),
      test_package_info=Convert(obj.test_package_info, TestPackageInfo)
  )


def _GetTestRunStateInfo(obj):
  """Determine an ndb_models.TestRun's relevant state information."""
  if obj.state == ndb_models.TestRunState.ERROR:
    return obj.error_reason
  if obj.state == ndb_models.TestRunState.CANCELED:
    return _TEST_RUN_CANCEL_REASON_MAP.get(obj.cancel_reason)
  if obj.state == ndb_models.TestRunState.PENDING:
    # TODO: consider adding a download progress endpoint instead
    for resource in obj.test_resources:
      if resource.cache_url:
        continue  # already downloaded
      tracker = ndb_models.TestResourceTracker.get_by_id(resource.url)
      if tracker is None or tracker.completed:
        continue  # download either not started or already completed
      return 'Downloading %s [%d%%]' % (resource.name,
                                        100 * tracker.download_progress)
  return None


class TestRunSummary(messages.Message):
  """A test run."""
  id = messages.StringField(1)
  labels = messages.StringField(2, repeated=True)
  test_name = messages.StringField(3)
  run_target = messages.StringField(4)
  state = messages.EnumField(ndb_models.TestRunState, 5)
  test_package_info = messages.MessageField(TestPackageInfo, 6)
  test_devices = messages.MessageField(TestDeviceInfo, 7, repeated=True)
  total_test_count = messages.IntegerField(8)
  failed_test_count = messages.IntegerField(9)
  failed_test_run_count = messages.IntegerField(10)
  create_time = message_types.DateTimeField(11)
  update_time = message_types.DateTimeField(12)


@Converter(ndb_models.TestRunSummary, TestRunSummary)
def _TestRunSummaryConverter(obj):
  """Converts a ndb_models.TestRunSummary object to a message."""
  return TestRunSummary(
      id=str(obj.key.id()),
      labels=obj.labels,
      test_name=obj.test_name,
      run_target=obj.run_target,
      state=obj.state,
      test_package_info=Convert(obj.test_package_info, TestPackageInfo),
      test_devices=Convert(obj.test_devices, TestDeviceInfo),
      total_test_count=obj.total_test_count,
      failed_test_count=obj.failed_test_count,
      failed_test_run_count=obj.failed_test_run_count,
      create_time=_AddTimezone(obj.create_time),
      update_time=_AddTimezone(obj.update_time))


class TestRunSummaryList(messages.Message):
  """A list of test run summaries."""
  test_runs = messages.MessageField(TestRunSummary, 1, repeated=True)
  prev_page_token = messages.StringField(2)
  next_page_token = messages.StringField(3)


class TestRunMetadata(messages.Message):
  """Combination of a test run and its command attempts."""
  test_run = messages.MessageField(TestRun, 1, required=True)
  command_attempts = messages.MessageField(
      api_messages.CommandAttemptMessage, 2, repeated=True)


class TestRunMetadataList(messages.Message):
  """List of test run metadata."""
  test_runs = messages.MessageField(TestRunMetadata, 1, repeated=True)


class RerunContext(messages.Message):
  """Previous test run context used for rerun.

  Represents either a local test run (ID provided) or a remote test run (context
  file already uploaded to local file storage and filename provided).
  """
  test_run_id = messages.StringField(1)
  context_filename = messages.StringField(2)


class NewTestRunRequest(messages.Message):
  """A request object for test_runs.new API."""
  labels = messages.StringField(1, repeated=True)
  test_run_config = messages.MessageField(TestRunConfig, 2)
  test_resource_pipes = messages.MessageField(
      TestResourcePipe, 3, repeated=True)
  rerun_context = messages.MessageField(RerunContext, 4)


class TestArtifact(messages.Message):
  """A test artifact.

  This represents a file generated from a test run.
  """
  name = messages.StringField(1)
  path = messages.StringField(2)
  download_url = messages.StringField(3)
  size = messages.IntegerField(4)


class TestArtifactList(messages.Message):
  """A list of test artifacts."""
  test_artifacts = messages.MessageField(TestArtifact, 1, repeated=True)
  next_page_token = messages.StringField(2)


class ProxyConfig(messages.Message):
  """Proxy config."""
  http_proxy = messages.StringField(1)
  https_proxy = messages.StringField(2)
  ftp_proxy = messages.StringField(3)
  no_proxy = messages.StringField(4)


@Converter(ndb_models.ProxyConfig, ProxyConfig)
def _ProxyConfigConverter(obj):
  return ProxyConfig(
      http_proxy=obj.http_proxy,
      https_proxy=obj.https_proxy,
      ftp_proxy=obj.ftp_proxy,
      no_proxy=obj.no_proxy)


@Converter(ProxyConfig, ndb_models.ProxyConfig)
def _ProxyConfigMessageConverter(msg):
  return ndb_models.ProxyConfig(
      http_proxy=msg.http_proxy,
      https_proxy=msg.https_proxy,
      ftp_proxy=msg.ftp_proxy,
      no_proxy=msg.no_proxy)


class NodeConfig(messages.Message):
  """Node config."""
  env_vars = messages.MessageField(NameValuePair, 1, repeated=True)
  test_resource_default_download_urls = messages.MessageField(
      NameValuePair, 2, repeated=True)
  proxy_config = messages.MessageField(ProxyConfig, 3)


@Converter(ndb_models.NodeConfig, NodeConfig)
def _NodeConfigConverter(obj):
  return NodeConfig(
      env_vars=ConvertNameValuePairs(obj.env_vars, NameValuePair),
      test_resource_default_download_urls=ConvertNameValuePairs(
          obj.test_resource_default_download_urls, NameValuePair),
      proxy_config=Convert(obj.proxy_config, ProxyConfig))


@Converter(NodeConfig, ndb_models.NodeConfig)
def _NodeConfigMessageConverter(msg):
  """Converts a NodeConfig message into an object."""
  return ndb_models.NodeConfig(
      id=ndb_models.NODE_CONFIG_ID,
      env_vars=ConvertNameValuePairs(msg.env_vars, ndb_models.NameValuePair),
      test_resource_default_download_urls=ConvertNameValuePairs(
          msg.test_resource_default_download_urls, ndb_models.NameValuePair),
      proxy_config=Convert(msg.proxy_config, ndb_models.ProxyConfig))


class PrivateNodeConfig(messages.Message):
  """User-specific settings."""
  metrics_enabled = messages.BooleanField(1)
  setup_wizard_completed = messages.BooleanField(2)


@Converter(ndb_models.PrivateNodeConfig, PrivateNodeConfig)
def _PrivateNodeConfigConverter(obj):
  return PrivateNodeConfig(
      metrics_enabled=obj.metrics_enabled,
      setup_wizard_completed=obj.setup_wizard_completed)


@Converter(PrivateNodeConfig, ndb_models.PrivateNodeConfig)
def _PrivateNodeConfigMessageConverter(msg):
  """Converts a PrivateNodeConfig message into an object."""
  private_node_config = ndb_models.GetPrivateNodeConfig()
  private_node_config.metrics_enabled = msg.metrics_enabled
  private_node_config.setup_wizard_completed = msg.setup_wizard_completed
  return private_node_config
