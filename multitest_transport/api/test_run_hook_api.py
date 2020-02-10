# Copyright 2020 Google LLC
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

"""Test run hook APIs."""
from protorpc import message_types
from protorpc import messages
from protorpc import remote

import endpoints

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.util import oauth2_util


@base.MTT_API.api_class(resource_name='test_run_hook', path='test_run_hooks')
class TestRunHookApi(remote.Service):
  """Test run hook API handler."""

  def _GetHookConfigKey(self, hook_id):
    """Convert a test run hook configuration ID to a key."""
    return mtt_messages.ConvertToKey(ndb_models.TestRunHookConfig, hook_id)

  def _GetHookConfig(self, hook_id):
    """Fetch a test run hook configuration by its ID or throw if not found."""
    hook_config = self._GetHookConfigKey(hook_id).get()
    if not hook_config:
      raise endpoints.NotFoundException('Test run hook %s not found' % hook_id)
    return hook_config

  def _ConvertToMessage(self, hook_config):
    """Convert a hook configuration to a message with authorization state."""
    msg = mtt_messages.Convert(hook_config, mtt_messages.TestRunHookConfig)
    msg.authorization_state = test_run_hook.GetAuthorizationState(hook_config)
    return msg

  def _ConvertFromMessage(self, msg):
    """Convert a message to a hook configuration."""
    return mtt_messages.Convert(msg, ndb_models.TestRunHookConfig,
                                from_cls=mtt_messages.TestRunHookConfig)

  @base.convert_exception
  @endpoints.method(
      message_types.VoidMessage,
      mtt_messages.TestRunHookConfigList,
      path='configs', http_method='GET', name='list')
  def ListConfigs(self, _):
    """List test run hook configurations."""
    hook_configs = [
        self._ConvertToMessage(hook_config)
        for hook_config in ndb_models.TestRunHookConfig.query().fetch()
    ]
    return mtt_messages.TestRunHookConfigList(configs=hook_configs)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          hook_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunHookConfig,
      path='configs/{hook_id}', http_method='GET', name='get')
  def GetConfig(self, request):
    """Fetches a test run hook configuration."""
    hook_config = self._GetHookConfig(request.hook_id)
    return self._ConvertToMessage(hook_config)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.TestRunHookConfig),
      mtt_messages.TestRunHookConfig,
      path='configs', http_method='POST', name='create')
  def CreateConfig(self, request):
    """Create a new test run hook configuration."""
    hook_config = self._ConvertFromMessage(request)
    hook_config.key = None
    hook_config.put()
    return self._ConvertToMessage(hook_config)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.TestRunHookConfig,
          hook_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunHookConfig,
      path='configs/{hook_id}', http_method='PUT', name='update')
  def UpdateConfig(self, request):
    """Updates an existing test run hook configuration."""
    existing_hook_config = self._GetHookConfig(request.hook_id)
    hook_config = self._ConvertFromMessage(request)
    hook_config.key = existing_hook_config.key
    hook_config.put()
    return self._ConvertToMessage(hook_config)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          hook_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='configs/{hook_id}', http_method='DELETE', name='delete')
  def DeleteConfig(self, request):
    """Deletes a test run hook configuration if it exists."""
    self._GetHookConfigKey(request.hook_id).delete()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          hook_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True)),
      mtt_messages.AuthorizationInfo,
      path='configs/{hook_id}/auth', http_method='GET', name='auth')
  def GetAuthorizationInfo(self, request):
    """Determine a hook configuration's authorization information."""
    hook_config = self._GetHookConfig(request.hook_id)
    redirect_uri, is_manual = oauth2_util.GetRedirectUri(request.redirect_uri)
    oauth2_config = test_run_hook.GetOAuth2Config(hook_config)
    auth_url = oauth2_util.GetOAuth2Flow(
        oauth2_config, redirect_uri).step1_get_authorize_url()
    return mtt_messages.AuthorizationInfo(url=auth_url, is_manual=is_manual)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          hook_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True),
          code=messages.StringField(3, required=True)),
      message_types.VoidMessage,
      path='configs/{hook_id}/auth_return',
      http_method='POST',
      name='auth_return')
  def AuthorizeConfig(self, request):
    """Authorize a test run hook configuration with an authorization code."""
    hook_config = self._GetHookConfig(request.hook_id)
    redirect_uri, _ = oauth2_util.GetRedirectUri(request.redirect_uri)
    oauth2_config = test_run_hook.GetOAuth2Config(hook_config)
    hook_config.credentials = oauth2_util.GetOAuth2Flow(
        oauth2_config, redirect_uri).step2_exchange(request.code)
    hook_config.put()
    return message_types.VoidMessage()
