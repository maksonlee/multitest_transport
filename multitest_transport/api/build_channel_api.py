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

"""A module to provide build channel APIs."""
import multitest_transport.google_import_fixer  
import collections
import json

from protorpc import message_types
from protorpc import messages
from protorpc import remote

from google.oauth2 import service_account
import endpoints

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.util import oauth2_util


@base.MTT_API.api_class(resource_name='build_channel', path='build_channels')
class BuildChannelApi(remote.Service):
  """A handler for Build Channel API."""

  def _GetBuildChannel(self, build_channel_id):
    """Fetch a build channel by its ID or throw if not found."""
    build_channel = build.GetBuildChannel(build_channel_id)
    if not build_channel:
      raise endpoints.NotFoundException(
          'Build channel %s not found' % build_channel_id)
    return build_channel

  @base.convert_exception
  @endpoints.method(
      message_types.VoidMessage, mtt_messages.BuildChannelList,
      path='/build_channels', http_method='GET', name='list')
  def List(self, request):
    """List registered build channels.

    Args:
      request: a API request object.
    Returns:
      a mtt_messages.BuildChannelList object.
    """
    objs = build.ListBuildChannels()
    build_channels = mtt_messages.Convert(objs, mtt_messages.BuildChannel)
    return mtt_messages.BuildChannelList(build_channels=build_channels)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True)),
      mtt_messages.BuildChannelConfig,
      path='{build_channel_id}',
      http_method='GET',
      name='get')
  def Get(self, request):
    """Returns a build channel config.

    Args:
      request: an API request object.

    Returns:
      a mtt_messages.BuildChannelConfig object.
    Raises:
      endpoints.NotFoundException: if a given build channel config does not
      exist.
    """
    build_channel = self._GetBuildChannel(request.build_channel_id)
    return mtt_messages.Convert(build_channel.config,
                                mtt_messages.BuildChannelConfig)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True),
          path=messages.StringField(2),
          page_token=messages.StringField(3)),
      mtt_messages.BuildItemList, path='{build_channel_id}/build_items',
      http_method='GET', name='build_item.list')
  def ListBuildItems(self, request):
    """Returns a list of build items.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.BuildItemList object.
    Raises:
      endpoints.NotFoundException: if a given build channel does not exist.
    """
    build_channel = self._GetBuildChannel(request.build_channel_id)
    build_items, next_page_token = build_channel.ListBuildItems(
        path=request.path, page_token=request.page_token)
    return mtt_messages.BuildItemList(
        build_items=[mtt_messages.BuildItem(**b.__dict__) for b in build_items],
        next_page_token=next_page_token)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True),
          path=messages.StringField(2)),
      message_types.VoidMessage, path='{build_channel_id}/build_items/delete',
      http_method='POST', name='build_item.delete')
  def DeleteBuildItem(self, request):
    """Delete a build item.

    Args:
      request: an API request object.
    Returns:
      a message_types.VoidMessage.
    Raises:
      endpoints.NotFoundException: if a build channel/build item does not exist.
    """
    build_channel = self._GetBuildChannel(request.build_channel_id)
    build_channel.DeleteBuildItem(request.path)
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.BuildChannelConfig),
      mtt_messages.BuildChannelConfig,
      path='/build_channels',
      http_method='POST',
      name='create')
  def Create(self, request):
    """Create a build channel.

    Args:
      request: a API request object.

    Returns:
      a mtt_messages.BuildChannelConfig object
    """
    options = collections.OrderedDict()
    name_value_pair_list = request.options
    for pair in name_value_pair_list:
      if not pair.name:
        continue
      options[pair.name] = pair.value
    build_channel_config = build.AddBuildChannel(
        name=request.name, provider_name=request.provider_name, options=options)
    return mtt_messages.Convert(build_channel_config,
                                mtt_messages.BuildChannelConfig)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.BuildChannelConfig,
          build_channel_id=messages.StringField(1, required=True)),
      mtt_messages.BuildChannelConfig,
      path='{build_channel_id}',
      http_method='PUT',
      name='update')
  def Update(self, request):
    """Updates an existing build channel.

    Args:
      request: a API request object.

    Returns:
      a mtt_messages.BuildChannelConfig object
    """
    options = collections.OrderedDict()
    name_value_pair_list = request.options
    for pair in name_value_pair_list:
      if not pair.name:
        continue
      options[pair.name] = pair.value
    build_channel = self._GetBuildChannel(request.build_channel_id)
    build_channel_config = build_channel.Update(
        name=request.name, provider_name=request.provider_name, options=options)
    return mtt_messages.Convert(build_channel_config,
                                mtt_messages.BuildChannelConfig)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{build_channel_id}/delete',
      http_method='POST',
      name='delete')
  def Delete(self, request):
    build_channel_key = mtt_messages.ConvertToKey(
        ndb_models.BuildChannelConfig, request.build_channel_id)
    build_channel_key.delete()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True)),
      mtt_messages.AuthorizationInfo,
      path='{build_channel_id}/auth', http_method='GET', name='auth')
  def GetAuthorizationInfo(self, request):
    """Determine a build channel configuration's authorization information."""
    build_channel = self._GetBuildChannel(request.build_channel_id)
    redirect_uri, is_manual = oauth2_util.GetRedirectUri(request.redirect_uri)
    flow = oauth2_util.GetOAuth2Flow(build_channel.oauth2_config, redirect_uri)
    auth_url, _ = flow.authorization_url()
    return mtt_messages.AuthorizationInfo(url=auth_url, is_manual=is_manual)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True),
          code=messages.StringField(3, required=True)),
      message_types.VoidMessage,
      path='{build_channel_id}/auth',
      http_method='POST',
      name='authorize')
  def AuthorizeConfig(self, request):
    """Authorize a build channel configuration with an authorization code."""
    build_channel = self._GetBuildChannel(request.build_channel_id)
    redirect_uri, _ = oauth2_util.GetRedirectUri(request.redirect_uri)
    flow = oauth2_util.GetOAuth2Flow(build_channel.oauth2_config, redirect_uri)
    flow.fetch_token(code=request.code)
    build_channel.config.credentials = flow.credentials
    build_channel.config.put()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.SimpleMessage,
          build_channel_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{build_channel_id}/auth',
      http_method='PUT',
      name='authorize_with_service_account')
  def AuthorizeConfigWithServiceAccount(self, request):
    """Authorize a build channel configuration with a service account key."""
    build_channel = self._GetBuildChannel(request.build_channel_id)
    data = json.loads(request.value)
    credentials = service_account.Credentials.from_service_account_info(data)
    build_channel.config.credentials = credentials
    build_channel.config.put()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{build_channel_id}/auth',
      http_method='DELETE',
      name='unauthorize')
  def UnauthorizeConfig(self, request):
    """Revoke a build channel configuration's authorization."""
    build_channel = self._GetBuildChannel(request.build_channel_id)
    build_channel.config.credentials = None
    build_channel.config.put()
    return message_types.VoidMessage()
