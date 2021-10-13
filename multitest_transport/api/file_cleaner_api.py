# Copyright 2021 Google LLC
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

"""A module to provide file cleaner APIs."""
# Non-standard docstrings are used to generate the API documentation.
from protorpc import message_types
from protorpc import remote

from multitest_transport.api import base
from multitest_transport.models import messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='file_cleaner', path='file_cleaner')
class FileCleanerApi(remote.Service):
  """A handler for File Cleaner API."""

  @base.ApiMethod(
      message_types.VoidMessage,
      messages.FileCleanerSettings,
      http_method='GET',
      path='/file_cleaner/settings',
      name='get')
  def Get(self, request):
    """Fetches the server's file cleaner settings."""
    settings = ndb_models.GetFileCleanerSettings()
    return messages.Convert(settings, messages.FileCleanerSettings)

  @base.ApiMethod(
      messages.FileCleanerSettings,
      messages.FileCleanerSettings,
      http_method='PUT',
      path='/file_cleaner/settings',
      name='update')
  def Update(self, request):
    """Updates the server's file cleaner settings.

    Body:
      File cleaner settings data
    """
    settings = messages.Convert(request, ndb_models.FileCleanerSettings,
                                messages.FileCleanerSettings)
    settings.put()
    return messages.Convert(settings, messages.FileCleanerSettings)
