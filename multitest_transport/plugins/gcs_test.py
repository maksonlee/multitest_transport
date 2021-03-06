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

"""Unit tests for gcs."""

from absl.testing import absltest
import apiclient
import mock

from multitest_transport.models import event_log
from multitest_transport.plugins import base
from multitest_transport.plugins import constant
from multitest_transport.plugins import gcs
from multitest_transport.util import errors
from multitest_transport.util import file_util


class GCSBuildProviderTest(absltest.TestCase):

  def testGetBuildItem_withPathToFile(self):
    """Test GetBuildItem with input a path to file."""
    provider = gcs.GCSBuildProvider()
    path = 'sample_bucket/path/to/file/kitten.png'
    response = {
        'bucket': 'sample_bucket',
        'contentType': 'image/png',
        'crc32c': 'pNKjPQ==',
        'etag': 'CO7voM6XjtwCEAE=',
        'generation': '1531007560333294',
        'id': 'sample_bucket/path/to/file/kitten.png/1531007560333294',
        'kind': 'storage#object',
        'md5Hash': 'KCbI3PYk1aHfekIvf/osrw==',
        'mediaLink': 'https://sample_link_for_media_download',
        'metageneration': '1',
        'name': 'path/to/file/kitten.png',
        'selfLink': 'https://sample_link_to_the_object',
        'size': '168276',
        'storageClass': 'MULTI_REGIONAL',
        'timeCreated': '2018-07-07T23:52:40.332Z',
        'timeStorageClassUpdated': '2018-07-07T23:52:40.332Z',
        'updated': '2018-07-07T23:52:40.332Z'
    }

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().get().execute.return_value = response
    provider._client = mock_api_client

    build_item = provider.GetBuildItem(path)
    self.assertTrue(build_item.is_file)
    self.assertEqual(build_item.name, 'kitten.png')
    self.assertEqual(build_item.path, path)

  def testGetBuildItem_withInvalidBucketName(self):
    """Test GetBuildItem with invalid bucket name."""
    provider = gcs.GCSBuildProvider()
    path = 'invalid_bucket_name/path/to/file/kitten.png'

    mock_api_client = mock.MagicMock()
    side_effect = apiclient.http.HttpError(mock.Mock(status=404), 'not found')
    mock_api_client.objects().get().execute.side_effect = side_effect
    provider._client = mock_api_client

    build_item = provider.GetBuildItem(path)
    self.assertIsNone(build_item)

  def testGetBuildItem_withPathToDirectory(self):
    """Test GetBuildItem with input a path to directory."""
    provider = gcs.GCSBuildProvider()
    path = 'sample_bucket/pathToDirectory/'
    response = {
        'bucket': 'sample_bucket',
        'contentType': 'application/x-www-form-urlencoded;charset=UTF-8',
        'crc32c': 'AAAAAA==',
        'etag': 'CMaAgsuXjtwCEAE=',
        'generation': '1531007553536070',
        'id': 'sample_bucket/aa5/abc/bla//1531007553536070',
        'kind': 'storage#object',
        'md5Hash': '1B2M2Y8AsgTpgAmY7PhCfg==',
        'mediaLink': 'https://sample_link_for_media_download',
        'metageneration': '1',
        'name': 'pathToDirectory/',
        'selfLink': 'https://sample_link_to_the_object',
        'size': '0',
        'storageClass': 'MULTI_REGIONAL',
        'timeCreated': '2018-07-07T23:52:33.535Z',
        'timeStorageClassUpdated': '2018-07-07T23:52:33.535Z',
        'updated': '2018-07-07T23:52:33.535Z'
    }

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().get().execute.return_value = response
    provider._client = mock_api_client

    build_item = provider.GetBuildItem(path)
    self.assertFalse(build_item.is_file)
    self.assertEqual(build_item.size, 0)

  def testGetBuildItem_withNoObjectName(self):
    """Test GetBuildItem with input a path with no object name."""
    provider = gcs.GCSBuildProvider()
    path = 'sample_bucket'
    build_item = provider.GetBuildItem(path)
    self.assertFalse(build_item.is_file)
    self.assertEqual(build_item.size, None)
    self.assertEqual(build_item.path, path)

  @mock.patch.object(gcs.GCSBuildProvider, '_GetGCSObject')
  def testGetBuildItem_withNoFilename(self, mock_gcs_object):
    """Test GetBuildItem with input a path with no filename."""
    provider = gcs.GCSBuildProvider()
    path = 'sample_bucket/sample_path'
    mock_gcs_object.side_effect = [None, None]
    build_item = provider.GetBuildItem(path)
    self.assertEqual(build_item, None)
    mock_gcs_object.asset_has_calls([
        mock.call('sample_bucket', 'sample_path'),
        mock.call('sample_bucket', 'sample_path/')
    ])

  def testListBuildItems_withNormalResponse(self):
    """Test ListBuildItems with input that contains both file and directory."""
    provider = gcs.GCSBuildProvider()
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

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().list().execute.return_value = response
    provider._client = mock_api_client

    build_items, next_page_token = provider.ListBuildItems(
        path='sample_bucket/fake/path', page_token=None)
    self.assertIsNotNone(build_items)
    self.assertEqual(next_page_token, 'CgV0bXAzLw==')
    self.assertEqual(len(build_items), 3)
    self.assertEqual(build_items[0].name, 'kitten.png')
    self.assertEqual(build_items[0].path, 'sample_bucket/fake/path/kitten.png')

  def testListBuildItems_withFileOnlyResponse(self):
    """Test ListBuildItems with input that contains only files."""
    provider = gcs.GCSBuildProvider()
    response = {
        'items': [{
            'bucket': 'sample_bucket',
            'contentType': 'image/png',
            'name': 'kitten.png',
            'size': '168276',
            'updated': '2018-07-06T23:29:21.410Z'
        }],
        'nextPageToken':
            'CgV0bXAzLw==',
    }

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().list().execute.return_value = response
    provider._client = mock_api_client

    build_items, next_page_token = provider.ListBuildItems(
        path='sample_bucket', page_token=None)

    self.assertIsNotNone(build_items)
    self.assertEqual(next_page_token, 'CgV0bXAzLw==')
    self.assertEqual(len(build_items), 1)
    self.assertEqual(build_items[0].name, 'kitten.png')
    self.assertTrue(build_items[0].is_file)

  def testListBuildItems_withDirectoryOnlyResponse(self):
    """Test ListBuildItems with input that contains only directory."""
    provider = gcs.GCSBuildProvider()
    response = {'nextPageToken': 'CgV0bXAzLw==', 'prefixes': ['aa5/', 'tmp1/']}

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().list().execute.return_value = response
    provider._client = mock_api_client

    build_items, next_page_token = provider.ListBuildItems(
        path='sample_bucket/', page_token=None)
    self.assertIsNotNone(build_items)
    self.assertEqual(next_page_token, 'CgV0bXAzLw==')
    self.assertEqual(len(build_items), 2)
    self.assertFalse(build_items[0].is_file)

  def testListBuildItems_withEmptyFolder(self):
    """Test ListBuildItems with input that mimics an empty folder."""
    provider = gcs.GCSBuildProvider()
    response = {
        'items': [{
            'bucket': 'sample_bucket',
            'contentType': 'application/x-www-form-urlencoded;charset=UTF-8',
            'name': 'kitten.png',
            'size': '168276',
            'updated': '2018-07-06T23:29:21.410Z'
        }],
        'nextPageToken':
            'CgV0bXAzLw==',
    }

    mock_api_client = mock.MagicMock()
    mock_api_client.objects().list().execute.return_value = response
    provider._client = mock_api_client

    build_items, next_page_token = provider.ListBuildItems(
        path='sample_bucket/', page_token=None)
    self.assertIsNotNone(build_items)
    self.assertEqual(next_page_token, 'CgV0bXAzLw==')
    self.assertEqual(len(build_items), 0)

  def testListBuildItems_withInvalidBucket(self):
    """Test ListBuildItems with Invalid Bucket Name."""
    provider = gcs.GCSBuildProvider()

    mock_api_client = mock.MagicMock()
    side_effect = apiclient.http.HttpError(mock.Mock(status=404), 'not found')
    mock_api_client.objects().list().execute.side_effect = side_effect
    provider._client = mock_api_client

    with self.assertRaises(gcs.GCSBucketNotFoundError) as e:
      provider.ListBuildItems(path='invalid_bucket/', page_token=None)

    self.assertEqual(
        e.exception.message, 'bucket invalid_bucket does not exist')

  @mock.patch.object(gcs.GCSBuildProvider, 'GetBuildItem')
  def testDownloadFile_withInvalidFile(self, mock_get_build_item):
    """Try to download folder instead of file."""
    provider = gcs.GCSBuildProvider()
    path = 'bucket/fake/path/'
    fake_build_item = base.BuildItem(
        name='path/',
        path='bucket/fake/path/',
        is_file=False,
        size=0,
        timestamp=None)
    mock_get_build_item.return_value = fake_build_item
    with self.assertRaises(errors.FileNotFoundError) as e:
      list(provider.DownloadFile(path))
    self.assertEqual(
        e.exception.message, 'Build item bucket/fake/path/ does not exist')

  @mock.patch.object(gcs.GCSBuildProvider, 'GetBuildItem')
  def testDownloadFile_withNoneValue(self, mock_get_build_item):
    """Try to download a file that does not exist."""
    provider = gcs.GCSBuildProvider()
    path = 'bucket/fake/path/'
    mock_get_build_item.return_value = None
    with self.assertRaises(errors.FileNotFoundError) as e:
      list(provider.DownloadFile(path))
    self.assertEqual(
        e.exception.message, 'Build item bucket/fake/path/ does not exist')

  @mock.patch.object(gcs.GCSBuildProvider, 'GetBuildItem')
  @mock.patch.object(
      apiclient.http.MediaIoBaseDownload, 'next_chunk', autospec=True)
  def testDownloadFile(self, mock_next_chunk, mock_get_build_item):
    """Test downloading a file with multiple chunks."""
    provider = gcs.GCSBuildProvider()
    provider._client = mock.MagicMock()
    path = 'bucket/fake/path/kitten.png'
    mock_get_build_item.return_value = base.BuildItem(
        name='kitten.png',
        path='bucket/fake/path/kitten.png',
        is_file=True,
        size=0,
        timestamp=None)

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

    result = list(provider.DownloadFile(path))
    provider._client.objects().get_media.assert_called_with(
        bucket='bucket', object='fake/path/kitten.png')
    expected = [file_util.FileChunk(data=b'hello', offset=5, total_size=10),
                file_util.FileChunk(data=b'world', offset=10, total_size=10)]
    self.assertEqual(expected, result)


