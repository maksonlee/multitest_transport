"""Tests for ssh_util."""
import os
import tempfile
from unittest import mock

from absl.testing import absltest

from multitest_transport.cli import ssh_util


class SshUtilTest(absltest.TestCase):
  """Unit test for ssh util."""

  def setUp(self):
    super(SshUtilTest, self).setUp()
    self.subprocess_patcher = mock.patch('__main__.ssh_util.subprocess')
    self.mock_subprocess_pkg = self.subprocess_patcher.start()
    self.mock_process = mock.MagicMock(returncode=0)
    self.mock_subprocess_pkg.Popen.return_value = self.mock_process
    self.mock_process.communicate.return_value = ('stdout', 'stderr')

  def tearDown(self):
    super(SshUtilTest, self).tearDown()
    self.subprocess_patcher.stop()

  def testRun(self):
    """Test run."""
    c = ssh_util.Context(ssh_util.SshConfig(user='auser', hostname='ahost'))
    res = c.run('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh', '-o', 'User=auser', 'ahost',
         '/bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  def testRun_withSshArgs(self):
    """Test run with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null')))
    res = c.run('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null',
         '-o', 'User=auser', 'ahost',
         '/bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  def testRun_withSshArgs_notTokenized(self):
    """Test run with ssh args."""
    c = ssh_util.Context(
        ssh_util.SshConfig(
            user='auser', hostname='ahost',
            ssh_args=('-o StrictHostKeyChecking=no '
                      '-o UserKnownHostsFile=/dev/null')))
    res = c.run('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null',
         '-o', 'User=auser', 'ahost',
         '/bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testRun_withPassword(self, mock_create_file):
    """Test run with password."""
    mock_file = mock.MagicMock()
    mock_file.name = '/atmpfile'
    mock_create_file.return_value = mock_file
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost', password='apass'))
    res = c.run('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['sshpass', '-f/atmpfile', 'ssh', '-o', 'User=auser', 'ahost',
         '/bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)
    mock_file.assert_has_calls([
        mock.call.write('apass'.encode()),
        mock.call.flush(),
        mock.call.__bool__(),
        mock.call.close()])

  def testRun_withSshKey(self):
    """Test run with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null'),
        ssh_key='/path/to/key'))
    res = c.run('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null',
         '-i', '/path/to/key',
         '-o', 'User=auser', 'ahost',
         '/bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  def testSudo(self):
    """Test run."""
    c = ssh_util.Context(ssh_util.SshConfig(user='auser', hostname='ahost'))
    res = c.sudo('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh', '-o', 'User=auser', 'ahost',
         'sudo /bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  def testSudo_withSshArgs(self):
    """Test run with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null')))
    res = c.sudo('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null',
         '-o', 'User=auser', 'ahost',
         'sudo /bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testSudo_withPassword(self, mock_create_file):
    """Test run with password."""
    mock_file = mock.MagicMock()
    mock_file.name = '/atmpfile'
    mock_create_file.return_value = mock_file
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost', password='apass'))
    res = c.sudo('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['sshpass', '-f/atmpfile', 'ssh', '-o', 'User=auser', 'ahost',
         'sudo /bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)
    mock_file.assert_has_calls([
        mock.call.write('apass'.encode()),
        mock.call.flush(),
        mock.call.__bool__(),
        mock.call.close()])

  def testSudo_withSshKey(self):
    """Test run with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null'),
        ssh_key='/path/to/key'))
    res = c.sudo('/tmp/mtt start /tmp/lab.yaml')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null',
         '-i', '/path/to/key',
         '-o', 'User=auser', 'ahost',
         'sudo /bin/sh -c \'/tmp/mtt start /tmp/lab.yaml\''],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertEqual(0, res.return_code)

  def testPut(self):
    """Test put."""
    c = ssh_util.Context(ssh_util.SshConfig(user='auser', hostname='ahost'))
    c.put('/path/to/local/file', '/path/to/remote/file')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['rsync', '/path/to/local/file', 'auser@ahost:/path/to/remote/file'],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertTrue(self.mock_process.communicate.called)

  def testPut_withSshArgs(self):
    """Test put with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null')))
    c.put('/path/to/local/file', '/path/to/remote/file')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['rsync', '-e',
         'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
         '/path/to/local/file', 'auser@ahost:/path/to/remote/file'],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertTrue(self.mock_process.communicate.called)

  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testPut_withPassword(self, mock_create_file):
    """Test put with password."""
    mock_file = mock.MagicMock()
    mock_file.name = '/atmpfile'
    mock_create_file.return_value = mock_file
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost', password='apass'))
    c.put('/path/to/local/file', '/path/to/remote/file')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['sshpass', '-f/atmpfile', 'rsync', '/path/to/local/file',
         'auser@ahost:/path/to/remote/file'],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertTrue(self.mock_process.communicate.called)
    mock_file.assert_has_calls([
        mock.call.write('apass'.encode()),
        mock.call.flush(),
        mock.call.__bool__(),
        mock.call.close()])

  def testPut_withSshKey(self):
    """Test put with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_key='/path/to/key'))
    c.put('/path/to/local/file', '/path/to/remote/file')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['rsync', '-e',
         'ssh -i /path/to/key',
         '/path/to/local/file', 'auser@ahost:/path/to/remote/file'],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertTrue(self.mock_process.communicate.called)

  def testPut_withSshKeyAndSshArgs(self):
    """Test put with ssh args."""
    c = ssh_util.Context(ssh_util.SshConfig(
        user='auser', hostname='ahost',
        ssh_args=('-o StrictHostKeyChecking=no '
                  '-o UserKnownHostsFile=/dev/null'),
        ssh_key='/path/to/key'))
    c.put('/path/to/local/file', '/path/to/remote/file')
    self.mock_subprocess_pkg.Popen.assert_called_once_with(
        ['rsync', '-e',
         ('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
          ' -i /path/to/key'),
         '/path/to/local/file', 'auser@ahost:/path/to/remote/file'],
        stdin=self.mock_subprocess_pkg.DEVNULL,
        stdout=self.mock_subprocess_pkg.PIPE,
        stderr=self.mock_subprocess_pkg.PIPE,
        universal_newlines=True)
    self.assertTrue(self.mock_process.communicate.called)

  def testBuildRemoteSshStr(self):
    """Test _build_remote_ssh_str."""
    self.assertEqual(
        '/bin/sh -c \'echo test\'',
        ssh_util._build_remote_ssh_str('echo test'))

    self.assertEqual(
        'sudo /bin/sh -c \'echo test\'',
        ssh_util._build_remote_ssh_str('echo test', sudo=True))

  def testTokenizeSshArg(self):
    """Test _tokenize_ssh_arg."""
    self.assertEqual(
        ['-o', 'StrictHostKeyChecking=no',
         '-o', 'UserKnownHostsFile=/dev/null'],
        ssh_util._tokenize_ssh_arg(
            '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'))

  def testSshWithPassword(self):
    """Test _ssh_with_password."""
    passfile, sshpass_args = ssh_util._ssh_with_password('apass')
    self.assertEqual(['sshpass', '-f' + passfile.name], sshpass_args)
    with open(passfile.name) as f:
      self.assertEqual('apass', f.read())
    passfile.close()
    self.assertFalse(os.path.exists(passfile.name))


if __name__ == '__main__':
  absltest.main()
