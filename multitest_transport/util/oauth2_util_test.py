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
import six
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.util import ndb_shim as ndb
from google.oauth2 import credentials as authorized_user
from google.oauth2 import service_account

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
    value = six.ensure_binary(json.dumps(data))
    credentials = prop._from_base_type(value)
    self.assertIsNotNone(credentials)
    self.assertEqual('client_id', credentials.client_id)
    self.assertEqual('client_secret', credentials.client_secret)
    self.assertEqual('refresh_token', credentials.refresh_token)


class OAuth2UtilTest(absltest.TestCase):

  def testGetRedirectUri_local(self):
    """Tests that local URIs can be used directly."""
    local_uri = 'http://localhost:8000/auth_return'
    self.assertEqual((local_uri, False), oauth2_util.GetRedirectUri(local_uri))

  def testGetRedirectUri_remote(self):
    """Tests that remote URIs must use the copy/paste flow."""
    remote_uri = 'http://www.google.com/auth_return'
    self.assertEqual((oauth2_util.MANUAL_COPY_PASTE_URI, True),
                     oauth2_util.GetRedirectUri(remote_uri))

  def testGetOAuth2Flow(self):
    """Tests that an OAuth2 flow can be constructed."""
    oauth2_config = oauth2_util.OAuth2Config(
        client_id='id', client_secret='secret', scopes=['lorem', 'ipsum'])
    flow = oauth2_util.GetOAuth2Flow(oauth2_config, 'redirect_uri')
    self.assertEqual('id', flow.oauth2session.client_id)
    self.assertEqual(['lorem', 'ipsum'], flow.oauth2session.scope)
    self.assertEqual('redirect_uri', flow.oauth2session.redirect_uri)

  def testGetOAuth2Flow_noConfig(self):
    """Tests that the OAuth2 config is required when creating a flow."""
    with self.assertRaises(ValueError):
      oauth2_util.GetOAuth2Flow(None, 'redirect_uri')


if __name__ == '__main__':
  absltest.main()
