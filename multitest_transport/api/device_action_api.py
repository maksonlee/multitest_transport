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

"""A module to provide device action APIs."""
# Non-standard docstrings are used to generate the API documentation.
import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='device_action', path='device_actions')
class DeviceActionApi(remote.Service):
  """A handler for Device Action API."""

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage),
      mtt_messages.DeviceActionList, path='/device_actions', http_method='GET',
      name='list')
  def List(self, request):
    """Lists device actions."""
    device_actions = list(ndb_models.DeviceAction.query()
                          .order(ndb_models.DeviceAction.name))
    device_action_msgs = mtt_messages.ConvertList(
        device_actions, mtt_messages.DeviceAction)
    return mtt_messages.DeviceActionList(
        device_actions=device_action_msgs)

  @base.ApiMethod(
      endpoints.ResourceContainer(mtt_messages.DeviceAction),
      mtt_messages.DeviceAction, path='/device_actions', http_method='POST',
      name='create')
  def Create(self, request):
    """Creates a device action.

    Body:
      Device action data
    """
    device_action = mtt_messages.Convert(
        request, ndb_models.DeviceAction, from_cls=mtt_messages.DeviceAction)
    device_action.put()
    return mtt_messages.Convert(device_action, mtt_messages.DeviceAction)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          device_action_id=messages.StringField(1, required=True)),
      mtt_messages.DeviceAction, path='{device_action_id}', http_method='GET',
      name='get')
  def Get(self, request):
    """Fetches a device action.

    Parameters:
      device_action_id: Device action ID
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

  @base.ApiMethod(
      endpoints.ResourceContainer(
          mtt_messages.DeviceAction,
          device_action_id=messages.StringField(1, required=True)),
      mtt_messages.DeviceAction, path='{device_action_id}', http_method='PUT',
      name='update')
  def Update(self, request):
    """Updates an existing device action.

    Body:
      Device action data
    Parameters:
      device_action_id: Device action ID
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

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          device_action_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{device_action_id}',
      http_method='DELETE',
      name='delete')
  def Delete(self, request):
    """Deletes an existing device action.

    Parameters:
      device_action_id: Device action ID
    """
    device_action_key = mtt_messages.ConvertToKey(
        ndb_models.DeviceAction, request.device_action_id)
    device_action_key.delete()
    return message_types.VoidMessage()
