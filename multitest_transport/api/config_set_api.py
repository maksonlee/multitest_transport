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

"""A module to provide config set APIs."""
# Non-standard docstrings are used to generate the API documentation.
import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import config_set_helper
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='config_set',
                        path='config_sets')
class ConfigSetApi(remote.Service):
  """A handler for Config Set API."""

  def _ConvertFromMessage(self, msg):
    """Convert a message to a config set info."""
    return mtt_messages.Convert(
        msg, ndb_models.ConfigSetInfo, from_cls=mtt_messages.ConfigSetInfo)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,),
      mtt_messages.BuildChannelList,
      path='build_channels', http_method='GET',
      name='build_channels')
  def ListBuildChannels(self, request):
    """Fetches a list of build channels used for importing config sets."""
    channels = []
    for channel_id in config_set_helper.CONFIG_SET_BUILD_CHANNEL_IDS:
      channels.append(build.GetBuildChannel(channel_id))
    return mtt_messages.BuildChannelList(
        build_channels=mtt_messages.ConvertList(
            channels, mtt_messages.BuildChannel))

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          include_remote=messages.BooleanField(1),
          statuses=messages.EnumField(
              ndb_models.ConfigSetStatus, 2, repeated=True),),
      mtt_messages.ConfigSetInfoList,
      path='/config_sets', http_method='GET', name='list')
  def List(self, request):
    """Fetches a list of config sets.

    Parameters:
      include_remote: True to check remote config sets and determine the
        imported config sets are updatable, False to only return imported
        config sets
      statuses: config set statuses to include
    """
    imported_infos = config_set_helper.GetLocalConfigSetInfos()

    remote_infos = []
    if request.include_remote:
      remote_infos = config_set_helper.GetRemoteConfigSetInfos()

    info_message_list = config_set_helper.UpdateConfigSetInfos(imported_infos,
                                                               remote_infos)
    if request.statuses:
      info_message_list = [msg for msg in info_message_list
                           if msg.status in request.statuses]

    return mtt_messages.ConfigSetInfoList(
        config_set_infos=info_message_list)

  @base.ApiMethod(
      endpoints.ResourceContainer(mtt_messages.ConfigSetInfo),
      mtt_messages.ConfigSetInfo,
      path='latest_version',
      http_method='POST',
      name='latest_version')
  def GetLatestVersion(self, request):
    imported_info = self._ConvertFromMessage(request)
    return config_set_helper.GetLatestVersion(imported_info)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          url=messages.StringField(1),
          content=messages.StringField(2)),
      mtt_messages.ConfigSetInfo,
      path='import/{url}',
      http_method='POST',
      name='import')
  def Import(self, request):
    """Downloads and imports a config set.

    Parameters:
      url: URL from which to download a config file
      content: contents of a config file, only used if url is not provided
    """
    content = (request.content.encode() if request.content else
               config_set_helper.ReadRemoteFile(request.url))
    return config_set_helper.Import(content)

  @base.ApiMethod(
      endpoints.ResourceContainer(message_types.VoidMessage,
                                  url=messages.StringField(1)),
      message_types.VoidMessage,
      path='{url}',
      http_method='DELETE',
      name='delete')
  def Delete(self, request):
    """Removes a config set and all associated objects (tests, etc).

    Parameters:
      url: the url of the config set to remove
    """
    config_set_helper.Delete(request.url)
    return message_types.VoidMessage()
