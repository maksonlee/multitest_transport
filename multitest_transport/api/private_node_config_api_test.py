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

"""Tests for private_node_config_api."""

import json
from absl.testing import absltest
import mock


from multitest_transport.api import api_test_util
from multitest_transport.api import private_node_config_api
from multitest_transport.models import ndb_models
from google.oauth2 import service_account


class PrivateNodeConfigApiTest(api_test_util.TestCase):

  def setUp(self):
    super(PrivateNodeConfigApiTest, self).setUp(
        private_node_config_api.PrivateNodeConfigApi)

  def _CreatePrivateNodeConfig(self, data):
    private_node_config = ndb_models.PrivateNodeConfig(
        id=1,
        metrics_enabled=data['metrics_enabled'])
    return private_node_config

  def testGet(self):
    data = {
        'metrics_enabled': True,
    }
    private_node_config = self._CreatePrivateNodeConfig(data)
    private_node_config.put()

    res = self.app.get('/_ah/api/mtt/v1/private_node_config')

    msg = json.loads(res.body)
    self.assertEqual(data, msg)

  def testUpdate(self):
    data = {
        'metrics_enabled': True,
    }

    self.app.put_json('/_ah/api/mtt/v1/private_node_config', data)
    self.assertEqual(self._CreatePrivateNodeConfig(data),
                     ndb_models.GetPrivateNodeConfig())

  @mock.patch.object(service_account.Credentials, 'from_service_account_info')
  def testSetDefaultServiceAccount(self, mock_parse_key):
    """Tests setting the default service account."""

    # Mock parsing service account JSON key
    mock_parse_key.return_value = service_account.Credentials(None, None, None)
    # Set default auth
    self.app.put_json(
        '/_ah/api/mtt/v1/private_node_config/default_service_account',
        {'value': '{}'})

    # Verify that credentials were set
    private_node_config = ndb_models.GetPrivateNodeConfig()
    self.assertIsNotNone(private_node_config.default_credentials)

  def testRemoveDefaultServiceAccount(self):
    """Tests removing the default service account."""
    credentials = service_account.Credentials(None, None, None)
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.default_credentials = credentials
    private_node_config.put()

    # Remove default auth
    self.app.delete(
        '/_ah/api/mtt/v1/private_node_config/default_service_account')

    # Verify that credentials were cleared
    private_node_config = ndb_models.GetPrivateNodeConfig()
    self.assertIsNone(private_node_config.default_credentials)


if __name__ == '__main__':
  absltest.main()
