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

"""Unit tests for command_util."""
import getpass
import os
import socket

from absl.testing import absltest
import mock

from multitest_transport.cli import command_util


class CommandContextTest(absltest.TestCase):
  """Unit test for CommandUtil."""

  def setUp(self):
    super(CommandContextTest, self).setUp()
    self.wrapped_context = mock.MagicMock()
    self.wrapped_context.run.return_value = mock.MagicMock(return_code=0)
    self.wrapped_context.sudo.return_value = mock.MagicMock(return_code=0)
    self.remote_context = command_util.CommandContext(
        'remotehost', 'remoteuser',
        wrapped_context=self.wrapped_context,
        sudo_password='sudopwd')

  def testRun(self):
    res = self.remote_context.Run(['cmd'])
    self.wrapped_context.assert_has_calls([
        mock.call.run(
            'cmd', warn=True, out_stream=mock.ANY, err_stream=mock.ANY)])
    self.assertEqual(0, res.return_code)

  def testCreateCommandContext(self):
    context = command_util.CommandContext()
    self.assertTrue(context.IsLocal())

  @mock.patch.object(getpass, 'getuser')
  @mock.patch.object(socket, 'gethostname')
  def testCreateCommandContext_local(self, get_hostname, get_user):
    get_hostname.return_value = 'ahost'
    get_user.return_value = 'auser'
    context = command_util.CommandContext(
        socket.gethostname(), getpass.getuser())
    self.assertTrue(context.IsLocal())
    self.assertEqual('ahost', context.host)
    self.assertEqual('auser', context.user)

  @mock.patch.object(command_util, 'fabric')
  def testCreateCommandContext_remote(self, mock_fabric):
    fabric_config = mock.MagicMock()
    mock_fabric.Config.return_value = fabric_config
    context = command_util.CommandContext(
        'remotehost', 'remoteuser')
    self.assertFalse(context.IsLocal())
    self.assertEqual('remotehost', context.host)
    self.assertEqual('remoteuser', context.user)
    mock_fabric.Config.assert_called_once_with(
        system_ssh_path='~/.ssh/config')
    mock_fabric.Connection.assert_called_once_with(
        host='remotehost',
        user='remoteuser',
        config=fabric_config)

  @mock.patch.object(command_util, 'fabric')
  @mock.patch.object(command_util, 'invoke')
  def testCreateCommandContext_withSudoPwd(self, _, mock_fabric):
    fabric_config = mock.MagicMock()
    mock_fabric.Config.return_value = fabric_config
    context = command_util.CommandContext(
        'host1', 'user1', login_password=None, ssh_key=None,
        sudo_password='sudopwd')
    context.wrapped_context.sudo.assert_called_once()
    self.assertEqual('host1', context.host)
    self.assertEqual('user1', context.user)
    mock_fabric.Config.assert_called_once_with(
        system_ssh_path='~/.ssh/config')
    mock_fabric.Connection.assert_called_once_with(
        host='host1',
        user='user1',
        config=fabric_config)

  def testFindGcloud(self):
    context = command_util.CommandContext(
        wrapped_context=self.wrapped_context)
    self.assertFalse(context._tried_gcloud)
    gcloud = context._FindGCloud()
    self.assertEqual('gcloud', gcloud)
    self.wrapped_context.assert_has_calls([
        mock.call.run(
            'which gcloud', out_stream=mock.ANY, err_stream=mock.ANY,
            warn=True)])
    self.assertTrue(context._tried_gcloud)

  def testFindGcloud_noGcloud(self):
    self.wrapped_context.run.side_effect = [
        mock.MagicMock(return_code=1),
        mock.MagicMock(return_code=1)]
    context = command_util.CommandContext(
        wrapped_context=self.wrapped_context)
    self.assertFalse(context._tried_gcloud)
    gcloud = context._FindGCloud()
    self.assertIsNone(gcloud)
    self.wrapped_context.assert_has_calls(
        [
            mock.call.run(
                'which gcloud', out_stream=mock.ANY, err_stream=mock.ANY,
                warn=True),
            mock.call.run(
                'which /google/data/ro/teams/cloud-sdk/gcloud',
                out_stream=mock.ANY, err_stream=mock.ANY, warn=True)
        ],
        any_order=True)
    self.assertTrue(context._tried_gcloud)

  def testRun_withEnv(self):
    env = {'key1': 'value1', 'key2': 'value2'}
    res = self.remote_context.Run(['cmd'], env=env)
    self.wrapped_context.assert_has_calls([
        mock.call.run(
            'cmd', env=env, out_stream=mock.ANY, err_stream=mock.ANY,
            warn=True)])
    self.assertEqual(0, res.return_code)

  def testRun_sudo(self):
    res = self.remote_context.Run(['cmd'], sudo=True)
    self.wrapped_context.assert_has_calls([
        mock.call.sudo(
            'cmd', out_stream=mock.ANY, err_stream=mock.ANY, warn=True,
            password='sudopwd')])
    self.assertEqual(0, res.return_code)

  def testRun_raiseOnFailure(self):
    self.wrapped_context.run.return_value = mock.MagicMock(
        return_code=1, stdout='stdout', stderr='stderr')
    with self.assertRaises(RuntimeError):
      self.remote_context.Run(['cmd'], raise_on_failure=True)
    self.wrapped_context.assert_has_calls([
        mock.call.run(
            'cmd', warn=True, out_stream=mock.ANY, err_stream=mock.ANY)])

  def testRun_notRaiseOnFailure(self):
    self.wrapped_context.run.return_value = mock.MagicMock(
        return_code=1, stdout='stdout', stderr='stderr')
    res = self.remote_context.Run(['cmd'], raise_on_failure=False)
    self.assertEqual(1, res.return_code)
    self.assertEqual('stdout', res.stdout)
    self.assertEqual('stderr', res.stderr)
    self.wrapped_context.assert_has_calls([
        mock.call.run(
            'cmd', warn=True, out_stream=mock.ANY, err_stream=mock.ANY)])

  @mock.patch.object(command_util, 'CommandThread')
  def testRun_async(self, command_thread_class):
    command_thread = mock.MagicMock()
    command_thread_class.return_value = command_thread
    self.remote_context.Run(['cmd'], sync=False)
    run_config = command_util.CommandRunConfig(
        sudo=False, env=None, raise_on_failure=True, timeout=None)
    command_thread_class.assert_called_once_with(
        self.remote_context, ['cmd'], run_config)
    command_thread.start.assert_called_once_with()

  @mock.patch.object(os.path, 'exists')
  def testCopyFile(self, exists):
    exists.return_value = True
    self.remote_context.CopyFile('/local/file', '/remote/file')
    exists.assert_called_once_with('/local/file')
    self.wrapped_context.run.assert_called_once_with(
        'mkdir -p /remote', out_stream=mock.ANY, err_stream=mock.ANY, warn=True)
    self.wrapped_context.put.assert_called_once_with(
        '/local/file', '/remote/file')

  @mock.patch.object(os.path, 'exists')
  def testCopyFile_donotExist(self, exists):
    exists.return_value = False
    with self.assertRaises(IOError):
      self.remote_context.CopyFile('/do/not/exist/file', '/remote/path')

  @mock.patch.object(os.path, 'exists')
  def testCopyFile_local(self, exists):
    exists.return_value = True
    context = command_util.CommandContext(wrapped_context=self.wrapped_context)
    self.assertTrue(context.IsLocal())
    context.CopyFile('/local/file', '/remote/file')
    exists.assert_called_once_with('/local/file')
    self.wrapped_context.run.assert_has_calls([
        mock.call('mkdir -p /remote',
                  out_stream=mock.ANY, err_stream=mock.ANY, warn=True),
        mock.call('cp -rf /local/file /remote/file',
                  out_stream=mock.ANY, err_stream=mock.ANY, warn=True)])

  @mock.patch.object(os.path, 'exists')
  def testCopyFile_localSameFile(self, exists):
    exists.return_value = True
    context = command_util.CommandContext(wrapped_context=self.wrapped_context)
    self.assertTrue(context.IsLocal())
    context.CopyFile('/local/file', '/local/file')
    exists.assert_called_once_with('/local/file')
    self.wrapped_context.run.assert_called_once_with(
        'mkdir -p /local', out_stream=mock.ANY, err_stream=mock.ANY, warn=True)

  def testClose(self):
    self.assertFalse(self.remote_context._closed)
    self.remote_context.Close()
    self.assertTrue(self.remote_context._closed)
    with self.assertRaises(command_util.CommandContextClosedError):
      self.remote_context.Run(['command'])

  def testClose_local(self):
    context = command_util.CommandContext(wrapped_context=self.wrapped_context)
    self.assertTrue(context.IsLocal())
    self.assertFalse(context._closed)
    context.Close()
    self.assertTrue(context._closed)
    with self.assertRaises(command_util.CommandContextClosedError):
      context.Run(['command'])
    self.assertFalse(self.wrapped_context.close.called)


