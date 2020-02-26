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
from multitest_transport.api import test_run_action_api
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


class TestRunActionApiTest(api_test_util.TestCase):

  def setUp(self, api_class=test_run_action_api.TestRunActionApi):
    super(TestRunActionApiTest, self).setUp(api_class)
    self.test_run_actions = [
        self._CreateTestRunAction(name='one', hook_class_name='simple'),
        self._CreateTestRunAction(name='two', hook_class_name='oauth2'),
        self._CreateTestRunAction(name='three', hook_class_name='oauth2',
                                  credentials=client.Credentials())
    ]

  def _CreateTestRunAction(self, **kwargs):
    """Convenience method to create a test run action."""
    action = ndb_models.TestRunAction(**kwargs)
    action.put()
    return action

  def _VerifyAttrs(self, obj, **kwargs):
    """Verifies that the object contains the specified attributes."""
    for key, value in kwargs.items():
      self.assertEqual(getattr(obj, key), value)

  def testList(self):
    """Tests that a list of actions can be fetched."""
    response = self.app.get('/_ah/api/mtt/v1/test_run_actions')
    actions = protojson.decode_message(messages.TestRunActionList,
                                       response.body).actions
    # All actions found with their authorization states
    self.assertLen(actions, 3)
    self._VerifyAttrs(
        actions[0], name='one', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)
    self._VerifyAttrs(
        actions[1], name='two', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.UNAUTHORIZED)
    self._VerifyAttrs(
        actions[2], name='three', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.AUTHORIZED)

  def testGet(self):
    """Tests that a single action can be fetched."""
    action_id = str(self.test_run_actions[0].key.id())
    response = self.app.get('/_ah/api/mtt/v1/test_run_actions/%s' % action_id)
    action = protojson.decode_message(messages.TestRunAction, response.body)
    self._VerifyAttrs(
        action, id=action_id, name='one', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)

  def testGet_notFound(self):
    """Tests that an error occurs when an action is not found."""
    response = self.app.get(
        '/_ah/api/mtt/v1/test_run_actions/unknown', expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testCreate(self):
    """Tests that a new action can be created."""
    data = {'name': 'created', 'hook_class_name': 'simple'}
    response = self.app.post_json('/_ah/api/mtt/v1/test_run_actions', data)
    action = protojson.decode_message(messages.TestRunAction, response.body)
    self._VerifyAttrs(
        action, name='created', hook_class_name='simple',
        authorization_state=ndb_models.AuthorizationState.NOT_APPLICABLE)

  def testCreate_stripId(self):
    """Tests that new actions have new IDs."""
    data = {'id': '1', 'name': 'created', 'hook_class_name': 'simple'}
    response = self.app.post_json('/_ah/api/mtt/v1/test_run_actions', data)
    action = protojson.decode_message(messages.TestRunAction, response.body)
    self.assertNotEqual('1', action.id)

  def testCreate_missingFields(self):
    """Tests that an error occurs if fields are missing."""
    response = self.app.post_json(
        '/_ah/api/mtt/v1/test_run_actions', {}, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status)

  def testUpdate(self):
    """Tests that an existing action can be updated."""
    action_id = str(self.test_run_actions[0].key.id())
    data = {'name': 'updated', 'hook_class_name': 'oauth2'}
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_actions/%s' % action_id, data)
    action = protojson.decode_message(messages.TestRunAction, response.body)
    self._VerifyAttrs(
        action,
        id=action_id, name='updated', hook_class_name='oauth2',
        authorization_state=ndb_models.AuthorizationState.UNAUTHORIZED)

  def testUpdate_notFound(self):
    """Tests that an error occurs when an action is not found."""
    data = {'name': 'updated', 'hook_class_name': 'oauth2'}
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_actions/unknown', data, expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testDelete(self):
    """Tests that an existing action can be deleted."""
    action_key = self.test_run_actions[0].key
    self.app.delete('/_ah/api/mtt/v1/test_run_actions/%s' % action_key.id())
    self.assertIsNone(action_key.get())

  def testDelete_notFound(self):
    """Tests that no error occurs when deleting an unknown action."""
    self.app.delete('/_ah/api/mtt/v1/test_run_actions/unknown')

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  @mock.patch.object(oauth2_util, 'GetRedirectUri')
  def testGetAuthorizationInfo(self, mock_get_redirect, mock_get_flow):
    """Tests that authorization info can be retrieved."""
    action_id = str(self.test_run_actions[1].key.id())  # unauthorized
    # Mock getting URIs from OAuth2 utilities
    mock_get_redirect.return_value = 'redirect_uri', True
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step1_get_authorize_url.return_value = 'auth_uri'
    mock_get_flow.return_value = oauth2_flow
    # Verify authorization info
    response = self.app.get(
        '/_ah/api/mtt/v1/test_run_actions/%s/auth?redirect_uri=%s' %
        (action_id, 'redirect_uri'))
    authorization_info = protojson.decode_message(messages.AuthorizationInfo,
                                                  response.body)
    self.assertEqual(authorization_info.url, 'auth_uri')
    self.assertEqual(authorization_info.is_manual, True)

  def testGetAuthorizationInfo_notFound(self):
    """Tests that an error occurs when an action is not found."""
    response = self.app.put_json(
        '/_ah/api/mtt/v1/test_run_actions/%s/auth?redirect_uri=%s' %
        ('unknown', 'redirect_uri'),
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  def testAuthorize(self, mock_get_flow):
    """Tests that an action can be authorized."""
    action_id = str(self.test_run_actions[1].key.id())  # unauthorized
    # Mock getting credentials from OAuth2 utilities
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step2_exchange.return_value = client.Credentials()
    mock_get_flow.return_value = oauth2_flow
    # Verify that credentials were obtained and stored
    self.app.post(
        '/_ah/api/mtt/v1/test_run_actions/%s/auth?redirect_uri=%s&code=%s' %
        (action_id, 'redirect_uri', 'code'))
    oauth2_flow.step2_exchange.assert_called_once_with('code')
    self.assertIsNotNone(self.test_run_actions[1].credentials)

  def testAuthorize_notFound(self):
    """Tests that an error occurs when an action is not found."""
    response = self.app.post(
        '/_ah/api/mtt/v1/test_run_actions/%s/auth?redirect_uri=%s&code=%s' %
        ('unknown', 'redirect_uri', 'code'),
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  def testUnauthorize(self):
    """Tests that an action can be unauthorized."""
    action_id = str(self.test_run_actions[2].key.id())  # authorized
    # Verify that credentials were removed
    self.app.delete('/_ah/api/mtt/v1/test_run_actions/%s/auth' % action_id)
    self.assertIsNone(self.test_run_actions[2].credentials)

  def testUnauthorize_notFound(self):
    """Tests that an error occurs when an action is not found."""
    response = self.app.delete(
        '/_ah/api/mtt/v1/test_run_actions/%s/auth' % 'unknown',
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)


if __name__ == '__main__':
  absltest.main()
