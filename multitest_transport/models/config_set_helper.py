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

"""A module to provide helper functions for the config set APIs."""

import hashlib
import logging

import six

from multitest_transport.models import build
from multitest_transport.models import config_encoder
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import errors
from multitest_transport.util import file_util
from tradefed_cluster.util import ndb_shim as ndb

CONFIG_SET_BUILD_CHANNEL_IDS = ['google_cloud_storage']
CONFIG_SET_URL = 'mtt:///google_cloud_storage/android-test-catalog/prod'


def _ConvertToMessage(info, status=None):
  """Converts a ndb_models.ConfigSetInfo to an mtt_messages.ConfigSetInfo."""
  message = mtt_messages.Convert(info, mtt_messages.ConfigSetInfo)
  message.status = status
  return message


def _GetAuthorizedBuildChannel():
  """Gets the build channel for config sets if it is authorized.

  Raises ValueError if the channel is not authorized.

  Returns:
    build_channel: The build channel object
    locator: The parsed url
  """
  locator = build.BuildLocator.ParseUrl(CONFIG_SET_URL)
  if not locator:
    raise ValueError('Invalid URL: %s' % CONFIG_SET_URL)
  build_channel = build.GetBuildChannel(locator.build_channel_id)
  if (not build_channel) or (build_channel.auth_state ==
                             ndb_models.AuthorizationState.UNAUTHORIZED):
    raise ValueError('Build channel %s not authorized' %
                     locator.build_channel_id)
  return build_channel, locator


def _GetEntityKeysByPrefix(model, prefix):
  """Gets keys for all entities of the given model whose id starts with prefix.

  Args:
    model: The type of entity to query for
    prefix: Only keys whose id starts with the prefix will be returned

  Returns:
    a list of entity keys that match the prefix
  """
  return model.query().filter(
      model.key >= ndb.Key(model, prefix),
      model.key < ndb.Key(model, prefix + u'ufffd')).fetch(keys_only=True)


def _ParseConfigSet(content):
  """Converts a string of data into a ConfigSet object.

  Args:
    content: a string, usually the contents of a config file
  Returns:
    A ndb_models.ConfigSet object
  """
  config_set = config_encoder.Decode(content)
  info = config_set.info
  # TODO: Split HostConfigs from ConfigSets and make info required
  if info:
    info.hash = _Hash(content)
  return config_set


def _ParseBuildItem(build_item):
  """Converts a built item to a config set."""
  if not build_item:
    logging.info('Failed to find build item')
    return None

  if (not build_item.is_file or not build_item.name or
      not build_item.name.endswith('.yaml')):
    logging.info('%s is not a valid config file', build_item.name)
    return None

  # Read and parse file
  file_url = '%s/%s' % (CONFIG_SET_URL, build_item.name)
  try:
    contents = ReadRemoteFile(file_url)
    return _ParseConfigSet(contents)
  except errors.FilePermissionError as err:
    logging.info('No permission to access %s: %s', file_url, err)
    return None  # Ignore files users don't have access to


def GetLocalConfigSetInfos():
  """Get list of config infos imported to the current MTT instance.

  Returns:
    A list of mtt_messages.ConfigSetInfo
  """
  query = ndb_models.ConfigSetInfo.query().order(
      ndb_models.ConfigSetInfo.name)
  infos = query.fetch()
  info_messages = []
  for info in infos:
    info_message = mtt_messages.Convert(info, mtt_messages.ConfigSetInfo)
    info_message.status = ndb_models.ConfigSetStatus.IMPORTED
    info_messages.append(info_message)
  return info_messages


def GetRemoteConfigSetInfo(url):
  """Reads a remote config set from the given url and parses the info."""
  # Get the build item
  build_channel, locator = _GetAuthorizedBuildChannel()
  try:
    channel_path = locator.path
    path = channel_path + url.split(channel_path)[1]
    build_item = build_channel.GetBuildItem(path)
  except errors.FilePermissionError as err:
    logging.info('No permission to access %s: %s', CONFIG_SET_URL, err)
    return None

  # Parse the build item
  remote_config = _ParseBuildItem(build_item)
  return remote_config.info if remote_config else None