class CommandThreadTest(absltest.TestCase):
  """Unit test for CommandThread."""

  def testRun(self):
    context = mock.MagicMock()
    run_config = command_util.CommandRunConfig(
        sudo=False, env=None, raise_on_failure=True, timeout=None)
    thread = command_util.CommandThread(context, ['cmd'], run_config)
    thread.run()
    context.assert_has_calls([
        mock.call.Run(['cmd'],
                      sync=True,
                      sudo=False,
                      env=None,
                      raise_on_failure=True,
                      timeout=None)
    ])


class LocalCommandContextTest(absltest.TestCase):
  """Unit test for CommandContext when invoke is not imported."""

  def setUp(self):
    super(LocalCommandContextTest, self).setUp()
    self.subprocess_patcher = mock.patch('__main__.command_util.subprocess')
    self.mock_subprocess_pkg = self.subprocess_patcher.start()
    self.mock_process = mock.MagicMock(returncode=0)
    self.mock_subprocess_pkg.Popen.return_value = self.mock_process
    self.mock_process.communicate.return_value = ('stdout', 'stderr')
    self.context = command_util.CommandContext()

  def tearDown(self):
    self.subprocess_patcher.stop()
    super(LocalCommandContextTest, self).tearDown()

  def testRun(self):
    res = self.context.Run(['ls', '-al'])
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(['ls', '-al'])])
    self.assertEqual(0, res.return_code)
    self.assertEqual('stdout', res.stdout)
    self.assertEqual('stderr', res.stderr)

  def testRun_failed(self):
    self.mock_process.returncode = 1
    with self.assertRaises(RuntimeError):
      self.context.Run(['ls', '-al'])
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(['ls', '-al'])])

  def testRun_notRaiseOnFailure(self):
    self.mock_process.returncode = 1
    res = self.context.Run(['ls', '-al'], raise_on_failure=False)
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(
            ['ls', '-al'],
            stdout=self.mock_subprocess_pkg.PIPE,
            stderr=self.mock_subprocess_pkg.PIPE)])
    self.assertEqual(1, res.return_code)
    self.assertEqual('stdout', res.stdout)
    self.assertEqual('stderr', res.stderr)

  @mock.patch.object(os, 'environ', {'KEY': 'value'})
  def testRun_withEnv(self):
    res = self.context.Run(['ls', '-al'], env={'KEY1': 'value1'})
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(
            ['ls', '-al'], env={'KEY': 'value', 'KEY1': 'value1'})])
    self.assertEqual(0, res.return_code)
    self.assertEqual('stdout', res.stdout)
    self.assertEqual('stderr', res.stderr)

  def testRun_sudo(self):
    res = self.context.Run(['ls', '-al'], sudo=True)
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(['sudo', 'ls', '-al'])])
    self.assertEqual(0, res.return_code)
    self.assertEqual('stdout', res.stdout)
    self.assertEqual('stderr', res.stderr)

  @mock.patch.object(os.path, 'exists')
  def testCopyFile(self, exists):
    exists.return_value = True
    self.context.CopyFile('/local/file', '/remote/file')
    exists.assert_called_once_with('/local/file')
    self.mock_subprocess_pkg.assert_has_calls([
        mock.call.Popen(['mkdir', '-p', '/remote']),
        mock.call.Popen().communicate(),
        mock.call.Popen(['cp', '-rf', '/local/file', '/remote/file']),
        mock.call.Popen().communicate()])


