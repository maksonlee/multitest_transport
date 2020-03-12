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

"""Unit tests for cli."""
import os
import shutil
import tempfile

from absl.testing import absltest
from absl.testing import parameterized
import mock
from tradefed_cluster.configs import lab_config

from multitest_transport.cli import command_util
from multitest_transport.cli import cli
from multitest_transport.cli import unittest_util

_DOCKER_VERSION_STRING = 'Docker version 18.06.1-ce'


class CliTest(parameterized.TestCase):
  """Unit tests for cli."""

  def setUp(self):
    super(CliTest, self).setUp()
    self.mock_context = mock.MagicMock()
    self.context_patcher = mock.patch(
        '__main__.cli.command_util.CommandContext',
        return_value=self.mock_context)
    self.mock_create_context = self.context_patcher.start()
    self.mock_context.Run.return_value = (
        mock.MagicMock(return_code=0, stdout=_DOCKER_VERSION_STRING))
    self.mock_context.IsLocal.return_value = True

    self.mock_auth_patcher = mock.patch(
        '__main__.cli.command_util.google_auth_util'
        '.CreateCredentialFromServiceAccount')
    self.mock_auth_patcher.start()
    self.expanduser_patcher = mock.patch(
        '__main__.os.path.expanduser', return_value='/local/.android')
    self.mock_expanduser = self.expanduser_patcher.start()
    self.file_exists_patcher = mock.patch(
        '__main__.os.path.exists',
        side_effect=lambda p: p in self.mock_exist_files)
    self.file_exists_patcher.start()
    self.mock_exist_files = ['/local/.android']
    self.old_user = os.environ.get('USER')
    os.environ['USER'] = 'user'
    self.mock_timezone_patcher = mock.patch(
        '__main__.cli._GetHostTimezone', return_value='Etc/UTC')
    self.mock_timezone_patcher.start()
    self.mock_waiter_patcher = mock.patch('__main__.cli._WaitForServer')
    self.mock_waiter_patcher.start()
    self.tmp_root = tempfile.mkdtemp()

    self.arg_parser = cli.CreateParser()

  def tearDown(self):
    os.environ['USER'] = self.old_user
    self.expanduser_patcher.stop()
    self.file_exists_patcher.stop()
    self.mock_auth_patcher.stop()
    self.context_patcher.stop()
    super(CliTest, self).tearDown()

  def testGetDockerImageName(self):
    self.assertEqual(
        'image:xxx',
        cli._GetDockerImageName('image:xxx'))
    self.assertEqual(
        'image:yyy',
        cli._GetDockerImageName('image:xxx', tag='yyy'))

  def _CreateHost(self,
                  hostname=None,
                  cluster_name=None,
                  login_name=None,
                  tmpfs_configs=None,
                  docker_image='gcr.io/android-mtt/mtt:prod',
                  master_url='url',
                  graceful_shutdown=False,
                  enable_stackdriver=False,
                  lab_name=None,
                  enable_autoupdate=None,
                  service_account_json_key_path=None):

    host = cli.host_util.Host(
        lab_config.CreateHostConfig(
            hostname=hostname,
            lab_name=lab_name,
            cluster_name=cluster_name,
            host_login_name=login_name,
            tmpfs_configs=tmpfs_configs,
            docker_image=docker_image,
            master_url=master_url,
            graceful_shutdown=graceful_shutdown,
            enable_stackdriver=enable_stackdriver,
            enable_autoupdate=enable_autoupdate,
            service_account_json_key_path=service_account_json_key_path))
    host.context = self.mock_context
    return host

  def testStart(self):
    """Test start without service account."""
    args = self.arg_parser.parse_args(['start'])
    cli.Start(
        args,
        self._CreateHost(
            cluster_name='acluster',
            lab_name='alab'))

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'LAB_NAME=alab',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call(['docker', 'start', 'mtt'])])

  @mock.patch.dict(
      os.environ, {
          'http_proxy': 'http_proxy',
          'https_proxy': 'https_proxy',
          'ftp_proxy': 'ftp_proxy',
          'no_proxy': 'no_proxy'
      })
  def testStart_withProxySettings(self):
    """Test start with local proxy settings."""
    args = self.arg_parser.parse_args(['start'])
    cli.Start(
        args,
        self._CreateHost(cluster_name='acluster'))

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '-e', 'http_proxy=http_proxy',
            '-e', 'https_proxy=https_proxy',
            '-e', 'ftp_proxy=ftp_proxy',
            '-e', 'no_proxy=no_proxy,127.0.0.1',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call(['docker', 'start', 'mtt'])])

  @mock.patch.object(cli.command_util.DockerHelper, 'IsContainerRunning')
  def testStart_alreadyRunning(self, mock_is_running):
    """Test start with MTT already running."""
    mock_is_running.return_value = True

    args = self.arg_parser.parse_args(['start'])
    cli.Start(args, self._CreateHost(cluster_name='acluster'))

    # exited early after checking docker and authentication
    self.mock_context.IsLocal.assert_not_called()
    self.mock_context.CopyFile.assert_not_called()
    self.assertEqual(2, self.mock_context.Run.call_count)

  def testStart_localNoAndroid(self):
    """Test start local but no ~/.android."""
    self.mock_exist_files = []
    args = self.arg_parser.parse_args(['start'])
    cli.Start(
        args,
        self._CreateHost(cluster_name='acluster'))

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call(['docker', 'start', 'mtt'])])

  def testStart_withServiceAccount(self):
    """Test Start function."""
    args = self.arg_parser.parse_args([
        'start', '--service_account_json_key_path', '/path/to/key.json'])
    cli.Start(
        args,
        self._CreateHost(
            cluster_name='acluster',
            service_account_json_key_path='/path/to/key.json'))

    self.mock_context.Run.assert_has_calls([
        mock.call(
            ['docker', 'volume', 'rm', 'mtt-temp'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '-e', 'JSON_KEY_PATH=/tmp/keyfile/key.json',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=volume,src=mtt-key,dst=/tmp/keyfile',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call([
            'docker', 'cp', '-L',
            '/path/to/key.json', 'mtt:/tmp/keyfile/key.json']),
        mock.call(['docker', 'start', 'mtt'])])

  @mock.patch.object(cli, '_WaitForServer')
  def testStart_standalone(self, wait_for_server):
    wait_for_server.return_value = True

    args = self.arg_parser.parse_args(['start'])
    cli.Start(args, self._CreateHost(master_url=None))

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_PORT=8000',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call(['docker', 'start', 'mtt'])])

  def testStart_argsWithContainerNameAndImageName(self):
    """Test Start function."""
    args = self.arg_parser.parse_args(
        ['start', '--name', 'acontainer', '--image_name', 'animage',
         '--tag', 'atag'])
    cli.Start(
        args,
        self._CreateHost(cluster_name='acluster'))

    self.mock_context.Run.assert_has_calls([
        mock.call(
            ['docker', 'volume', 'rm', 'mtt-temp'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'acontainer'],
                  raise_on_failure=False),
        mock.call([
            'docker', 'create',
            '--name', 'acontainer', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'animage:atag']),
        mock.call(['docker', 'start', 'acontainer'])])

  @mock.patch.object(shutil, 'rmtree')
  @mock.patch.object(shutil, 'copy')
  @mock.patch.object(tempfile, 'mkdtemp')
  def testStart_adb(self, mock_temp_dir, mock_copy_file, mock_rm_dir):
    """Test starting with a custom ADB tool."""
    mock_temp_dir.return_value = '/tmp/dir'
    args = self.arg_parser.parse_args(
        ['start', '--custom_adb_path', '/local/adb'])
    cli.Start(
        args,
        self._CreateHost(cluster_name='acluster'))

    # file copied over to temp directory and ultimately cleaned up
    mock_copy_file.assert_called_with('/local/adb', '/tmp/dir/adb')
    mock_rm_dir.assert_called_with('/tmp/dir')

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call([  # temp directory copied over to container
            'docker',
            'cp', '-L', '/tmp/dir', 'mtt:/tmp/custom_sdk_tools']),
        mock.call(['docker', 'start', 'mtt'])])

  def testStart_withStackdriver(self):
    """Test Start with stackdriver logging enabled."""
    args = self.arg_parser.parse_args([
        'start', '--service_account_json_key_path', '/path/to/key.json'])
    cli.Start(
        args,
        self._CreateHost(
            cluster_name='acluster',
            enable_stackdriver=True,
            service_account_json_key_path='/path/to/key.json'))

    self.mock_context.Run.assert_has_calls([
        mock.call(
            ['docker', 'volume', 'rm', 'mtt-temp'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '-e', 'JSON_KEY_PATH=/tmp/keyfile/key.json',
            '-e', 'ENABLE_STACKDRIVER_LOGGING=1',
            '-e', 'ENABLE_STACKDRIVER_MONITORING=1',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=volume,src=mtt-key,dst=/tmp/keyfile',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'gcr.io/android-mtt/mtt:prod']),
        mock.call([
            'docker', 'cp', '-L',
            '/path/to/key.json', 'mtt:/tmp/keyfile/key.json']),
        mock.call(['docker', 'start', 'mtt'])])

  def testStart_withTmpfs(self):
    """Test Start with tmpfs."""
    args = self.arg_parser.parse_args(['start'])
    cli.Start(
        args,
        self._CreateHost(
            cluster_name='acluster',
            tmpfs_configs=[
                lab_config.CreateTmpfsConfig('/atmpfs', 1000, '750')]))

    self.mock_context.Run.assert_has_calls([
        mock.call(
            ['docker', 'volume', 'rm', 'mtt-temp'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=url',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            '--mount', 'type=tmpfs,dst=/atmpfs,tmpfs-size=1000,tmpfs-mode=750',
            'gcr.io/android-mtt/mtt:prod']),
        mock.call(['docker', 'start', 'mtt'])])

  def testStart_imageNameAndMasterUrlInHost(self):
    """Test start with image name and master url in host."""
    args = self.arg_parser.parse_args(['start'])
    cli.Start(
        args,
        self._CreateHost(
            cluster_name='acluster', master_url='tfc',
            docker_image='a_docker_image'))

    self.mock_context.Run.assert_has_calls([
        mock.call([
            'docker', 'create',
            '--name', 'mtt', '-it',
            '-v', '/dev/bus/usb:/dev/bus/usb',
            '-v', '/run/udev/control:/run/udev/control',
            '--device-cgroup-rule', 'c 189:* rwm',
            '--net=host',
            '--cap-add', 'syslog',
            '-e', 'MTT_MASTER_URL=tfc',
            '-e', 'CLUSTER=acluster',
            '-e', 'USER=user',
            '-e', 'TZ=Etc/UTC',
            '--mount', 'type=volume,src=mtt-data,dst=/data',
            '--mount', 'type=volume,src=mtt-temp,dst=/tmp',
            '--mount', 'type=bind,src=/local/.android,dst=/root/.android',
            '--mount', ('type=bind,src=/var/run/docker.sock,'
                        'dst=/var/run/docker.sock'),
            'a_docker_image']),
        mock.call(['docker', 'start', 'mtt'])])

  @mock.patch.object(cli, '_StartMttNode')
  @mock.patch.object(cli, '_StartMttDaemon')
  def testStart_EnableAutoupdate_DaemonAlreadyActive(
      self, start_mttd, start_mtt):
    args = self.arg_parser.parse_args(['start'])
    host = self._CreateHost(
        cluster_name='acluster', hostname='ahost', enable_autoupdate=True)

    cli.Start(args, host)

    start_mtt.assert_not_called()
    start_mttd.assert_called_once_with(args, host)

  @mock.patch.object(cli, '_IsDaemonActive')
  @mock.patch.object(cli, '_SetupSystemdScript')
  @mock.patch.object(cli, '_SetupMTTRuntimeIntoLibPath')
  def testStartMttDaemon_AlreadyActive(
      self, setup_permanent_bin, setup_mttd, is_active):
    args = mock.create_autospec(cli.argparse.Namespace)
    host = self._CreateHost(
        cluster_name='acluster', hostname='ahost', enable_autoupdate=True)
    is_active.return_value = True

    cli._StartMttDaemon(args, host)
    setup_mttd.assert_not_called()
    setup_permanent_bin.assert_not_called()

  @mock.patch.object(cli, '_IsDaemonActive')
  @mock.patch.object(cli, '_SetupSystemdScript')
  @mock.patch.object(cli, '_SetupMTTRuntimeIntoLibPath')
  def testStartMttDaemon_NotYetActive(
      self, setup_permanent_bin, setup_mttd, is_active):
    args = mock.create_autospec(cli.argparse.Namespace)
    host = self._CreateHost(
        cluster_name='acluster', hostname='ahost', enable_autoupdate=True)
    is_active.return_value = False

    cli._StartMttDaemon(args, host)
    setup_mttd.assert_called_with(args, host)
    setup_permanent_bin.assert_called_with(args, host)
    self.mock_context.Run.assert_has_calls([
        mock.call(['systemctl', 'enable', 'mttd.service']),
        mock.call(['systemctl', 'start', 'mttd.service']),
    ])

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.os.geteuid')
  def testStop(self, euid, is_running):
    euid.return_value = 123
    is_running.return_value = True
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop'])
    cli.Stop(args, self._CreateHost())

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'kill', '-s', 'TERM', 'mtt'],
                  timeout=command_util._DOCKER_KILL_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'container', 'wait', 'mtt'],
                  timeout=command_util._DOCKER_WAIT_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    is_running.assert_called_once_with('mtt')

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  def testStop_notRunning(self, is_running):
    is_running.return_value = False
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop'])
    cli.Stop(args, self._CreateHost())

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    is_running.assert_called_once_with('mtt')

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.os.geteuid')
  def testStop_gracefulShutdownWithWaitFlag(self, euid, is_running):
    """Test Stop with wait flag set."""
    euid.return_value = 123
    is_running.return_value = True
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop', '--wait'])
    cli.Stop(args, self._CreateHost())

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'kill', '-s', 'TSTP', 'mtt'],
                  timeout=command_util._DOCKER_KILL_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'container', 'wait', 'mtt'],
                  timeout=command_util._DOCKER_WAIT_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    is_running.assert_called_once_with('mtt')

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.os.geteuid')
  def testStop_gracefulShutdownWithConfig(self, euid, is_running):
    """Test Stop with graceful shutdown set in host config."""
    euid.return_value = 123
    is_running.return_value = True
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop'])
    cli.Stop(args, self._CreateHost(graceful_shutdown=True))

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'kill', '-s', 'TSTP', 'mtt'],
                  timeout=command_util._DOCKER_KILL_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'container', 'wait', 'mtt'],
                  timeout=command_util._DOCKER_WAIT_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    is_running.assert_called_once_with('mtt')

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.os.geteuid')
  def testStop_noMasterUrl(self, euid, is_running):
    """Test Stop with kill mtt with master_url in host config."""
    euid.return_value = 123
    is_running.return_value = True
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop'])
    cli.Stop(args, self._CreateHost(master_url=None))

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'stop', 'mtt'],
                  timeout=command_util._DOCKER_STOP_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'container', 'wait', 'mtt'],
                  timeout=command_util._DOCKER_WAIT_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    is_running.assert_called_once_with('mtt')

  @mock.patch.object(cli, '_StopMttNode')
  @mock.patch.object(cli, '_IsDaemonActive')
  def testStop_DaemonIsClosedIfActive(self, is_active, stop_mtt):
    is_active.return_value = True
    args = self.arg_parser.parse_args(['stop'])
    host = self._CreateHost(hostname='ahost')

    cli.Stop(args, host)

    stop_mtt.assert_called_with(args, host)
    self.mock_context.Run.assert_has_calls([
        mock.call(['systemctl', 'stop', 'mttd.service']),
        mock.call(['systemctl', 'disable', 'mttd.service']),
    ])

  @mock.patch('__main__.cli.os.geteuid')
  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch.object(cli, '_DetectAndKillDeadContainer')
  def testStop_ForceKillInSudoMode(self, detect_and_kill, is_running, euid):
    euid.return_value = 0
    is_running.return_value = True
    self.mock_context.host = 'ahost'
    args = self.arg_parser.parse_args(['stop'])

    cli.Stop(args, self._CreateHost())

    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'kill', '-s', 'TERM', 'mtt'],
                  timeout=command_util._DOCKER_KILL_CMD_TIMEOUT_SEC),
        mock.call(['docker', 'inspect', 'mtt'], raise_on_failure=False),
        mock.call(['docker', 'container', 'rm', 'mtt'],
                  raise_on_failure=False),
    ])
    detect_and_kill.assert_called_once()

  @mock.patch.object(cli, '_StartMttNode')
  @mock.patch.object(cli, '_StopMttNode')
  @mock.patch.object(cli, '_StartMttDaemon')
  @mock.patch.object(cli, '_StopMttDaemon')
  def testRestart(self, stop_mttd, start_mttd, stop_mtt, start_mtt):
    """Test Restart."""
    args = self.arg_parser.parse_args(['restart'])
    host = self._CreateHost()
    cli.Restart(args, host)
    stop_mttd.assert_called_with(host)
    stop_mtt.assert_called_once_with(args, host)
    start_mttd.assert_not_called()
    start_mtt.assert_called_once_with(args, host)

  @mock.patch.object(cli, '_StartMttNode')
  @mock.patch.object(cli, '_StopMttNode')
  @mock.patch.object(cli, '_StartMttDaemon')
  @mock.patch.object(cli, '_StopMttDaemon')
  def testRestart_EnableAutoupdate(
      self, stop_mttd, start_mttd, stop_mtt, start_mtt):
    """Test Restart."""
    args = self.arg_parser.parse_args(['restart'])
    host = self._CreateHost(enable_autoupdate=True)
    cli.Restart(args, host)
    stop_mttd.assert_called_with(host)
    stop_mtt.assert_called_once_with(args, host)
    start_mtt.assert_not_called()
    start_mttd.assert_called_once_with(args, host)

  @mock.patch.object(cli, '_StartMttNode')
  @mock.patch.object(cli, '_StopMttNode')
  @mock.patch.object(cli, '_PullUpdate')
  def testUpdate(self, pull_update, stop_mtt, start_mtt):
    """Test Update."""
    pull_update.return_value = True
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost()
    cli.Update(args, host)
    stop_mtt.assert_called_once_with(args, host)
    start_mtt.assert_called_once_with(args, host)

  @mock.patch.object(cli, '_StartMttNode')
  @mock.patch.object(cli, '_StopMttNode')
  @mock.patch.object(cli, '_PullUpdate')
  def testUpdate_notUpdate(self, pull_update, stop_mtt, start_mtt):
    """Test Update but skip."""
    pull_update.return_value = False
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost()
    cli.Update(args, host)

    self.assertFalse(stop_mtt.called)
    self.assertFalse(start_mtt.called)

  @mock.patch.object(cli, '_UpdateMttNode')
  @mock.patch.object(cli, '_StartMttDaemon')
  def testUpdate_EnableAutoupdate(self, start_mttd, update_mtt):
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost(enable_autoupdate=True)
    cli.Update(args, host)
    start_mttd.assert_called_once()
    update_mtt.assert_not_called()

  def testPullUpdate_forceUpdate(self):
    """Test PullUpdate with force_update."""
    args = self.arg_parser.parse_args(['update', '--force_update'])
    host = self._CreateHost()
    self.assertTrue(cli._PullUpdate(args, host))

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  def testPullUpdate_notRunning(self, is_running):
    """Test PullUpdate when container is not running."""
    is_running.return_value = False
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost()
    self.assertTrue(cli._PullUpdate(args, host))
    is_running.assert_called_once_with('mtt')

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.command_util.DockerHelper.GetImageIdForContainer')
  @mock.patch('__main__.cli.command_util.DockerHelper.GetRemoteImageDigest')
  def testPullUpdate_differetImage(
      self, get_remote_image_digest, get_image_id, is_running):
    """Test PullUpdate with different remote image."""
    is_running.return_value = True
    get_image_id.return_value = 'image_id'
    get_remote_image_digest.side_effect = ['container_image', 'remote_image']
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost(docker_image='gcr.io/android-mtt/mtt:prod')
    self.assertTrue(cli._PullUpdate(args, host))

    is_running.assert_called_once_with('mtt')
    get_image_id.assert_called_once_with('mtt')
    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'pull', 'gcr.io/android-mtt/mtt:prod'])])
    get_remote_image_digest.assert_has_calls([
        mock.call('image_id'),
        mock.call('gcr.io/android-mtt/mtt:prod'),
    ])

  @mock.patch('__main__.cli.command_util.DockerHelper.IsContainerRunning')
  @mock.patch('__main__.cli.command_util.DockerHelper.GetImageIdForContainer')
  @mock.patch('__main__.cli.command_util.DockerHelper.GetRemoteImageDigest')
  def testPullUpdate_sameImage(
      self, get_remote_image_digest, get_image_id, is_running):
    """Test PullUpdate with the same remote image."""
    is_running.return_value = 'running'
    get_image_id.return_value = 'image_id'
    get_remote_image_digest.return_value = 'remote_image'
    args = self.arg_parser.parse_args(['update'])
    host = self._CreateHost(docker_image='gcr.io/android-mtt/mtt:prod')
    self.assertFalse(cli._PullUpdate(args, host))

    is_running.assert_called_once_with('mtt')
    get_image_id.assert_called_once_with('mtt')
    self.mock_context.Run.assert_has_calls([
        mock.call(['docker', 'pull', 'gcr.io/android-mtt/mtt:prod'])])
    get_remote_image_digest.assert_has_calls([
        mock.call('image_id'),
        mock.call('gcr.io/android-mtt/mtt:prod'),
    ])

  @mock.patch.object(tempfile, 'mkdtemp')
  def testSetupSystemdScript(self, mock_create_temp):
    tmp_folder = os.path.join(self.tmp_root, 'mtt_extracted')
    os.mkdir(tmp_folder)
    mock_create_temp.return_value = tmp_folder
    mtt_path = os.path.join(self.tmp_root, 'mtt')
    unittest_util.CreateZipFile(
        mtt_path,
        [unittest_util.File(
            filename='multitest_transport/mttd.service',
            content='this is a fake mttd systemd script')])

    args = mock.create_autospec(cli.argparse.Namespace)
    args.cli_path = mtt_path
    host = mock.create_autospec(cli.host_util.Host)
    host.name = 'host1'
    cli._SetupSystemdScript(args, host)
    host.context.CopyFile.assert_called_once_with(
        os.path.join(tmp_folder, cli._ZIPPED_MTTD_FILE),
        cli._MTTD_FILE)
    host.context.Run.assert_has_calls([
        mock.call(['systemctl', 'daemon-reload'])])

  def testSetupMTTRuntimeIntoPermanentPath(self):
    mtt_path = os.path.join(self.tmp_root, 'mtt')
    key_path = os.path.join(self.tmp_root, 'keyfile', 'key.json')
    args = mock.create_autospec(cli.argparse.Namespace)
    args.cli_path = mtt_path
    host = mock.create_autospec(cli.host_util.Host)
    host.config.service_account_json_key_path = key_path
    cli._SetupMTTRuntimeIntoLibPath(args, host)
    host.context.assert_has_calls([
        mock.call.CopyFile(mtt_path, cli._MTT_BINARY),
        mock.call.CopyFile(key_path, cli._KEY_FILE),
    ])
    host.config.Save.assert_called_once_with(cli._HOST_CONFIG)

  @parameterized.named_parameters(
      ('Daemon is active', True, 0, '**/nActive: active (running)\n**', ''),
      ('Daemon is inactive', False, 3, '**/nActive: inactive (dead)\n**', ''),
      ('Daemon is not registered', False, 4, '', '**could not be found.\n'))
  def testIsDaemonActive(self, expect_active, return_code, stdout, stderr):
    host = self._CreateHost()
    host.context.Run.return_value = cli.command_util.CommandResult(
        return_code=return_code, stdout=stdout, stderr=stderr)
    self.assertEqual(expect_active, cli._IsDaemonActive(host))

  def testForceKillMttNode_withoutContainerRunning(self):
    host = self._CreateHost()
    docker_helper = mock.create_autospec(cli.command_util.DockerHelper)
    docker_helper.IsContainerRunning.return_value = False
    cli._ForceKillMttNode(host, docker_helper, 'a_container_name')
    host.context.Run.assert_not_called()
    docker_helper.IsContainerRunning.assert_called_with('a_container_name')

  def testForceKillMttNode_withContainerRunning(self):
    host = self._CreateHost()
    docker_helper = mock.create_autospec(cli.command_util.DockerHelper)
    docker_helper.IsContainerRunning.side_effect = [
        True,
        True,
        False,
    ]
    docker_helper.GetProcessIdForContainer.return_value = 'acontainer_pid'
    host.context.Run.side_effect = [
        cli.command_util.CommandResult(0, 'a_parent_pid\n', None),
        cli.command_util.CommandResult(0, None, None),
    ]

    cli._ForceKillMttNode(host, docker_helper, 'a_container_name')

    docker_helper.GetProcessIdForContainer.assert_called_with(
        'a_container_name')
    docker_helper.IsContainerRunning.assert_called_with('a_container_name')
    docker_helper.Wait.assert_called_with(['a_container_name'])
    host.context.Run.assert_has_calls([
        mock.call(['ps', '-o', 'ppid=', '-p', 'acontainer_pid'],
                  raise_on_failure=True),
        mock.call(['kill', '-9', 'a_parent_pid'], raise_on_failure=True),
    ])

  @mock.patch.object(cli, '_ForceKillMttNode')
  @mock.patch('__main__.cli.time')
  def testDetectAndKillDeadContainer_detectedAndKilled(self, mock_time,
                                                       mock_kill):
    docker_helper = mock.create_autospec(cli.command_util.DockerHelper)
    docker_helper.IsContainerAlive.side_effect = [True, True, False]
    mock_time.time.side_effect = [0, 0, 30, 60, 90]
    host = self._CreateHost()
    container_name = 'container_1'

    cli._DetectAndKillDeadContainer(
        host, docker_helper, container_name, total_wait_sec=90)

    mock_kill.assert_called_with(host, docker_helper, container_name)
    self.assertLen(mock_time.sleep.call_args_list, 2)

  @mock.patch.object(cli, '_ForceKillMttNode')
  @mock.patch('__main__.cli.time')
  def testDetectAndKillDeadContainer_timedOut(self, mock_time, mock_kill):
    docker_helper = mock.create_autospec(cli.command_util.DockerHelper)
    docker_helper.IsContainerAlive.return_value = True
    mock_time.time.side_effect = [0, 0, 30, 60, 90]
    host = self._CreateHost()
    container_name = 'container_1'

    cli._DetectAndKillDeadContainer(
        host, docker_helper, container_name, total_wait_sec=90)

    mock_kill.assert_called_with(host, docker_helper, container_name)
    self.assertLen(mock_time.sleep.call_args_list, 3)


