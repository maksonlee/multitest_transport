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

"""Android Test Station local file server tests."""
import io
import json
import os
import shutil
import tempfile

from absl.testing import absltest
import werkzeug

from multitest_transport.file_server import file_server

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


class FileServerTest(absltest.TestCase):
  """"Tests fetching file information and uploading/downloading files."""

  def setUp(self):
    super(FileServerTest, self).setUp()
    self.app = file_server.flask_app
    self.app.root_path = tempfile.mkdtemp()
    self.app.tmp_upload_dir = tempfile.mkdtemp()
    for test_file in os.scandir(TEST_DATA_DIR):
      shutil.copy(os.path.join(TEST_DATA_DIR, test_file), self.app.root_path)

  def tearDown(self):
    super(FileServerTest, self).tearDown()
    shutil.rmtree(self.app.root_path)

  def testDownloadFile(self):
    """Tests that files can be downloaded."""
    with self.app.test_client() as client:
      response = client.get('/file/test.txt')
      self.assertEqual(200, response.status_code)
      self.assertEqual(b'hello world', response.data)

  def testDownloadFile_withRange(self):
    """Tests that a subset of the file can be downloaded."""
    with self.app.test_client() as client:
      response = client.get('/file/test.txt', headers={'Range': 'bytes=3-7'})
      self.assertEqual(206, response.status_code)
      self.assertEqual(b'lo wo', response.data)
      self.assertEqual('bytes 3-7/11', str(response.content_range))

  def testDownloadFile_notFound(self):
    """Tests that file not found errors are handled."""
    with self.app.test_client() as client:
      response = client.get('/file/unknown.txt')
      self.assertEqual(404, response.status_code)
      data = json.loads(response.data)
      self.assertEqual('File \'unknown.txt\' not found', data['message'])

  def testDownloadFile_wrongType(self):
    """Tests that the path to download must be a file."""
    os.mkdir(self.app.root_path + '/foo')
    with self.app.test_client() as client:
      response = client.get('/file/foo')
      self.assertEqual(404, response.status_code)
      data = json.loads(response.data)
      self.assertEqual('File \'foo\' not found', data['message'])

  def testUploadFile_postMethod(self):
    """Tests that new files can be uploaded by post method."""
    with self.app.test_client() as client:
      file = werkzeug.datastructures.FileStorage(
          stream=io.BytesIO(b'test'),
          filename='/file/upload.txt',
          content_type='text/plain',
      )
      response = client.post(
          '/file/upload.txt',
          data=dict(file=file,),
          follow_redirects=True,
          content_type='multipart/form-data',
      )
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/upload.txt').read())

  def testUploadFile_multipleFiles(self):
    """Tests that uploading fails if request has multiple files."""
    with self.app.test_client() as client:
      file = werkzeug.datastructures.FileStorage(
          stream=io.BytesIO(b'test'),
          filename='/file/upload.txt',
          content_type='text/plain',
      )
      response = client.post(
          '/file/upload.txt',
          data=dict(file1=file, file2=file),
          follow_redirects=True,
          content_type='multipart/form-data',
      )
      self.assertEqual(400, response.status_code)

  def testUploadFile_emptyRequest(self):
    """Tests that uploading files fails when request doesn't have a file."""
    with self.app.test_client() as client:
      response = client.post(
          '/file/test.txt',
          follow_redirects=True,
          content_type='multipart/form-data',
      )
      self.assertEqual(400, response.status_code)

  def testUploadFile_overwriteFile(self):
    """Tests that uploaded files can overwrite existing files."""
    with self.app.test_client() as client:
      file = werkzeug.datastructures.FileStorage(
          stream=io.BytesIO(b'test'),
          filename='/file/test.txt',
          content_type='text/plain',
      )
      response = client.post(
          '/file/test.txt',
          data=dict(file=file,),
          follow_redirects=True,
          content_type='multipart/form-data',
      )
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/test.txt').read())

  def testUploadFile_longFilename(self):
    """Tests that a file can be uploaded to a long destination (b/172595968)."""
    with self.app.test_client() as client:
      filename = os.path.join('a' * 100, 'b' * 100, 'c' * 100, 'upload.txt')
      file = werkzeug.datastructures.FileStorage(
          stream=io.BytesIO(b'test'),
          filename='/file/' + filename,
          content_type='text/plain',
      )
      response = client.post(
          '/file/' + filename,
          data=dict(file=file,),
          follow_redirects=True,
          content_type='multipart/form-data',
      )
      response = client.put('/file/' + filename, data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/' + filename).read())

  def testUploadFileByChunks_putMethod(self):
    """Tests that new files can be uploaded by chunks by put method."""
    with self.app.test_client() as client:
      response = client.put('/file/upload.txt', data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/upload.txt').read())

  def testUploadFileByChunks_overwriteFile(self):
    """Tests that uploaded files by chunks can overwrite existing files."""
    with self.app.test_client() as client:
      response = client.put('/file/test.txt', data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/test.txt').read())

  def testUploadFileByChunks_resumeUpload(self):
    """Tests that files can be uploaded progressively."""
    with self.app.test_client() as client:
      # Upload half of a file's content
      response = client.put(
          '/file/upload.txt',
          data='hello ',
          headers={'Content-Range': 'bytes 0-5/11'})
      self.assertEqual(206, response.status_code)
      # File doesn't exist after incomplete upload
      self.assertFalse(os.path.isfile(self.app.root_path + '/upload.txt'))

      # Send remainder of file content
      response = client.put(
          '/file/upload.txt',
          data='world',
          headers={'Content-Range': 'bytes 6-10/11'})
      self.assertEqual(201, response.status_code)
      # File created with the concatenated content
      self.assertEqual('hello world',
                       open(self.app.root_path + '/upload.txt').read())

  def testUploadFileByChunks_restartUpload(self):
    """Tests that a resumable upload can be restarted."""
    with self.app.test_client() as client:
      # Upload half of a file's content
      response = client.put(
          '/file/upload.txt',
          data='hello ',
          headers={'Content-Range': 'bytes 0-5/11'})
      self.assertEqual(206, response.status_code)
      # File doesn't exist after incomplete upload
      self.assertFalse(os.path.isfile(self.app.root_path + '/upload.txt'))

      # Restart the upload from the first byte
      response = client.put(
          '/file/upload.txt',
          data='test',
          headers={'Content-Range': 'bytes 0-3/4'})
      self.assertEqual(201, response.status_code)
      # File created with the new content
      self.assertEqual('test', open(self.app.root_path + '/upload.txt').read())

  def testUploadFileByChunks_invalidOffset(self):
    """Tests that the starting offset is verified during a resumable upload."""
    with self.app.test_client() as client:
      # Upload half of a file's content
      response = client.put(
          '/file/upload.txt',
          data='hello ',
          headers={'Content-Range': 'bytes 0-5/11'})
      self.assertEqual(206, response.status_code)
      self.assertFalse(os.path.isfile(self.app.root_path + '/upload.txt'))

      # Send wrong starting offset which should return an error
      response = client.put(
          '/file/upload.txt',
          data='world',
          headers={'Content-Range': 'bytes 4-8/11'})
      self.assertEqual(400, response.status_code)
      data = json.loads(response.data)
      self.assertEqual('Invalid offset 4 (expected 6)', data['message'])

  def testUploadFileByChunks_longFilename(self):
    """Tests that a file can be uploaded to a long destination (b/172595968)."""
    with self.app.test_client() as client:
      filename = os.path.join('a' * 100, 'b' * 100, 'c' * 100, 'upload.txt')
      response = client.put('/file/' + filename, data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/' + filename).read())

  def testDeleteFile(self):
    """Tests that files can be deleted."""
    with self.app.test_client() as client:
      response = client.delete('/file/test.txt')
      self.assertEqual(204, response.status_code)
      self.assertFalse(os.path.isfile(self.app.root_path + '/test.txt'))

  def testDeleteFile_notFound(self):
    """Tests that missing files are ignored when deleting."""
    with self.app.test_client() as client:
      response = client.delete('/file/unknown.txt')
      self.assertEqual(204, response.status_code)

  def testListDirectory(self):
    """Tests that directory contents can be listed."""
    # Create two directories and an additional file
    os.mkdir(self.app.root_path + '/foo')
    os.mkdir(self.app.root_path + '/bar')
    os.mknod(self.app.root_path + '/empty.txt')

    with self.app.test_client() as client:
      response = client.get('/dir/')
      self.assertEqual(200, response.status_code)
      # Four nodes found in the right order (bar, foo, empty.txt, test.txt)
      data = json.loads(response.data)
      self.assertLen(data, 4)
      self.assertEqual('bar', data[0]['path'])
      self.assertEqual('DIRECTORY', data[0]['type'])
      self.assertEqual('foo', data[1]['path'])
      self.assertEqual('DIRECTORY', data[1]['type'])
      self.assertEqual('empty.txt', data[2]['path'])
      self.assertEqual('FILE', data[2]['type'])
      self.assertEqual('test.txt', data[3]['path'])
      self.assertEqual('FILE', data[3]['type'])

  def testListDirectory_notFound(self):
    """Tests that directory not found errors are handled."""
    with self.app.test_client() as client:
      response = client.get('/dir/unknown')
      self.assertEqual(404, response.status_code)
      data = json.loads(response.data)
      self.assertEqual('Directory \'unknown\' not found', data['message'])

  def testListDirectory_wrongType(self):
    """Tests that the path to list must be a directory."""
    with self.app.test_client() as client:
      response = client.get('/dir/test.txt')
      self.assertEqual(404, response.status_code)
      data = json.loads(response.data)
      self.assertEqual('Directory \'test.txt\' not found', data['message'])


if __name__ == '__main__':
  absltest.main()
