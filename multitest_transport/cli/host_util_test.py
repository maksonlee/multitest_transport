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

"""Tests for google3.wireless.android.test_tools.multitest_transport.cli.host_util."""
import collections
import getpass
import socket

from absl.testing import absltest
from absl.testing import parameterized
import mock

from multitest_transport.cli import host_util
from multitest_transport.cli import ssh_util


class HostUtilTest(parameterized.TestCase):
  """Unit tests for host util."""

  def setUp(self):
    super(HostUtilTest, self).setUp()
    self.mock_context = mock.MagicMock()
    self.context_patcher = mock.patch(
        '__main__.host_util.command_util.CommandContext',
        return_value=self.mock_context)
    self.mock_create_context = self.context_patcher.start()
    self.host_config1 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster1', hostname='host1',
        host_login_name='user1', docker_image='image1')
    self.ssh_config1 = ssh_util.SshConfig(user='user1', hostname='host1')
    self.host_config2 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster2', hostname='host2',
        host_login_name='user1', docker_image='image1')
    self.ssh_config2 = ssh_util.SshConfig(user='user1', hostname='host2')
    self.host_config3 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster3', hostname='host3', host_login_name='user1')
    self.ssh_config3 = ssh_util.SshConfig(user='user1', hostname='host3')
    self.mock_lab_config_pool = mock.MagicMock()
    self.mock_func_calls = collections.OrderedDict()
    self.mock_func_exceptions = {}
    self.default_args = {
        'lab_config_path': 'lab_config.yaml',
        'hosts_or_clusters': [],
        'parallel': False,
        'host_func': self._MockFunc,
        'ssh_key': None,
        'ask_login_password': False,
        'ask_sudo_password': False,
        'sudo_user': None,
        'use_native_ssh': True,
        'no_use_native_ssh': False,
        'ssh_arg': None,
    }

  def tearDown(self):
    self.context_patcher.stop()
    super(HostUtilTest, self).tearDown()

  def _MockFunc(self, args, host):
    # Instead of using mock package, this _MockFunc simulate the
    # real host_func behavior.
    host.context.Run('a_command')
    self.mock_func_calls[host.name] = (args, host.config)
    if host.name in self.mock_func_exceptions:
      raise self.mock_func_exceptions[host.name]

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  def testExecute(self, mock_build_lab_config_pool):
    """Test execute."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args_dict = self.default_args.copy()
    args_dict.update(
        service_account_json_key_path='path/to/key',
    )
    args = mock.MagicMock(**args_dict)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1',
                  ssh_config=self.ssh_config1, sudo_ssh_config=None),
        mock.call('host2', 'user1',
                  ssh_config=self.ssh_config2, sudo_ssh_config=None)])
    self.assertSameElements(['host1', 'host2'], self.mock_func_calls.keys())
    self.assertEqual(args, self.mock_func_calls['host1'][0])
    self.assertEqual(
        self.host_config1.SetServiceAccountJsonKeyPath('path/to/key'),
        self.mock_func_calls['host1'][1])
    self.assertEqual(args, self.mock_func_calls['host2'][0])
    self.assertEqual(
        self.host_config2.SetServiceAccountJsonKeyPath('path/to/key'),
        self.mock_func_calls['host2'][1])

  @mock.patch.object(getpass, 'getpass')
  @mock.patch.object(host_util, 'BuildLabConfigPool')
  def testExecute_askPass(self, mock_build_lab_config_pool, mock_getpass):
    """Test execute on multiple hosts with password."""
    mock_getpass.side_effect = ['login_pswd', 'sudo_pswd']
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args_dict = self.default_args.copy()
    args_dict.update(
        ask_login_password=True,
        ask_sudo_password=True,
        sudo_user='sudo_user',
        service_account_json_key_path='path/to/key',
    )
    args = mock.MagicMock(**args_dict)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host1',
                      password='login_pswd'),
                  sudo_ssh_config=ssh_util.SshConfig(
                      user='sudo_user', hostname='host1',
                      password='sudo_pswd')),
        mock.call('host2', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host2',
                      password='login_pswd'),
                  sudo_ssh_config=ssh_util.SshConfig(
                      user='sudo_user', hostname='host2',
                      password='sudo_pswd'))])
    self.assertSameElements(['host1', 'host2'], self.mock_func_calls.keys())

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  def testExecute_nativeSsh(self, mock_build_lab_config_pool):
    """Test execute."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args_dict = self.default_args.copy()
    args_dict.update(
        use_native_ssh=True,
        ssh_arg='-o op1=v1 -o op2=v2',
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host1',
                      ssh_args='-o op1=v1 -o op2=v2',
                      use_native_ssh=True),
                  sudo_ssh_config=None),
        mock.call('host2', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host2',
                      ssh_args='-o op1=v1 -o op2=v2',
                      use_native_ssh=True),
                  sudo_ssh_config=None)])
    self.assertSameElements(['host1', 'host2'], self.mock_func_calls.keys())

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  def testExecute_nativeSsh_sshArgInConfig(self, mock_build_lab_config_pool):
    """Test execute."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    host_config = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster1', hostname='host1',
        host_login_name='user1',
        ssh_arg='-o op1=v1 -o op2=v2')
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[host_config]]
    args_dict = self.default_args.copy()
    args_dict.update(
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host1',
                      ssh_args='-o op1=v1 -o op2=v2',
                      use_native_ssh=True),
                  sudo_ssh_config=None)])
    self.assertSameElements(['host1'], self.mock_func_calls.keys())

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  def testExecute_noNativeSsh(self, mock_build_lab_config_pool):
    """Test execute."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args_dict = self.default_args.copy()
    args_dict.update(
        no_use_native_ssh=True,
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host1',
                      use_native_ssh=False),
                  sudo_ssh_config=None),
        mock.call('host2', 'user1',
                  ssh_config=ssh_util.SshConfig(
                      user='user1', hostname='host2',
                      use_native_ssh=False),
                  sudo_ssh_config=None)])
    self.assertSameElements(['host1', 'host2'], self.mock_func_calls.keys())

  def testSequentialExecute_exitOnError(self):
    """Test _SequentialExecute multiple hosts sequentially and failed."""
    hosts = [
        host_util.Host(host_config, context=self.mock_context)
        for host_config in
        [self.host_config1, self.host_config2]]
    for host in hosts:
      host._control_server_client = mock.MagicMock()
    self.mock_func_exceptions['host1'] = Exception()
    args_dict = self.default_args.copy()
    args_dict.update(
        parallel=False,
        exit_on_error=True,
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    with self.assertRaises(Exception):
      host_util._SequentialExecute(
          host_util._WrapFuncForSetHost(self._MockFunc),
          args,
          hosts,
          exit_on_error=True)

    (hosts[0].control_server_client.SubmitHostUpdateStateChangedEvent
     .assert_called_with(hosts[0].config.hostname,
                         host_util.HostUpdateState.ERRORED,
                         target_image='image1'))

    self.assertSameElements(['host1'], self.mock_func_calls.keys())
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.UNKNOWN,
                     hosts[1].execution_state)

  def testParallelExecute(self):
    """Test ParallelExecute on multiple hosts parallel."""
    hosts = [
        host_util.Host(host_config, context=self.mock_context)
        for host_config in
        [self.host_config1, self.host_config2, self.host_config3]]
    for host in hosts:
      host._control_server_client = mock.MagicMock()
    args_dict = self.default_args.copy()
    args_dict.update(
        parallel=2,
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    host_util._ParallelExecute(
        host_util._WrapFuncForSetHost(self._MockFunc),
        args,
        hosts)

    # We don't know the order of the call since it's parallel.
    self.assertSameElements(
        ['host1', 'host2', 'host3'], self.mock_func_calls.keys())
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     hosts[1].execution_state)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     hosts[2].execution_state)

  def testParallelExecute_partialFailed(self):
    """Test ParallelExecute on multiple hosts parallel with some host failed."""
    hosts = [
        host_util.Host(host_config, context=self.mock_context)
        for host_config in
        [self.host_config1, self.host_config2]]
    for host in hosts:
      host._control_server_client = mock.MagicMock()
    excecution_exception = Exception('some error message.')
    self.mock_func_exceptions['host2'] = excecution_exception
    args_dict = self.default_args.copy()
    args_dict.update(
        parallel=True,
        service_account_json_key_path='path/to/key',
        )
    args = mock.MagicMock(**args_dict)

    host_util._ParallelExecute(
        host_util._WrapFuncForSetHost(self._MockFunc),
        args,
        hosts)

    # We don't know the order of the call since it's parallel.
    self.assertSameElements(['host1', 'host2'], self.mock_func_calls.keys())
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     hosts[1].execution_state)
    (hosts[1].control_server_client.SubmitHostUpdateStateChangedEvent
     .assert_called_with(hosts[1].config.hostname,
                         host_util.HostUpdateState.ERRORED,
                         display_message=str(excecution_exception),
                         target_image='image1'))

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  @mock.patch.object(socket, 'gethostname')
  def testCreateHost(
      self, mock_gethostname, mock_build_lab_config_pool):
    mock_gethostname.return_value = 'host1'
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.return_value = self.host_config1
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml', service_account_json_key_path=None)
    host = host_util.CreateHost(args)
    self.assertEqual(self.host_config1, host.config)
    self.assertIsNotNone(host.context)

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  @mock.patch.object(socket, 'gethostname')
  def testCreateHost_WithOverrideValue(
      self, mock_gethostname, mock_build_lab_config_pool):
    json_key_path = '/path/to/key.json'
    mock_gethostname.return_value = 'host1'
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.return_value = self.host_config1
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        service_account_json_key_path=json_key_path)
    host = host_util.CreateHost(args)
    self.assertEqual(json_key_path, host.config.service_account_json_key_path)
    self.assertIsNotNone(host.context)

  @mock.patch.object(socket, 'getfqdn')
  def testCreateHost_withoutLabConfig(self, mock_getfqdn):
    mock_getfqdn.return_value = 'host1.google.com'
    args = mock.MagicMock(
        lab_config_path=None, service_account_json_key_path=None)
    host = host_util.CreateHost(args)
    self.assertEqual('host1.google.com', host.config.hostname)
    self.assertEqual(host_util._DEFAULT_MTT_IMAGE, host.config.docker_image)
    self.assertIsNotNone(host.context)

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  @mock.patch.object(socket, 'gethostname')
  def testGetHostConfig(
      self, mock_gethostname, mock_build_lab_config_pool):
    mock_gethostname.return_value = 'host1'
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.return_value = self.host_config1
    host_config = host_util._GetHostConfig(
        lab_config_path='lab_config.yaml')
    self.assertEqual(self.host_config1, host_config)
    self.mock_lab_config_pool.GetHostConfig.assert_called_once_with('host1')

  @mock.patch.object(host_util, 'BuildLabConfigPool')
  @mock.patch.object(socket, 'getfqdn')
  @mock.patch.object(socket, 'gethostname')
  def testGetHostConfig_noHostConfig(
      self, mock_gethostname, mock_getfqdn, mock_build_lab_config_pool):
    mock_gethostname.return_value = 'host1'
    mock_getfqdn.return_value = 'host1.google.com'
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.side_effect = [
        None, None]

    with self.assertRaises(host_util.ConfigurationError):
      host_util._GetHostConfig(lab_config_path='lab_config.yaml')
    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfig('host1'),
        mock.call.GetHostConfig('host1.google.com')])

  def testGetHostConfigs(self):
    """Test _GetHostConfigs."""
    self.mock_lab_config_pool.GetHostConfig.side_effect = [
        self.host_config1, None]
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config2]]

    host_configs = host_util._GetHostConfigs(
        self.mock_lab_config_pool, ['host1', 'cluster2'])

    self.assertLen(host_configs, 2)
    self.assertEqual('host1', host_configs[0].hostname)
    self.assertEqual('host2', host_configs[1].hostname)

  def testGetHostConfigs_withDuplicatedHostOrCluster(self):
    """Test _GetHostConfigs with hosts_or_clusters and there is duplicate."""
    self.mock_lab_config_pool.GetHostConfig.side_effect = [
        self.host_config1, None]
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]

    host_configs = host_util._GetHostConfigs(
        self.mock_lab_config_pool, ['host1', 'cluster1'])

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfig('host1'),
        mock.call.GetHostConfig('cluster1'),
        mock.call.GetHostConfigs('cluster1')])
    self.assertLen(host_configs, 2)
    self.assertEqual('host1', host_configs[0].hostname)
    self.assertEqual('host2', host_configs[1].hostname)

  @mock.patch.object(host_util.lab_config, 'LocalFileEnumerator')
  @mock.patch.object(host_util.lab_config, 'LabConfigPool')
  def testBuildLabConfigPool(
      self, mock_create_lab_config_pool, mock_local_file_enumerator):
    mock_create_lab_config_pool.return_value = self.mock_lab_config_pool

    host_util.BuildLabConfigPool(lab_config_path='lab_config.yaml')

    mock_local_file_enumerator.assert_called_once_with(
        'lab_config.yaml', mock.ANY)
    self.mock_lab_config_pool.LoadConfigs.assert_called_once_with()

  def testBuildLabConfigPool_noLabConfig(self):
    lab_config_pool = host_util.BuildLabConfigPool(lab_config_path=None)
    self.assertEmpty(lab_config_pool.GetHostConfigs())

  @mock.patch.object(host_util.google_auth_util, 'GetGCloudCredential')
  @mock.patch.object(host_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(host_util.gcs_file_util, 'GCSFileEnumerator')
  @mock.patch.object(host_util.lab_config, 'LabConfigPool')
  def testBuildLabConfigPool_withGCS(
      self, mock_create_lab_config_pool, mock_gcs_file_enumerator,
      mock_create_gcs_client, mock_get_cred):
    mock_create_lab_config_pool.return_value = self.mock_lab_config_pool

    host_util.BuildLabConfigPool(lab_config_path='gs://bucket/lab_config.yaml')

    mock_gcs_file_enumerator.assert_called_once_with(
        mock.ANY, 'gs://bucket/lab_config.yaml', mock.ANY)
    self.mock_lab_config_pool.LoadConfigs.assert_called_once_with()
    self.assertTrue(mock_create_gcs_client.called)
    self.assertTrue(mock_get_cred.called)

  @mock.patch.object(host_util.lab_config, 'UnifiedLabConfigPool')
  def testBuildLabConfigPool_unifiedLabConfigPool(
      self, mock_create_lab_config_pool):
    mock_create_lab_config_pool.return_value = self.mock_lab_config_pool

    host_util.BuildLabConfigPool(lab_config_path='path/to/hosts')

    self.mock_lab_config_pool.LoadConfigs.assert_called_once_with()

  def testHostContext(self):
    """Test Host.context."""
    host = host_util.Host(self.host_config1, self.ssh_config1)
    self.assertIsNotNone(host.context)
    self.mock_create_context.assert_called_once_with(
        self.host_config1.hostname, self.host_config1.host_login_name,
        ssh_config=self.ssh_config1, sudo_ssh_config=None)

  def testHostContext_withSSHInfo(self):
    ssh_config = ssh_util.SshConfig(
        user='user1', hostname='host1', password='loginpwd',
        ssh_key='/ssh_key')
    sudo_ssh_config = ssh_util.SshConfig(
        user='sudo_user1', hostname='host1', password='sudopwd',
        ssh_key='/ssh_key')
    host = host_util.Host(
        self.host_config1,
        ssh_config=ssh_config,
        sudo_ssh_config=sudo_ssh_config)

    self.assertIsNotNone(host.context)
    self.mock_create_context.assert_called_once_with(
        'host1', 'user1',
        ssh_config=ssh_config,
        sudo_ssh_config=sudo_ssh_config)

  def testHostContext_unknownException(self):
    """Test Host.context with exception."""
    self.mock_create_context.side_effect = Exception('Connection timeout.')

    context = None
    with self.assertRaises(Exception):
      context = host_util.Host(self.host_config1, self.ssh_config1).context
    self.assertIsNone(context)
    self.mock_create_context.assert_called_once_with(
        'host1', 'user1', ssh_config=self.ssh_config1, sudo_ssh_config=None)

  def testWrapFuncForSetHost(self):
    host = host_util.Host(self.host_config1, self.ssh_config1)
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    args = mock.MagicMock(**self.default_args)
    f = host_util._WrapFuncForSetHost(self._MockFunc)

    f(args, host)

    self.assertSameElements(['host1'], self.mock_func_calls.keys())
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     host.execution_state)
    host.StartExecutionTimer.assert_called_once()
    host.StopExecutionTimer.assert_called_once()

  def testWrapFuncForSetHost_error(self):
    host = host_util.Host(self.host_config1, self.ssh_config1)
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    args = mock.MagicMock(**self.default_args)
    f = host_util._WrapFuncForSetHost(self._MockFunc)
    e = Exception('Fail to run command.')
    self.mock_func_exceptions['host1'] = e
    with self.assertRaises(Exception):
      f(args, host)

    self.assertSameElements(['host1'], self.mock_func_calls.keys())
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     host.execution_state)
    self.assertEqual(e, host.error)
    host.StartExecutionTimer.assert_called_once()
    host.StopExecutionTimer.assert_called_once()

  def testWrapFuncForSetHost_skip(self):
    host = host_util.Host(self.host_config1, self.ssh_config1)
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    host.execution_state = host_util.HostExecutionState.COMPLETED
    args = mock.MagicMock(**self.default_args)
    f = host_util._WrapFuncForSetHost(self._MockFunc)

    f(args, host)

    self.assertEmpty(self.mock_func_calls)
    host.StartExecutionTimer.assert_not_called()
    host.StopExecutionTimer.assert_not_called()

  @parameterized.parameters(
      (None, None, 10, 'Time elapsed: 0 min 0 s(not started)'),
      (1, None, 10, 'Time elapsed: 0 min 9 s(running)'),
      (1, 602, 608, 'Time elapsed: 10 min 1 s(ended)'),
      (1.3, 602.5, 608.7, 'Time elapsed: 10 min 1 s(ended)'),
      )
  @mock.patch('__main__.host_util.time')
  def testExecutionTimeElapsed(
      self, start_time, end_time, current_time, expected_expression, mock_time):
    mock_time.time.return_value = current_time
    host = host_util.Host(host_util.lab_config.CreateHostConfig())
    host._execution_start_time = start_time
    host._execution_end_time = end_time
    self.assertEqual(expected_expression, host.execution_time_elapsed)

  @parameterized.parameters(
      (False, 1),
      (8, 8),
      (-99, 1),
      )
  def testGetMaxWorker(self, parallel, expected_max_worker):
    args = mock.MagicMock(parallel=parallel)
    hosts = [host_util.Host(host_util.lab_config.CreateHostConfig())
             for _ in range(3)]
    self.assertEqual(expected_max_worker, host_util._GetMaxWorker(args, hosts))

  def testGetMaxWorker_ParallelAllHosts(self):
    args = mock.MagicMock(parallel=True)
    hosts = [host_util.Host(host_util.lab_config.CreateHostConfig())
             for _ in range(3)]
    self.assertEqual(3, host_util._GetMaxWorker(args, hosts))


