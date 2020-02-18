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
import json
import os
import shutil
import tempfile

from absl.testing import absltest

from multitest_transport.file_server import file_server

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


class FileServerTest(absltest.TestCase):
  """"Tests fetching file information and uploading/downloading files."""

  def setUp(self):
    super(FileServerTest, self).setUp()
    self.app = file_server.flask_app
    self.app.root_path = tempfile.mkdtemp()
    for test_file in os.scandir(TEST_DATA_DIR):
      shutil.copy(os.path.join(TEST_DATA_DIR, test_file), self.app.root_path)
    self.app.upload_cache = file_server.UploadCache(10, 60)

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

  def testUploadFile(self):
    """Tests that new files can be uploaded."""
    with self.app.test_client() as client:
      response = client.put('/file/upload.txt', data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/upload.txt').read())

  def testUploadFile_overwriteFile(self):
    """Tests that uploaded files can overwrite existing files."""
    with self.app.test_client() as client:
      response = client.put('/file/test.txt', data='test')
      self.assertEqual(201, response.status_code)
      self.assertEqual('test', open(self.app.root_path + '/test.txt').read())

  def testUploadFile_resumeUpload(self):
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

  def testUploadFile_restartUpload(self):
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

  def testUploadFile_invalidOffset(self):
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
