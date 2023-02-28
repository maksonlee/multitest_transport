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

"""Unit tests for google_drive."""
import json
from unittest import mock

from absl.testing import absltest
import apiclient


from multitest_transport.plugins import base
from multitest_transport.plugins import google_drive
from multitest_transport.util import errors
from multitest_transport.util import file_util


class GoogleDriveTest(absltest.TestCase):

  def testFindBuildItemPath(self):
    provider = google_drive.GoogleDriveBuildProvider()
    self.assertEqual(
        None, provider.FindBuildItemPath('http://foo.com/bar/zzz'))
    self.assertEqual(
        '_id/1MpKCcIbPWmqwljk26onhQgENlL8lSdjg',
        provider.FindBuildItemPath(
            'https://drive.google.com/file/d/1MpKCcIbPWmqwljk26onhQgENlL8lSdjg/view'
        ))
    self.assertEqual(
        '_id/1IrGl5_Zoj1mGMIuhzHAJB-lDpFfBWq3H',
        provider.FindBuildItemPath(
            'https://drive.google.com/open?id=1IrGl5_Zoj1mGMIuhzHAJB-lDpFfBWq3H'
        ))

  def testGetFileIds(self):
    """Test GetFileIds."""
    provider = google_drive.GoogleDriveBuildProvider()
    response = {
        u'kind':
            u'drive#fileList',
        u'incompleteSearch':
            False,
        u'files': [{
            u'mimeType': u'application/vnd.google-apps.document',
            u'name': u'Midterm Eval',
            u'kind': u'drive#file',
            u'id': u'file_id1'
        }, {
            u'mimeType': u'image/jpeg',
            u'name': u'cat.jpg',
            u'kind': u'drive#file',
            u'id': u'file_id2'
        }, {
            u'mimeType': u'application/vnd.google-apps.folder',
            u'name': u'random',
            u'kind': u'drive#file',
            u'id': u'file_id3'
        }]
    }
    mock_api_client = mock.MagicMock()
    mock_api_client.files().list().execute.return_value = response
    provider._client = mock_api_client

    child_ids, page_token = provider._GetFileIds(param={})
    self.assertIsNotNone(child_ids)
    self.assertIsNone(page_token)
    self.assertEqual(3, len(child_ids))
    self.assertEqual(child_ids, ['file_id1', 'file_id2', 'file_id3'])

  def testGetFileIds_withEmptyResponse(self):
    """Test GetFileIds with empty response."""
    provider = google_drive.GoogleDriveBuildProvider()

    mock_api_client = mock.MagicMock()
    mock_api_client.files().list().execute.return_value = {}
    provider._client = mock_api_client

    child_ids, page_token = provider._GetFileIds(param={})
    self.assertIsNotNone(child_ids)
    self.assertIsNone(page_token)
    self.assertEqual(0, len(child_ids))
    self.assertEqual(child_ids, [])

  def testGetFileIds_withInvalidFileId(self):
    """Test GetFileIds with invalid field id."""
    provider = google_drive.GoogleDriveBuildProvider()

    mock_api_client = mock.MagicMock()
    side_effect = apiclient.http.HttpError(mock.Mock(status=404), 'not found')
    mock_api_client.files().list().execute.side_effect = side_effect
    provider._client = mock_api_client
    with self.assertRaises(errors.PluginError) as e:
      param = {}
      param['q'] = (
          google_drive._QUERY_ITEM_FORMAT % ('parent_id', 'child_name'))
      provider._GetFileIds(param=param)
    self.assertEqual(e.exception.message,
                     google_drive._PARAM_NOT_VALID_ERROR % json.dumps(param))

  def testGetFileItem_withInvalidFileId(self):
    """Test GetFileItem with invalid file id."""
    provider = google_drive.GoogleDriveBuildProvider()

    mock_api_client = mock.MagicMock()
    side_effect = apiclient.http.HttpError(mock.Mock(status=404), 'not found')
    mock_api_client.files().get().execute.side_effect = side_effect
    provider._client = mock_api_client

    with self.assertRaises(errors.FileNotFoundError) as e:
      provider._GetFileItem(file_id='invalid_file_id')
    self.assertEqual(e.exception.message,
                     google_drive._INVALID_FILE_ID_ERROR % 'invalid_file_id')

  def testGetFileItem(self):
    """Test GetFileItem."""
    provider = google_drive.GoogleDriveBuildProvider()
    response = {
        u'mimeType': u'application/vnd.google-apps.folder',
        u'name': u'sample_folder',
        u'modifiedTime': u'2018-06-25T18:24:52.049Z'
    }

    mock_api_client = mock.MagicMock()
    mock_api_client.files().get().execute.return_value = response
    provider._client = mock_api_client

    file_item = provider._GetFileItem(file_id='sample_folder_id')
    self.assertIsNotNone(file_item)
    self.assertEqual(file_item['mimeType'], google_drive._FOLDER_TYPE)
    self.assertEqual(file_item['name'], 'sample_folder')

  def testConvertFileToBuildItem_withFolderObject(self):
    """test _ConvertFileToBuildItem with a folder object."""
    provider = google_drive.GoogleDriveBuildProvider()

    file_item = {
        u'mimeType': u'application/vnd.google-apps.folder',
        u'name': u'sample_folder',
        u'modifiedTime': u'2018-06-25T18:24:52.049Z'
    }
    path = 'folderA/sample_folder/'
    build_item = provider._ConvertFileToBuildItem(file_item, path)
    self.assertIsNotNone(build_item)
    self.assertEqual(build_item.name, 'sample_folder/')
    self.assertEqual(build_item.path, path)
    self.assertFalse(build_item.is_file)
    self.assertEqual(build_item.size, 0)
    self.assertIsNone(build_item.timestamp)

  def testConvertFileToBuildItem_withFileObject(self):
    """Test _ConvertFileToBuildItem with a file object."""
    provider = google_drive.GoogleDriveBuildProvider()

    file_item = {
        u'mimeType': u'application/vnd.google-apps.document',
        u'name': u'sample_file.txt',
        u'modifiedTime': u'2018-07-23T05:24:23.624Z'
    }
    path = 'folderA/sample_folder/sample_file.txt'
    build_item = provider._ConvertFileToBuildItem(
        file_item, path)
    self.assertIsNotNone(build_item)
    self.assertEqual(build_item.name, 'sample_file.txt')
    self.assertEqual(build_item.path, path)
    self.assertTrue(build_item.is_file)
    self.assertEqual(build_item.size, 0)
    self.assertIsNotNone(build_item.timestamp)

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileIds')
  def testGetFileIdHelper_withDuplicatedObjectNames(
      self, mock_get_file_ids):
    """Test _GetFileIdHelper with duplicated object names."""
    provider = google_drive.GoogleDriveBuildProvider()
    mock_get_file_ids.return_value = (['id_1', 'id_2'], None)

    with self.assertRaises(errors.PluginError) as e:
      provider._GetFileIdHelper(parent_folder_id='parent', name='folderA')

    self.assertEqual(e.exception.message,
                     google_drive._DUPLICATED_OBJECT_NAME_ERROR % 'folderA')

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileIds')
  def testGetFileIdHelper_withEmptyResults(
      self, mock_get_file_ids):
    """Test _GetFileIdHelper with empty reults."""
    provider = google_drive.GoogleDriveBuildProvider()

    mock_get_file_ids.return_value = ([], None)

    with self.assertRaises(errors.FileNotFoundError) as e:
      provider._GetFileIdHelper(parent_folder_id='parent', name='folderA')

    self.assertEqual(e.exception.message,
                     google_drive._FILE_NOT_FOUND_ERROR % 'folderA')

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileIds')
  def testGetFileIdHelper(
      self, mock_get_file_ids):
    """Test _GetFileIdHelper with empty reults."""
    provider = google_drive.GoogleDriveBuildProvider()

    mock_get_file_ids.return_value = (['id_1'], None)
    object_id = provider._GetFileIdHelper(
        parent_folder_id='parent', name='folderA')

    self.assertIsNotNone(object_id)
    self.assertEqual(object_id, 'id_1')

  def testGetFileId_withEmptyPath(self):
    """Test _GetFileId from path with empty path."""
    provider = google_drive.GoogleDriveBuildProvider()
    folder_id = provider._GetFileId('')
    self.assertEqual(folder_id, 'root')

  def testGetFileId_withFileIdPath(self):
    """Test _GetFileId with file ID path."""
    provider = google_drive.GoogleDriveBuildProvider()
    file_id = 'file_id'
    self.assertEqual(
        file_id,
        provider._GetFileId(google_drive._FILE_ID_PATH_PREFIX + file_id))

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileIdHelper')
  def testGetFolderIdFromPath_withValidPath(self, mock_get_object_id_helper):
    """Test _GetFileId with valid path."""
    provider = google_drive.GoogleDriveBuildProvider()
    mock_get_object_id_helper.return_value = 'folderA_valid_id'
    folder_id = provider._GetFileId('folderA/')
    self.assertEqual(folder_id, 'folderA_valid_id')

    mock_get_object_id_helper.return_value = 'folderC_valid_id'
    folder_id = provider._GetFileId('folder A/folder B/folder C')
    self.assertEqual(folder_id, 'folderC_valid_id')

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileItem')
  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileId')
  def testGetBuildItem_withPathToFile(
      self, mock_get_object_id, mock_get_file_item):
    """Test GetBuildItem with path to file."""
    provider = google_drive.GoogleDriveBuildProvider()
    mock_get_object_id.return_value = 'valid_id'
    response = {
        u'mimeType': u'application/vnd.google-apps.folder',
        u'name': u'sample_folder',
        u'modifiedTime': u'2018-06-25T18:24:52.049Z'
    }
    mock_get_file_item.return_value = response
    build_item = provider.GetBuildItem('folderA/folderB/sample_folder')
    self.assertIsNotNone(build_item)
    self.assertEqual(build_item.name, 'sample_folder/')
    self.assertEqual(build_item.path, 'folderA/folderB/sample_folder')
    self.assertFalse(build_item.is_file)
    self.assertEqual(build_item.size, 0)
    self.assertIsNone(build_item.timestamp)

  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileItem')
  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileIds')
  @mock.patch.object(google_drive.GoogleDriveBuildProvider,
                     '_GetFileId')
  def testListBuildItems(
      self, mock_get_object_id, mock_get_file_ids, mock_get_file_item):
    """Test ListBuildItems."""
    provider = google_drive.GoogleDriveBuildProvider()
    mock_get_object_id.return_value = 'valid_id'
    mock_get_file_ids.return_value = (['id_1', 'id_2'], None)
    response = {
        u'mimeType': u'application/vnd.google-apps.folder',
        u'name': u'sample_folder',
        u'modifiedTime': u'2018-06-25T18:24:52.049Z'
    }
    mock_get_file_item.return_value = response
    build_items, next_page_token = provider.ListBuildItems(
        path='', page_token=None)
    self.assertIsNotNone(build_items)
    self.assertEqual(len(build_items), 2)
    self.assertIsNone(next_page_token)
    self.assertEqual(build_items[0].name, 'sample_folder/')
    self.assertEqual(build_items[0].path, 'sample_folder')
    self.assertFalse(build_items[0].is_file)
    self.assertEqual(build_items[0].size, 0)
    self.assertIsNone(build_items[0].timestamp)

  @mock.patch.object(google_drive.GoogleDriveBuildProvider, 'GetBuildItem')
  def testDownloadFile_withInvalidFile(self, mock_get_build_item):
    """Try to download folder instead of file."""
    provider = google_drive.GoogleDriveBuildProvider()
    path = 'fake/path/'
    fake_build_item = base.BuildItem(
        name='fake/path/',
        path='fake/path/',
        is_file=False,
        size=0,
        timestamp=None)
    mock_get_build_item.return_value = fake_build_item
    with self.assertRaises(errors.FileNotFoundError) as e:
      list(provider.DownloadFile(path))
    self.assertEqual(
        e.exception.message, google_drive._FILE_NOT_FOUND_ERROR % path)

  @mock.patch.object(google_drive.GoogleDriveBuildProvider, 'GetBuildItem')
  def testDownloadFile_withNoneValue(self, mock_get_build_item):
    """Try to download a file that does not exist."""
    provider = google_drive.GoogleDriveBuildProvider()
    path = 'fake/path/'
    mock_get_build_item.return_value = None
    with self.assertRaises(errors.FileNotFoundError) as e:
      list(provider.DownloadFile(path))
    self.assertEqual(
        e.exception.message, google_drive._FILE_NOT_FOUND_ERROR % path)

  @mock.patch.object(google_drive.GoogleDriveBuildProvider, '_GetFileId')
  @mock.patch.object(google_drive.GoogleDriveBuildProvider, 'GetBuildItem')
  @mock.patch.object(
      apiclient.http.MediaIoBaseDownload, 'next_chunk', autospec=True)
  def testDownloadFile(self, mock_next_chunk, mock_build_item, mock_file_id):
    """Test downloading a file with multiple chunks."""
    provider = google_drive.GoogleDriveBuildProvider()
    provider._client = mock.MagicMock()
    path = 'fake/path/kitten.png'
    mock_build_item.return_value = base.BuildItem(
        name='fake/path/kitten.png',
        path='fake/path/kitten.png',
        is_file=True,
        size=0,
        timestamp=None)
    mock_file_id.return_value = 'file_id'

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
    mock_file_id.assert_called_with('fake/path/kitten.png')
    provider._client.files().get_media.assert_called_with(fileId='file_id')
    expected = [file_util.FileChunk(data=b'hello', offset=5, total_size=10),
                file_util.FileChunk(data=b'world', offset=10, total_size=10)]
    self.assertEqual(expected, result)


if __name__ == '__main__':
  absltest.main()
