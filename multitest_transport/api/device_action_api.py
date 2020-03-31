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

"""A module to provide device action APIs.

A device action is an object defines a type of device interaction to be
performed before/after test run. It can be referenced in test run configs to
instruct MTT to do certain device interactions before running a test.
"""

from protorpc import message_types
from protorpc import messages
from protorpc import remote

from google.appengine.ext import ndb
from google3.third_party.apphosting.python.endpoints.v1_1 import endpoints

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='device_action', path='device_actions')
class DeviceActionApi(remote.Service):
  """A handler for Device Action API."""

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          page_token=messages.StringField(1),
          max_results=messages.IntegerField(
              2, default=base.DEFAULT_MAX_RESULTS)),
      mtt_messages.DeviceActionList, path='/device_actions', http_method='GET',
      name='list')
  def List(self, request):
    """List device actions.

    Args:
      request: a API request object.
    Returns:
      a mtt_messages.DeviceActionList object.
    """
    query = ndb_models.DeviceAction.query().order(ndb_models.DeviceAction.name)
    cursor = None
    if request.page_token:
      cursor = ndb.Cursor(urlsafe=request.page_token)
    device_actions, next_cursor, has_more = query.fetch_page(
        request.max_results, start_cursor=cursor)
    device_action_msgs = mtt_messages.Convert(
        device_actions, mtt_messages.DeviceAction)
    next_page_token = next_cursor.urlsafe() if has_more else None
    return mtt_messages.DeviceActionList(
        device_actions=device_action_msgs, next_page_token=next_page_token)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.DeviceAction),
      mtt_messages.DeviceAction, path='/device_actions', http_method='POST',
      name='create')
  def Create(self, request):
    """Create a device action.

    Args:
      request: a API request object.
    Returns:
      a mtt_messages.DeviceAction object
    """
    device_action = mtt_messages.Convert(
        request, ndb_models.DeviceAction, from_cls=mtt_messages.DeviceAction)
    device_action.put()
    return mtt_messages.Convert(device_action, mtt_messages.DeviceAction)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          device_action_id=messages.StringField(1, required=True)),
      mtt_messages.DeviceAction, path='{device_action_id}', http_method='GET',
      name='get')
  def Get(self, request):
    """Returns a device action.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.DeviceAction object.
    Raises:
      endpoints.NotFoundException: if a given device action does not exist.
    """
    if request.device_action_id == '0':
      device_action = ndb_models.DeviceAction(name='')
    else:
      device_action = mtt_messages.ConvertToKey(
          ndb_models.DeviceAction, request.device_action_id).get()
    if not device_action:
      raise endpoints.NotFoundException(
          'No device action with ID %s' % request.device_action_id)
    return mtt_messages.Convert(device_action, mtt_messages.DeviceAction)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.DeviceAction,
          device_action_id=messages.StringField(1, required=True)),
      mtt_messages.DeviceAction, path='{device_action_id}', http_method='POST',
      name='update')
  def Update(self, request):
    """Updates an existing device action.

    Args:
      request: a API request object.
    Returns:
      a mtt_messages.DeviceAction object
    """
    device_action = mtt_messages.ConvertToKey(
        ndb_models.DeviceAction, request.device_action_id).get()
    if not device_action:
      raise endpoints.NotFoundException(
          'no device action found for ID %s' % request.device_action_id)
    request.id = request.device_action_id
    device_action = mtt_messages.Convert(
        request, ndb_models.DeviceAction, mtt_messages.DeviceAction)
    device_action.put()
    return mtt_messages.Convert(device_action, mtt_messages.DeviceAction)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          device_action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{device_action_id}/delete',
      http_method='POST',
      name='delete')
  def Delete(self, request):
    """Deletes an existing device action.

    Args:
      request: a API request object.
    Returns:
      a void message.
    """
    device_action_key = mtt_messages.ConvertToKey(
        ndb_models.DeviceAction, request.device_action_id)
    device_action_key.delete()
    return message_types.VoidMessage()
