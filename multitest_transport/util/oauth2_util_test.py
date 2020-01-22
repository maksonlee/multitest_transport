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
from absl.testing import absltest

from multitest_transport.util import oauth2_util


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
    oauth2_config = oauth2_util.OAuth2Config('id', 'secret', ['lorem', 'ipsum'])
    flow = oauth2_util.GetOAuth2Flow(oauth2_config, 'redirect')
    self.assertEqual('id', flow.client_id)
    self.assertEqual('secret', flow.client_secret)
    self.assertEqual('lorem ipsum', flow.scope)
    self.assertEqual('redirect', flow.redirect_uri)

  def testGetOAuth2Flow_noConfig(self):
    """Tests that the OAuth2 config is required when creating a flow."""
    with self.assertRaises(ValueError):
      oauth2_util.GetOAuth2Flow(None, 'redirect_uri')


if __name__ == '__main__':
  absltest.main()
