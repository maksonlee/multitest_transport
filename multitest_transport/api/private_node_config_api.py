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

"""A module to provide private node config APIs."""
# Non-standard docstrings are used to generate the API documentation.

import json
import endpoints
from protorpc import message_types
from protorpc import remote

from google.oauth2 import service_account


from multitest_transport.api import base
from multitest_transport.models import messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='private_node_config',
                        path='private_node_config')
class PrivateNodeConfigApi(remote.Service):
  """A handler for User Settings API."""

  @base.ApiMethod(message_types.VoidMessage, messages.PrivateNodeConfig,
                  http_method='GET', path='/private_node_config', name='get')
  def Get(self, request):
    """Fetches the server's private node configuration."""
    private_node_config = ndb_models.GetPrivateNodeConfig()
    return messages.Convert(private_node_config, messages.PrivateNodeConfig)

  @base.ApiMethod(messages.PrivateNodeConfig, messages.PrivateNodeConfig,
                  http_method='PUT', path='/private_node_config',
                  name='update')
  def Update(self, request):
    """Updates the server's private node configuration.

    Body:
      Private node configuration data
    """
    private_node_config = messages.Convert(
        request, ndb_models.PrivateNodeConfig, messages.PrivateNodeConfig)
    private_node_config.put()
    return messages.Convert(private_node_config, messages.PrivateNodeConfig)

  @base.ApiMethod(
      endpoints.ResourceContainer(
          messages.SimpleMessage,),
      message_types.VoidMessage,
      path='/private_node_config/default_service_account',
      http_method='PUT',
      name='set_default_service_account')
  def SetDefaultServiceAccount(self, request):
    """Sets the default service account key to use for all services.

    Body:
      Service account JSON key file data
    """
    data = json.loads(request.value)
    credentials = service_account.Credentials.from_service_account_info(data)

    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.default_credentials = credentials
    private_node_config.put()
    return message_types.VoidMessage()

  @base.ApiMethod(
      message_types.VoidMessage,
      message_types.VoidMessage,
      path='/private_node_config/default_service_account',
      http_method='DELETE',
      name='remove_default_service_account')
  def RemoveDefaultServiceAccount(self, request):
    """Removes the default service account credentials."""
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.default_credentials = None
    private_node_config.put()
    return message_types.VoidMessage()
