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

"""Tests for gcs_file_util."""
import datetime
import os
import tempfile
from unittest import mock

from absl.testing import absltest
from google.cloud import exceptions as cloud_exceptions
from google.cloud import storage  
import six
from tradefed_cluster.configs import lab_config


from multitest_transport.cli import gcs_file_util


class GCSFileUtilTest(absltest.TestCase):
  """Unit test for gcs_file_util."""

  def testGetGCSBlob(self):
    mock_blob = mock.MagicMock()
    mock_bucket = mock.MagicMock()
    mock_client = mock.MagicMock()
    mock_client.get_bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = mock_blob
    blob = gcs_file_util.GetGCSBlob(mock_client, 'gs://bucket/path/to/file')
    self.assertEqual(mock_blob, blob)
    mock_bucket.get_blob.assert_called_once_with('path/to/file')
    mock_client.get_bucket.assert_called_once_with('bucket')

  def testGetGCSBlob_noBucket(self):
    mock_client = mock.MagicMock()
    mock_client.get_bucket.side_effect = cloud_exceptions.NotFound('')
    with self.assertRaisesRegex(
        gcs_file_util.GCSError, r'bucket doesn\'t exist.'):
      gcs_file_util.GetGCSBlob(
          mock_client, 'gs://bucket/path/to/file')
    mock_client.get_bucket.assert_called_once_with('bucket')

  def testGetGCSBlob_noBlob(self):
    mock_bucket = mock.MagicMock()
    mock_client = mock.MagicMock()
    mock_client.get_bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = None

    with self.assertRaisesRegex(
        gcs_file_util.GCSError, r'gs://bucket/path/to/file doesn\'t exist.'):
      gcs_file_util.GetGCSBlob(
          mock_client, 'gs://bucket/path/to/file')
    mock_bucket.get_blob.assert_called_once_with('path/to/file')
    mock_client.get_bucket.assert_called_once_with('bucket')

  def testParseGCSPath(self):
    bucket_name, path = gcs_file_util.ParseGCSPath(
        'gs://bucket/file/to/path.ext')
    self.assertEqual('bucket', bucket_name)
    self.assertEqual('file/to/path.ext', path)

  def testGCSFileEnumerator(self):
    mock_client = mock.MagicMock()
    mock_blob1 = mock.MagicMock()
    mock_blob1.name = 'configs/config1.yaml'
    mock_blob1.download_as_string.return_value = b'config1'
    mock_blob2 = mock.MagicMock()
    mock_blob2.name = 'configs/folder'
    mock_blob3 = mock.MagicMock()
    mock_blob3.name = 'configs/config2.yaml'
    mock_blob3.download_as_string.return_value = b'config2'
    mock_bucket = mock.MagicMock()
    mock_bucket.list_blobs.return_value = iter(
        [mock_blob1, mock_blob2, mock_blob3])
    mock_client.get_bucket.return_value = mock_bucket

    g = gcs_file_util.GCSFileEnumerator(
        mock_client, 'gs://bucket/path/to/folder', lab_config.IsYaml)
    objs = list(g)

    mock_client.get_bucket.assert_called_once_with('bucket')
    mock_bucket.list_blobs.assert_called_once_with(prefix='path/to/folder')
    self.assertEqual('config1', objs[0].read())
    self.assertEqual('config2', objs[1].read())

  @mock.patch.object(datetime, 'datetime')
  def testCreateBackupFilePath(self, mock_datetime):
    mock_datetime.now().strftime.return_value = '2019-02-10-10-10-10'
    backup_path = gcs_file_util.CreateBackupFilePath('/path/to/file.par')
    self.assertEqual(
        '/path/to/file-2019-02-10-10-10-10.par',
        backup_path)

  def testCalculateMd5Hash(self):
    try:
      f = tempfile.NamedTemporaryFile()
      f.write(b'test')
      md5hash = gcs_file_util.CalculateMd5Hash(f.name)
      self.assertEqual(six.ensure_text('1B2M2Y8AsgTpgAmY7PhCfg=='), md5hash)
    finally:
      # Close will delete the file.
      f.close()
      self.assertFalse(os.path.exists(f.name))


if __name__ == '__main__':
  absltest.main()
