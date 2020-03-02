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

"""A utility for running local/remote commands."""
import collections
import getpass
import logging
import os
import pipes
import socket
import subprocess
import threading
import time

import six

from multitest_transport.cli import google_auth_util

logger = logging.getLogger(__name__)


try:
  import invoke  except ImportError:
  invoke = None
  logging.warn('Failed to import invoke')

try:
  # Test importing paramiko.
  # Importing fabric can error out in uncatchable ways if paramiko errors out.
  import paramiko    import fabric  except ImportError:
  fabric = None
  paramiko = None
  logging.warn('Failed to import fabric or paramiko')

_GCLOUD_PATHS = ['gcloud', '/google/data/ro/teams/cloud-sdk/gcloud']
_REMOTE_IMAGE_DIGEST_FORMAT = '{{index .RepoDigests 0}}'
_IMAGE_ID_FORMAT = '{{.Image}}'
_CONTAINER_STATUS_FORMAT = '{{.State.Status}}'
_CONTAINER_PID_FORMAT = '{{.State.Pid}}'
_CONTAINER_RUNNING_STATUS = 'running'
_NO_SUCH_OBJECT_ERROR = 'No such object'
_DEFAULT_TMPFS_SIZE_IN_BYTES = 10 * 2 ** 30  # 10G
_DOCKER_SERVER = 'https://gcr.io'
_DOCKER_STOP_CMD_TIMEOUT_SEC = 60 * 60
_DOCKER_KILL_CMD_TIMEOUT_SEC = 60
_DOCKER_WAIT_CMD_TIMEOUT_SEC = 2 * 60 * 60

CommandResult = collections.namedtuple(
    'CommandResult', ['return_code', 'stdout', 'stderr'])


CommandRunConfig = collections.namedtuple(
    'CommandRunConfig', ['sudo', 'env', 'raise_on_failure', 'timeout'])


class CommandContextClosedError(Exception):
  """Error for running command on a closed context."""


class DockerError(Exception):
  """Docker-related error."""


class DockerNotFoundError(DockerError):
  """Docker is not found on a host."""


class DockerVersionTooOldError(DockerError):
  """Docker version is too old."""


class DockerVersionNotFoundError(DockerError):
  """Docker version is not found."""


class GCloudError(Exception):
  """GCloud-related error."""


class GCloudNotFoundError(GCloudError):
  """GCloud is not found on a host."""


class FabricNotFoundError(Exception):
  """Fabric is not found on a host."""


class AuthenticationError(Exception):
  """Fail to auth a user on a host."""


class HostCommandOutStream(object):
  """Customized file object like output stream.

  This is not thread safe.
  This is used to distinguish output from different hosts.
  """

  def __init__(self, host, tag='', log_level=logging.DEBUG):
    self.log_level = log_level
    prefixs = []
    if host:
      prefixs.append(host)
    if tag:
      prefixs.append(tag)
    self._prefix = ' '.join(prefixs)
    if self._prefix:
      self._prefix += ': '
    self._last_incomplete_line = ''

  def write(self, b):      """Write a string to the stream."""
    decoded_stream = six.ensure_text(b, errors='ignore')
    lines = decoded_stream.split('\n')
    if not lines:
      return
    lines[0] = self._last_incomplete_line + lines[0]
    self._last_incomplete_line = lines.pop()
    for line in lines:
      self._Print(self._prefix + line)

  def flush(self):      pass

  def _Print(self, line):
    """Print a line, expose for testing."""
    logger.log(self.log_level, line)


