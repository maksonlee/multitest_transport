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

from protorpc import message_types
from protorpc import remote

from google3.third_party.apphosting.python.endpoints.v1_1 import endpoints

from multitest_transport.api import base
from multitest_transport.models import messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='private_node_config',
                        path='private_node_config')
class PrivateNodeConfigApi(remote.Service):
  """A handler for User Settings API."""

  @base.convert_exception
  @endpoints.method(message_types.VoidMessage, messages.PrivateNodeConfig,
                    http_method='GET', path='/private_node_config', name='get')
  def Get(self, request):
    private_node_config = ndb_models.GetPrivateNodeConfig()
    return messages.Convert(private_node_config, messages.PrivateNodeConfig)

  @base.convert_exception
  @endpoints.method(messages.PrivateNodeConfig, messages.PrivateNodeConfig,
                    http_method='POST', path='/private_node_config',
                    name='update')
  def Update(self, request):
    private_node_config = messages.Convert(
        request, ndb_models.PrivateNodeConfig, messages.PrivateNodeConfig)
    private_node_config.put()
    return messages.Convert(private_node_config, messages.PrivateNodeConfig)