class DockerHelperTest(absltest.TestCase):
  """Unit test for DockerHelper."""

  def setUp(self):
    super(DockerHelperTest, self).setUp()
    self._docker_context = mock.MagicMock()
    self._image = 'aimage'
    self._docker_helper = command_util.DockerHelper(
        self._docker_context, self._image)

  def testBuild(self):
    self._docker_helper.Build('path')
    self._docker_context.assert_has_calls([
        mock.call.Run(['build', '-t', self._image, 'path'])])

  def testPush(self):
    self._docker_helper.Push()
    self._docker_context.assert_has_calls([
        mock.call.Run(['push', self._image])])

  def testPull(self):
    self._docker_helper.Pull()
    self._docker_context.assert_has_calls([
        mock.call.Run(['pull', self._image])])

  @mock.patch.dict(os.environ, {'ENV3': 'value3'})
  def testRun(self):
    self._docker_helper.AddEnv('ENV1', 'value1')
    self._docker_helper.AddEnv('ENV2', 'value2')
    self._docker_helper.CopyEnv('ENV3')
    self._docker_helper.CopyEnv('ENV4')  # Should ignore non-existing envs.
    self._docker_helper.AddBind('/local/folder1', '/docker/folder1')
    self._docker_helper.AddVolume('mtt-folder2', '/docker/folder2')
    self._docker_helper.AddTmpfs('/atmpfs', 1000)
    self._docker_helper.AddPort(8001, 8001)
    self._docker_helper.AddPort(8002, 8002)
    self._docker_helper.AddFile('/local/file1', '/docker/file1')
    self._docker_helper.AddFile('/local/file2', '/docker/file2')
    self._docker_helper.Run('acontainer')
    self._docker_context.assert_has_calls([
        mock.call.Run(
            ['create', '--name', 'acontainer', '-it',
             '-v', '/etc/localtime:/etc/localtime:ro',
             '-v', '/etc/timezone:/etc/timezone:ro',
             '-v', '/dev/bus/usb:/dev/bus/usb',
             '-v', '/run/udev/control:/run/udev/control',
             '--device-cgroup-rule', 'c 189:* rwm',
             '--net=host',
             '--cap-add', 'syslog',
             '-e', 'ENV1=value1',
             '-e', 'ENV2=value2',
             '-e', 'ENV3=value3',
             '--mount', 'type=volume,src=mtt-folder2,dst=/docker/folder2',
             '--mount', 'type=bind,src=/local/folder1,dst=/docker/folder1',
             '--mount', 'type=tmpfs,dst=/atmpfs,tmpfs-size=1000',
             '-p', '8001:8001', '-p', '8002:8002',
             self._image]),
        mock.call.Run(['cp', '-L', '/local/file1', 'acontainer:/docker/file1']),
        mock.call.Run(['cp', '-L', '/local/file2', 'acontainer:/docker/file2']),
        mock.call.Run(['start', 'acontainer'])])

  def testStop(self):
    self._docker_helper.Stop(['c1', 'c2'])
    self._docker_context.assert_has_calls([
        mock.call.Run(['stop', 'c1', 'c2'],
                      timeout=command_util._DOCKER_STOP_CMD_TIMEOUT_SEC)
    ])

  def testKill(self):
    """Test DockerHelper.Kill."""
    self._docker_helper.Kill(['c1', 'c2'], 'SIG')
    self._docker_context.assert_has_calls([
        mock.call.Run(['kill', '-s', 'SIG', 'c1', 'c2'],
                      timeout=command_util._DOCKER_KILL_CMD_TIMEOUT_SEC)
    ])

  def testWait(self):
    """Test DockerHelper.Wait."""
    self._docker_helper.Wait(['c1', 'c2'])
    self._docker_context.assert_has_calls([
        mock.call.Run(['container', 'wait', 'c1', 'c2'],
                      timeout=command_util._DOCKER_WAIT_CMD_TIMEOUT_SEC)
    ])

  def testInspect(self):
    self._docker_helper.Inspect('c1')
    self._docker_context.assert_has_calls([
        mock.call.Run(['inspect', 'c1'], raise_on_failure=False)])

  def testInspect_withFormat(self):
    self._docker_helper.Inspect('c1', output_format='{{format}}')
    self._docker_context.assert_has_calls([
        mock.call.Run(['inspect', 'c1', '--format', '{{format}}'],
                      raise_on_failure=False)])

  def testGetRemoteImageDigest(self):
    self._docker_context.Run.side_effect = [
        command_util.CommandResult(0, 'aimage_digest', None),
    ]
    self.assertEqual(
        'aimage_digest', self._docker_helper.GetRemoteImageDigest('image_id'))
    self._docker_context.assert_has_calls([
        mock.call.Run(
            ['inspect', 'image_id', '--format', '{{index .RepoDigests 0}}'],
            raise_on_failure=True)])

  def testGetImageIdForContainer(self):
    self._docker_context.Run.side_effect = [
        command_util.CommandResult(0, 'aimage_id', None),
    ]
    self.assertEqual(
        'aimage_id',
        self._docker_helper.GetImageIdForContainer('c1'))
    self._docker_context.assert_has_calls([
        mock.call.Run(
            ['inspect', 'c1', '--format', '{{.Image}}'],
            raise_on_failure=True)])

  def testCleanupDanglingImages(self):
    self._docker_helper.CleanupDanglingImages()
    self._docker_context.assert_has_calls(
        [mock.call.Run(['image', 'prune', '-f', '--filter', '"until=240h"'],
                       raise_on_failure=False)])

  def testIsContainerRunning(self):
    self._docker_context.Run.side_effect = [
        command_util.CommandResult(0, 'running', None),
    ]
    self.assertTrue(self._docker_helper.IsContainerRunning('c1'))
    self._docker_context.assert_has_calls([
        mock.call.Run(['inspect', 'c1', '--format', '{{.State.Status}}'],
                      raise_on_failure=False)])

  def testIsContainerRunning_noExist(self):
    self._docker_context.Run.side_effect = [
        command_util.CommandResult(1, None, 'Error: No such object: c1'),
    ]
    self.assertFalse(self._docker_helper.IsContainerRunning('c1'))
    self._docker_context.assert_has_calls([
        mock.call.Run(['inspect', 'c1', '--format', '{{.State.Status}}'],
                      raise_on_failure=False)])

  def testRemoveContainers(self):
    self._docker_helper.RemoveContainers(['c1', 'c2'])
    self._docker_context.assert_has_calls([
        mock.call.Run(['container', 'rm', 'c1', 'c2'])])

  def testRemoveVolumes(self):
    self._docker_helper.RemoveVolumes(['v1', 'v2'])
    self._docker_context.assert_has_calls([
        mock.call.Run(['volume', 'rm', 'v1', 'v2'], raise_on_failure=False)])


