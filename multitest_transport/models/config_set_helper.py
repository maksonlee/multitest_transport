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


MTT_CONFIG_SET_PATH = 'android-mtt.appspot.com/prod/config_sets'
GCS_BUILD_CHANNEL_ID = 'google_cloud_storage'
GCS_URL = 'mtt:///%s/%s' % (GCS_BUILD_CHANNEL_ID, MTT_CONFIG_SET_PATH)


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
    info_message.imported = True
    info_message.update_available = False
    info_messages.append(info_message)
  return info_messages


def ParseConfigSetInfo(local_url):
  """Reads a config file and returns the config set info data.

  Args:
    local_url: A link to the file in the local gcs storage (file:///...)
  Returns:
    A ndb_models.ConfigSetInfo object
  """
  file_data = file_util.ReadFile(local_url, split_lines=False)
  content = file_data.lines

  config_set = config_encoder.Decode(content)
  info = config_set.config_set_info
  if info:
    info.hash = _Hash(content)
  return info


def GetRemoteConfigSetInfos():
  """Gets a list of build items, and downloads and parses each config info.

  Returns:
    A list of mtt_messages.ConfigSetInfo
  """
  # Get build items from MTT GCS bucket
  build_channel = build.GetBuildChannel(GCS_BUILD_CHANNEL_ID)
  if not build_channel:
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
    build_item_url = '%s/%s' % (GCS_URL, build_item.name)
    local_url = download_util.DownloadResource(build_item_url)
    info = ParseConfigSetInfo(local_url)
    if info:
      info_message = mtt_messages.Convert(info, mtt_messages.ConfigSetInfo)
      info_message.imported = False
      info_message.update_available = False
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
        existing_info.update_available = True
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


def _Hash(content):
  """Returns the SHA256 hash of a file.

  Args:
    content: The contents of the file as a single string
  Returns:
    A string representing the SHA256 hash
  """
  return hashlib.sha256(content).hexdigest()
