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
"""Tests for test_run_hook_api."""
from absl.testing import absltest
import mock
from oauth2client import client
from protorpc import protojson

from multitest_transport.api import api_test_util
from multitest_transport.api import test_run_hook_api
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.util import oauth2_util


class SimpleHook(plugins.TestRunHook):
  """Simple test run hook."""
  name = 'simple'


class OAuth2Hook(plugins.TestRunHook):
  """Test run hook with OAuth2 configuration."""
  name = 'oauth2'
  oauth2_config = plugins.OAuth2Config('id', 'secret', ['scope'])


class TestRunHookApiTest(api_test_util.TestCase):

  def setUp(self, api_class=test_run_hook_api.TestRunHookApi):
    super(TestRunHookApiTest, self).setUp(api_class)
    self.hook_configs = [
        self._CreateHookConfig(name='one', hook_class_name='simple'),
        self._CreateHookConfig(name='two', hook_class_name='oauth2'),
        self._CreateHookConfig(name='three', hook_class_name='oauth2',
                               credentials=client.Credentials())
    ]

  def _CreateHookConfig(self, **kwargs):
    """Convenience method to create a hook configuration."""
    hook_config = ndb_models.TestRunHookConfig(**kwargs)
    hook_config.put()
    return hook_config

  def _VerifyAttrs(self, obj, **kwargs):
    """Verifies that the object contains the specified attributes."""
    for key, value in kwargs.items():
      self.assertEqual(getattr(obj, key), value)

  def testListConfigs(self):
    """Tests that a list of hook configs can be fetched."""
    response = self.app.get('/_ah/api/mtt/v1/test_run_hooks/configs')
    hook_configs = protojson.decode_message(messages.TestRunHookConfigList,
                                            response.body).configs
    # All hook configs found with their authorization states
    self.assertLen(hook_configs, 3)
    self._VerifyAttrs(
        hook_configs[0], name='one', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)
    self._VerifyAttrs(
        hook_configs[1], name='two', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.UNAUTHORIZED)
    self._VerifyAttrs(
        hook_configs[2], name='three', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.AUTHORIZED)

  def testGetConfig(self):
    """Tests that a single hook config can be fetched."""
    hook_config_id = str(self.hook_configs[0].key.id())
    response = self.app.get('/_ah/api/mtt/v1/test_run_hooks/configs/%s' %
                            hook_config_id)
    hook_config = protojson.decode_message(messages.TestRunHookConfig,
                                           response.body)
    self._VerifyAttrs(
        hook_config, id=hook_config_id, name='one', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)

  def testGetConfig_notFound(self):
    """Tests that an error occurs when a hook config is not found."""
    response = self.app.get(
        '/_ah/api/mtt/v1/test_run_hooks/configs/unknown', expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testCreateConfig(self):
    """Tests that a new hook config can be created."""
    data = {'name': 'created', 'hook_class_name': 'simple'}
    response = self.app.post_json('/_ah/api/mtt/v1/test_run_hooks/configs',
                                  data)
    hook_config = protojson.decode_message(messages.TestRunHookConfig,
                                           response.body)
    self._VerifyAttrs(
        hook_config, name='created', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)

  def testCreateConfig_stripId(self):
    """Tests that new hook configs have new IDs."""
    data = {'id': '1', 'name': 'created', 'hook_class_name': 'simple'}
    response = self.app.post_json('/_ah/api/mtt/v1/test_run_hooks/configs',
                                  data)
    hook_config = protojson.decode_message(messages.TestRunHookConfig,
                                           response.body)
    self.assertNotEqual('1', hook_config.id)

  def testCreateConfig_missingFields(self):
    """Tests that an error occurs if fields are missing."""
    response = self.app.post_json(
        '/_ah/api/mtt/v1/test_run_hooks/configs', {}, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status)

  def testUpdateConfig(self):
    """Tests that an existing hook config can be updated."""
    hook_config_id = str(self.hook_configs[0].key.id())
    data = {'name': 'updated', 'hook_class_name': 'oauth2'}
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_hooks/configs/%s' % hook_config_id, data)
    hook_config = protojson.decode_message(messages.TestRunHookConfig,
                                           response.body)
    self._VerifyAttrs(
        hook_config,
        id=hook_config_id, name='updated', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.UNAUTHORIZED)

  def testUpdateConfig_notFound(self):
    """Tests that an error occurs when a hook config is not found."""
    data = {'name': 'updated', 'hook_class_name': 'oauth2'}
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_hooks/configs/unknown', data,
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testDeleteConfig(self):
    """Tests that an existing hook config can be deleted."""
    hook_config_key = self.hook_configs[0].key
    self.app.delete('/_ah/api/mtt/v1/test_run_hooks/configs/%s' %
                    hook_config_key.id())
    self.assertIsNone(hook_config_key.get())

  def testDeleteConfig_notFound(self):
    """Tests that no error occurs when deleting an unknown hook config."""
    self.app.delete('/_ah/api/mtt/v1/test_run_hooks/configs/unknown')

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  @mock.patch.object(oauth2_util, 'GetRedirectUri')
  def testGetAuthorizationInfo(self, mock_get_redirect, mock_get_flow):
    """Tests that authorization info can be retrieved."""
    hook_config_id = str(self.hook_configs[1].key.id())  # unauthorized
    # Mock getting URIs from OAuth2 utilities
    mock_get_redirect.return_value = 'redirect_uri', True
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step1_get_authorize_url.return_value = 'auth_uri'
    mock_get_flow.return_value = oauth2_flow
    # Verify authorization info
    response = self.app.get(
        '/_ah/api/mtt/v1/test_run_hooks/configs/%s/auth?redirect_uri=%s' %
        (hook_config_id, 'redirect_uri'))
    authorization_info = protojson.decode_message(messages.AuthorizationInfo,
                                                  response.body)
    self.assertEqual(authorization_info.url, 'auth_uri')
    self.assertEqual(authorization_info.is_manual, True)

  def testGetAuthorizationInfo_notFound(self):
    """Tests that an error occurs when a hook config is not found."""
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_hooks/configs/%s/auth?redirect_uri=%s' %
        ('unknown', 'redirect_uri'),
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  def testAuthorizeConfig(self, mock_get_flow):
    """Tests that a hook configuration can be authorized."""
    hook_config_id = str(self.hook_configs[1].key.id())  # unauthorized
    # Mock getting credentials from OAuth2 utilities
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step2_exchange.return_value = client.Credentials()
    mock_get_flow.return_value = oauth2_flow
    # Verify that credentials were obtained and stored
    self.app.post(
        '/_ah/api/mtt/v1/test_run_hooks/configs/%s/auth_return?redirect_uri=%s&code=%s'
        % (hook_config_id, 'redirect_uri', 'code'))
    oauth2_flow.step2_exchange.assert_called_once_with('code')
    self.assertIsNotNone(self.hook_configs[1].credentials)

  def testAuthorizeConfig_notFound(self):
    """Tests that an error occurs when a hook config is not found."""
    response = self.app.post(
        '/_ah/api/mtt/v1/test_run_hooks/configs/%s/auth_return?redirect_uri=%s&code=%s'
        % ('unknown', 'redirect_uri', 'code'), expect_errors=True)
    self.assertEqual('404 Not Found', response.status)


if __name__ == '__main__':
  absltest.main()