class DockerContextTest(absltest.TestCase):
  """Unit test for DockerContext."""

  def setUp(self):
    super(DockerContextTest, self).setUp()
    self.command_context = mock.MagicMock()
    self.command_context.gcloud = 'gcloud'
    self.auth_patcher = mock.patch('__main__.command_util.google_auth_util')
    self.mock_auth_util = self.auth_patcher.start()

  def tearDown(self):
    self.auth_patcher.stop()
    super(DockerContextTest, self).tearDown()

  def testInit(self):
    self.command_context.Run.side_effect = [
        mock.MagicMock(return_code=0),
        mock.MagicMock(return_code=0),
        mock.MagicMock(return_code=0)
    ]
    command_util.DockerContext(self.command_context)
    self.command_context.assert_has_calls([
        mock.call.Run(['docker', '-v'], raise_on_failure=False),
        mock.call.Run(['gcloud', 'auth', 'configure-docker', '--quiet'],
                      raise_on_failure=False)
    ])

  def testInit_notGCloud_withServiceAccount(self):
    """Test init DockerContext without gcloud but with service account."""
    self.command_context.gcloud = None
    self.command_context.Run.side_effect = [
        mock.MagicMock(return_code=0),
        mock.MagicMock(return_code=0)
    ]
    cred = mock.MagicMock(token='atoken')
    self.mock_auth_util.CreateCredentialFromServiceAccount.return_value = cred
    self.mock_auth_util.GCS_READ_SCOPE = 'gcs_read_scope'
    command_util.DockerContext(
        self.command_context, service_account_json_key_path='key.json')

    self.command_context.assert_has_calls([
        mock.call.Run(['docker', '-v'], raise_on_failure=False),
        mock.call.Run(
            ['docker', 'login',
             '-u', 'oauth2accesstoken',
             '-p', 'atoken',
             command_util._DOCKER_SERVER],
            raise_on_failure=False)
    ])
    (self.mock_auth_util
     .CreateCredentialFromServiceAccount.assert_called_once_with(
         service_account_json_key_path='key.json',
         scopes=['gcs_read_scope']))

  def testRunCommand(self):
    self.command_context.Run.side_effect = [
        mock.MagicMock(return_code=0),
        mock.MagicMock(return_code=0),
        mock.MagicMock(return_code=0),
    ]
    docker_context = command_util.DockerContext(self.command_context)

    res = docker_context.Run(['images'])
    self.assertEqual(0, res.return_code)

    self.command_context.assert_has_calls([
        mock.call.Run(['docker', '-v'], raise_on_failure=False),
        mock.call.Run(['gcloud', 'auth', 'configure-docker', '--quiet'],
                      raise_on_failure=False),
        mock.call.Run(['docker', 'images'])
    ])


class HostCommandOutStreamTest(absltest.TestCase):
  """Unit test for HostCommandOutStream."""

  @mock.patch.object(command_util.HostCommandOutStream, '_Print')
  def testWrite(self, mock_print):
    """Test write."""
    out_stream = command_util.HostCommandOutStream('ahost', 'tag')
    out_stream.write(b'line1\n')
    out_stream.write(b'lin')
    out_stream.write(b'e2\n')
    out_stream.write(b'line3\nline4\n')
    out_stream.write(b'line5')
    out_stream.write(b'\n')
    mock_print.assert_has_calls([
        mock.call('ahost tag: line1'),
        mock.call('ahost tag: line2'),
        mock.call('ahost tag: line3'),
        mock.call('ahost tag: line4'),
    ])

  def testInit_hostIsNone(self):
    """Test __init__ with host is None."""
    out_stream = command_util.HostCommandOutStream(None, 'tag')
    self.assertEqual('tag: ', out_stream._prefix)


if __name__ == '__main__':
  absltest.main()
