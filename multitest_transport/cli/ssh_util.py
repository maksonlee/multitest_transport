"""SSH utils."""
import logging
import shlex
import subprocess
import tempfile

from typing import List

import attr

from multitest_transport.cli import common

logger = logging.getLogger(__name__)


def _tokenize_ssh_arg(ssh_arg):
  """Tokenize ssh arg.

  For example, '-o op1=v1 -o op2=v2' should be tokenized to
  ['-o', 'op1=v1', '-o', 'op2=v2'].

  Args:
    ssh_arg: a list of ssh args, one ssh arg may contain multiple parts.
  Returns:
    tokenized ssh args.
  """
  if not ssh_arg:
    return []
  return shlex.split(ssh_arg)


def _build_remote_ssh_str(command_str, sudo=False):
  """Build remote command line ssh can understand."""
  remote_cmd_str = '/bin/sh -c \'%s\'' % command_str
  if sudo:
    remote_cmd_str = 'sudo ' + remote_cmd_str
  return remote_cmd_str


def _ssh_with_password(password):
  """Ssh with password need a password file and use sshpass."""
  passfile = tempfile.NamedTemporaryFile()
  passfile.write(password.encode())
  passfile.flush()
  # passfile will be deleted at exit.
  return passfile, ['sshpass', '-f%s' % passfile.name]


@attr.s
class SshConfig(object):
  """Information to ssh to remote host."""
  # User to login.
  user = attr.ib(type=str)
  # Hostname to login.
  hostname = attr.ib(type=str)
  # Password for user.
  password = attr.ib(type=str, default=None)
  # ssh args.
  ssh_args = attr.ib(type=List[str], converter=_tokenize_ssh_arg, default=())
  # ssh key.
  ssh_key = attr.ib(type=str, default=None)
  # Use native ssh or fabric ssh.
  use_native_ssh = attr.ib(type=bool, default=False)


class Context(object):
  """A wrapper around ssh client.

  We were using paramiko, but paramiko:
  1. It doesn't support some syntax in ssh config, e.g. Include, which makes
      manage ssh config for multiple labs become difficult.
  2. There is a inconsistency between ssh to the host and use mtt_lab to manage
      the hosts. Debuging for this is really hard and people keep asking why
      mtt_lab failed but ssh succeeded.
  3. paramiko seems leaking pipe it opened, which causing errors when managing
      large a mount of hosts.
  Looking at other ssh libs, AsyncSSH, etc, they provide some nice features, but
  they are all not fully compatible with ssh config.

  Here we impement a simple wrapper around local ssh client. It just creates
  ssh commands and run through subprocess.
  """

  def __init__(self, ssh_config):
    """Create a ssh context.

    Args:
      ssh_config: SshConfig.
    """
    # TOOD(xingdai): timeout, logging, environment, etc.
    self._hostname = ssh_config.hostname
    self._user = ssh_config.user
    self._password = ssh_config.password
    self._ssh_config = ssh_config

  def run(self, command_str, **run_kwargs):
    """Run command on remote host.

    Args:
      command_str: a string to represent the command to run on remote host.
      **run_kwargs: args for the run.
    Returns:
      common.CommandResult.
    """
    return self._run(_build_remote_ssh_str(command_str), **run_kwargs)

  def sudo(self, command_str, **run_kwargs):
    """Run command as on remote host.

    Args:
      command_str: a string to represent the command to run on remote host.
      **run_kwargs: args for the run.
    Returns:
      common.CommandResult.
    """
    return self._run(_build_remote_ssh_str(command_str, sudo=True),
                     **run_kwargs)

  def _run(self, remote_cmd_str, **run_kwargs):
    """Run command on remote host."""
    # TOOD(xingdai): timeout, logging, environment, etc.
    password = self._password or run_kwargs.get('password')
    del run_kwargs
    logger.debug(
        'Run on %s@%s %s password: %s', self._user, self._hostname,
        'with' if password else 'without', remote_cmd_str)
    ssh_cmds = ['ssh']
    ssh_cmds.extend(self._ssh_config.ssh_args)
    ssh_cmds.extend([
        '-o', 'User=%s' % self._user, self._hostname,
        remote_cmd_str])
    password_file = None
    try:
      if password:
        password_file, sshpass_cmds = _ssh_with_password(password)
        ssh_cmds = sshpass_cmds + ssh_cmds
      return self._execute_cmd(ssh_cmds)
    finally:
      if password_file:
        password_file.close()

  def put(self, local_file_path, remote_file_path):
    """Copy local file to remote.

    Only supports copying file, does not support folders.

    Args:
      local_file_path: local file path.
      remote_file_path: remote file path.
    """
    password = self._password
    logger.debug(
        'Copy %s to %s %s password', local_file_path, remote_file_path,
        'with' if password else 'without')
    ssh_arg_str = ''
    if self._ssh_config.ssh_args:
      ssh_arg_str = ' '.join(['ssh'] + self._ssh_config.ssh_args)
    rsync_cmds = ['rsync']
    if ssh_arg_str:
      rsync_cmds.extend(['-e', ssh_arg_str])
    rsync_cmds.extend([
        local_file_path,
        '%s@%s:%s' % (self._user, self._hostname, remote_file_path)
    ])
    password_file = None
    try:
      if password:
        password_file, sshpass_cmds = _ssh_with_password(password)
        rsync_cmds = sshpass_cmds + rsync_cmds
      self._execute_cmd(rsync_cmds)
    finally:
      if password_file:
        # close will also delete the file.
        password_file.close()

  def close(self):
    """Close connection to remote host."""
    # ssh session is controlled by ssh client, we don't need to
    # do anything here.
    pass

  def _execute_cmd(self, cmd):
    """Execute command line.

    Args:
      cmd: a list represents a command line.
    Returns:
      CommandResult.
    """
    logger.debug('Run: %r', cmd)
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)
    outs, errs = p.communicate()
    self._print_pipe(outs)
    self._print_pipe(errs)
    return common.CommandResult(p.returncode, outs, errs)

  def _print_pipe(self, outs):
    """Print stdout and stderr.

    Args:
      outs: stdout or stderr of subprocess.
    """
    if not outs:
      return
    for line in outs.split('\n'):
      logger.debug('%s@%s stdout: %s', self._user, self._hostname, line)
