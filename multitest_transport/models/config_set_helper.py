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

from multitest_transport.models import build
from multitest_transport.models import config_encoder
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import file_util


MTT_CONFIG_SET_PATH = 'android-test-catalog/prod'
GCS_BUILD_CHANNEL_ID = 'google_cloud_storage'
CONFIG_SET_URL = 'mtt:///%s/%s' % (GCS_BUILD_CHANNEL_ID, MTT_CONFIG_SET_PATH)
CONFIG_SET_BUILD_CHANNEL_IDS = [GCS_BUILD_CHANNEL_ID]


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


def GetRemoteConfigSetInfos():
  """Gets a list of build items, and downloads and parses each config info.

  Returns:
    A list of mtt_messages.ConfigSetInfo
  """
  # TODO: Allow for multiple config set sources
  # Get build items from MTT GCS bucket
  build_channel = build.GetBuildChannel(GCS_BUILD_CHANNEL_ID)
  if (not build_channel) or (build_channel.auth_state ==
                             ndb_models.BuildChannelAuthState.NOT_AUTHORIZED):
    return []
  build_items, _ = build_channel.ListBuildItems(
      path=MTT_CONFIG_SET_PATH)
  build_item_list = [mtt_messages.BuildItem(**b.__dict__)
                     for b in build_items]

  # Parse build items to config set infos
  info_messages = []
  for build_item in build_item_list:
    if (not build_item.is_file or not build_item.name or
        not build_item.name.endswith('.yaml')):
      continue

    # Read file
    gcs_url = '%s/%s' % (CONFIG_SET_URL, build_item.name)
    contents = ReadRemoteFile(gcs_url)
    info = _ParseConfigSet(contents).info
    if info:
      info_message = mtt_messages.Convert(info, mtt_messages.ConfigSetInfo)
      info_message.status = ndb_models.ConfigSetStatus.NOT_IMPORTED
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


def Import(content):
  config_set = _ParseConfigSet(content)
  config_encoder.Load(config_set)
  config_set.info.put()
  return mtt_messages.Convert(config_set.info, mtt_messages.ConfigSetInfo)


def ReadRemoteFile(url):
  """Downloads a file from GCS and returns the contents.

  Args:
    url: An MTT GCS built item url, e.g. mtt:///google_cloud_storage/...
  Returns:
    A string of the contents of the file
  """

  local_url = download_util.DownloadResource(url)
  file_data = file_util.ReadFile(local_url, split_lines=False)
  return file_data.lines


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


def _Hash(content):
  """Returns the SHA256 hash of a file.

  Args:
    content: The contents of the file as a single string
  Returns:
    A string representing the SHA256 hash
  """
  return hashlib.sha256(content).hexdigest()
