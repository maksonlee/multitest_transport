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

"""Unit tests for parter_android_build."""

import json
import urllib2

import mock

from absl.testing import absltest
from multitest_transport.plugins import base
from multitest_transport.plugins import partner_android_build

from multitest_transport.util import file_util


class PartnerAndroidBuildProviderTest(absltest.TestCase):

  def setUp(self):
    super(PartnerAndroidBuildProviderTest, self).setUp()
    self.provider = partner_android_build.PartnerAndroidBuildProvider()
    self.provider.UpdateOptions(account_id='account_id')
    self.mock_credentials = mock.MagicMock()
    self.provider.UpdateCredentials(self.mock_credentials)

  def testListBuildItems_branches(self):
    """Test ListBuildItems for branches."""
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path='', item_type=base.BuildItemType.DIRECTORY))
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path='', item_type=base.BuildItemType.FILE))

  def testListBuildItems_targets(self):
    """Test ListBuildItems for targets."""
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path='foo', item_type=base.BuildItemType.DIRECTORY))
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path='foo', item_type=base.BuildItemType.FILE))

  @mock.patch.object(urllib2, 'urlopen', autospec=True)
  @mock.patch.object(urllib2, 'Request', autospec=True)
  def testListBuildItems_builds_forDirectory(self, mock_request, mock_urlopen):
    """Test ListBuildItems for builds."""
    mock_request_obj = mock.MagicMock()
    mock_request.return_value = mock_request_obj
    mock_response_obj = mock.MagicMock()
    mock_urlopen.return_value = mock_response_obj
    mock_response_obj.read.return_value = json.dumps({
        'build': [{
            'build_id': 'build_id',
            'release_candidate_name': 'release_candidate_name',
            'build_attempt_status': 'COMPLETE',
            'success': 'boolean'
        }]
    })

    build_items, page_token = self.provider.ListBuildItems(
        path='foo/bar', item_type=base.BuildItemType.DIRECTORY)

    options = self.provider.GetOptions()
    exp_url = '%s/builds/list/foo/bar/DUMMY/DUMMY?a=%s' % (
        partner_android_build.API_BASE_URL, options.account_id)
    self.mock_credentials.apply.assert_called()
    mock_request.assert_called_with(exp_url, headers=mock.ANY)
    mock_urlopen.assert_called_with(mock_request_obj)
    mock_response_obj.read.assert_called()
    exp_build_items = [
        base.BuildItem(
            name='build_id',
            path='foo/bar/build_id',
            is_file=False,
            size=None,
            timestamp=None)
    ]
    self.assertEqual(exp_build_items, build_items)
    self.assertIsNone(page_token)

  def testListBuildItems_builds_forFile(self):
    """Test ListBuildItems for builds."""
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path='foo/bar', item_type=base.BuildItemType.FILE))

  def testListBuildItems_buildArtifacts_forDirectory(self):
    """Test ListBuildItems for build artifacts."""
    path = 'foo/bar/zzz'
    self.assertEqual(
        ([], None), self.provider.ListBuildItems(
            path=path, item_type=base.BuildItemType.DIRECTORY))

  @mock.patch.object(urllib2, 'urlopen', autospec=True)
  @mock.patch.object(urllib2, 'Request', autospec=True)
  def testListBuildItems_buildArtifacts_forFile(
      self, mock_request, mock_urlopen):
    """Test ListBuildItems for build artifactss."""
    mock_request_obj = mock.MagicMock()
    mock_request.return_value = mock_request_obj
    mock_response_obj = mock.MagicMock()
    mock_urlopen.return_value = mock_response_obj
    mock_response_obj.read.return_value = json.dumps({
        'buildArtifacts': [{
            'name': 'name',
            'size': 12345,
            'content_type': 'content_type',
            'internal': False
        }]
    })

    build_items, page_token = self.provider.ListBuildItems(
        path='foo/bar/zzz', item_type=base.BuildItemType.FILE)

    options = self.provider.GetOptions()
    exp_url = '%s/builds/artifacts/foo/bar/zzz/DUMMY?a=%s' % (
        partner_android_build.API_BASE_URL, options.account_id)
    self.mock_credentials.apply.assert_called()
    mock_request.assert_called_with(exp_url, headers=mock.ANY)
    mock_urlopen.assert_called_with(mock_request_obj)
    mock_response_obj.read.assert_called()
    exp_build_items = [
        base.BuildItem(
            name='name',
            path='foo/bar/zzz/name',
            is_file=True,
            size=12345,
            timestamp=None)
    ]
    self.assertEqual(exp_build_items, build_items)
    self.assertIsNone(page_token)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(
      partner_android_build.PartnerAndroidBuildProvider, '_CallAPI')
  def testDownloadFile(self, mock_call_api, mock_download_file):
    download_url = 'download_url'
    mock_call_api.return_value = {'url': download_url}

    self.provider.DownloadFile('foo/bar/zzz/yyy', offset=12)
    mock_download_file.assert_called_with(download_url, offset=12)

if __name__ == '__main__':
  absltest.main()
