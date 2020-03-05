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

"""Test run action APIs."""
import multitest_transport.google_import_fixer  
import json
from protorpc import message_types
from protorpc import messages
from protorpc import remote
from google.oauth2 import service_account

import endpoints

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.util import oauth2_util


@base.MTT_API.api_class(resource_name='test_run_action')
class TestRunActionApi(remote.Service):
  """Test run action API handler."""

  def _GetTestRunActionKey(self, action_id):
    """Convert a test run action ID to a key."""
    return mtt_messages.ConvertToKey(ndb_models.TestRunAction, action_id)

  def _GetTestRunAction(self, action_id):
    """Fetch a test run action by its ID or throw if not found."""
    action = self._GetTestRunActionKey(action_id).get()
    if not action:
      raise endpoints.NotFoundException('Test run action %s not found' %
                                        action_id)
    return action

  def _ConvertToMessage(self, action):
    """Convert a test run action to a message with authorization state."""
    msg = mtt_messages.Convert(action, mtt_messages.TestRunAction)
    msg.authorization_state = test_run_hook.GetAuthorizationState(action)
    return msg

  def _ConvertFromMessage(self, msg):
    """Convert a message to a test run action."""
    return mtt_messages.Convert(
        msg, ndb_models.TestRunAction, from_cls=mtt_messages.TestRunAction)

  @base.convert_exception
  @endpoints.method(
      message_types.VoidMessage,
      mtt_messages.TestRunActionList,
      path='test_run_actions', http_method='GET', name='list')
  def List(self, _):
    """List test run actions."""
    actions = [
        self._ConvertToMessage(action)
        for action in ndb_models.TestRunAction.query().fetch()
    ]
    return mtt_messages.TestRunActionList(actions=actions)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunAction,
      path='test_run_actions/{action_id}', http_method='GET', name='get')
  def Get(self, request):
    """Fetches a test run action."""
    action = self._GetTestRunAction(request.action_id)
    return self._ConvertToMessage(action)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.TestRunAction),
      mtt_messages.TestRunAction,
      path='test_run_actions', http_method='POST', name='create')
  def Create(self, request):
    """Create a new test run action."""
    action = self._ConvertFromMessage(request)
    action.key = None
    action.put()
    return self._ConvertToMessage(action)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.TestRunAction,
          action_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunAction,
      path='test_run_actions/{action_id}', http_method='PUT', name='update')
  def Update(self, request):
    """Updates an existing test run action."""
    existing_action = self._GetTestRunAction(request.action_id)
    updated_action = self._ConvertFromMessage(request)
    updated_action.key = existing_action.key
    updated_action.put()
    return self._ConvertToMessage(updated_action)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}', http_method='DELETE', name='delete')
  def Delete(self, request):
    """Deletes a test run action if it exists."""
    self._GetTestRunActionKey(request.action_id).delete()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True)),
      mtt_messages.AuthorizationInfo,
      path='test_run_actions/{action_id}/auth',
      http_method='GET',
      name='get_auth_info')
  def GetAuthorizationInfo(self, request):
    """Determine a test run action's authorization information."""
    action = self._GetTestRunAction(request.action_id)
    redirect_uri, is_manual = oauth2_util.GetRedirectUri(request.redirect_uri)
    oauth2_config = test_run_hook.GetOAuth2Config(action)
    flow = oauth2_util.GetOAuth2Flow(oauth2_config, redirect_uri)
    auth_url, _ = flow.authorization_url()
    return mtt_messages.AuthorizationInfo(url=auth_url, is_manual=is_manual)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True),
          redirect_uri=messages.StringField(2, required=True),
          code=messages.StringField(3, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}/auth',
      http_method='POST',
      name='authorize')
  def Authorize(self, request):
    """Authorize a test run action with an authorization code."""
    action = self._GetTestRunAction(request.action_id)
    redirect_uri, _ = oauth2_util.GetRedirectUri(request.redirect_uri)
    oauth2_config = test_run_hook.GetOAuth2Config(action)
    flow = oauth2_util.GetOAuth2Flow(oauth2_config, redirect_uri)
    flow.fetch_token(code=request.code)
    action.credentials = flow.credentials
    action.put()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.SimpleMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}/auth',
      http_method='PUT',
      name='authorize_with_service_account')
  def AuthorizeWithServiceAccount(self, request):
    """Authorize a test run action with an service account JSON key."""
    action = self._GetTestRunAction(request.action_id)
    data = json.loads(request.value)
    credentials = service_account.Credentials.from_service_account_info(data)
    action.credentials = credentials
    action.put()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}/auth',
      http_method='DELETE',
      name='unauthorize')
  def Unauthorize(self, request):
    """Revoke a test run action's authorization."""
    action = self._GetTestRunAction(request.action_id)
    action.credentials = None
    action.put()
    return message_types.VoidMessage()