class CommandContext(object):
  """Wrap around invoke.Context."""

  def __init__(self, host=None, user=None, login_password=None,
               wrapped_context=None, ssh_key=None, sudo_password=None,
               sudo_user=None, remote_sudo_wrapped_context=None):
    """Create context that will be used to run command with.

    Args:
      host: a host name.
      user: username of the host.
      login_password: password for user to login.
      wrapped_context: invoke context, used for test.
      ssh_key: ssh key file to use.
      sudo_password: Text or None, password to run sudo commands.
      sudo_user: Text or None, user to run sudo commands.
      remote_sudo_wrapped_context: invoke context, used for sudo test.
    Raises:
      FabricNotFoundError: fabric is not installed.
    """
    self._host = host or socket.gethostname()
    self._user = user or getpass.getuser()
    self._is_local = False
    self._tried_gcloud = False
    self._gcloud = None
    if socket.gethostname() == self._host:
      self._is_local = True

    self._login_password = login_password
    self._ssh_key = ssh_key
    self._closed = False
    self._sudo_password = sudo_password
    self._sudo_user = sudo_user
    self._out_stream = HostCommandOutStream(
        None if self._is_local else host, 'stdout')
    # We also output stderr to DEBUG level, if the command failed and
    # raise on failure, the raised exception will have the information.
    self._err_stream = HostCommandOutStream(
        None if self._is_local else host, 'stderr')
    self.wrapped_context = None
    self.remote_sudo_wrapped_context = remote_sudo_wrapped_context
    if wrapped_context:
      self.wrapped_context = wrapped_context
      return
    if self._is_local:
      if invoke:
        # Use invoke context to running locally.
        self.wrapped_context = invoke.Context()
      # Else use _RunDirectly instead of using invoke.context.
      return
    if not fabric:
      raise FabricNotFoundError(
          'Fabric is not installed. Can not run on remote host.')
    self._CreateRemoteWrappedContext()

  def _CreateRemoteWrappedContext(self):
    """Create wrapped context for a remote host.

    This function creates two fabric connections, one for sudo commands, another
    for regular commands.

    Raises:
      AuthenticationError: failed to auth
    """
    # fabric has problems to understand complex ssh config.
    # Point to a user config
    fab_config = fabric.Config(system_ssh_path='~/.ssh/config')
    connect_kwargs = {
        'config': fab_config
    }
    if self._ssh_key or self._login_password:
      connect_kwargs['connect_kwargs'] = {}
      if self._ssh_key:
        logger.debug(
            'Use ssh key %s ssh %s@%s.', self._ssh_key, self._user, self._host)
        connect_kwargs['connect_kwargs']['key_filename'] = self._ssh_key
      if self._login_password:
        logger.debug('Use password to ssh %s@%s.', self._user, self._host)
        connect_kwargs['connect_kwargs']['password'] = self._login_password
    regular_connect_kwargs = connect_kwargs.copy()
    regular_connect_kwargs['user'] = self._user
    try:
      self.wrapped_context = fabric.Connection(
          host=self._host, **regular_connect_kwargs)
      self.wrapped_context.open()
      if (not self.remote_sudo_wrapped_context
          and self._sudo_password is not None):
        sudo_connect_kwargs = connect_kwargs.copy()
        sudo_connect_kwargs['user'] = self._sudo_user
        self.remote_sudo_wrapped_context = fabric.Connection(
            host=self._host, **sudo_connect_kwargs)
        self._TestSudoAccess()
      logger.info('Connected to %s@%s.', self._user, self._host)
    except (paramiko.AuthenticationException, paramiko.SSHException) as e:
      logger.debug(e)
      raise AuthenticationError(e)

  def _TestSudoAccess(self):
    """Test sudo access on a host."""
    logger.debug('Testing sudo access.')
    try:
      self.remote_sudo_wrapped_context.sudo(
          'echo "Testing sudo access..."',
          hide=True,
          password=self._sudo_password)
    except invoke.exceptions.AuthFailure as e:
      logger.debug('Sudo access failed: %s', e)
      raise AuthenticationError(e)

  @property
  def host(self):
    return self._host

  @property
  def user(self):
    return self._user

  @property
  def gcloud(self):
    return self._FindGCloud()

  def _FindGCloud(self):
    """Find a gcloud binary path if available.

    Returns:
      A gcloud binary path. None if not available.
    """
    if not self._tried_gcloud:
      self._tried_gcloud = True
      for path in _GCLOUD_PATHS:
        try:
          res = self.Run(['which', path], raise_on_failure=False)
          if res.return_code == 0:
            self._gcloud = path
            break
        except OSError as e:
          logger.debug('Failed to find %s: %s', path, e)
    return self._gcloud

  def IsLocal(self):
    return self._is_local

  def CopyFile(self, local_file_path, remote_file_path):
    """Copy a local file to the command context's host.

    Args:
      local_file_path: a local file path.
      remote_file_path: the remote file path.
    Raises:
      IOError: if the local file doesn't exist
    """
    if not os.path.exists(local_file_path):
      raise IOError('%s doesn\'t exist.' % local_file_path)
    self.Run(['mkdir', '-p', os.path.dirname(remote_file_path)])
    if not self.IsLocal():
      self.wrapped_context.put(local_file_path, remote_file_path)
      return
    if local_file_path != remote_file_path:
      self.Run(['cp', '-rf', local_file_path, remote_file_path])

  def Close(self):
    """Close the context so no more command can run."""
    logger.debug('Close connection to %s.', self.host)
    if self._closed:
      logger.debug('Connection to %s already closed.', self.host)
      return
    self._closed = True
    if not self.IsLocal() and self.wrapped_context:
      # Local wrapped context doesn't support close.
      # And also there is no need to close a local context.
      self.wrapped_context.close()
    self.wrapped_context = None

  def Run(self,
          command,
          sync=True,
          sudo=False,
          raise_on_failure=True,
          env=None,
          timeout=None):
    """Run a command in context.

    Args:
        command: the command to run, a list of string args.
        sync: run the command sync or async
        sudo: run as sudo
        raise_on_failure: raise Exception on failure or not.
        env: additional environment variables.
        timeout: int, the timeout to run the command, in seconds.
    Returns:
        a CommandResult
    Raises:
        CommandContextClosedError: run command on a closed context.
    """
    if self._closed:
      raise CommandContextClosedError('%s is already closed' % self.host)
    run_config = CommandRunConfig(
        sudo=sudo, raise_on_failure=raise_on_failure, env=env, timeout=timeout)
    if not sync:
      CommandThread(self, command, run_config).start()
      return None
    if self.wrapped_context:
      return self._RunOnWrappedContext(command, run_config)
    return self._RunDirectly(command, run_config)

  def _RunOnWrappedContext(self, command, run_config):
    """Run the command on a wrapped invoke.context.

    Args:
      command: a list of string.
      run_config: CommandRunConfig that config how to run the command.
    Returns:
      a CommandResult
    Raises:
      RuntimeError: failed to run command and raise_on_failure is true.
    """
    run_kwargs = {}
    # Instead of raise by fabric, we should raise by ourself.
    # Raise by fabric the output is hard to control.
    run_kwargs['warn'] = True
    if run_config.env:
      run_kwargs['env'] = run_config.env
    if isinstance(run_config.timeout, int):
      run_kwargs['timeout'] = run_config.timeout
    if self._out_stream:
      run_kwargs['out_stream'] = self._out_stream
      run_kwargs['err_stream'] = self._out_stream
    if self._err_stream:
      run_kwargs['err_stream'] = self._err_stream
    command_str = u' '.join([pipes.quote(token) for token in command])
    res = None
    try:
      if run_config.sudo:
        res = self.remote_sudo_wrapped_context.sudo(
            command_str, password=self._sudo_password, **run_kwargs)
      else:
        res = self.wrapped_context.run(command_str, **run_kwargs)
    except invoke.exceptions.CommandTimedOut as err:
      logger.warn('The command <%s> fails to execute within given time <%s s>.',
                  command_str, run_kwargs['timeout'])
      return CommandResult(
          return_code=err.result.exited, stdout='', stderr=str(err))

    if run_config.raise_on_failure and res.return_code != 0:
      raise RuntimeError(
          'command returned %s: stdout=%s, stderr=%s' % (
              res.return_code, res.stdout, res.stderr))
    return CommandResult(
        return_code=res.return_code,
        stdout=res.stdout,
        stderr=res.stderr)

  def _RunDirectly(self, command, run_config):
    """Run the command on a wrapped invoke.context.

    Args:
      command: a list of string.
      run_config: CommandRunConfig that config how to run the command.
    Returns:
      a CommandResult.
    Raises:
      RuntimeError: failed to run command and raise_on_failure=True
    """
    if run_config.sudo:
      command = ['sudo'] + command
    logger.debug('Running command: %s', command)
    kwargs = {}
    if not run_config.raise_on_failure:
      kwargs['stdout'] = subprocess.PIPE
      kwargs['stderr'] = subprocess.PIPE
    if run_config.env:
      kwargs['env'] = dict(os.environ, **run_config.env)
    start_time = time.time()
    # TODO: apply timeout once subprocess supports in python3.
    proc = subprocess.Popen(command, **kwargs)
    stdout, stderr = proc.communicate()
    stdout = six.ensure_str(stdout) if stdout else None
    stderr = six.ensure_str(stderr) if stderr else None
    logger.debug(
        'Finished running command (took %.1fs): '
        'result=%s, stdout=%s, stderr=%s',
        time.time() - start_time, proc.returncode, stdout, stderr)
    if proc.returncode and run_config.raise_on_failure:
      raise RuntimeError(
          'command returned %s: stdout=%s, stderr=%s' % (
              proc.returncode, stdout, stderr))
    return CommandResult(
        return_code=proc.returncode, stdout=stdout, stderr=stderr)


