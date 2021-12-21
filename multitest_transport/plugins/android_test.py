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

"""Unit tests for android module."""
import datetime
from unittest import mock

from absl.testing import absltest
import apiclient

from multitest_transport.plugins import android
from multitest_transport.util import file_util


class AndroidBuildProviderTest(absltest.TestCase):

  def setUp(self):
    super(AndroidBuildProviderTest, self).setUp()
    self.provider = android.AndroidBuildProvider()
    self.client = mock.MagicMock()
    self.provider._client = self.client

  def assertBuildItem(self, item, name, path, is_file=False, size=None,
                      timestamp=None):
    """Validates a build item."""
    self.assertEqual(item.name, name)
    self.assertEqual(item.path, path)
    self.assertEqual(item.is_file, is_file)
    self.assertEqual(item.size, size)
    self.assertEqual(item.timestamp, timestamp)

  def testListBuildItems_branches(self):
    """Tests that branch items can be listed."""
    self.client.branch().list().execute.return_value = {
        'branches': [{'name': 'first'}, {'name': 'second'}],
        'nextPageToken': 'next_token',
    }
    # Returns a list of directory items and a page token
    items, token = self.provider.ListBuildItems(page_token='token')
    self.assertLen(items, 2)
    self.assertBuildItem(items[0], 'first', 'first')
    self.assertBuildItem(items[1], 'second', 'second')
    self.assertEqual(token, 'next_token')
    self.client.branch().list.assert_called_with(
        pageToken='token', fields=mock.ANY)

  def testListBuildItems_targets(self):
    """Tests that target items can be listed."""
    self.client.target().list().execute.return_value = {
        'targets': [{'name': 'first'}, {'name': 'second'}],
        'nextPageToken': 'next_token',
    }
    # Returns a list of directory items and a page token
    items, token = self.provider.ListBuildItems(
        path='branch', page_token='token')
    self.assertLen(items, 2)
    self.assertBuildItem(items[0], 'first', 'branch/first')
    self.assertBuildItem(items[1], 'second', 'branch/second')
    self.assertEqual(token, 'next_token')
    self.client.target().list.assert_called_with(
        branch='branch', pageToken='token', fields=mock.ANY)

  def testListBuildItems_builds(self):
    """Tests that build items can be listed."""
    self.client.build().list().execute.return_value = {
        'builds': [{'buildId': '123'}, {'buildId': '456'}, {'buildId': 'T789'}],
        'nextPageToken': 'next_token',
    }
    # Returns a list of directory items and a page token
    items, token = self.provider.ListBuildItems(path='branch/target')
    self.assertLen(items, 4)  # Additional LATEST item prepended
    self.assertBuildItem(items[0], 'LATEST', 'branch/target/LATEST')
    self.assertBuildItem(items[1], '123', 'branch/target/123')
    self.assertBuildItem(items[2], '456', 'branch/target/456')
    self.assertBuildItem(items[3], 'T789', 'branch/target/T789')
    self.assertEqual(token, 'next_token')
    self.client.build().list.assert_called_with(
        buildType='submitted',
        buildAttemptStatus='complete',
        branch='branch',
        target='target',
        pageToken=None)

  @mock.patch.object(android.AndroidBuildProvider, '_GetLatestBuild')
  def testListBuildItems_artifacts(self, mock_get_latest_build):
    """Tests that build artifact items can be listed."""
    mock_get_latest_build.return_value = {'buildId': '123'}
    self.client.buildartifact().list().execute.return_value = {
        'artifacts': [{
            'name': 'file',
            'size': '123',
            'lastModifiedTime': '946684800000',
        }],
        'nextPageToken': 'next_token',
    }
    # Returns a list of file items and a page token
    items, token = self.provider.ListBuildItems(path='branch/target/LATEST')
    self.assertLen(items, 1)
    self.assertBuildItem(items[0], 'file', 'branch/target/LATEST/file',
                         is_file=True, size=123,
                         timestamp=datetime.datetime(2000, 1, 1))
    self.assertEqual(token, 'next_token')
    self.client.buildartifact().list.assert_called_with(
        target='target',
        buildId='123',  # Called with actual build ID (instead of LATEST)
        attemptId='latest',
        pageToken=None)

  def testListBuildItems_invalidPath(self):
    """Tests that the providing too many path parts is forbidden."""
    with self.assertRaises(ValueError):
      self.provider.ListBuildItems('branch/target/LATEST/extra')

  def testGetBuildItem_branch(self):
    """Tests that a branch item can be retrieved."""
    self.client.branch().get().execute.return_value = {'name': 'branch'}
    # Returns a directory item with the right data
    item = self.provider.GetBuildItem('branch')  # one part
    self.assertBuildItem(item, 'branch', 'branch')
    self.client.branch().get.assert_called_with(
        resourceId='branch', fields=mock.ANY)

  def testGetBuildItem_target(self):
    """Tests that a target item can be retrieved."""
    self.client.target().get().execute.return_value = {'name': 'target'}
    # Returns a directory item with the right data
    item = self.provider.GetBuildItem('branch/target')  # two parts
    self.assertBuildItem(item, 'target', 'branch/target')
    self.client.target().get.assert_called_with(
        branch='branch', resourceId='target')

  def testGetBuildItem_build(self):
    """Tests that a build item can be retrieved."""
    self.client.build().get().execute.return_value = {
        'buildId': '123',
        'creationTimestamp': '946771200000'
    }
    # Returns a directory item with the right data
    item = self.provider.GetBuildItem('branch/target/123')  # three parts
    self.assertBuildItem(item, '123', 'branch/target/123',
                         timestamp=datetime.datetime(2000, 1, 2))
    self.client.build().get.assert_called_with(target='target', buildId='123')

  @mock.patch.object(android.AndroidBuildProvider, '_GetLatestBuild')
  def testGetBuildItem_latestBuild(self, mock_get_latest_build):
    """Tests that the LATEST build item can be retrieved."""
    mock_get_latest_build.return_value = {'buildId': '123'}
    # Returns a directory item with the right name
    item = self.provider.GetBuildItem('branch/target/LATEST')
    self.assertBuildItem(item, '123', 'branch/target/123')

  def testGetBuildItem_artifact(self):
    """Tests that a build artifact item can be retrieved."""
    self.client.buildartifact().get().execute.return_value = {
        'name': 'path/to/file',
        'size': 123,
        'lastModifiedTime': '946857600000'
    }
    # Returns a file item with the right data
    item = self.provider.GetBuildItem('branch/target/123/path/to/file')
    self.assertBuildItem(item, 'path/to/file', 'branch/target/123/path/to/file',
                         is_file=True, size=123,
                         timestamp=datetime.datetime(2000, 1, 3))
    self.client.buildartifact().get.assert_called_with(
        target='target',
        buildId='123',
        attemptId='latest',
        resourceId='path/to/file')

  def testGetBuildItem_notFound(self):
    """Tests that missing build items can be handled."""
    error = apiclient.http.HttpError(mock.Mock(status=404), 'not found')
    self.client.buildartifact().get().execute.side_effect = error
    # Returns None when encountering 404 errors
    item = self.provider.GetBuildItem('branch/target/123/path/to/file')
    self.assertIsNone(item)

  def testGetBuildItem_invalidPath(self):
    """Tests that the build item path is required."""
    with self.assertRaises(ValueError):
      self.provider.GetBuildItem('')

  def testGetLatestBuild(self):
    """Tests retrieving the LATEST build."""
    build = {'buildId': '123'}
    self.client.build().list().execute.return_value = {'builds': [build]}
    # Returns first build which was completed successfully
    self.assertEqual(build, self.provider._GetLatestBuild('branch', 'target'))
    self.client.build().list.assert_called_with(
        buildType='submitted',
        buildAttemptStatus='complete',
        branch='branch',
        successful=True,
        target='target',
        maxResults=1)

  def testGetLatestBuild_notFound(self):
    """Tests that a missing LATEST build can be handled."""
    self.client.build().list().execute.return_value = {'builds': []}
    with self.assertRaises(ValueError):
      self.provider._GetLatestBuild('branch', 'target')

  @mock.patch.object(
      apiclient.http.MediaIoBaseDownload, 'next_chunk', autospec=True)
  def testDownloadFile(self, mock_next_chunk):
    """Test downloading a file with multiple chunks."""
    path = 'branch/target/123/path/to/file'

    # Mock downloader that processes two chunks of data
    mock_progress = iter([
        (b'hello', mock.MagicMock(resumable_progress=5, total_size=10), False),
        (b'world', mock.MagicMock(resumable_progress=10, total_size=10), True),
    ])
    def _next_chunk(self, **_):
      value, status, done = next(mock_progress)
      self._fd.write(value)
      return status, done
    mock_next_chunk.side_effect = _next_chunk

    result = list(self.provider.DownloadFile(path))
    self.client.buildartifact().get_media.assert_called_with(
        buildId='123',
        target='target',
        attemptId='latest',
        resourceId='path/to/file')
    expected = [file_util.FileChunk(data=b'hello', offset=5, total_size=10),
                file_util.FileChunk(data=b'world', offset=10, total_size=10)]
    self.assertEqual(expected, result)


if __name__ == '__main__':
  absltest.main()
