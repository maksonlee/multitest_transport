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


from protorpc import message_types
from protorpc import messages
from protorpc import remote

import endpoints

from multitest_transport.api import base
from multitest_transport.models import config_encoder
from multitest_transport.models import config_set_helper
from multitest_transport.models import messages as mtt_messages


@base.MTT_API.api_class(resource_name='config_set',
                        path='config_set')
class ConfigSetApi(remote.Service):
  """A handler for Config Set API."""

  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          include_remote=messages.BooleanField(1)),
      mtt_messages.ConfigSetInfoList,
      path='/config_sets', http_method='GET', name='list')
  def List(self, request):
    """Returns a list of ConfigSetStatuses.

    If include_remote is false, returns only the imported infos
    If include_remote is true, downloads the available configs from the MTT GCS
      bucket and checks if any currently imported configs can be updated.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.ConfigSetStatusList object.
    """
    imported_infos = config_set_helper.GetLocalConfigSetInfos()

    remote_infos = []
    if request.include_remote:
      remote_infos = config_set_helper.GetRemoteConfigSetInfos()

    info_message_list = config_set_helper.UpdateConfigSetInfos(imported_infos,
                                                               remote_infos)

    return mtt_messages.ConfigSetInfoList(
        config_set_infos=info_message_list)

  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          url=messages.StringField(1)),
      mtt_messages.ConfigSetInfo,
      path='/config_sets/import',
      http_method='GET',
      name='import')
  def Import(self, request):
    config_set = config_set_helper.ParseConfigSet(request.url)
    config_encoder.Load(config_set)
    config_set.info.put()
    return mtt_messages.Convert(config_set.info, mtt_messages.ConfigSetInfo)

