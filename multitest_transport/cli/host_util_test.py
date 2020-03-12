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
import getpass
import socket

from absl.testing import absltest
from absl.testing import parameterized
import mock

from multitest_transport.cli import host_util


class HostUtilTest(parameterized.TestCase):
  """Unit tests for host util."""

  def setUp(self):
    super(HostUtilTest, self).setUp()
    self.mock_context = mock.MagicMock()
    self.context_patcher = mock.patch(
        '__main__.host_util.command_util.CommandContext',
        return_value=self.mock_context)
    self.mock_create_context = self.context_patcher.start()
    self.mock_host_func = mock.MagicMock(__name__='mock_host_func')
    self.host_config1 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster1', hostname='host1',
        host_login_name='user1')
    self.host_config2 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster2', hostname='host2',
        host_login_name='user1')
    self.host_config3 = host_util.lab_config.CreateHostConfig(
        cluster_name='cluster3', hostname='host3', host_login_name='user1')
    self.mock_lab_config_pool = mock.MagicMock()

  def tearDown(self):
    self.context_patcher.stop()
    super(HostUtilTest, self).tearDown()

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testExecute(self, mock_build_lab_config_pool):
    """Test execute."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=False,
        ssh_key=None,
        host_func=self.mock_host_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user=None),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user=None)])
    self.assertLen(self.mock_host_func.call_args_list, 2)
    args1, host1 = self.mock_host_func.call_args_list[0][0]
    args2, host2 = self.mock_host_func.call_args_list[1][0]
    self.assertEqual(args, args1)
    self.assertEqual('host1', host1.name)
    self.assertEqual(args, args2)
    self.assertEqual('host2', host2.name)

  @mock.patch.object(getpass, 'getpass')
  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testExecute_askPass(self, mock_build_lab_config_pool, mock_getpass):
    """Test execute on multiple hosts with password."""
    mock_getpass.side_effect = ['login_pswd', 'sudo_pswd']
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=False,
        ssh_key=None,
        host_func=self.mock_host_func,
        ask_password=True,
        ask_sudo_password=True,
        sudo_user='sudo_user')

    host_util.Execute(args)

    self.mock_lab_config_pool.GetHostConfigs.assert_called_once_with()
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password='login_pswd', ssh_key=None,
                  sudo_password='sudo_pswd', sudo_user='sudo_user'),
        mock.call('host2', 'user1', login_password='login_pswd', ssh_key=None,
                  sudo_password='sudo_pswd', sudo_user='sudo_user')])
    self.assertLen(self.mock_host_func.call_args_list, 2)
    args1, host1 = self.mock_host_func.call_args_list[0][0]
    args2, host2 = self.mock_host_func.call_args_list[1][0]
    self.assertEqual(args, args1)
    self.assertEqual('host1', host1.name)
    self.assertEqual(args, args2)
    self.assertEqual('host2', host2.name)

  def testSequentialExecute_exitOnError(self):
    """Test _SequentialExecute multiple hosts sequentially and failed."""
    hosts = [
        host_util.Host(host_config, context=self.mock_context)
        for host_config in
        [self.host_config1, self.host_config2]]
    self.mock_host_func.side_effect = [Exception(), None]
    args = mock.MagicMock(
        parallel=False,
        exit_on_error=True,
        host_func=self.mock_host_func)

    with self.assertRaises(Exception):
      host_util._SequentialExecute(
          host_util._WrapFuncForSetHost(self.mock_host_func),
          args,
          hosts,
          exit_on_error=True)

    self.mock_host_func.assert_called_once_with(args, hosts[0])
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
    args = mock.MagicMock(
        parallel=2,
        host_func=self.mock_host_func)

    host_util._ParallelExecute(
        host_util._WrapFuncForSetHost(self.mock_host_func),
        args,
        hosts)

    # We don't know the order of the call since it's parallel.
    self.mock_host_func.assert_has_calls([mock.call(args, hosts[0])])
    self.mock_host_func.assert_has_calls([mock.call(args, hosts[1])])
    self.mock_host_func.assert_has_calls([mock.call(args, hosts[2])])
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
    def _FakeHostFuncFactory(bad_hosts):
      def _FakeHostFunc(unused_args, host):
        if host in bad_hosts:
          raise Exception()
      return _FakeHostFunc
    self.mock_host_func.side_effect = _FakeHostFuncFactory(bad_hosts=[hosts[1]])
    args = mock.MagicMock(
        parallel=True,
        host_func=self.mock_host_func)

    host_util._ParallelExecute(
        host_util._WrapFuncForSetHost(self.mock_host_func),
        args,
        hosts)

    # We don't know the order of the call since it's parallel.
    self.mock_host_func.assert_has_calls([
        mock.call(args, hosts[0])])
    self.mock_host_func.assert_has_calls([
        mock.call(args, hosts[1])])
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     hosts[1].execution_state)

  @mock.patch.object(host_util, '_BuildLabConfigPool')
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

  @mock.patch.object(host_util, '_BuildLabConfigPool')
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

  @mock.patch.object(host_util, '_BuildLabConfigPool')
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

  @mock.patch.object(host_util, '_BuildLabConfigPool')
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

    host_util._BuildLabConfigPool(lab_config_path='lab_config.yaml')

    mock_local_file_enumerator.assert_called_once_with(
        'lab_config.yaml', mock.ANY)
    self.mock_lab_config_pool.LoadConfigs.assert_called_once_with()

  def testBuildLabConfigPool_noLabConfig(self):
    lab_config_pool = host_util._BuildLabConfigPool(lab_config_path=None)
    self.assertEmpty(lab_config_pool.GetHostConfigs())

  @mock.patch.object(host_util.google_auth_util, 'GetGCloudCredential')
  @mock.patch.object(host_util.gcs_file_util, 'CreateGCSClient')
  @mock.patch.object(host_util.gcs_file_util, 'GCSFileEnumerator')
  @mock.patch.object(host_util.lab_config, 'LabConfigPool')
  def testBuildLabConfigPool_withGCS(
      self, mock_create_lab_config_pool, mock_gcs_file_enumerator,
      mock_create_gcs_client, mock_get_cred):
    mock_create_lab_config_pool.return_value = self.mock_lab_config_pool

    host_util._BuildLabConfigPool(lab_config_path='gs://bucket/lab_config.yaml')

    mock_gcs_file_enumerator.assert_called_once_with(
        mock.ANY, 'gs://bucket/lab_config.yaml', mock.ANY)
    self.mock_lab_config_pool.LoadConfigs.assert_called_once_with()
    self.assertTrue(mock_create_gcs_client.called)
    self.assertTrue(mock_get_cred.called)

  def testHostContext(self):
    """Test Host.context."""
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='ahost', host_login_name='auser')
    host = host_util.Host(host_config)
    self.assertIsNotNone(host.context)
    self.mock_create_context.assert_called_once_with(
        'ahost', 'auser', login_password=None, ssh_key=None, sudo_password=None,
        sudo_user=None)

  def testHostContext_withSSHInfo(self):
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='host1', host_login_name='user1')
    host = host_util.Host(
        host_config, sudo_user='sudo_user1', sudo_password='sudopwd',
        login_password='loginpwd', ssh_key='/ssh_key')
    self.assertIsNotNone(host.context)
    self.mock_create_context.assert_called_once_with(
        'host1', 'user1', login_password='loginpwd',
        ssh_key='/ssh_key', sudo_password='sudopwd', sudo_user='sudo_user1')

  def testHostContext_unknownException(self):
    """Test Host.context with exception."""
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='host1', host_login_name='auser')
    self.mock_create_context.side_effect = Exception('Connection timeout.')

    context = None
    with self.assertRaises(Exception):
      context = host_util.Host(host_config).context
    self.assertIsNone(context)
    self.mock_create_context.assert_called_once_with(
        'host1', 'auser', login_password=None, ssh_key=None,
        sudo_password=None, sudo_user=None)

  def testWrapFuncForSetHost(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_host_func)
    f = host_util._WrapFuncForSetHost(self.mock_host_func)

    f(args, host)

    self.mock_host_func.assert_called_once_with(args, host)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     host.execution_state)
    host.StartExecutionTimer.assert_called_once()
    host.StopExecutionTimer.assert_called_once()

  def testWrapFuncForSetHost_error(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_host_func)
    f = host_util._WrapFuncForSetHost(self.mock_host_func)
    e = Exception('Fail to run command.')
    self.mock_host_func.side_effect = [e]

    with self.assertRaises(Exception):
      f(args, host)

    self.mock_host_func.assert_called_once_with(args, host)
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     host.execution_state)
    self.assertEqual(e, host.error)
    host.StartExecutionTimer.assert_called_once()
    host.StopExecutionTimer.assert_called_once()

  def testWrapFuncForSetHost_skip(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    host.StartExecutionTimer = mock.MagicMock()
    host.StopExecutionTimer = mock.MagicMock()
    host.execution_state = host_util.HostExecutionState.COMPLETED
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_host_func)
    f = host_util._WrapFuncForSetHost(self.mock_host_func)

    f(args, host)

    self.assertFalse(self.mock_host_func.called)
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

  @mock.patch.object(host_util, 'logger')
  def testPrintExecutionState(self, mock_logger):
    host1 = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host1.execution_state = 'Step1'
    host1.execution_state = 'Step2'
    host2 = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='auser'))
    host2.execution_state = 'Step1'
    host3 = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host3', host_login_name='auser'))
    host3.execution_state = 'Step1'
    host3.execution_state = 'Step2'
    host4 = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host4', host_login_name='auser'))
    host4.execution_state = 'Step1'
    host_util._PrintExecutionState([host4, host3, host2, host1])
    mock_logger.assert_has_calls([
        mock.call.info('%r host in "%s": %s', 2, 'Step1', 'host2 host4'),
        mock.call.info('%r host in "%s": %s', 2, 'Step2', 'host1 host3')])


if __name__ == '__main__':
  absltest.main()
