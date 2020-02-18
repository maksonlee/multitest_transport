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

"""Tests for multitest_transport.util.file_util.py."""
import datetime
import io
import os
import urllib2

from absl.testing import absltest
import cloudstorage as gcs
import mock

from multitest_transport.util import env
from multitest_transport.util import file_util


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


class FileUtilTest(absltest.TestCase):
  """Test for file_util functions."""

  def setUp(self):
    super(FileUtilTest, self).setUp()
    env.FILE_SERVER_URL = 'browsepy/'
    env.STORAGE_PATH = 'root'

  def testFileHandle_Get(self):
    # GCS URL
    handle = file_util.FileHandle.Get('gs://bucket/filename')
    self.assertIsInstance(handle, file_util.GCSFileHandle)
    self.assertEqual(handle.file_path, '/bucket/filename')

    # Browsepy URL
    handle = file_util.FileHandle.Get('file://root/path')
    self.assertIsInstance(handle, file_util.BrowsepyFileHandle)
    self.assertEqual(handle.file_path, '/path')
    self.assertEqual(handle.request_url, 'browsepy/open/path')

    # Default URL
    handle = file_util.FileHandle.Get('http://localhost:8000/path')
    self.assertIsInstance(handle, file_util.HttpFileHandle)

  @mock.patch.object(file_util.FileHandle, 'ReadBytes')
  def testFileHandle_FileObject(self, mock_read_byte):
    # Mocking ReadBytes() method with StringIO.
    f = io.StringIO(u'hello\nworld')
    def ReadBytes(offset, length):
      f.seek(offset)
      if length is None:
        length = -1
      return f.read(length)
    mock_read_byte.side_effect = ReadBytes

    file_handle = file_util.FileHandle('url')
    self.assertEqual('hello\nworld', file_handle.read())

    file_handle.seek(0)
    self.assertEqual('h', file_handle.read(1))
    self.assertEqual('e', file_handle.read(1))
    self.assertEqual('l', file_handle.read(1))
    self.assertEqual('l', file_handle.read(1))
    self.assertEqual('o', file_handle.read(1))

    file_handle.seek(0)
    self.assertEqual('hello', file_handle.readline())
    self.assertEqual(6, file_handle.tell())
    self.assertEqual('world', file_handle.readline())
    self.assertEqual(11, file_handle.tell())

    file_handle.seek(0)
    self.assertEqual('h', file_handle.readline(1))

    file_handle.seek(0)
    self.assertEqual(['hello', 'world'], file_handle.readlines())
    self.assertEqual([], file_handle.readlines())

    file_handle.seek(0)
    self.assertEqual(['hello'], file_handle.readlines(5))
    self.assertEqual(['world'], file_handle.readlines())

    file_handle.seek(0)
    self.assertEqual('hello', file_handle.next())
    self.assertEqual('world', file_handle.next())
    self.assertIsNone(file_handle.next())

  @mock.patch.object(urllib2, 'urlopen')
  def testHttpFileHandle_Info(self, mock_urlopen):
    def Info(key):
      if key == 'content-length':
        return '123'
      if key == 'content-type':
        return 'type'
      if key == 'last-modified':
        return 'Fri, 01 Jan 1990 00:00:00 GMT'
      return None

    mock_file = mock.MagicMock()
    mock_file.info().get.side_effect = Info
    mock_urlopen.return_value = mock_file

    file_info = file_util.HttpFileHandle('url').Info()
    self.assertEqual(file_info.total_size, 123)
    self.assertEqual(file_info.content_type, 'type')
    self.assertEqual(file_info.timestamp, datetime.datetime(1990, 1, 1))

  @mock.patch.object(urllib2, 'urlopen')
  def testHttpFileHandle_Info_notFound(self, mock_urlopen):
    mock_urlopen.side_effect = urllib2.HTTPError(None, 404, None, None, None)
    self.assertIsNone(file_util.HttpFileHandle('url').Info())

  @mock.patch.object(gcs, 'stat')
  def testGCSFileHandle_Info(self, mock_stat):
    mock_info = mock.MagicMock()
    mock_info.st_size = 123
    mock_info.content_type = 'type'
    mock_info.st_ctime = 631152000
    mock_stat.return_value = mock_info

    file_info = file_util.GCSFileHandle('url').Info()
    self.assertEqual(file_info.total_size, 123)
    self.assertEqual(file_info.content_type, 'type')
    self.assertEqual(file_info.timestamp, datetime.datetime(1990, 1, 1))

  @mock.patch.object(gcs, 'stat')
  def testGCSFileHandle_Info_notFound(self, mock_stat):
    mock_stat.side_effect = gcs.errors.NotFoundError()
    self.assertIsNone(file_util.GCSFileHandle('url').Info())

  @mock.patch.object(urllib2, 'urlopen')
  def testHttpFileHandle_Read(self, mock_urlopen):
    mock_file = mock.MagicMock()
    mock_file.read.return_value = 'hello\nworld'
    mock_urlopen.return_value = mock_file

    # fetches partial file content
    file_segment = file_util.HttpFileHandle('url').Read(offset=123, length=456)
    self.assertEqual(123, file_segment.offset)
    self.assertEqual(11, file_segment.length)
    self.assertListEqual(['hello\n', 'world'], file_segment.lines)

    # called with right arguments
    request = mock_urlopen.call_args[0][0]
    self.assertEqual('url', request.get_full_url())
    self.assertEqual('bytes=123-578', request.get_header('Range'))

  @mock.patch.object(urllib2, 'urlopen')
  def testHttpFileHandle_Read_notFound(self, mock_urlopen):
    mock_urlopen.side_effect = urllib2.HTTPError(None, 404, None, None, None)
    self.assertIsNone(file_util.HttpFileHandle('url').Read())

  @mock.patch.object(gcs, 'open')
  def testGCSFileHandle_Read(self, mock_open):
    mock_file = mock.MagicMock()
    mock_file.read.return_value = 'hello\nworld'
    mock_open.return_value = mock_file

    # fetches partial file content
    file_segment = file_util.GCSFileHandle('url').Read(offset=123, length=456)
    self.assertEqual(123, file_segment.offset)
    self.assertEqual(11, file_segment.length)
    self.assertListEqual(['hello\n', 'world'], file_segment.lines)

    # called with right arguments
    mock_file.read.assert_called_with(size=456)

  @mock.patch.object(gcs, 'open')
  def testGCSFileHandle_Read_notFound(self, mock_open):
    mock_open.side_effect = gcs.errors.NotFoundError()
    self.assertIsNone(file_util.GCSFileHandle('url').Read())

  def testGetWorkFileUrl(self):
    attempt = mock.MagicMock()
    attempt.attempt_id = 'attempt'

    self.assertEqual('file://root/tmp/attempt/',
                     file_util.GetWorkFileUrl(attempt))
    self.assertEqual('file://root/tmp/attempt/file',
                     file_util.GetWorkFileUrl(attempt, 'file'))

  def testGetOutputFileUrl_cloud(self):
    attempt = mock.MagicMock()
    attempt.command_id = 'command'
    attempt.attempt_id = 'attempt'

    test_run = mock.MagicMock()
    test_run.output_storage = file_util.FileStorage.GOOGLE_CLOUD_STORAGE
    test_run.output_path = '/base/'

    self.assertEqual('gs://base/command/attempt/',
                     file_util.GetOutputFileUrl(test_run, attempt))
    self.assertEqual('gs://base/command/attempt/file',
                     file_util.GetOutputFileUrl(test_run, attempt, 'file'))

  def testGetOutputFileUrl_file(self):
    attempt = mock.MagicMock()
    attempt.command_id = 'command'
    attempt.attempt_id = 'attempt'

    test_run = mock.MagicMock()
    test_run.output_storage = file_util.FileStorage.LOCAL_FILE_SYSTEM
    test_run.output_path = '/base/'

    self.assertEqual('file://root/base/command/attempt/',
                     file_util.GetOutputFileUrl(test_run, attempt))
    self.assertEqual('file://root/base/command/attempt/file',
                     file_util.GetOutputFileUrl(test_run, attempt, 'file'))

  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(file_util, 'GetOutputFileUrl')
  def testGetOutputFilenames(self, mock_get_output_url, mock_handle_factory):
    """Tests that an attempt's output filenames can retrieved."""
    test_run = mock.MagicMock()
    attempt = mock.MagicMock()
    summary_file = file(os.path.join(TEST_DATA_DIR, 'FILES'))
    mock_handle_factory.return_value = summary_file
    # List of filenames read from 'FILES' summary file
    filenames = file_util.GetOutputFilenames(test_run, attempt)
    self.assertEqual(['test_result.xml', 'tool-logs/stdout.txt'], filenames)
    mock_get_output_url.assert_called_once_with(test_run, attempt, 'FILES')

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testTailFile(self, mock_handler_factory):
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.return_value = file_util.FileInfo(1000, 'type', None)
    file_util.TailFile('url', 123)
    mock_handler.Read.assert_called_with(877)

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testTailFile_outOfBounds(self, mock_handler_factory):
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.return_value = file_util.FileInfo(1000, 'type', None)
    file_util.TailFile('url', 2000)
    mock_handler.Read.assert_called_with(0)

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testTailFile_notFound(self, mock_handler_factory):
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.return_value = None
    self.assertIsNone(file_util.TailFile('url', 123))
    mock_handler.Read.assert_not_called()

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadFile(self, mock_handler_factory):
    # configure content chunks
    bufsize = file_util.DOWNLOAD_BUFFER_SIZE
    size = bufsize * 2 + 1
    data = b'a' * size
    chunks = [
        data[0:bufsize],
        data[bufsize:bufsize * 2],
        data[bufsize * 2:]
    ]

    # mock file handle to return chunks when read
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.return_value = file_util.FileInfo(size, 'type', None)
    mock_handler.ReadBytes.side_effect = chunks

    result = list(file_util.DownloadFile('url'))

    # right bytes were read and progress was reported correctly
    mock_handler.ReadBytes.assert_has_calls([
        mock.call(i * bufsize, bufsize) for i in range(len(chunks))
    ])
    expected_result = [(chunks[i], min((i + 1) * bufsize, size), size)
                       for i in range(len(chunks))]
    self.assertEqual(expected_result, result)

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadFile_notFound(self, mock_handler_factory):
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.return_value = None

    with self.assertRaises(RuntimeError):
      list(file_util.DownloadFile('url'))

  def testGetTestSuiteInfo(self):
    # Test package contains a tradefed jar file with test suite information.
    test_file = os.path.join(TEST_DATA_DIR, 'test_package.zip')
    mock_file_handle = file(test_file)
    suite_info = file_util.GetTestSuiteInfo(mock_file_handle)
    self.assertEqual('1234567', suite_info.build_number)
    self.assertEqual('x86_64', suite_info.target_architecture)
    self.assertEqual('DTS', suite_info.name)
    self.assertEqual('Dummy Test Suite', suite_info.fullname)
    self.assertEqual('1.0', suite_info.version)

  def testGetTestSuiteInfo_empty(self):
    # Test package does not contain a tradefed jar file.
    test_file = os.path.join(TEST_DATA_DIR, 'test_package-empty.zip')
    mock_file_handle = file(test_file)
    self.assertIsNone(file_util.GetTestSuiteInfo(mock_file_handle))

  def testGetTestSuiteInfo_invalid(self):
    # Test package contains a tradefed jar file without test suite information.
    test_file = os.path.join(TEST_DATA_DIR, 'test_package-invalid.zip')
    mock_file_handle = file(test_file)
    self.assertIsNone(file_util.GetTestSuiteInfo(mock_file_handle))

  def testGetXtsTestResultSummary(self):
    test_file = os.path.join(TEST_DATA_DIR, 'test_result.xml')
    mock_file_handle = file(test_file)
    summary = file_util.GetXtsTestResultSummary(mock_file_handle)
    self.assertEqual(12, summary.passed)
    self.assertEqual(34, summary.failed)
    self.assertEqual(56, summary.modules_done)
    self.assertEqual(78, summary.modules_total)

  def testFileHandleMediaUpload(self):
    # Create mock file handle which delegates to a file-like object
    test_file = file(os.path.join(TEST_DATA_DIR, 'test_result.xml'))
    mock_file_handle = mock.MagicMock()
    mock_file_handle.Info.return_value = file_util.FileInfo(146, 'type', None)
    mock_file_handle.seek = test_file.seek
    mock_file_handle.tell = test_file.tell
    mock_file_handle.read = test_file.read

    # Test that media upload can read bytes and calculate size
    media_upload = file_util.FileHandleMediaUpload(mock_file_handle)
    self.assertEqual(146, media_upload.size())
    self.assertEqual('?xml', media_upload.getbytes(1, 4))
    self.assertEqual('type', media_upload.mimetype())
    self.assertFalse(media_upload.has_stream())


if __name__ == '__main__':
  absltest.main()
