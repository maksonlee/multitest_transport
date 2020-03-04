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

"""Tests for cli_util."""
import os
import tempfile

from absl.testing import absltest
from absl.testing import parameterized
import mock
import six

from multitest_transport.cli import cli_util
from multitest_transport.cli import unittest_util


class CliUtilTest(absltest.TestCase):

  def testGetVersion(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      unittest_util.CreateZipFile(
          f.name, [unittest_util.File(
              filename='VERSION',
              content='[version]\nVERSION=aversion\nBUILD_ENVIRONMENT=test')])
      self.assertEqual(
          ('aversion', 'test'),
          cli_util.GetVersion(f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testGetVersion_notZip(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      f.write(b'afile')
      f.close()
      self.assertEqual(
          ('unknown', 'unknown'),
          cli_util.GetVersion(cli_path=f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testGetVersion_noVersion(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      unittest_util.CreateZipFile(
          f.name,
          [unittest_util.File(filename='INVALID_VERSION', content='aversion')])
      self.assertEqual(
          ('unknown', 'unknown'),
          cli_util.GetVersion(cli_path=f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testCreateLogger(self):
    try:
      f = tempfile.NamedTemporaryFile()
      arg_parser = cli_util. CreateLoggingArgParser()
      args = arg_parser.parse_args([
          '--logtostderr', '-v', '--log_file', f.name])
      logger = cli_util.CreateLogger(args)
      self.assertIsNotNone(logger)
    finally:
      f.close()

  @mock.patch.object(os, 'rename')
  @mock.patch.object(os, 'chmod')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateBackupFilePath')
  @mock.patch.object(cli_util.gcs_file_util, 'CalculateMd5Hash')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(cli_util.gcs_file_util, 'GetGCSBlob')
  @mock.patch.object(cli_util.google_auth_util, 'GetGCloudCredential')
  def testCheckAndUpdateTool(
      self, create_cred, mock_get_blob, mock_create_gcs_client, mock_md5hash,
      mock_create_backup_path, mock_chmod, mock_rename):
    cred = mock.MagicMock()
    create_cred.return_value = cred
    mock_client = mock.MagicMock()
    mock_create_gcs_client.return_value = mock_client
    mock_blob = mock.MagicMock(md5_hash='new_md5hash')
    mock_get_blob.return_value = mock_blob
    mock_create_backup_path.return_value = '/path/to/backup.par'
    mock_md5hash.return_value = six.ensure_text('md5hash')

    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', 'gs://bucket/remote/path/file.par')
    self.assertEqual('/local/path/file.par', new_path)

    self.assertTrue(create_cred.called)
    mock_create_gcs_client.assert_called_once_with('android-mtt', cred)
    mock_get_blob.assert_called_once_with(
        mock_client, 'gs://bucket/remote/path/file.par')
    mock_create_backup_path.assert_called_once_with('/local/path/file.par')
    mock_rename('/local/path/file.par', '/path/to/backup.par')
    mock_blob.download_to_filename.assert_called_once_with(
        '/local/path/file.par')
    mock_chmod.assert_called_once_with('/local/path/file.par', 0o770)

  @mock.patch.object(os, 'rename')
  @mock.patch.object(os, 'chmod')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateBackupFilePath')
  @mock.patch.object(cli_util.gcs_file_util, 'CalculateMd5Hash')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(cli_util.gcs_file_util, 'GetGCSBlob')
  @mock.patch.object(cli_util.google_auth_util, 'GetGCloudCredential')
  @mock.patch.object(cli_util, 'GetVersion')
  def testCheckAndUpdateTool_remoteNotSet(
      self, mock_get_version, create_cred, mock_get_blob,
      mock_create_gcs_client, mock_md5hash, mock_create_backup_path,
      mock_chmod, mock_rename):
    mock_get_version.return_value = ('aversion', 'prod')
    cred = mock.MagicMock()
    create_cred.return_value = cred
    mock_client = mock.MagicMock()
    mock_create_gcs_client.return_value = mock_client
    mock_blob = mock.MagicMock(md5_hash='new_md5hash')
    mock_get_blob.return_value = mock_blob
    mock_create_backup_path.return_value = '/path/to/mtt_backup'
    mock_md5hash.return_value = six.ensure_text('md5hash')

    new_path = cli_util.CheckAndUpdateTool('/local/path/mtt')
    self.assertEqual('/local/path/mtt', new_path)

    mock_get_version.assert_called_once_with('/local/path/mtt')
    self.assertTrue(create_cred.called)
    mock_create_gcs_client.assert_called_once_with('android-mtt', cred)
    mock_get_blob.assert_called_once_with(
        mock_client, 'gs://android-mtt.appspot.com/prod/mtt')
    mock_create_backup_path.assert_called_once_with('/local/path/mtt')
    mock_rename('/local/path/mtt', '/path/to/mtt_backup')
    mock_blob.download_to_filename.assert_called_once_with(
        '/local/path/mtt')
    mock_chmod.assert_called_once_with('/local/path/mtt', 0o770)

  @mock.patch.object(cli_util, 'GetVersion')
  def testCheckAndUpdateTool_devEnvironment(self, mock_get_version):
    mock_get_version.return_value = ('dev', 'dev')

    new_path = cli_util.CheckAndUpdateTool('/local/path/mtt')
    self.assertIsNone(new_path)

    mock_get_version.assert_called_once_with('/local/path/mtt')

  def testCheckAndUpdateTool_remoteNotGCS(self):
    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', '/bucket/remote/path/file.par')
    self.assertIsNone(new_path)

  def testCheckAndUpdateTool_remoteDifferentName(self):
    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', 'gs://bucket/remote/path/new_file.par')
    self.assertIsNone(new_path)

  @mock.patch.object(cli_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(cli_util.gcs_file_util, 'GetGCSBlob')
  @mock.patch.object(cli_util.google_auth_util, 'GetGCloudCredential')
  def testCheckAndUpdateTool_remoteNotExist(
      self, create_cred, mock_get_blob, mock_create_gcs_client):
    cred = mock.MagicMock()
    create_cred.return_value = cred
    mock_client = mock.MagicMock()
    mock_create_gcs_client.return_value = mock_client
    mock_get_blob.side_effect = cli_util.gcs_file_util.GCSError('No file.par')
    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', 'gs://bucket/remote/not/exist/path/file.par')
    self.assertIsNone(new_path)
    mock_get_blob.assert_called_once_with(
        mock_client, 'gs://bucket/remote/not/exist/path/file.par')

  @mock.patch.object(cli_util.gcs_file_util, 'CalculateMd5Hash')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(cli_util.gcs_file_util, 'GetGCSBlob')
  @mock.patch.object(cli_util.google_auth_util, 'GetGCloudCredential')
  def testCheckAndUpdateTool_sameMd5Hash(
      self, create_cred, mock_get_blob, mock_create_gcs_client, mock_md5hash):
    cred = mock.MagicMock()
    create_cred.return_value = cred
    mock_client = mock.MagicMock()
    mock_create_gcs_client.return_value = mock_client
    mock_blob = mock.MagicMock(md5_hash='md5hash')
    mock_get_blob.return_value = mock_blob
    mock_md5hash.return_value = six.ensure_text('md5hash')
    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', 'gs://bucket/remote/path/file.par')
    self.assertIsNone(new_path)
    mock_get_blob.assert_called_once_with(
        mock_client, 'gs://bucket/remote/path/file.par')

  @mock.patch.object(os, 'rename')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateBackupFilePath')
  @mock.patch.object(cli_util.gcs_file_util, 'CalculateMd5Hash')
  @mock.patch.object(cli_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(cli_util.gcs_file_util, 'GetGCSBlob')
  @mock.patch.object(cli_util.google_auth_util, 'GetGCloudCredential')
  def testCheckAndUpdateTool_noWriteAccess(
      self, create_cred, mock_get_blob, mock_create_gcs_client, mock_md5hash,
      mock_create_backup_path, mock_rename):
    cred = mock.MagicMock()
    create_cred.return_value = cred
    mock_client = mock.MagicMock()
    mock_create_gcs_client.return_value = mock_client
    mock_create_backup_path.return_value = '/path/to/backup.par'
    mock_blob = mock.MagicMock(md5_hash='new_md5hash')
    mock_get_blob.return_value = mock_blob
    mock_blob.download_to_filename.side_effect = [OSError()]
    mock_md5hash.return_value = six.ensure_text('md5hash')

    new_path = cli_util.CheckAndUpdateTool(
        '/local/path/file.par', 'gs://bucket/remote/path/file.par')
    self.assertIsNone(new_path)

    mock_get_blob.assert_called_once_with(
        mock_client, 'gs://bucket/remote/path/file.par')
    mock_rename('/local/path/file.par', '/path/to/backup.par')
    mock_blob.download_to_filename.assert_called_once_with(
        '/local/path/file.par')


class ArgumentParserTest(parameterized.TestCase):

  @parameterized.parameters(
      ([], False),
      (['--parallel'], True),
      (['--parallel', '8'], 8),
      )
  def testParseParallelExecuteOption(self, cmd_args, expected_val):
    arg_parser = cli_util.CreateMultiHostCommandArgParser()
    args = arg_parser.parse_args(cmd_args)
    self.assertEqual(expected_val, args.parallel)


if __name__ == '__main__':
  absltest.main()
