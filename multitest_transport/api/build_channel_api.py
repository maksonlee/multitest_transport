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
import collections

from protorpc import message_types
from protorpc import messages
from protorpc import remote
import six.moves.urllib.parse

import endpoints

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='build_channel', path='build_channels')
class BuildChannelApi(remote.Service):
  """A handler for Build Channel API."""

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
    build_channel_config = ndb_models.BuildChannelConfig.get_by_id(
        request.build_channel_id)
    if not build_channel_config:
      raise endpoints.NotFoundException('No build channel config with ID %s' %
                                        request.build_channel_id)
    return mtt_messages.Convert(build_channel_config,
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
    build_channel = build.GetBuildChannel(request.build_channel_id)
    if not build_channel:
      raise endpoints.NotFoundException(
          'No build channel with ID %s' % request.build_channel_id)
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
    build_channel = build.GetBuildChannel(request.build_channel_id)
    if not build_channel:
      raise endpoints.NotFoundException(
          'No build channel with ID %s' % request.build_channel_id)
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
    build_channel = build.GetBuildChannel(request.id)
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
          redirect_uri=messages.StringField(2)),
      mtt_messages.AuthorizationInfo,
      path='{build_channel_id}/get_authorize_url',
      http_method='GET',
      name='authorize_url.get')
  def GetAuthorizeUrl(self, request):
    """Returns a SimpleMessage containing an authorize url.

    Args:
      request: an API request object.

    Returns:
      a mtt_messages.SimpleMessage that contains the url
    """
    # Sample redirect_uri: http://127.0.0.1:8000/ui2/auth_return
    redirect_uri = request.redirect_uri
    hostname = six.moves.urllib.parse.urlparse(redirect_uri).hostname
    is_manual = False
    if hostname not in ('127.0.0.1', 'localhost'):
      redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
      is_manual = True
    build_channel = build.GetBuildChannel(request.build_channel_id)
    if not build_channel:
      raise endpoints.NotFoundException('No build channel has id: %s' %
                                        request.build_channel_id)
    auth_url = build_channel.GetAuthorizeUrl(redirect_uri)
    return mtt_messages.AuthorizationInfo(url=auth_url, is_manual=is_manual)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          build_channel_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2),
          code=messages.StringField(3)),
      message_types.VoidMessage,
      path='{build_channel_id}/authorize',
      http_method='POST',
      name='auth_return.post')
  def Authorize(self, request):
    """Authorize the build channel with code information.

    Args:
      request: an API request object.

    Returns:
      a void message
    """
    build_channel = build.GetBuildChannel(request.build_channel_id)
    if not build_channel:
      raise endpoints.NotFoundException('No build channel has id: %s' %
                                        request.build_channel_id)
    error_message = None
    if request.code:
      try:
        build_channel.Authorize(request.redirect_uri, request.code)
      except Exception as e:          error_message = 'Failed to authorize a build channel: %s' % e
        raise endpoints.UnauthorizedException(error_message)
    return message_types.VoidMessage()
