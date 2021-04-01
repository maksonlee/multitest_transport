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

"""A module to provide build channel provider APIs."""
# Non-standard docstrings are used to generate the API documentation.
import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import messages as mtt_messages


@base.MTT_API.api_class(
    resource_name='build_channel_provider', path='build_channel_providers')
class BuildChannelProviderApi(remote.Service):
  """A handler for Build Channel Provider API."""

  @base.ApiMethod(
      message_types.VoidMessage,
      mtt_messages.BuildChannelProviderList,
      path='/build_channel_providers',
      http_method='GET',
      name='list')
  def List(self, request):
    """Lists registered build channel providers."""
    provider_names = build.ListBuildProviderNames()
    build_channel_providers = []
    for name in provider_names:
      cls = build.GetBuildProviderClass(name)
      assert cls
      option_defs = cls().GetOptionDefs()
      build_channel_providers.append(
          mtt_messages.BuildChannelProvider(
              name=name,
              option_defs=mtt_messages.ConvertList(
                  option_defs, mtt_messages.OptionDef)))
    return mtt_messages.BuildChannelProviderList(
        build_channel_providers=build_channel_providers)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_provider_id=messages.StringField(1, required=True)),
      mtt_messages.BuildChannelProvider,
      path='{build_channel_provider_id}',
      http_method='GET',
      name='get')
  def Get(self, request):
    """Fetches a build channel provider.

    Parameters:
      build_channel_provider_id: Build channel provider ID
    """
    provider_id = request.build_channel_provider_id
    cls = build.GetBuildProviderClass(provider_id)
    if not cls:
      raise endpoints.NotFoundException(
          'Build channel provider %s not found' % provider_id)
    provider = cls()
    option_defs = provider.GetOptionDefs()
    return mtt_messages.BuildChannelProvider(
        name=provider_id,
        option_defs=mtt_messages.ConvertList(
            option_defs, mtt_messages.OptionDef))