class GCSFileUploadHookTest(absltest.TestCase):

  @mock.patch.object(event_log, 'Info')
  @mock.patch.object(file_util, 'FileHandleMediaUpload')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testUploadFile(self, mock_handle_factory, mock_media_upload_ctor,
                     mock_log):
    """Tests uploading a file to GCS."""
    hook = gcs.GCSFileUploadHook(file_pattern='.*')

    # Configure mock file handle
    mock_handle = mock.MagicMock()
    mock_handle_factory.return_value = mock_handle
    # Configure mock media uploader
    mock_media_upload = mock.MagicMock()
    mock_media_upload_ctor.return_value = mock_media_upload
    # Configure mock client and response (upload will be done)
    hook._client = mock.MagicMock()
    hook._client.objects().insert().next_chunk.return_value = None, True

    # Upload file and verify that client and uploader used properly
    hook.UploadFile(mock.MagicMock(), 'file_url', 'bucket/test_run/file.txt')
    mock_media_upload_ctor.assert_called_with(
        mock_handle, chunksize=constant.UPLOAD_CHUNK_SIZE, resumable=True)
    hook._client.objects().insert.assert_called_with(
        bucket='bucket',
        name='test_run/file.txt',
        media_body=mock_media_upload)
    mock_log.assert_called_with(
        mock.ANY, '[GCS] Uploaded file_url to bucket/test_run/file.txt.')


if __name__ == '__main__':
  absltest.main()
