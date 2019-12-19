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

"""Integration Tests for build_channel_api.

This integration test went through the flow from hitting the listBuildItem
api to getting the proper response. It currently uses fake credential object
and mocked out Google Cloud Storage Service.
"""

import collections
import json

from absl.testing import absltest
import mock
from oauth2client import client

from multitest_transport.api import api_test_util
from multitest_transport.api import build_channel_api
from multitest_transport.models import build
from multitest_transport.plugins import gcs


class BuildChannelApiIntegrationTest(api_test_util.TestCase):
  """An integration test for BuildChannelApi."""

  def setUp(self):
    super(BuildChannelApiIntegrationTest, self).setUp(
        build_channel_api.BuildChannelApi)

  def _CreateMockBuildGCSChannel(self):
    """Create a mock build google cloud storage channel."""
    return build.AddBuildChannel(
        'integration_test',
        'Google Cloud Storage',
        collections.OrderedDict([(u'bucket_name', u'mtt_gcs_test')]))

  def _FakeOAuthCredentials(self):
    """Create a fake oauth credentials for authentication purpose."""
    credentials = client.OAuth2Credentials(
        access_token='fake-access-token',
        client_id='fake-client-id',
        client_secret='fake-client-secret',
        refresh_token='fake-refresh-token',
        token_expiry=None,
        token_uri='fake-token-uri',
        user_agent='fake-user-agent')
    return credentials

  @mock.patch.object(gcs.GCSBuildProvider, '_GetClient')
  def testListBuildItems_withGoogleCloudStorage(self, mock_get_client):
    """Test List Build Items with response from google cloud storage."""
    config = self._CreateMockBuildGCSChannel()

    build_channel_id = config.key.id()
    build_channel = build.GetBuildChannel(build_channel_id)
    build_channel._StoreCredentials(self._FakeOAuthCredentials())
    self.assertIsNotNone(build_channel._LoadCredentials())

    response = {
        'items': [{
            'bucket': 'sample_bucket',
            'contentType': 'image/png',
            'name': 'fake/path/kitten.png',
            'size': '168276',
            'updated': '2018-07-06T23:29:21.410Z'
        }],
        'nextPageToken':
            'CgV0bXAzLw==',
        'prefixes': ['fake/path/temp1/', 'fake/path/temp2/']
    }
    mock_client = mock.MagicMock()
    mock_client.objects().list().execute.return_value = response
    mock_get_client.return_value = mock_client

    app_response = self.app.get(
        '/_ah/api/mtt/v1/build_channels/%s/build_items?path=%s' % (
            config.key.id(), 'sample_bucket/fake/path/'))
    body = json.loads(app_response.body)
    self.assertEqual(len(body['build_items']), 3)
    file_item = body['build_items'][0]
    self.assertTrue(file_item['is_file'])
    self.assertEqual(file_item['name'], 'kitten.png')
    self.assertEqual(file_item['path'], 'sample_bucket/fake/path/kitten.png')
    self.assertEqual(int(file_item['size']), 168276)
    folder_item = body['build_items'][1]
    self.assertFalse(folder_item['is_file'])
    self.assertEqual(folder_item['name'], 'temp1/')
    self.assertEqual(folder_item['path'], 'sample_bucket/fake/path/temp1/')


if __name__ == '__main__':
  absltest.main()
