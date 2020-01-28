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

"""Tests for build_channel_api."""

from absl.testing import absltest

import mock
from oauth2client import client
from protorpc import protojson

from multitest_transport.api import api_test_util
from multitest_transport.api import build_channel_api
from multitest_transport.models import build
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.util import oauth2_util


class AndroidBuildProvider(plugins.BuildProvider):
  """Dummy build provider for testing."""
  name = 'Android'

  def __init__(self):
    super(AndroidBuildProvider, self).__init__()
    self.AddOptionDef('mock_option')


class GoogleDriverBuildProvider(plugins.BuildProvider):
  """Dummy build provider for testing."""
  name = 'Google Drive'


class BuildChannelApiTest(api_test_util.TestCase):

  def setUp(self):
    super(BuildChannelApiTest, self).setUp(build_channel_api.BuildChannelApi)

  def _CreateMockBuildChannel(self, name='android', provider='Android'):
    return build.AddBuildChannel(name, provider, {})

  def testList(self):
    self._CreateMockBuildChannel(name='android', provider='Android')
    self._CreateMockBuildChannel(name='drive', provider='Google Drive')

    res = self.app.get('/_ah/api/mtt/v1/build_channels')
    build_channel_list = protojson.decode_message(
        messages.BuildChannelList, res.body)

    # verify that the right channels are returned
    build_channels = build_channel_list.build_channels
    self.assertEqual(2, len(build_channels))
    self.assertItemsEqual(['android', 'drive'], [
        channel.name for channel in build_channels])
    self.assertItemsEqual(['Android', 'Google Drive'], [
        channel.provider_name for channel in build_channels])

  def testGet(self):
    config = self._CreateMockBuildChannel()

    res = self.app.get('/_ah/api/mtt/v1/build_channels/%s' % config.key.id())
    build_channel_config = protojson.decode_message(messages.BuildChannelConfig,
                                                    res.body)

    # verify that the right channel is returned
    self.assertEqual(config.key.id(), build_channel_config.id)
    self.assertEqual('android', build_channel_config.name)

  def testGet_notFound(self):
    # unknown build channel ID
    res = self.app.get('/_ah/api/mtt/v1/build_channels/%s' % 666,
                       expect_errors=True)
    # throws if channel not found
    self.assertEqual('404 Not Found', res.status)

  @mock.patch.object(build.BuildChannel, 'ListBuildItems')
  def testListBuildItems(self, mock_channel):
    # create dummy build items to return from channel
    build_items = [
        plugins.BuildItem(name='item1', path=u'path1', is_file=True),
        plugins.BuildItem(name='item2', path=u'path2', is_file=True)
    ]
    mock_channel.return_value = build_items, 'next_page_token'
    config = self._CreateMockBuildChannel()

    res = self.app.get(
        '/_ah/api/mtt/v1/build_channels/%s/build_items' % config.key.id())
    build_item_list = protojson.decode_message(messages.BuildItemList, res.body)

    # verify same build items are returned
    self.assertEqual('next_page_token', build_item_list.next_page_token)
    self.assertItemsEqual(['item1', 'item2'], [
        item.name for item in build_item_list.build_items])

  def testListBuildItems_notFound(self):
    # unknown build channel ID
    res = self.app.get('/_ah/api/mtt/v1/build_channels/%s/build_items' % 666,
                       expect_errors=True)
    # throws if channel not found
    self.assertEqual('404 Not Found', res.status)

  def testDelete(self):
    # create build channel and confirm it exists
    config = self._CreateMockBuildChannel()
    self.assertIsNotNone(config.key.get())

    # delete channel and verify that it no longer exists
    self.app.post('/_ah/api/mtt/v1/build_channels/%s/delete' % config.key.id())
    self.assertIsNone(config.key.get())

  def testCreate(self):
    data = {
        'name': 'testName',
        'id': '',
        'provider_name': 'Android',
        'options': [{
            'name': 'mock_option',
            'value': '123123123'
        }]
    }
    res = self.app.post_json('/_ah/api/mtt/v1/build_channels', data)
    msg = protojson.decode_message(messages.BuildChannelConfig, res.body)
    build_channel_config = messages.ConvertToKey(ndb_models.BuildChannelConfig,
                                                 msg.id).get()
    self.assertIsNotNone(build_channel_config)
    self.assertEqual(data['name'], build_channel_config.name)
    self.assertEqual(data['provider_name'], build_channel_config.provider_name)
    self.assertEqual(data['options'][0]['name'],
                     build_channel_config.options[0].name)

  def testUpdate(self):
    build_channel_config = self._CreateMockBuildChannel()
    build_channel_config_id = str(build_channel_config.key.id())
    data = {
        'id': build_channel_config_id,
        'name': 'bar',
        'provider_name': 'Android'
    }
    res = self.app.put_json(
        '/_ah/api/mtt/v1/build_channels/%s' % build_channel_config_id, data)

    build_channel_config = build_channel_config.key.get()
    msg = protojson.decode_message(messages.BuildChannelConfig, res.body)
    self.assertEqual(
        messages.Convert(build_channel_config, messages.BuildChannelConfig),
        msg)
    self.assertEqual(data['name'], build_channel_config.name)

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  @mock.patch.object(oauth2_util, 'GetRedirectUri')
  def testGetAuthorizationInfo(self, mock_get_redirect, mock_get_flow):
    """Tests that authorization info can be retrieved."""
    config = self._CreateMockBuildChannel(name='android', provider='Android')
    # Mock getting URIs from OAuth2 utilities
    mock_get_redirect.return_value = 'redirect_uri', True
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step1_get_authorize_url.return_value = 'auth_uri'
    mock_get_flow.return_value = oauth2_flow
    # Verify authorization info
    response = self.app.get(
        '/_ah/api/mtt/v1/build_channels/%s/get_authorize_url?redirect_uri=%s' %
        (config.key.id(), 'redirect_uri'))
    authorization_info = protojson.decode_message(messages.AuthorizationInfo,
                                                  response.body)
    self.assertEqual(authorization_info.url, 'auth_uri')
    self.assertEqual(authorization_info.is_manual, True)

  def testGetAuthorizationInfo_notFound(self):
    """Tests that an error occurs when a build channel is not found."""
    response = self.app.put_json(
        '/_ah/api/mtt/v1/build_channels/%s/get_authorize_url?redirect_uri=%s' %
        ('unknown', 'redirect_uri'),
        expect_errors=True)
    self.assertEqual('404 Not Found', response.status)

  @mock.patch.object(oauth2_util, 'GetOAuth2Flow')
  def testAuthorizeConfig(self, mock_get_flow):
    """Tests that a build channel can be authorized."""
    config = self._CreateMockBuildChannel(name='android', provider='Android')
    # Mock getting credentials from OAuth2 utilities
    oauth2_flow = mock.MagicMock()
    oauth2_flow.step2_exchange.return_value = client.Credentials()
    mock_get_flow.return_value = oauth2_flow
    # Verify that credentials were obtained and stored
    self.app.post(
        '/_ah/api/mtt/v1/build_channels/%s/authorize?redirect_uri=%s&code=%s'
        % (config.key.id(), 'redirect_uri', 'code'))
    oauth2_flow.step2_exchange.assert_called_once_with('code')
    self.assertIsNotNone(config.credentials)

  def testAuthorizeConfig_notFound(self):
    """Tests that an error occurs when a build channel is not found."""
    response = self.app.post(
        '/_ah/api/mtt/v1/build_channels/%s/authorize?redirect_uri=%s&code=%s'
        % ('unknown', 'redirect_uri', 'code'), expect_errors=True)
    self.assertEqual('404 Not Found', response.status)


if __name__ == '__main__':
  absltest.main()
