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
import copy
import datetime
import json
import os
import shutil
import tempfile

from absl.testing import absltest
from absl.testing import parameterized
import mock
from tradefed_cluster.configs import lab_config

from multitest_transport.cli import lab_cli
from multitest_transport.cli import unittest_util


_PROJECT = 'aproject'
_SERVICE_ACCOUNT_EMAIL = 'as@gsa.com'
_KEY_CREATE_TIME = '2021-04-15T23:13:34Z'
_SERVICE_ACCOUNT_KEY_ID = 'akey_id'
_SERVICE_ACCOUNT_KEY = {
    'type': 'service_account',
    'project_id': _PROJECT,
    'private_key_id': _SERVICE_ACCOUNT_KEY_ID,
    'private_key': 'aprivate_key',
    'client_email': _SERVICE_ACCOUNT_EMAIL,
    'client_id': '1234',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'url'
}
_SERVICE_ACCOUNT_KEY_INFO = {
    'name': (f'projects/{_PROJECT}/serviceAccounts/'
             f'{_SERVICE_ACCOUNT_EMAIL}/keys/{_SERVICE_ACCOUNT_KEY_ID}'),
    'validAfterTime': _KEY_CREATE_TIME,
    'validBeforeTime': '2021-07-14T23:13:34Z',
    'keyAlgorithm': 'KEY_ALG_RSA_2048',
    'keyOrigin': 'GOOGLE_PROVIDED',
    'keyType': 'USER_MANAGED'
}


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
  @mock.patch.object(lab_cli.google_auth_util, 'CreateKey')
  @mock.patch.object(lab_cli.google_auth_util, 'UpdateSecret')
  @mock.patch.object(lab_cli.google_auth_util, 'GetServiceAccountKeyInfo')
  @mock.patch.object(lab_cli.google_auth_util, 'GetSecret')
  @mock.patch.object(lab_cli.google_auth_util, 'CanCreateKey')
  @mock.patch.object(lab_cli.google_auth_util, 'CanUpdateSecret')
  @mock.patch.object(atexit, 'register')
  def testGetServiceAccountKeyFilePath(
      self, mock_register, mock_can_update_secret, mock_can_create_key,
      mock_get_secret, mock_get_key_info, mock_update_secret,
      mock_create_key, mock_make_tmpfile):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/sa_key.json'
    mock_make_tmpfile.return_value = mock_tmpfile
    mock_get_secret.return_value = json.dumps(_SERVICE_ACCOUNT_KEY).encode()
    key_info = copy.deepcopy(_SERVICE_ACCOUNT_KEY_INFO)
    key_info['validAfterTime'] = (
        datetime.datetime.now(tz=datetime.timezone.utc)
        - datetime.timedelta(days=3)).isoformat()
    mock_get_key_info.return_value = key_info

    lab_cli._GetServiceAccountKeyFilePath('secret_project', 'sa_key')

    mock_get_key_info.assert_called_once_with(
        _SERVICE_ACCOUNT_EMAIL, _SERVICE_ACCOUNT_KEY_ID)
    self.assertFalse(mock_can_create_key.called)
    self.assertFalse(mock_can_update_secret.called)
    self.assertFalse(mock_create_key.called)
    self.assertFalse(mock_update_secret.called)
    mock_tmpfile.write.assert_called_once_with(
        json.dumps(_SERVICE_ACCOUNT_KEY).encode())
    mock_tmpfile.flush.assert_called_once_with()
    mock_get_secret.assert_called_once_with('secret_project', 'sa_key')
    mock_register.assert_called_once_with(mock_tmpfile.close)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(lab_cli.google_auth_util, 'CreateKey')
  @mock.patch.object(lab_cli.google_auth_util, 'UpdateSecret')
  @mock.patch.object(lab_cli.google_auth_util, 'GetServiceAccountKeyInfo')
  @mock.patch.object(lab_cli.google_auth_util, 'GetSecret')
  @mock.patch.object(lab_cli.google_auth_util, 'CanCreateKey')
  @mock.patch.object(lab_cli.google_auth_util, 'CanUpdateSecret')
  @mock.patch.object(atexit, 'register')
  def testGetServiceAccountKeyFilePath_renew(
      self, mock_register, mock_can_update_secret, mock_can_create_key,
      mock_get_secret, mock_get_key_info, mock_update_secret,
      mock_create_key, mock_make_tmpfile):
    mock_tmpfile = mock.MagicMock()
    mock_tmpfile.name = '/local/sa_key.json'
    mock_make_tmpfile.return_value = mock_tmpfile
    mock_get_secret.return_value = json.dumps(_SERVICE_ACCOUNT_KEY).encode()
    key_info = copy.deepcopy(_SERVICE_ACCOUNT_KEY_INFO)
    key_info['validAfterTime'] = (
        datetime.datetime.now(tz=datetime.timezone.utc)
        - datetime.timedelta(days=10)).isoformat()
    mock_get_key_info.return_value = key_info
    mock_can_create_key.return_value = True
    mock_can_update_secret.return_value = True
    new_key = copy.deepcopy(_SERVICE_ACCOUNT_KEY)
    new_key['private_key_id'] = 'new_key_id'
    mock_create_key.return_value = new_key
    mock_update_secret.return_value = 'new_version'

    lab_cli._GetServiceAccountKeyFilePath('secret_project', 'sa_key')

    mock_get_key_info.assert_called_once_with(
        _SERVICE_ACCOUNT_EMAIL, _SERVICE_ACCOUNT_KEY_ID)
    mock_can_update_secret.assert_called_once_with('secret_project', 'sa_key')
    mock_can_create_key.assert_called_once_with(_SERVICE_ACCOUNT_EMAIL)
    mock_create_key.assert_called_once_with(_SERVICE_ACCOUNT_EMAIL)
    mock_update_secret.assert_called_once_with(
        'secret_project', 'sa_key', json.dumps(new_key).encode())
    mock_tmpfile.write.assert_called_once_with(json.dumps(new_key).encode())
    mock_tmpfile.flush.assert_called_once_with()
    mock_get_secret.assert_called_once_with('secret_project', 'sa_key')
    mock_register.assert_called_once_with(mock_tmpfile.close)

  @mock.patch.object(lab_cli.google_auth_util, 'GetServiceAccountKeyInfo')
  def testShouldRenewServiceAccountKey_noNeedToRenew(self, mock_get_key_info):
    key_info = copy.deepcopy(_SERVICE_ACCOUNT_KEY_INFO)
    key_info['validAfterTime'] = (
        datetime.datetime.now(tz=datetime.timezone.utc)
        - datetime.timedelta(days=3)).isoformat()
    mock_get_key_info.return_value = key_info

    shoud_renew = lab_cli._ShouldRenewServiceAccountKey(_SERVICE_ACCOUNT_KEY)

    self.assertFalse(shoud_renew)
    mock_get_key_info.assert_called_once_with(
        _SERVICE_ACCOUNT_EMAIL, _SERVICE_ACCOUNT_KEY_ID)

  @mock.patch.object(lab_cli.google_auth_util, 'GetServiceAccountKeyInfo')
  def testShouldRenewServiceAccountKey_shouldRenew(self, mock_get_key_info):
    key_info = copy.deepcopy(_SERVICE_ACCOUNT_KEY_INFO)
    key_info['validAfterTime'] = (
        datetime.datetime.now(tz=datetime.timezone.utc)
        - datetime.timedelta(days=10)).isoformat()
    mock_get_key_info.return_value = key_info

    shoud_renew = lab_cli._ShouldRenewServiceAccountKey(_SERVICE_ACCOUNT_KEY)

    self.assertTrue(shoud_renew)
    mock_get_key_info.assert_called_once_with(
        _SERVICE_ACCOUNT_EMAIL, _SERVICE_ACCOUNT_KEY_ID)


if __name__ == '__main__':
  absltest.main()
