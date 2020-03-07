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
    self.mock_func = mock.MagicMock(__name__='mock_func')
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
  def testLabExecutor(self, mock_build_lab_config_pool):
    """Test lab executor on multiple hosts sequentially."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=False,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfigs()])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[0]),
        mock.call(args, executor.hosts[1])])

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_withHostOrCluster(self, mock_build_lab_config_pool):
    """Test lab executor with hosts_or_clusters provided."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.side_effect = [
        self.host_config1, None]
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=['host1', 'cluster2'],
        parallel=False,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfig('host1'),
        mock.call.GetHostConfig('cluster2'),
        mock.call.GetHostConfigs('cluster2')])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[0]),
        mock.call(args, executor.hosts[1])])

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_withDuplicatedHostOrCluster(
      self, mock_build_lab_config_pool):
    """Test lab executor with hosts_or_clusters and there is duplicate."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfig.side_effect = [
        self.host_config1, None]
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=['host1', 'cluster1'],
        parallel=False,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfig('host1'),
        mock.call.GetHostConfig('cluster1'),
        mock.call.GetHostConfigs('cluster1')])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[0]),
        mock.call(args, executor.hosts[1])])

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_exitOnError(self, mock_build_lab_config_pool):
    """Test lab executor on multiple hosts sequentially and failed."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    self.mock_func.side_effect = [Exception(), None]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=False,
        ssh_key=None,
        exit_on_error=True,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    with self.assertRaises(Exception):
      executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfigs()])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    self.mock_func.assert_called_once_with(args, executor.hosts[0])
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     executor.hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.UNKNOWN,
                     executor.hosts[1].execution_state)

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_parallel(self, mock_build_lab_config_pool):
    """Test lab executor on multiple hosts parallel."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [
        [self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=True,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfigs()])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    # We don't know the order of the call since it's parallel.
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[0])])
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[1])])
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[1].execution_state)

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_parallel_partialFailed(self, mock_build_lab_config_pool):
    """Test lab executor on multiple hosts parallel with some failed."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_func.side_effect = [None, Exception()]
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=True,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    with self.assertRaises(Exception):
      executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([
        mock.call.GetHostConfigs()])
    self.assertLen(executor.hosts, 2)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1'),
        mock.call('host2', 'user1', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='user1')])
    # We don't know the order of the call since it's parallel.
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[0])])
    self.mock_func.assert_has_calls([
        mock.call(args, executor.hosts[1])])
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     executor.hosts[1].execution_state)

  @mock.patch.object(host_util, '_BuildLabConfigPool')
  def testLabExecutor_parallelWithFixedThreads(self,
                                               mock_build_lab_config_pool):
    """Test lab executor on multiple hosts parallel."""
    mock_build_lab_config_pool.return_value = self.mock_lab_config_pool
    self.mock_lab_config_pool.GetHostConfigs.side_effect = [[
        self.host_config1, self.host_config2, self.host_config3
    ]]
    args = mock.MagicMock(
        lab_config_path='lab_config.yaml',
        hosts_or_clusters=[],
        parallel=2,
        ssh_key=None,
        func=self.mock_func,
        ask_login_password=False,
        ask_sudo_password=False,
        sudo_user=None)

    executor = host_util.LabExecutor(args)
    executor.Execute()

    self.mock_lab_config_pool.assert_has_calls([mock.call.GetHostConfigs()])
    self.assertLen(executor.hosts, 3)
    self.assertEqual('host1', executor.hosts[0].config.hostname)
    self.assertEqual('host2', executor.hosts[1].config.hostname)
    self.assertEqual('host3', executor.hosts[2].config.hostname)
    self.mock_create_context.assert_has_calls([
        mock.call(
            'host1',
            'user1',
            login_password=None,
            ssh_key=None,
            sudo_password=None,
            sudo_user='user1'),
        mock.call(
            'host2',
            'user1',
            login_password=None,
            ssh_key=None,
            sudo_password=None,
            sudo_user='user1'),
        mock.call(
            'host3',
            'user1',
            login_password=None,
            ssh_key=None,
            sudo_password=None,
            sudo_user='user1')
    ])
    # We don't know the order of the call since it's parallel.
    self.mock_func.assert_has_calls([mock.call(args, executor.hosts[0])])
    self.mock_func.assert_has_calls([mock.call(args, executor.hosts[1])])
    self.mock_func.assert_has_calls([mock.call(args, executor.hosts[2])])
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[0].execution_state)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[1].execution_state)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     executor.hosts[2].execution_state)

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

  @mock.patch.object(socket, 'getfqdn')
  def testGetHostConfig_withoutLabConfig(self, mock_getfqdn):
    mock_getfqdn.return_value = 'host1.google.com'
    host_config = host_util._GetHostConfig(None)
    self.assertEqual('host1.google.com', host_config.hostname)

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

  def testBuildHostsWithContext_remoteHost(self):
    """Test _BuildHostsWithContext for a remote host."""
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='ahost', host_login_name='auser')
    hosts = host_util._BuildHostsWithContext([host_config])
    self.assertLen(hosts, 1)
    self.mock_create_context.assert_called_once_with(
        'ahost', 'auser', login_password=None, ssh_key=None, sudo_password=None,
        sudo_user='auser')

  def testBuildHostsWithContext_remoteHosts(self):
    """Test _BuildHostsWithContext for multiple remote hosts."""
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='auser')]
    hosts = host_util._BuildHostsWithContext(host_configs)
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'auser', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='auser'),
        mock.call('host2', 'auser', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='auser')])

  def testBuildHostsWithContext_remoteHost_sshkey(self):
    """Test _BuildHostsWithContext for a remote host with ssh key."""
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='ahost', host_login_name='auser')
    hosts = host_util._BuildHostsWithContext([host_config], ssh_key='/sshkey')
    self.assertLen(hosts, 1)
    self.mock_create_context.assert_called_once_with(
        'ahost', 'auser', login_password=None, ssh_key='/sshkey',
        sudo_password=None, sudo_user='auser')

  def testBuildHostsWithContext_remoteHosts_sshkey(self):
    """Test _BuildHostsWithContext for multiple remote hosts with ssh key."""
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='auser')]
    hosts = host_util._BuildHostsWithContext(host_configs, ssh_key='/sshkey')
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'auser', login_password=None, ssh_key='/sshkey',
                  sudo_password=None, sudo_user='auser'),
        mock.call('host2', 'auser', login_password=None, ssh_key='/sshkey',
                  sudo_password=None, sudo_user='auser')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_remoteHost_password(self, mock_getpass):
    """Test _BuildHostsWithContext for a remote host without ssh key."""
    mock_getpass.return_value = 'apassword'
    host_config = host_util.lab_config.CreateHostConfig(
        hostname='ahost', host_login_name='auser')
    hosts = host_util._BuildHostsWithContext(
        [host_config], ask_login_password=True)
    self.assertLen(hosts, 1)
    self.mock_create_context.assert_has_calls([
        mock.call('ahost', 'auser', login_password='apassword', ssh_key=None,
                  sudo_password=None, sudo_user='auser')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_remoteHosts_password(self, mock_getpass):
    """Test _BuildHostsWithContext for multiple remote hosts without ssh key."""
    mock_getpass.return_value = 'apassword'
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='auser')]
    hosts = host_util._BuildHostsWithContext(
        host_configs, ask_login_password=True)
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'auser', login_password='apassword', ssh_key=None,
                  sudo_password=None, sudo_user='auser'),
        mock.call('host2', 'auser', login_password='apassword', ssh_key=None,
                  sudo_password=None, sudo_user='auser')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_SudoPwdAndSshKey(self, mock_getpass):
    mock_getpass.return_value = 'sudopwd'
    self.mock_create_context.side_effect = [mock.MagicMock(), mock.MagicMock()]
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='user1'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='user2')]
    hosts = host_util._BuildHostsWithContext(
        host_configs, ssh_key='/sshkey', ask_sudo_password=True)
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key='/sshkey',
                  sudo_password='sudopwd', sudo_user='user1'),
        mock.call('host2', 'user2', login_password=None, ssh_key='/sshkey',
                  sudo_password='sudopwd', sudo_user='user2')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_SudoPwdAndNoLoginPwd(self, mock_getpass):
    mock_getpass.return_value = 'sudopwd'
    self.mock_create_context.side_effect = [mock.MagicMock(), mock.MagicMock()]
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='user1'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='user2')]
    hosts = host_util._BuildHostsWithContext(
        host_configs, ask_sudo_password=True)
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password='sudopwd', sudo_user='user1'),
        mock.call('host2', 'user2', login_password=None, ssh_key=None,
                  sudo_password='sudopwd', sudo_user='user2')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_SudoPwdAndLoginPwd(self, mock_getpass):
    mock_getpass.side_effect = ['loginpwd', 'sudopwd']
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='user1'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='user2')]
    hosts = host_util._BuildHostsWithContext(
        host_configs, ask_login_password=True, ask_sudo_password=True)
    self.assertLen(hosts, 2)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password='loginpwd', ssh_key=None,
                  sudo_password='sudopwd', sudo_user='user1'),
        mock.call('host2', 'user2', login_password='loginpwd', ssh_key=None,
                  sudo_password='sudopwd', sudo_user='user2')])

  @mock.patch.object(getpass, 'getpass')
  def testBuildHostsWithContext_SudoPwdAndSudoUser(self, mock_getpass):
    mock_getpass.side_effect = ['sudopwd']
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='user1')]
    hosts = host_util._BuildHostsWithContext(
        host_configs, ask_sudo_password=True, sudo_user='sudo_user1')
    self.assertLen(hosts, 1)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'user1', login_password=None, ssh_key=None,
                  sudo_password='sudopwd', sudo_user='sudo_user1')])

  def testBuildHostsWithContext_unknownException(self):
    """Test _BuildHostsWithContext for multiple remote hosts."""
    host_configs = [
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'),
        host_util.lab_config.CreateHostConfig(
            hostname='host2', host_login_name='auser')]
    self.mock_create_context.side_effect = [
        Exception('Connection timeout.'),
        self.mock_context]

    hosts = host_util._BuildHostsWithContext(host_configs)
    self.assertLen(hosts, 2)
    self.assertEqual('host1', hosts[0].name)
    self.assertEqual(
        host_util.HostExecutionState.ERROR, hosts[0].execution_state)
    self.assertEqual('host2', hosts[1].name)
    self.mock_create_context.assert_has_calls([
        mock.call('host1', 'auser', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='auser'),
        mock.call('host2', 'auser', login_password=None, ssh_key=None,
                  sudo_password=None, sudo_user='auser')])

  def testWrapFuncForSetHost(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_func)
    f = host_util._WrapFuncForSetHost(self.mock_func)

    f(args, host)

    self.mock_func.assert_called_once_with(args, host)
    self.assertEqual(host_util.HostExecutionState.COMPLETED,
                     host.execution_state)

  def testWrapFuncForSetHost_error(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_func)
    f = host_util._WrapFuncForSetHost(self.mock_func)
    e = Exception('Fail to run command.')
    self.mock_func.side_effect = [e]

    with self.assertRaises(Exception):
      f(args, host)

    self.mock_func.assert_called_once_with(args, host)
    self.assertEqual(host_util.HostExecutionState.ERROR,
                     host.execution_state)
    self.assertEqual(e, host.error)

  def testWrapFuncForSetHost_skip(self):
    host = host_util.Host(
        host_util.lab_config.CreateHostConfig(
            hostname='host1', host_login_name='auser'))
    host.context = self.mock_context
    host.execution_state = host_util.HostExecutionState.COMPLETED
    args = mock.MagicMock(
        hosts=[],
        extra_hosts=None,
        user=None,
        cluster=None,
        parallel=False,
        func=self.mock_func)
    f = host_util._WrapFuncForSetHost(self.mock_func)

    f(args, host)

    self.assertFalse(self.mock_func.called)

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
