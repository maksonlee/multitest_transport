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
# Non-standard docstrings are used to generate the API documentation.

import json
import endpoints

from google.oauth2 import service_account
from protorpc import message_types
from protorpc import messages
from protorpc import remote


from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook


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

  @base.ApiMethod(
      message_types.VoidMessage,
      mtt_messages.TestRunActionList,
      path='test_run_actions', http_method='GET', name='list')
  def List(self, _):
    """Lists test run actions."""
    actions = [
        self._ConvertToMessage(action)
        for action in ndb_models.TestRunAction.query().fetch()
    ]
    return mtt_messages.TestRunActionList(actions=actions)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunAction,
      path='test_run_actions/{action_id}', http_method='GET', name='get')
  def Get(self, request):
    """Fetches a test run action.

    Parameters:
      action_id: Test run action ID
    """
    action = self._GetTestRunAction(request.action_id)
    return self._ConvertToMessage(action)

  @base.ApiMethod(
      endpoints.ResourceContainer(mtt_messages.TestRunAction),
      mtt_messages.TestRunAction,
      path='test_run_actions', http_method='POST', name='create')
  def Create(self, request):
    """Creates a new test run action.

    Body:
      Test run action data
    """
    action = self._ConvertFromMessage(request)
    action.key = None
    action.put()
    return self._ConvertToMessage(action)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          mtt_messages.TestRunAction,
          action_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunAction,
      path='test_run_actions/{action_id}', http_method='PUT', name='update')
  def Update(self, request):
    """Updates an existing test run action.

    Body:
      Test run action data
    Parameters:
      action_id: Test run action ID
    """
    existing_action = self._GetTestRunAction(request.action_id)
    updated_action = self._ConvertFromMessage(request)
    updated_action.key = existing_action.key
    updated_action.put()
    return self._ConvertToMessage(updated_action)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}', http_method='DELETE', name='delete')
  def Delete(self, request):
    """Deletes a test run action if it exists.

    Parameters:
      action_id: Test run action ID
    """
    self._GetTestRunActionKey(request.action_id).delete()
    return message_types.VoidMessage()

  @base.ApiMethod(
      endpoints.ResourceContainer(
          mtt_messages.SimpleMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}/auth',
      http_method='PUT',
      name='authorize_with_service_account')
  def AuthorizeWithServiceAccount(self, request):
    """Authorize a test run action with a service account key.

    Body:
      Service account JSON key file data
    Parameters:
      action_id: Test run action ID
    """
    action = self._GetTestRunAction(request.action_id)
    data = json.loads(request.value)
    credentials = service_account.Credentials.from_service_account_info(data)
    action.credentials = credentials
    action.put()
    return message_types.VoidMessage()

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{action_id}/auth',
      http_method='DELETE',
      name='unauthorize')
  def Unauthorize(self, request):
    """Revoke a test run action's authorization.

    Parameters:
      action_id: Test run action ID
    """
    action = self._GetTestRunAction(request.action_id)
    action.credentials = None
    action.put()
    return message_types.VoidMessage()

  @base.ApiMethod(
      endpoints.ResourceContainer(
          mtt_messages.TestRunActionRefList,
          test_run_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='test_run_actions/{test_run_id}',
      http_method='POST',
      name='execute')
  def ExecuteTestRunActions(self, request):
    """Execute test run actions.

    Body:
      A list of test run action references
    Parameters:
      test_run_id: Test run ID
    """
    test_run = ndb_models.TestRun.get_by_id(request.test_run_id)
    if not test_run:
      raise endpoints.NotFoundException('no test run found for ID %s' %
                                        request.test_run_id)
    action_refs = mtt_messages.ConvertList(request.refs,
                                           ndb_models.TestRunActionRef)
    actions = [ref.ToAction() for ref in action_refs]
    test_run_hook.ExecuteHooks(
        request.test_run_id,
        ndb_models.TestRunPhase.MANUAL,
        test_run_actions=actions)
    return message_types.VoidMessage()