def GetRemoteConfigSetInfos():
  """Gets a list of build items, and downloads and parses each config info.

  Returns:
    A list of mtt_messages.ConfigSetInfo
  """
  # TODO: Allow for multiple config set sources
  # Get build items from MTT GCS bucket
  build_channel, locator = _GetAuthorizedBuildChannel()
  try:
    build_items, _ = build_channel.ListBuildItems(path=locator.path)
  except errors.FilePermissionError as err:
    logging.info('No permission to access %s: %s', CONFIG_SET_URL, err)
    return []

  # Parse build items to config set infos
  info_messages = []
  for build_item in build_items:
    remote_config = _ParseBuildItem(build_item)
    if not remote_config or not remote_config.info:
      continue

    info_message = _ConvertToMessage(remote_config.info,
                                     ndb_models.ConfigSetStatus.NOT_IMPORTED)
    info_messages.append(info_message)

  return info_messages


def UpdateConfigSetInfos(imported_infos, remote_infos):
  """Updates local infos based on given remote infos.

  Args:
    imported_infos: A list of messages for the imported config set infos
    remote_infos: A list of messages for the remote config set infos
  Returns:
    A list of mtt_messages.ConfigSetInfo
  """
  info_map = dict((info.url, info) for info in imported_infos)

  for info in remote_infos:
    existing_info = info_map.get(info.url)
    if existing_info:
      if existing_info.hash != info.hash:
        # Imported file is different
        existing_info.status = ndb_models.ConfigSetStatus.UPDATABLE
        info_map[info.url] = existing_info
      # If imported file is same, keep as imported=True and update=False
    else:
      # Not imported
      info_map[info.url] = info

  # Sort for consistent ordering
  info_list = []
  for key in sorted(info_map):
    info_list.append(info_map.get(key))
  return info_list


def GetLatestVersion(imported_info):
  """Checks if there's an update available for an imported info.

  Args:
    imported_info: an already imported config set info
  Returns:
    the imported info message with the updated state
  """
  updated_message = _ConvertToMessage(imported_info,
                                      ndb_models.ConfigSetStatus.IMPORTED)

  remote_info = GetRemoteConfigSetInfo(imported_info.url)
  if remote_info and remote_info.hash != imported_info.hash:
    updated_message.status = ndb_models.ConfigSetStatus.UPDATABLE

  return updated_message


def Import(content):
  """Parses the content and adds all configs in the config set.

  Any data from an older version of the config set will be removed.

  Args:
    content: the text content of a config set file
  Returns:
    the parsed ConfigSetInfo
  """
  config_set = _ParseConfigSet(content)

  # Remove any older data
  info = config_set.info
  if info and info.key.get():
    Delete(info.url)

  config_encoder.Load(config_set)
  info.put()
  return mtt_messages.Convert(info, mtt_messages.ConfigSetInfo)


def Delete(url):
  """Removes a config set info and its related objects.

  Args:
    url: source url of the config set to remove
  """

  prefix = ''.join([url, config_encoder.NAMESPACE_SEPARATOR])

  # Remove Test Suites
  test_keys = _GetEntityKeysByPrefix(ndb_models.Test, prefix)
  ndb.delete_multi(test_keys)

  # Remove Device Actions
  device_action_keys = _GetEntityKeysByPrefix(ndb_models.DeviceAction, prefix)
  ndb.delete_multi(device_action_keys)

  # Remove Test Run Actions
  test_run_action_keys = _GetEntityKeysByPrefix(
      ndb_models.TestRunAction, prefix)
  ndb.delete_multi(test_run_action_keys)

  # Remove Config Set Info
  config_set_info_key = mtt_messages.ConvertToKey(ndb_models.ConfigSetInfo, url)
  config_set_info_key.delete()


def ReadRemoteFile(url):
  """Downloads a config set file and returns the contents.

  Args:
    url: A MTT-compatible URL for a config set file.
  Returns:
    A string of the contents of the file
  """
  local_url = download_util.DownloadResource(url)
  return file_util.OpenFile(local_url).read()


def _Hash(content):
  """Returns the SHA256 hash of a file.

  Args:
    content: The contents of the file as a single string
  Returns:
    A string representing the SHA256 hash
  """
  return hashlib.sha256(six.ensure_binary(content)).hexdigest()
