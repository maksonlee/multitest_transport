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

"""A module to provide test APIs."""

from protorpc import message_types
from protorpc import messages
from protorpc import remote

from google3.third_party.apphosting.python.endpoints.v1_1 import endpoints

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


@base.MTT_API.api_class(resource_name='test', path='tests')
class TestApi(remote.Service):
  """A handler for Test API."""

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(message_types.VoidMessage),
      mtt_messages.TestList, path='/tests', http_method='GET',
      name='list')
  def List(self, request):
    tests = list(ndb_models.Test.query().order(ndb_models.Test.name))
    test_msgs = mtt_messages.Convert(tests, mtt_messages.Test)
    return mtt_messages.TestList(tests=test_msgs)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.Test),
      mtt_messages.Test, path='/tests', http_method='POST',
      name='create')
  def Create(self, request):
    test = mtt_messages.Convert(
        request, ndb_models.Test, from_cls=mtt_messages.Test)
    test.put()
    return mtt_messages.Convert(test, mtt_messages.Test)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_id=messages.StringField(1, required=True)),
      mtt_messages.Test, path='{test_id}', http_method='GET',
      name='get')
  def Get(self, request):
    test = None
    # For test plan ID 0, it should return a default test plan object which can
    # be used as a template in UI.
    if request.test_id == '0':
      test = ndb_models.Test(name='')
    else:
      test = mtt_messages.ConvertToKey(ndb_models.Test, request.test_id).get()
    if not test:
      raise endpoints.NotFoundException(
          'no test found for ID %s' % request.test_id)
    return mtt_messages.Convert(test, mtt_messages.Test)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.Test, test_id=messages.StringField(1, required=True)),
      mtt_messages.Test, path='{test_id}', http_method='POST',
      name='update')
  def Update(self, request):
    test = mtt_messages.ConvertToKey(ndb_models.Test, request.test_id).get()
    if not test:
      raise endpoints.NotFoundException(
          'no test found for ID %s' % request.test_id)
    request.id = request.test_id
    test = mtt_messages.Convert(request, ndb_models.Test, mtt_messages.Test)
    test.put()
    return mtt_messages.Convert(test, mtt_messages.Test)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_id=messages.StringField(1, required=True)),
      message_types.VoidMessage, path='{test_id}/delete', http_method='POST',
      name='delete')
  def Delete(self, request):
    test_key = mtt_messages.ConvertToKey(ndb_models.Test, request.test_id)
    test_key.delete()
    return message_types.VoidMessage()