class CommandThread(threading.Thread):
  """Command thread for async run."""

  def __init__(self, command_context, command, run_config):
    super(CommandThread, self).__init__()
    self.command_context = command_context
    self.command = command
    self.run_config = run_config
    self.daemon = True

  def run(self):      self.command_context.Run(
        self.command, sync=True, **self.run_config._asdict())


class DockerContext(object):
  """Docker command context."""

  def __init__(self, command_context, login=True,
               service_account_json_key_path=None):
    self._context = command_context
    self._docker_client_version = None
    self._CheckDocker()
    if login:
      self._DockerLogin(service_account_json_key_path)

  def _DockerLogin(self, service_account_json_key_path):
    """Login docker server."""
    if service_account_json_key_path:
      credential = google_auth_util.CreateCredentialFromServiceAccount(
          service_account_json_key_path=service_account_json_key_path,
          scopes=[google_auth_util.GCS_READ_SCOPE])
      self._context.Run(
          ['docker',
           'login',
           '-u', 'oauth2accesstoken',
           '-p', credential.token,
           _DOCKER_SERVER],
          raise_on_failure=False)
      return
    if self._context.gcloud:
      self._context.Run(
          [self._context.gcloud, 'auth', 'configure-docker', '--quiet'],
          raise_on_failure=False)
      logger.info('gcloud auth configure-docker')
      return
    logger.warn('No gcloud or service account json key file, can not login %s.',
                _DOCKER_SERVER)

  def _CheckDocker(self):
    """Check if docker is installed."""
    try:
      res = self._context.Run(['docker', '-v'], raise_on_failure=False)
    except OSError as e:
      logger.info('Failed to execute docker: %s', e)
      res = None
    if not res or res.return_code:
      raise DockerNotFoundError('Failed to run docker: res=%s' % res)

  def Run(self, command, **kwargs):
    """Run docker command. It's a wrap for context.run.

    Args:
      command: a str
      **kwargs: key value args
    Returns:
      invoke.runners.Result
    """
    args = ['docker']
    return self._context.Run(args + command, **kwargs)


