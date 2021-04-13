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
import atexit
import os
import shutil
import tempfile

from absl.testing import absltest
from absl.testing import parameterized
import mock
from tradefed_cluster.configs import lab_config

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
    self.assertEqual('version', args.action)

  def testCreateParser_withLoggingArgs(self):
    args = self.arg_parser.parse_args([
        '-v', '--log_file', 'file.log', 'version'])
    self.assertEqual('version', args.action)
    self.assertTrue(args.verbose)
    self.assertEqual('file.log', args.log_file)

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
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'))
    lab_cli._SetupMTTBinary(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile(
            os.path.join(tmp_folder, 'mtt_binary'),
            '/tmp/testuser/mtt'),
        mock.call.Run(['chmod', '+x', '/tmp/testuser/mtt'])])
    self.assertEqual('Setting up MTT Binary', host.execution_state)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testSetupHostConfig(self, mock_make_tmpfile):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    host = mock.MagicMock(context=mock.MagicMock(user='testuser'))
    lab_cli._SetupHostConfig(host)

    host.config.Save.assert_called_once_with('/local/config.yaml')
    host.context.CopyFile.assert_called_once_with(
        '/local/config.yaml', '/tmp/testuser/mtt_host_config.yaml')
    mock_tmpfile.close.assert_called_once_with()
    self.assertEqual('Setting up host config', host.execution_state)

  @parameterized.named_parameters(
      ('$ mtt_lab start --ask_sudo_password --sudo_user user',
       True, 'user', True),
      ('$ mtt_lab start --sudo_user user', False, 'user', True),
      ('$ mtt_lab start --ask_sudo_password', True, None, True),
      ('$ mtt_lab start', False, None, False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_config.HostConfig, 'Save')
  def testStart(
      self, ask_sudo_password, sudo_user, use_sudo, mock_save,
      mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        sudo_user=sudo_user,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'),
        config=lab_config.CreateHostConfig(
            service_account_json_key_path='/path/to/keyfile.json'))
    lab_cli.Start(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json',
                           '/tmp/testuser/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml',
                           '/tmp/testuser/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/testuser/mtt', '--no_check_update', 'start',
                       '/tmp/testuser/mtt_host_config.yaml'],
                      sudo=use_sudo)])
    self.assertEqual('/tmp/testuser/keyfile/key.json',
                     host.config.service_account_json_key_path)
    mock_save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()
    self.assertEqual('Running start', host.execution_state)

  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_config.HostConfig, 'Save')
  def testStart_noServiceAccountKey(
      self, mock_save, mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path=None,
        sudo_user=None,
        ask_sudo_password=False,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'),
        config=lab_config.CreateHostConfig(
            service_account_json_key_path=None))
    lab_cli.Start(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile(
            '/local/config.yaml', '/tmp/testuser/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/testuser/mtt', '--no_check_update', 'start',
                       '/tmp/testuser/mtt_host_config.yaml'], sudo=False)])
    mock_save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()

  @parameterized.named_parameters(
      ('$ mtt_lab update --ask_sudo_password --sudo_user user',
       True, 'user', True),
      ('$ mtt_lab update --sudo_user user', False, 'user', True),
      ('$ mtt_lab update --ask_sudo_password', True, None, True),
      ('$ mtt_lab update', False, None, False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_config.HostConfig, 'Save')
  def testUpdate(
      self, ask_sudo_password, sudo_user, use_sudo, mock_save,
      mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        sudo_user=sudo_user,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'),
        config=lab_config.CreateHostConfig(
            service_account_json_key_path='/path/to/keyfile.json'))
    lab_cli.Update(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json',
                           '/tmp/testuser/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml',
                           '/tmp/testuser/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/testuser/mtt', '--no_check_update', 'update',
                       '/tmp/testuser/mtt_host_config.yaml'],
                      sudo=use_sudo)])
    self.assertEqual('/tmp/testuser/keyfile/key.json',
                     host.config.service_account_json_key_path)
    mock_save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()
    self.assertEqual('Running update', host.execution_state)

  @parameterized.named_parameters(
      ('$ mtt_lab restart --ask_sudo_password --sudo_user user',
       True, 'user', True),
      ('$ mtt_lab restart --sudo_user user', False, 'user', True),
      ('$ mtt_lab restart --ask_sudo_password', True, None, True),
      ('$ mtt_lab restart', False, None, False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_config.HostConfig, 'Save')
  def testRestart(
      self, ask_sudo_password, sudo_user, use_sudo, mock_save,
      mock_make_tmpfile, mock_setup):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/config.yaml'
    mock_make_tmpfile.return_value = mock_tmpfile
    args = mock.MagicMock(
        service_account_json_key_path='/path/to/keyfile.json',
        ask_sudo_password=ask_sudo_password,
        sudo_user=sudo_user,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'),
        config=lab_config.CreateHostConfig(
            service_account_json_key_path='/path/to/keyfile.json'))
    lab_cli.Restart(args, host)

    host.context.assert_has_calls([
        mock.call.CopyFile('/path/to/keyfile.json',
                           '/tmp/testuser/keyfile/key.json'),
        mock.call.CopyFile('/local/config.yaml',
                           '/tmp/testuser/mtt_host_config.yaml'),
        mock.call.Run(['/tmp/testuser/mtt', '--no_check_update', 'restart',
                       '/tmp/testuser/mtt_host_config.yaml'],
                      sudo=use_sudo)])
    self.assertEqual('/tmp/testuser/keyfile/key.json',
                     host.config.service_account_json_key_path)
    mock_save.assert_called_once_with('/local/config.yaml')
    mock_setup.assert_called_once_with(args, host)
    mock_tmpfile.close.assert_called_once_with()
    self.assertEqual('Running restart', host.execution_state)

  @parameterized.named_parameters(
      ('$ mtt_lab stop --ask_sudo_password --sudo_user user',
       True, 'user', True),
      ('$ mtt_lab stop --sudo_user user', False, 'user', True),
      ('$ mtt_lab stop --ask_sudo_password', True, None, True),
      ('$ mtt_lab stop', False, None, False))
  @mock.patch.object(lab_cli, '_SetupMTTBinary')
  def testStop(self, ask_sudo_password, sudo_user, use_sudo, mock_setup):
    args = mock.MagicMock(
        ask_sudo_password=ask_sudo_password,
        sudo_user=sudo_user,
        verbose=False,
        very_verbose=False)
    host = mock.MagicMock(context=mock.MagicMock(user='testuser'))
    lab_cli.Stop(args, host)

    host.context.Run.assert_called_once_with(
        ['/tmp/testuser/mtt', '--no_check_update', 'stop'],
        sudo=use_sudo)
    mock_setup.assert_called_once_with(args, host)
    self.assertEqual('Running stop', host.execution_state)

  @parameterized.named_parameters(
      ('run_cmd_with_sudo_pwd_and_user', True, 'user', True),
      ('run_cmd_with_sudo_user', False, 'user', True),
      ('run_cmd_with_sudo_pwd', True, 'user', True),
      ('run_cmd_without_sudo', False, None, False))
  def testRunCmd(self, ask_sudo_password, sudo_user, use_sudo):
    args = mock.MagicMock(
        ask_sudo_password=ask_sudo_password,
        sudo_user=sudo_user,
        cmd='run a command line')
    host = mock.MagicMock()
    lab_cli.RunCmd(args, host)
    host.context.Run.assert_called_once_with(
        ['run', 'a', 'command', 'line'], sudo=use_sudo)
    self.assertEqual('Running cmd', host.execution_state)

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
      ('no_verbose', [], ['--no_check_update']),
      ('verbose', ['-v'], ['-v', '--no_check_update']),
      ('very_verbose', ['-vv'], ['-vv', '--no_check_update']),
      ('both', ['-v', '-vv'], ['-vv', '--no_check_update']))
  def testBuildBaseMTTCmd(self, verbose_flag, res_flag):
    parser = lab_cli.cli_util.CreateLoggingArgParser()
    args = parser.parse_args(verbose_flag)
    host = mock.MagicMock(context=mock.MagicMock(user='testuser'))
    cmd = lab_cli._BuildBaseMTTCmd(args, host)
    self.assertEqual(
        ['/tmp/testuser/mtt'] + res_flag,
        cmd)

  def testSetupServiceAccountKey(self):
    args = mock.MagicMock(service_account_json_key_path=None)
    host = mock.MagicMock(
        context=mock.MagicMock(user='testuser'),
        config=lab_config.CreateHostConfig(
            service_account_json_key_path='/path/to/keyfile.json'))
    lab_cli._SetupServiceAccountKey(args, host)

    host.context.CopyFile.assert_called_once_with(
        '/path/to/keyfile.json', '/tmp/testuser/keyfile/key.json')
    self.assertEqual('/tmp/testuser/keyfile/key.json',
                     host.config.service_account_json_key_path)
    self.assertEqual('Setting up service account key', host.execution_state)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_cli.google_auth_util, 'GetSecret')
  @mock.patch.object(atexit, 'register')
  def testGetServiceAccountKeyFromSecretManager(
      self, mock_register, mock_get_secret, mock_make_tmpfile):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/sa_key.json'
    mock_make_tmpfile.return_value = mock_tmpfile
    mock_get_secret.return_value = b'secret'

    lab_cli._GetServiceAccountKeyFromSecretManager('secret_project', 'sa_key')

    mock_tmpfile.write.assert_called_once_with(b'secret')
    mock_tmpfile.flush.assert_called_once_with()
    mock_get_secret.assert_called_once_with('secret_project', 'sa_key')
    mock_register.assert_called_once_with(mock_tmpfile.close)


if __name__ == '__main__':
  absltest.main()
