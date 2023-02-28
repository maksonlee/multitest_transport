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

"""Unit tests for oauth2_util."""
import json

from absl.testing import absltest
from google.oauth2 import credentials as authorized_user
from google.oauth2 import service_account
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.util import ndb_shim as ndb


from multitest_transport.util import oauth2_util


class TestModel(ndb.Model):
  """Dummy model to test storing credentials."""
  credentials = oauth2_util.CredentialsProperty()


class CredentialsPropertyTest(testbed_dependent_test.TestbedDependentTest):
  """Tests for oauth2_util.CredentialsProperty."""

  def testStore(self):
    """Tests that credentials can be stored and retrieved."""
    credentials = authorized_user.Credentials.from_authorized_user_info({
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'refresh_token',
    })
    entity = TestModel(id='foo', credentials=credentials)
    entity.put()
    retrieved = TestModel.get_by_id('foo')
    self.assertIsNotNone(retrieved.credentials)
    self.assertEqual('client_id', retrieved.credentials.client_id)
    self.assertEqual('client_secret', retrieved.credentials.client_secret)
    self.assertEqual('refresh_token', retrieved.credentials.refresh_token)

  def testValidate(self):
    """Tests that the credentials type is validated."""
    prop = oauth2_util.CredentialsProperty()
    # None is allowed
    prop._validate(None)
    # User authorization and service accounts are allowed
    prop._validate(authorized_user.Credentials(None))
    prop._validate(service_account.Credentials(None, None, None))
    # Anything else is forbidden
    with self.assertRaises(TypeError):
      prop._validate({})

  def testParseLegacy(self):
    """Tests that legacy JSON blobs can be parsed."""
    prop = oauth2_util.CredentialsProperty()
    data = {
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'refresh_token',
    }
    value = json.dumps(data).encode()
    credentials = prop._from_base_type(value)
    self.assertIsNotNone(credentials)
    self.assertEqual('client_id', credentials.client_id)
    self.assertEqual('client_secret', credentials.client_secret)
    self.assertEqual('refresh_token', credentials.refresh_token)


if __name__ == '__main__':
  absltest.main()