class ExecutionStatePrinterTest(absltest.TestCase):
  """Unit test for ExecutionStatePrinter."""

  def setUp(self):
    super(ExecutionStatePrinterTest, self).setUp()
    self.logger_patcher = mock.patch('__main__.host_util.logger')
    self.mock_logger = self.logger_patcher.start()
    self.now_patcher = mock.patch('__main__.host_util._GetCurrentTime')
    self.mock_now = self.now_patcher.start()
    self.mock_now.return_value = 1
    self.hosts = []
    for i in range(5):
      self.hosts.append(
          host_util.Host(
              host_util.lab_config.CreateHostConfig(
                  hostname='host' + str(i), host_login_name='auser')))
    self.mock_now.return_value = 11
    for i in range(5):
      self.hosts[i].StartExecutionTimer()
      self.hosts[i].execution_state = 'Step1'
    self.mock_now.return_value = 21
    self.hosts[0].execution_state = 'Step2'
    self.hosts[2].execution_state = 'Step2'
    self.mock_now.return_value = 31
    self.hosts[0].execution_state = host_util.HostExecutionState.COMPLETED
    self.hosts[4].execution_state = host_util.HostExecutionState.ERROR
    self.printer = host_util.ExecutionStatePrinter(self.hosts)

  def tearDown(self):
    super(ExecutionStatePrinterTest, self).tearDown()
    self.now_patcher.stop()
    self.logger_patcher.stop()

  def testPrintState(self):
    self.printer.PrintState()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed.', 1, 5),
        mock.call.error('%r of %r hosts errored: %s', 1, 5, 'host4'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 2, 5, 'Step1', 'host1 host3'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 1, 5, 'Step2', 'host2')])
    self.assertEqual(31, self.printer._previous_print_time)
    self.assertEqual(
        [(host_util.HostExecutionState.COMPLETED, 1),
         (host_util.HostExecutionState.ERROR, 1),
         ('Step1', 2), ('Step2', 1)],
        self.printer._previous_overview)

    self.mock_logger.reset_mock()
    self.mock_now.return_value = 41
    self.hosts[2].execution_state = host_util.HostExecutionState.COMPLETED
    self.printer.PrintState()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed.', 2, 5),
        mock.call.error('%r of %r hosts errored: %s', 1, 5, 'host4'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 2, 5, 'Step1', 'host1 host3')])
    self.assertEqual(41, self.printer._previous_print_time)

  def testPrintState_unchanged(self):
    self.printer.PrintState()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed.', 1, 5),
        mock.call.error('%r of %r hosts errored: %s', 1, 5, 'host4'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 2, 5, 'Step1', 'host1 host3'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 1, 5, 'Step2', 'host2')])
    self.assertEqual(31, self.printer._previous_print_time)
    self.mock_logger.reset_mock()
    self.mock_now.return_value = 41
    self.printer.PrintState()
    # The state doesn't change and it's only 10 seconds from last print.
    # So this no print this round.
    self.assertEqual(31, self.printer._previous_print_time)
    self.assertFalse(self.mock_logger.called)

  def testPrintState_longGapSinceLastPrint(self):
    time1 = 41
    self.mock_now.return_value = time1
    self.printer.PrintState()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed.', 1, 5),
        mock.call.error('%r of %r hosts errored: %s', 1, 5, 'host4'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 2, 5, 'Step1', 'host1 host3'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 1, 5, 'Step2', 'host2')])
    self.assertEqual(time1, self.printer._previous_print_time)

    self.mock_logger.reset_mock()
    time2 = time1 + host_util._MAX_LOGGING_TIME_GAP_IN_SEC + 10
    self.mock_now.return_value = time2
    self.printer.PrintState()
    # The state doesn't change but it's long time since last print.
    self.assertEqual(time2, self.printer._previous_print_time)
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed.', 1, 5),
        mock.call.error('%r of %r hosts errored: %s', 1, 5, 'host4'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 2, 5, 'Step1', 'host1 host3'),
        mock.call.info(
            '%r of %r hosts in "%s": %s', 1, 5, 'Step2', 'host2')])
    self.assertEqual(time2, self.printer._previous_print_time)

  def testPrintResult(self):
    self.mock_now.return_value = 51
    for i in range(5):
      self.hosts[i].StopExecutionTimer()
    with self.assertRaises(host_util.ExecutionError):
      self.printer.PrintResult()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed:', 1, 5),
        mock.call.info('%s [%s]', 'host0', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.error('1 of 5 hosts errored:'),
        mock.call.error('%s [%s]', 'host4', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.error('2 of 5 hosts in "Step1":'),
        mock.call.error('%s [%s]', 'host1', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.error('%s [%s]', 'host3', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.error('1 of 5 hosts in "Step2":'),
        mock.call.error('%s [%s]', 'host2', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('Total: 5, Completed: 1, Error: 1, Step1: 2, Step2: 1')])

  def testPrintResult_allCompleted(self):
    self.mock_now.return_value = 51
    for i in range(5):
      self.hosts[i].execution_state = host_util.HostExecutionState.COMPLETED
      self.hosts[i].StopExecutionTimer()
    self.printer.PrintResult()
    self.mock_logger.assert_has_calls([
        mock.call.info('%r of %r hosts completed:', 5, 5),
        mock.call.info('%s [%s]', 'host0', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('%s [%s]', 'host1', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('%s [%s]', 'host2', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('%s [%s]', 'host3', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('%s [%s]', 'host4', 'Time elapsed: 0 min 40 s(ended)'),
        mock.call.info('Total: 5, Completed: 5, Error: 0')])


if __name__ == '__main__':
  absltest.main()
