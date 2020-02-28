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

"""Tests for lab_cli."""
import os
import shutil
import tempfile

from absl.testing import absltest
from absl.testing import parameterized
import mock

from multitest_transport.cli import lab_cli
from multitest_transport.cli import unittest_util


class LabCliTest(parameterized.TestCase):

  def setUp(self):
    super(LabCliTest, self).setUp()
    self.arg_parser = lab_cli.CreateParser()
    self.tmp_root = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.tmp_root)
    super(LabCliTest, self).tearDown()

  def testCreateParser(self):
    args = self.arg_parser.parse_args(['version'])
    self.assertEqual(lab_cli.cli_util.PrintVersion, args.func)

  def testCreateParser_withLoggingArgs(self):
    args = self.arg_parser.parse_args([
        '-v', '--logtostderr', '--log_file', 'file.log', 'version'])
    self.assertEqual(lab_cli.cli_util.PrintVersion, args.func)
    self.assertTrue(args.verbose)
    self.assertEqual('file.log', args.log_file)
    self.assertTrue(args.logtostderr)

  @mock.patch.object(tempfile, 'mkdtemp')
  def testSetupMTTBinary(self, mock_create_temp):
    tmp_folder = os.path.join(self.tmp_root, 'mtt_lab_extracted')
    os.mkdir(tmp_folder)
    mock_create_temp.return_value = tmp_folder
    mtt_lab_path = os.path.join(self.tmp_root, 'mtt_lab')
    unittest_util.CreateZipFile(
        mtt_lab_path,
        [unittest_util.File(
            filename='mtt_binary', content='this is a mtt binary')])

    args = mock.MagicMock(cli_path=mtt_lab_path)
    host = mock.MagicMock()
    lab_cli._SetupMTTBinary(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile(
            os.path.join(tmp_folder, 'mtt_binary'),
            '/tmp/mtt'),
        mock.call.Run(['chmod', '+x', '/tmp/mtt'])])

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testSetupHostConfig(self, mock_make_tmpfile):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    host = mock.MagicMock()
    lab_cli._SetupHostConfig(host)

    host.config.Save.assert_called_once_with('/local/config.yaml')
    host.context.CopyFile.assert_called_once_with(
        '/local/config.yaml', '/tmp/mtt_host_config.yaml')
    mock_tmpfile.close.assert_called_once_with()

  @parameterized.named_parameters(
      ('$ sudo mtt start', True),
      ('$ mtt start', False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testStart(self, ask_sudo_password, mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock()
    host.config.service_account_json_key_path = '/path/to/keyfile.json'
    lab_cli.Start(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json', '/tmp/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml', '/tmp/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/mtt', 'start', '/tmp/mtt_host_config.yaml'],
                      sudo=ask_sudo_password)])
    self.assertEqual('/tmp/keyfile/key.json',
                     host.config.service_account_json_key_path)
    host.config.Save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()

  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testStart_noServiceAccountKey(self, mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path=None,
        ask_sudo_password=False,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock()
    host.config.service_account_json_key_path = None
    lab_cli.Start(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/local/config.yaml', '/tmp/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/mtt', 'start', '/tmp/mtt_host_config.yaml'],
                      sudo=False)])
    host.config.Save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()

  @parameterized.named_parameters(
      ('$ sudo mtt update', True),
      ('$ mtt update', False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testUpdate(self, ask_sudo_password, mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock()
    host.config.service_account_json_key_path = '/path/to/keyfile.json'
    lab_cli.Update(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json', '/tmp/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml', '/tmp/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/mtt', 'update', '/tmp/mtt_host_config.yaml'],
                      sudo=ask_sudo_password)])
    self.assertEqual('/tmp/keyfile/key.json',
                     host.config.service_account_json_key_path)
    host.config.Save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()

  @parameterized.named_parameters(
      ('$ sudo mtt restart', True),
      ('$ mtt restart', False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testRestart(self, ask_sudo_password, mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock()
    host.config.service_account_json_key_path = '/path/to/keyfile.json'
    lab_cli.Restart(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json', '/tmp/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml', '/tmp/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/mtt', 'restart', '/tmp/mtt_host_config.yaml'],
                      sudo=ask_sudo_password)])
    self.assertEqual('/tmp/keyfile/key.json',
                     host.config.service_account_json_key_path)
    host.config.Save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()

  @parameterized.named_parameters(
      ('$ sudo mtt stop', True),
      ('$ mtt stop', False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  def testStop(self, ask_sudo_password, mock_setup):
    args = mock.MagicMock(
        ask_sudo_password=ask_sudo_password,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock()
    lab_cli.Stop(args, host)

    host.context.Run.assert_called_once_with(
        ['/tmp/mtt', 'stop'], sudo=ask_sudo_password)
    mock_setup.assert_called_once_with(args, host)

  @parameterized.named_parameters(
      ('run_cmd_with_sudo', True),
      ('run_cmd_without_sudo', False))
  def testRunCmd(self, ask_sudo_password):
    args = mock.MagicMock(
        ask_sudo_password=ask_sudo_password,
        cmd='run a command line')
    host = mock.MagicMock()
    lab_cli.RunCmd(args, host)
    host.context.Run.assert_called_once_with(
        ['run', 'a', 'command', 'line'], sudo=ask_sudo_password)

  def testCreateLabCommandArgParser(self):
    parser = lab_cli._CreateLabCommandArgParser()
    args = parser.parse_args(['lab_config.yaml'])
    self.assertEqual('lab_config.yaml', args.lab_config_path)
    self.assertEmpty(args.hosts_or_clusters)

  def testCreateLabCommandArgParser_withHostOrCluster(self):
    parser = lab_cli._CreateLabCommandArgParser()
    args = parser.parse_args(['lab_config.yaml', 'host1', 'cluster1'])
    self.assertEqual('lab_config.yaml', args.lab_config_path)
    self.assertEqual(['host1', 'cluster1'], args.hosts_or_clusters)

  @parameterized.named_parameters(
      ('no_verbose', [], []),
      ('verbose', ['-v'], ['-v']),
      ('very_verbose', ['-vv'], ['-vv']),
      ('both', ['-v', '-vv'], ['-vv']))
  def testBuildBaseMTTCmd(self, verbose_flag, res_flag):
    parser = lab_cli.cli_util.CreateLoggingArgParser()
    args = parser.parse_args(verbose_flag)
    cmd = lab_cli._BuildBaseMTTCmd(args)
    self.assertEqual(
        [lab_cli._REMOTE_MTT_BINARY] + res_flag,
        cmd)


if __name__ == '__main__':
  absltest.main()