_ALL_START_OPTIONS = (
    ('force_update', True),
    ('name', 'container'),
    ('image_name', 'image'),
    ('tag', 'tag'),
    ('service_account_json_key_path', 'key.json'),
    ('port', 8001),
)
_ALL_STOP_OPTIONS = (
    ('name', 'container'),
    ('wait', True),
)
_ALL_RESTART_OPTIONS = tuple(
    _ALL_START_OPTIONS + _ALL_STOP_OPTIONS)
_ALL_UPDATE_OPTIONS = tuple(
    _ALL_START_OPTIONS + _ALL_STOP_OPTIONS)


class CliParserTest(parameterized.TestCase):
  """Unit tests for cli."""

  def setUp(self):
    super(CliParserTest, self).setUp()
    self.arg_parser = cli.CreateParser()

  def _CreateCommandLine(self, prefix_args, options, suffix_args):
    cmd = prefix_args[:]
    for key, value in options:
      cmd.append('--%s' % key)
      if not isinstance(value, bool):
        cmd.append(value.__str__())
    cmd.extend(suffix_args)
    return cmd

  @parameterized.named_parameters(
      ('start', 'start', cli.Start),
      ('stop', 'stop', cli.Stop),
      ('restart', 'restart', cli.Restart),
      ('update', 'update', cli.Update))
  def testParseArg_defaultOptions(self, cmd, f):
    """Test arg parsing for default options."""
    args = self.arg_parser.parse_args([cmd])
    self.assertEqual(f, args.func)

  @parameterized.named_parameters(
      ('start', 'start', cli.Start, _ALL_START_OPTIONS),
      ('stop', 'stop', cli.Stop, _ALL_STOP_OPTIONS),
      ('restart', 'restart', cli.Restart, _ALL_RESTART_OPTIONS),
      ('update', 'update', cli.Update, _ALL_UPDATE_OPTIONS))
  def testParseArg_AllOptions(self, cmd, f, options):
    """Test arg parsing for default options."""
    cmd = self._CreateCommandLine([cmd], options, ['lab_config.yaml'])
    args = self.arg_parser.parse_args(cmd)
    self.assertEqual(f, args.func)
    for key, value in options:
      self.assertEqual(value, getattr(args, key))
    self.assertEqual('lab_config.yaml', args.lab_config_path)
    self.assertEqual(f, args.func)


if __name__ == '__main__':
  absltest.main()