class DockerHelper(object):
  """Helper to operate docker."""

  def __init__(self, docker_context, image_name=None):
    self._docker_context = docker_context
    self._image_name = image_name
    self._env = []
    self._binds = []
    self._volumes = []
    self._tmpfss = []
    self._ports = []
    self._files = []

  def Build(self, path, build_args=None):
    """Build the docker image from given path.

    Args:
      path: the path which include DockerFile to build.
      build_args: build args to pass to Docker build command.
    """
    args = ['build', '-t', self._image_name]
    for build_arg in build_args or []:
      args.extend(['--build-arg', build_arg])
    args.append(path)
    self._docker_context.Run(args)

  def Push(self):
    """Push the docker image to remote repository."""
    self._docker_context.Run(['push', self._image_name])

  def Pull(self):
    """Pull the docker image from remote repository."""
    logger.info('Pulling %s from remote repository.',
                self._image_name)
    self._docker_context.Run(['pull', self._image_name])

  def AddEnv(self, key, value):
    """Add environment to inject into the docker container.

    Args:
      key: environement variable's key
      value: environement variable's value
    """
    self._env.append((key, value))

  def CopyEnv(self, key):
    """Copy an environment variable from the current environment if exists.

    Args:
      key: an environment variable name.
    """
    value = os.environ.get(key)
    if value is not None:
      self.AddEnv(key, value)

  def AddVolume(self, volume_name, dst):
    """Create a volume to mount to docker container.

    Args:
      volume_name: volume name
      dst: the path to mount inside docker container.
    """
    self._volumes.append((volume_name, dst))

  def AddTmpfs(self, path, size=_DEFAULT_TMPFS_SIZE_IN_BYTES, mode=None):
    """Mount a tmpfs in the container.

    The mode is the linux file mode, for example 750 is for owner can read,
    write and execute, group can read and execute but no write and other has
    no access.

    Args:
      path: the destination path in container.
      size: the size of the tmpfs size in bytes.
      mode: the linux file mode of the tmpfs.
    """
    self._tmpfss.append((path, size, mode))

  def AddBind(self, src, dst):
    """Mount file/dir on the local host to the docker container.

    Args:
      src: local file path
      dst: the path to mount inside docker container.
    """
    self._binds.append((src, dst))

  def AddPort(self, local_port, docker_port):
    """Map local port to docker port.

    Args:
      local_port: local port
      docker_port: the docker port that the local port map to.
    """
    self._ports.append((local_port, docker_port))

  def AddFile(self, local_path, docker_path):
    """Copy a file to the docker container.

    Args:
      local_path: local file path
      docker_path: docker file path to copy to
    """
    self._files.append((local_path, docker_path))

  def Run(self, container_name):
    """Start a container with the docker images.

    Args:
      container_name: the container name to use when start the container.
    Returns:
      CommandResult
    """
    # Remove existing container if necessary
    self._docker_context.Run(['container', 'rm', container_name],
                             raise_on_failure=False)

    # Create new container
    args = [
        'create',
        '--name', container_name,
        '-it',
        '-v', '/etc/localtime:/etc/localtime:ro',  # Sync localtime
        '-v', '/etc/timezone:/etc/timezone:ro',  # Sync timezone
        '-v', '/dev/bus/usb:/dev/bus/usb',  # Mount USB devices
        '-v', '/run/udev/control:/run/udev/control',  # Receive udev events
        '--device-cgroup-rule', 'c 189:* rwm',  # Grant access to USB devices
        '--net=host',  # Allow the container to share host network.
        '--cap-add', 'syslog',  # Enables host system logs (e.g. dmesg) access
    ]
    for key, value in self._env:
      args.extend(['-e', '%s=%s' % (key, value)])
    for volume_name, dst in self._volumes:
      args.extend(['--mount', 'type=volume,src=%s,dst=%s' % (volume_name, dst)])
    for src, dst in self._binds:
      args.extend(['--mount', 'type=bind,src=%s,dst=%s' % (src, dst)])
    for path, size, mode in self._tmpfss:
      tmpfs_arg = 'type=tmpfs,dst=%s' % path
      if size:
        tmpfs_arg += ',tmpfs-size=%s' % size
      if mode:
        tmpfs_arg += ',tmpfs-mode=%s' % mode
      args.extend(['--mount', tmpfs_arg])
    for local_port, docker_port in self._ports:
      args.extend(['-p', '%r:%r' % (local_port, docker_port)])
    args.append(self._image_name)
    self._docker_context.Run(args)

    # Copy additional files
    for local_path, docker_path in self._files:
      self._docker_context.Run(['cp', '-L', local_path,
                                '%s:%s' % (container_name, docker_path)])

    # Start container
    return self._docker_context.Run(['start', container_name])

  def Stop(self, container_names):
    """Stop the given containers.

    Args:
      container_names: a list of container_names to stop
    Returns:
      the CommandResult
    """
    return self._docker_context.Run(
        ['stop'] + container_names, timeout=_DOCKER_STOP_CMD_TIMEOUT_SEC)

  def Kill(self, container_names, signal):
    """Send a signal to container with kill command.

    Args:
      container_names: a list of container_names to stop
      signal: the signal send to the container.
    Returns:
      the CommandResult
    """
    return self._docker_context.Run(
        ['kill', '-s', signal] + container_names,
        timeout=_DOCKER_KILL_CMD_TIMEOUT_SEC)

  def Wait(self, container_names):
    """Wait the containers to stop.

    Args:
      container_names: a list of container_names to stop
    Returns:
      the CommandResult
    """
    return self._docker_context.Run(
        ['container', 'wait'] + container_names,
        timeout=_DOCKER_WAIT_CMD_TIMEOUT_SEC)

  def Inspect(self, resource_name, output_format=None, raise_on_failure=False):
    """Inspect the given resource (image or container).

    Args:
      resource_name: the name of resource to inspect.
      output_format: --format value of inspect command.
      raise_on_failure: raise on failure or not.
    Returns:
      CommandResult
    """
    cmd = ['inspect', resource_name]
    if output_format:
      cmd.extend(['--format', output_format])
    return self._docker_context.Run(cmd, raise_on_failure=raise_on_failure)

  def GetRemoteImageDigest(self, image_id_or_name):
    """Get image's remote image digest."""
    res = self.Inspect(
        image_id_or_name, output_format=_REMOTE_IMAGE_DIGEST_FORMAT,
        raise_on_failure=True)
    return res.stdout.strip()

  def GetImageIdForContainer(self, container_name):
    """Get container's image id."""
    res = self.Inspect(
        container_name, output_format=_IMAGE_ID_FORMAT,
        raise_on_failure=True)
    return res.stdout.strip()

  def GetProcessIdForContainer(self, container_name):
    """Get container's process id."""
    res = self.Inspect(
        container_name,
        output_format=_CONTAINER_PID_FORMAT,
        raise_on_failure=True)
    return res.stdout.strip()

  def CleanupDanglingImages(self):
    """Clean up dangling docker images.

    Returns:
      An instance of CommandResult.
    """
    logging.info('Cleaning up dangling docker images...')
    return self._docker_context.Run(
        ['image', 'prune', '-f', '--filter', '"until=240h"'],
        raise_on_failure=False)

  def IsContainerRunning(self, container_name):
    """Check if container is running or not."""
    res = self.Inspect(container_name, output_format=_CONTAINER_STATUS_FORMAT)
    if res.return_code != 0:
      if _NO_SUCH_OBJECT_ERROR in res.stderr:
        logger.debug('No container %s.', container_name)
        return False
      raise DockerError(
          'Failed to inpect %s:\nstderr:%s\nstdout:%s.' % (
              container_name, res.stderr, res.stdout))
    return res.stdout.strip() == _CONTAINER_RUNNING_STATUS

  def RemoveContainers(self, container_names, raise_on_failure=True):
    """Remove given containers.

    Args:
        container_names: a list of container names to remove.
        raise_on_failure: raise an exception if an operation fails.
    Returns:
      the CommandResult
    """
    return self._docker_context.Run(
        ['container', 'rm'] + container_names,
        raise_on_failure=raise_on_failure)

  def RemoveVolumes(self, volume_names, raise_on_failure=False):
    """Remove given volumes.

    Args:
        volume_names: a list of volume names to remove.
        raise_on_failure: raise an exception if an operation fails.
    Returns:
      the CommandResult
    """
    return self._docker_context.Run(
        ['volume', 'rm'] + volume_names, raise_on_failure=raise_on_failure)
