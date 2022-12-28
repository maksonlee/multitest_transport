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

"""A package management CLI for MTT.

This tool is supposed to be bootstrapped by 'mtt' script and expects the current
working directory to be the root of MTT package.
"""
import argparse
import json
import logging
import os
import os.path
import re
import shlex
import shutil
import socket
import sys
import tempfile
import time
import urllib.parse
import zipfile
from packaging import version
import six

from multitest_transport.cli import cli_util
from multitest_transport.cli import command_util
from multitest_transport.cli import google_auth_util
from multitest_transport.cli import host_util
from tradefed_cluster.configs import lab_config_pb2

_MTT_CONTAINER_NAME = 'mtt'
# The port must be consistent with those in init.sh and serve.sh.
_MTT_CONTROL_SERVER_PORT = 8000
_MTT_SERVER_WAIT_TIME_SECONDS = 300  # 5min
_MTT_SERVER_LOG_PATH = '/data/log/server/current'

_MTT_LIB_DIR = '/var/lib/mtt'
_MTT_LOG_DIR = '/var/log/mtt'
_TMP_DIR = '/tmp'
_KEY_FILE = os.path.join(_MTT_LIB_DIR, 'keyfile', 'key.json')
_DOCKER_KEY_FILE = os.path.join(_TMP_DIR, 'keyfile', 'key.json')
# Permanent MTT binary path has to match the one in mttd.service file.
_MTT_BINARY = os.path.join(_MTT_LIB_DIR, 'mtt')
_HOST_CONFIG = os.path.join(_MTT_LIB_DIR, 'mtt_host_config.yaml')
_ZIPPED_MTTD_FILE = 'multitest_transport/mttd.service'
_MTTD_FILE = '/etc/systemd/system/mttd.service'
_CONFIG_ROOT = 'config'
_VERSION_FILE = 'VERSION'
_UNKNOWN_VERSION = 'unknown'
_DAEMON_UPDATE_INTERVAL_SEC = 60
_ADB_SERVER_PORT = 5037
# Docker networking arguments.
_DOCKER_BRIDGE_NETWORK = 'bridge'
_DOCKER_HOST_NETWORK = 'host'
# The device nodes required by local virtual devices.
_LOCAL_VIRTUAL_DEVICE_NODES = ('/dev/kvm', '/dev/vhost-vsock', '/dev/net/tun',
                               '/dev/vhost-net')

# Tradefed accept TSTP signal as 'quit', which will wait all running tests
# to finish.
_TF_QUIT = 'TSTP'
# Tradefed accept TERM signal as 'kill', which will kill all tests.
_TF_KILL = 'TERM'
# The long wait time for MTT docker container shutdown (graceful shutdown)
_LONG_CONTAINER_SHUTDOWN_TIMEOUT_SEC = 60 * 60
# The short wait time for MTT docker container shutdown (force shutdown)
_SHORT_CONTAINER_SHUTDOWN_TIMEOUT_SEC = 10 * 60
# The waiting interval to check mtt container liveliness
_DETECT_INTERVAL_SEC = 30
# The dict key name of test harness image from host metadata
_TEST_HARNESS_IMAGE_KEY = 'testHarnessImage'
# The dict key name of "allow_to_update" from host metadata
_ALLOW_TO_UPDATE_KEY = 'allowToUpdate'

# Success indicator once tradefed console started, should match to the println
# string in startConsole() method after console.start();
# in tools/tradefederation/core/src/com/android/tradefed/command/Console.java
_TF_CONSOLE_SUCCESS_INDICATOR = 'help all'
# command for check log: "docker logs mtt"
_DOCKER_LOGS_MTT_COMMAND = ['logs', 'mtt']
# interval in second for checking out the logs
_LOG_INQUIRE_INTERVAL_SEC = 5

_PRIVATE_KEY_ID_KEY = 'private_key_id'

PACKAGE_LOGGER_NAME = 'multitest_transport.cli'
logger = logging.getLogger(__name__)

_CRASH_REPORT_FILE_PATH = '/data/.crash_report_file'


class ActionableError(Exception):
  """Errors which can be corrected by user actions."""

  def __init__(self, message):
    super().__init__()
    self.message = message


def _WaitForServer(url, timeout):
  """Wait for a server to be ready.

  Args:
    url: a server url.
    timeout: max wait time.
  Returns:
    True if the service is ready. Otherwise False.
  """
  end_time = time.time() + timeout
  while True:
    remaining_time = end_time - time.time()
    if remaining_time <= 0:
      break
    try:
      six.moves.urllib.request.urlopen(url, timeout=remaining_time)
      return True
    except (socket.error, six.moves.urllib.error.URLError):
      time.sleep(0.1)
  return False


def _HasSudoAccess():
  """Check if the current process has sudo access."""
  return os.geteuid() == 0


def _GetDockerImageName(image_name, tag=None):
  """Get a Docker image name to use.

  Args:
    image_name: an image name.
    tag: an image tag (optional).
  Returns:
    a Docker image name.
  """
  if tag:
    image_name = image_name.split(':', 2)[0] + ':' + tag
  return image_name


def _GetMttServerPublicPorts(control_server_port):
  """Get the ports that the container should publish.

  The ports must be consistent with those in init.sh and serve.sh.

  Args:
    control_server_port: the control server port on the host.

  Returns:
    tuple of ports.
  """
  return (
      control_server_port,
      # TODO: Remove legacy FILE_BROWSER_PORT after a few releases.
      control_server_port + 5,  # FILE_BROWSER_PORT (backwards compatibility)
      control_server_port + 6,  # FILE_SERVER_PORT
  )


def _GetAdbVersion():
  """Determine the current adb version."""
  output = os.popen('adb version').read()
  match = re.search('Version (.*)\n', output)
  return match.group(1) if match else 'UNKNOWN'


def _IsDaemonActive(host):
  """Check if the mttd daemon process is active or not.

  Args:
    host: an instance of host_util.Host.

  Returns:
    Bool, True if the daemon is now active, otherwise False.
  """
  cmd_result = host.context.Run(['systemctl', 'status', 'mttd.service'],
                                raise_on_failure=False)
  return cmd_result.return_code == 0


def _SetupSystemdScript(args, host):
  """Setup the mttd systemd script on host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.

  Raises:
    zipfile.BadZipfile exception, when the zip file is bad.
    KeyError, when the mttd file does not exist in the zip.
  """
  logger.info('Setting up MTT systemd daemon script on %s', host.name)
  tmp_folder = tempfile.mkdtemp()
  try:
    with zipfile.ZipFile(args.cli_path, 'r') as cli_zip:
      mttd_path = cli_zip.extract(_ZIPPED_MTTD_FILE, tmp_folder)
  except zipfile.BadZipfile:
    logger.error('%s is not a zip file.', args.cli_path)
    raise
  except KeyError:
    logger.error('No %s in %s.', _ZIPPED_MTTD_FILE, args.cli_path)
    raise
  else:
    host.context.CopyFile(mttd_path, _MTTD_FILE)
    host.context.Run(['systemctl', 'daemon-reload'])
  finally:
    if tmp_folder:
      shutil.rmtree(tmp_folder)
  # Create a log folder for MTT system daemon.
  host.context.Run(['mkdir', '-p', _MTT_LOG_DIR])


def _SetupMTTRuntimeIntoLibPath(args, host):
  """Setup the mtt runtime files in a permanent directory on host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  host.context.CopyFile(args.cli_path, _MTT_BINARY)
  if host.config.service_account_json_key_path:
    host.context.CopyFile(
        host.config.service_account_json_key_path, _KEY_FILE)
    host.config = host.config.SetServiceAccountJsonKeyPath(_KEY_FILE)
  host.config.Save(_HOST_CONFIG)


def _GetHostTimezone():
  """Get a host timezone.

  Returns:
    A TZ name of a host timezone.
  """
  with open('/etc/timezone') as f:
    return f.read().strip()


def _CheckMttNodePrerequisites(args, host):
  """Check whether the host is set up for mtt.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.

  Raises:
    ActionableError: if any prerequisite is not met.
  """
  messages = []
  # Make sure that no adb server is running on the host.
  if not args.use_host_adb:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as adb_socket:
        adb_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        adb_socket.bind(('127.0.0.1', args.adb_server_port))
    except OSError:
      messages.append('Adb server port %d is not available. If adb is running, '
                      'please run `adb kill-server` and try again.' %
                      args.adb_server_port)
  # Check the device nodes required by local virtual devices.
  if ((args.max_local_virtual_devices or
       host.config.max_local_virtual_devices) and
      not all(os.path.exists(path) for path in _LOCAL_VIRTUAL_DEVICE_NODES)):
    messages.append('Some required device nodes are missing. '
                    'Try `sudo modprobe -a kvm tun vhost_net vhost_vsock`.')
  if messages:
    raise ActionableError('\n'.join(messages))


def _CheckDockerImageVersion(docker_helper, container_name):
  """Check a Docker image is compatible with CLI.

  Args:
    docker_helper: a command_util.DockerHelper object.
    container_name: a container name.
  Raises:
    ActionableError: if a Docker image is newer than CLI.
  """
  res = docker_helper.Exec(container_name, ['printenv', 'MTT_VERSION'])
  cli_version, _ = cli_util.GetVersion()
  image_version = res.stdout
  if (not cli_version or '_' not in cli_version or
      not image_version or '_' not in image_version):
    logger.debug(
        'CLI or Docker image version is unrecognizable; '
        'skipping version check: cli_version=%s, image_version=%s',
        cli_version, image_version)
    return
  cli_build_env, cli_version = cli_version.strip().split('_', 1)
  image_build_env, image_version = image_version.strip().split('_', 1)
  if cli_build_env != image_build_env:
    logger.warning(
        'CLI and Docker image are from different release channels; '
        'proceed with cautions (%s != %s)',
        cli_build_env, image_build_env)
    return

  try:
    cli_version_obj = version.parse(cli_version)
    image_version_obj = version.parse(image_version)
  except version.InvalidVersion:
    logger.debug(
        'CLI or Docker image version is unrecognizable; '
        'skipping version check: cli_version=%s, image_version=%s', cli_version,
        image_version)
    return

  if cli_version_obj < image_version_obj:
    # Stop a started container.
    docker_helper.Stop([container_name])
    raise ActionableError(
        'CLI is older than Docker image; please update CLI to a newer version'
        '(%s < %s)' % (cli_version, image_version))


def _IsTfConsoleSuccessfullyStarted(host):
  """Check is TF console started successfully.

  Args:
    host: an instance of host_util.Host.
  Returns:
    True if find the TF console success indicator in docker logs.
  Raises:
    RuntimeError: if exceptions detected in docker logs.
  """
  docker_context = command_util.DockerContext(host.context, login=False)
  end_time = time.time() + _MTT_SERVER_WAIT_TIME_SECONDS
  while time.time() <= end_time:
    remaining_time = int(end_time - time.time())
    docker_context.RequestTfConsolePrintOut()
    command_result = docker_context.Run(_DOCKER_LOGS_MTT_COMMAND,
                                        timeout=remaining_time)
    docker_log = command_result.stderr + '\n' + command_result.stdout

    if _TF_CONSOLE_SUCCESS_INDICATOR in command_result.stdout:
      return True
    elif 'exception' in docker_log.lower():
      raise RuntimeError(
          f'Tradefed failed to start with exception:\n{docker_log}')
    time.sleep(_LOG_INQUIRE_INTERVAL_SEC)
  # when timeout
  raise RuntimeError(
      'ATS replica failed to start in %ss' % _MTT_SERVER_WAIT_TIME_SECONDS)


def Start(args, host=None):
  """Execute 'mtt start [OPTION] ...' on local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.

  Raises:
    RuntimeError: if a MTT node fails to start.
  """
  host = host or host_util.CreateHost(args)
  if host.config.enable_autoupdate:
    _StartMttDaemon(args, host)
    return
  if host.config.enable_ui_update:
    host.control_server_client.PatchTestHarnessImageToHostMetadata(
        host.config.hostname, host.config.docker_image)
    _StartMttDaemon(args, host)
    return
  _StartMttNode(args, host)


def _StartMttNode(args, host):
  """Start MTT node on local hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  Raises:
    ActionableError: if a MTT node fails to start due to user errors.
    RuntimeError: if a MTT node fails to start.
  """
  host.control_server_client.SubmitHostUpdateStateChangedEvent(
      host.config.hostname, host_util.HostUpdateState.RESTARTING,
      target_image=host.config.docker_image)
  control_server_url = args.control_server_url or host.config.control_server_url
  control_file_server_url = args.control_file_server_url
  operation_mode = lab_config_pb2.OperationMode.Value(args.operation_mode)
  if operation_mode == lab_config_pb2.OperationMode.UNKNOWN and host.config.operation_mode:
    # Override operation mode if arg value is UNKNOWN and host has config.
    operation_mode = host.config.operation_mode
  image_name = _GetDockerImageName(
      args.image_name or host.config.docker_image, tag=args.tag)
  docker_server = args.docker_server or host.config.docker_server
  logger.info('Using image %s.', image_name)
  docker_context = command_util.DockerContext(
      host.context,
      docker_server=docker_server,
      service_account_json_key_path=host.config.service_account_json_key_path)
  docker_helper = command_util.DockerHelper(docker_context, image_name)

  if docker_helper.IsContainerRunning(args.name):
    logger.error('MTT is already running.')
    return

  _CheckMttNodePrerequisites(args, host)

  if args.force_update or not docker_helper.DoesResourceExist(image_name):
    docker_helper.Pull()

  # Enable FUSE
  docker_helper.AddDeviceNode('/dev/fuse')
  docker_helper.AddCapability('sys_admin')
  docker_helper.AddExtraArgs(['--security-opt', 'apparmor:unconfined'])

  if (not args.use_host_network and
      'MTT_SUPPORT_BRIDGE_NETWORK=true' in docker_helper.GetEnv(image_name)):
    docker_helper.SetHostname(host.name)
    network = _DOCKER_BRIDGE_NETWORK
  else:
    network = _DOCKER_HOST_NETWORK
  docker_helper.SetNetwork(network)

  docker_helper.AddEnv(
      'OPERATION_MODE',
      lab_config_pb2.OperationMode.Name(operation_mode).lower())
  docker_helper.AddEnv('MTT_CLI_VERSION', cli_util.GetVersion()[0])

  if control_server_url:
    docker_helper.AddEnv('MTT_CONTROL_SERVER_URL', control_server_url)
    u = urllib.parse.urlparse(control_server_url)
    if not control_file_server_url and u.hostname and u.port:
      # Set default value for control file server url
      control_file_server_url = u._replace(netloc=u.hostname + ':' +
                                           str(u.port + 6)).geturl()
    if control_file_server_url:
      docker_helper.AddEnv('MTT_CONTROL_FILE_SERVER_URL',
                           control_file_server_url)
  else:
    logger.info(
        'The control_server_url is not set; starting a standalone node.')
  # TODO: Use config to differentiate worker and controller.
  if (control_server_url and operation_mode
      == lab_config_pb2.OperationMode.ON_PREMISE) or not control_server_url:
    docker_helper.AddEnv('MTT_CONTROL_SERVER_PORT', args.port)
    if network == _DOCKER_BRIDGE_NETWORK:
      for port in _GetMttServerPublicPorts(args.port):
        # The server binds to IPv4 addresses only.
        docker_helper.AddPort('0.0.0.0:%d' % port, port)
      if not control_server_url:
        # Public Netdata port
        docker_helper.AddPort('0.0.0.0:%d' % (args.port + 8), args.port + 8)
  if host.config.lab_name:
    docker_helper.AddEnv('LAB_NAME', host.config.lab_name)
  if host.config.cluster_name:
    docker_helper.AddEnv('CLUSTER', host.config.cluster_name)
  docker_helper.AddEnv('IMAGE_NAME', image_name)

  if host.config.tf_global_config_path:
    docker_helper.AddEnv(
        'TF_GLOBAL_CONFIG_PATH',
        host.config.tf_global_config_path)

  docker_helper.AddEnv('USER', os.environ.get('USER'))
  docker_helper.AddEnv('TZ', _GetHostTimezone())

  # Copy proxy settings if exists.
  http_proxy = docker_helper.CopyEnv('HTTP_PROXY', ['http_proxy'])
  docker_helper.CopyEnv('HTTPS_PROXY', ['https_proxy'])
  docker_helper.CopyEnv('FTP_PROXY', ['ftp_proxy'])
  no_proxy = os.environ.get('NO_PROXY', os.environ.get('no_proxy'))
  if http_proxy or no_proxy:
    # Add localhost to NO_PROXY. This enables in-server API calls.
    no_proxy_list = ['127.0.0.1', '::1', 'localhost', host.name]
    if no_proxy:
      no_proxy_list.append(no_proxy)
    no_proxy = ','.join(no_proxy_list)
    os.environ['NO_PROXY'] = no_proxy
    logger.debug('NO_PROXY=%s', no_proxy)
    docker_helper.AddEnv('NO_PROXY', no_proxy)

  if host.context.IsLocal():
    android_sdk_path = os.path.expanduser('~/.android')
    if os.path.exists(android_sdk_path):
      # If running locally, bind ~/.android to access existing adb fingerprints.
      docker_helper.AddBind(android_sdk_path, '/root/.android')

  docker_helper.AddVolume('mtt-data', '/data')
  docker_helper.RemoveVolumes(['mtt-temp'])
  docker_helper.AddVolume('mtt-temp', '/tmp')
  docker_helper.AddBind('/var/run/docker.sock', '/var/run/docker.sock')

  if host.config.service_account_json_key_path:
    docker_helper.AddVolume('mtt-key', os.path.dirname(_DOCKER_KEY_FILE))
    docker_helper.AddFile(
        host.config.service_account_json_key_path, _DOCKER_KEY_FILE)
    docker_helper.AddEnv('JSON_KEY_PATH', _DOCKER_KEY_FILE)
  if host.config.enable_stackdriver:
    if host.config.service_account_json_key_path:
      docker_helper.AddEnv('ENABLE_STACKDRIVER_LOGGING', 1)
      docker_helper.AddEnv('ENABLE_STACKDRIVER_MONITORING', 1)
    else:
      logger.error(
          'Set "service_account_json_key_path" in lab config or command-line'
          'args to enable stackdriver.')

  for tmpfs_config in host.config.tmpfs_configs:
    docker_helper.AddTmpfs(
        tmpfs_config.path, size=tmpfs_config.size, mode=tmpfs_config.mode)

  extra_docker_args = (host.config.extra_docker_args +
                       (args.extra_docker_args or []))
  if extra_docker_args:
    # Use shlex.split to properly remove quotes.
    extra_docker_args = shlex.split(' '.join(extra_docker_args))
    logger.debug('Add extra docker args: %s', extra_docker_args)
    docker_helper.AddExtraArgs(extra_docker_args)

  # Create user file store if necessary, and then mount it and any additional
  # paths in the temporary volume. These files and directories will be linked
  # into the local file store.
  user_file_store = os.path.expanduser('~/.ats_storage')
  host.context.Run(['mkdir', '-p', user_file_store])
  mount_paths = [user_file_store]
  mount_paths.extend(args.mount_local_path or [])
  for mount_path in mount_paths:
    local_path, remote_path = (mount_path.split(':', 1) + [None])[:2]
    if not remote_path:
      remote_path = os.path.basename(local_path)
    remote_path = os.path.normpath('/tmp/.mnt/' + remote_path)
    logger.debug('Mounting \'%s\' to \'%s\'', local_path, remote_path)
    docker_helper.AddBind(local_path, remote_path)

  docker_helper.AddEnv('MTT_SERVER_LOG_LEVEL', args.server_log_level)

  enable_ipv6_bridge_network = False
  if network == _DOCKER_BRIDGE_NETWORK:
    network_info = docker_helper.GetBridgeNetworkInfo()
    if network_info.IsIPv6Enabled():
      enable_ipv6_bridge_network = True
      ipv6_subnet, _ = network_info.GetIPv6Subnet()
      if not ipv6_subnet:
        raise ActionableError('Cannot get IPv6 subnet of bridge network. '
                              'Please check fixed-cidr-v6 in '
                              '/etc/docker/daemon.json and restart docker '
                              'daemon.')
      docker_helper.AddEnv('IPV6_BRIDGE_NETWORK', ipv6_subnet)

    if args.use_host_adb:
      docker_helper.AddEnv('MTT_USE_HOST_ADB', '1')
      _, host_ip = network_info.GetIPv4Subnet()
      if not host_ip:
        raise ActionableError('Cannot get IPv4 gateway of bridge network. '
                              'Please check /etc/docker/daemon.json and '
                              'restart docker daemon.')
      logger.info(
          'Using host ADB; please forward %s:5037 to ADB server port '
          '(e.g. run "socat tcp-listen:5037,bind=%s,reuseaddr,fork tcp-connect:127.0.0.1:5037 &")',
          host_ip, host_ip)
    else:
      docker_helper.AddPort(
          '127.0.0.1:%d' % args.adb_server_port, _ADB_SERVER_PORT)

  custom_sdk_dir = None
  if args.custom_adb_path:
    # Create temp directory for custom SDK tools, will be copied over to ensure
    # MTT has access, and will be cleaned up on next start
    custom_sdk_dir = tempfile.mkdtemp()
    docker_helper.AddFile(custom_sdk_dir, '/tmp/custom_sdk_tools')
    # TODO: support GCS files
    shutil.copy(args.custom_adb_path, '%s/adb' % custom_sdk_dir)

  max_local_virtual_devices = args.max_local_virtual_devices
  if max_local_virtual_devices == 0 and host.config.max_local_virtual_devices:
    max_local_virtual_devices = host.config.max_local_virtual_devices
  if max_local_virtual_devices:
    docker_helper.AddEnv('MAX_LOCAL_VIRTUAL_DEVICES',
                         str(max_local_virtual_devices))
    # Add the dependency of crosvm and qemu.
    for device_node in _LOCAL_VIRTUAL_DEVICE_NODES:
      docker_helper.AddDeviceNode(device_node)
    # Allow crosvm to control the tun device.
    docker_helper.AddCapability('net_admin')
    # Enable IPv6 for the virtual network interfaces.
    if enable_ipv6_bridge_network:
      docker_helper.AddSysctl('net.ipv6.conf.all.disable_ipv6', '0')
      docker_helper.AddSysctl('net.ipv6.conf.all.forwarding', '1')

  if args.extra_ca_cert:
    docker_helper.AddFile(
        args.extra_ca_cert, '/usr/local/share/ca-certificates/')

  docker_helper.Run(args.name)

  _CheckDockerImageVersion(docker_helper, args.name)

  # Delete temp tools directory
  if custom_sdk_dir:
    shutil.rmtree(custom_sdk_dir)

  hostname = host.name
  if host.context.IsLocal():
    # We change hostname to localhost since
    # MTT's build channel authorization only works when accessed with
    # localhost URL.
    hostname = 'localhost'
  if control_server_url:
    if _IsTfConsoleSuccessfullyStarted(host):
      logger.info('ATS replica is running.')
  else:
    url = 'http://%s:%s' % (hostname, args.port)
    if not _WaitForServer(url, timeout=_MTT_SERVER_WAIT_TIME_SECONDS):
      docker_helper.Logs(args.name)
      docker_helper.Cat(args.name, _MTT_SERVER_LOG_PATH)
      raise RuntimeError(
          'ATS server failed to start in %ss' % _MTT_SERVER_WAIT_TIME_SECONDS)
    logger.info('ATS is serving at %s', url)


def _StartMttDaemon(args, host):
  """Start MTT daemon on local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.

  Raises:
    RuntimeError: when failing to run command on host.
    ActionableError: when root privileges are not granted.
  """
  logger.info('Starting MTT daemon on %s.', host.name)
  if _IsDaemonActive(host):
    logger.warning('MTT daemon is already running on %s.', host.name)
    return
  if not _HasSudoAccess():
    raise ActionableError(
        'The root privileges are required to start MTT daemon. '
        'Please consider run MTT CLI with sudo access. '
        'If you are running MTT Lab CLI, please consider adding flags '
        ' --sudo_user or/and --ask_sudo_password.')
  _SetupMTTRuntimeIntoLibPath(args, host)
  _SetupSystemdScript(args, host)
  # Enable mttd.service, to make sure it can "start" on system reboot.
  # Note: this command will not start the service immediately.
  host.context.Run(['systemctl', 'enable', 'mttd.service'])
  # Start mttd.service immediately.
  host.context.Run(['systemctl', 'start', 'mttd.service'])
  logger.info(('MTT daemon started on %s. '
               'It keeps MTT container up and running on the latest version.'),
              host.name)


def Stop(args, host=None):
  """Execute 'mtt stop [OPTION] ...' on local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  host = host or host_util.CreateHost(args)
  _StopMttDaemon(host)
  _StopMttNode(args, host)


def _StopMttNode(args, host):
  """Stop MTT node on a local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  host.control_server_client.SubmitHostUpdateStateChangedEvent(
      host.config.hostname, host_util.HostUpdateState.SHUTTING_DOWN,
      target_image=host.config.docker_image)
  docker_context = command_util.DockerContext(host.context, login=False)
  docker_helper = command_util.DockerHelper(docker_context)

  # TODO: The kill logic should be more general and works for both
  # mtt and dockerized tf.
  if docker_helper.IsContainerRunning(args.name):
    logger.info('Stopping running container %s.', args.name)

    # Remove crash report file to indicate that the docker container was
    # stopped properly (used to track reliability).
    docker_helper.Exec(args.name, ['rm', '-f', _CRASH_REPORT_FILE_PATH])

    timeout = None
    if host.config.graceful_shutdown or args.wait:
      logger.info('Wait all tests to finish.')
      docker_helper.Kill([args.name], _TF_QUIT)
      timeout = _LONG_CONTAINER_SHUTDOWN_TIMEOUT_SEC
    else:
      # This send "TERM" to TF inside the container.
      logger.info('Send TERM signal to TF. This will stop all running tests.')
      docker_helper.Kill([args.name], _TF_KILL)
      timeout = _SHORT_CONTAINER_SHUTDOWN_TIMEOUT_SEC
    if host.config.shutdown_timeout_sec:
      timeout = host.config.shutdown_timeout_sec
    if _HasSudoAccess():
      _DetectAndKillDeadContainer(host, docker_helper, args.name, timeout)
    else:
      try:
        docker_helper.Wait([args.name], timeout=timeout)
      except command_util.CommandTimeoutError:
        logger.warning(
            'Container is still running after %s seconds; killing...',
            timeout)
        docker_helper.Stop([args.name])
        docker_helper.Wait([args.name])
  logger.info('Container %s stopped.', args.name)
  res_inspect = docker_helper.Inspect(args.name)
  if res_inspect.return_code != 0:
    logger.info('No container %s.', args.name)
    return
  logger.info('Remove container %s.', args.name)
  docker_helper.RemoveContainers([args.name], raise_on_failure=False)


def _DetectAndKillDeadContainer(host, docker_helper, container_name, timeout):
  """Detect a dead MTT container, force kill it when detected or timed out.

  Args:
    host: an instance of host_util.Host.
    docker_helper: an instance of command_util.DockerHelper.
    container_name: string, the name of docker container to kill.
    timeout: seconds to wait before killing a container. Can be
        overidden by host config.
  """
  total_wait_sec = timeout
  logging.debug(
      'Waiting %d sec for docker container shutdown.', total_wait_sec)
  wait_end_sec = time.time() + total_wait_sec
  while time.time() < wait_end_sec:
    if not docker_helper.IsContainerRunning(container_name):
      logging.debug('The docker container %s has shut down already.',
                    container_name)
      return
    if docker_helper.IsContainerDead(container_name):
      logging.debug('The docker container %s is not alive.', container_name)
      _ForceKillMttNode(host, docker_helper, container_name)
      return
    logging.debug('Waiting for docker container <%s> on host <%s> shutdown.',
                  container_name, host.name)
    time.sleep(_DETECT_INTERVAL_SEC)
  logging.info(
      'The container <%s> failed to shutdown within given %ss on host <%s>.',
      container_name, total_wait_sec, host.name)
  _ForceKillMttNode(host, docker_helper, container_name)


def _ForceKillMttNode(host, docker_helper, container_name):
  """Force kill MTT container and its parent process.

  This method guarantees to kill a docker container, and it should be used only
  when "docker kill/stop" does not work, or times out.

  Args:
    host: an instance of host_util.Host.
    docker_helper: an instance of command_util.DockerHelper.
    container_name: string, the name of docker container to kill.
  """
  logger.info('Force killing MTT node on host %s', host.name)
  if not docker_helper.IsContainerRunning(container_name):
    logger.info('The container process does not exist, skipping killing.')
    return
  # Step 1: Find process ID of MTT container.
  mtt_pid = docker_helper.GetProcessIdForContainer(container_name)
  # Step 2: Get the parent process ID of MTT(containerd-shim process ID).
  containerd_pid = host.context.Run(['ps', '-o', 'ppid=', '-p', mtt_pid],
                                    raise_on_failure=True).stdout.strip()
  # Step 3: Kill the parent process of MTT and wait until it exists.
  host.context.Run(['kill', '-9', containerd_pid], raise_on_failure=True)
  docker_helper.Wait([container_name])


def _StopMttDaemon(host):
  """Restart MTT daemon on a local host.

  Args:
    host: an instance of host_util.Host.

  Raises:
    ActionableError: when root privileges are not granted.
  """
  if not _IsDaemonActive(host):
    logger.debug('MTT daemon is not active on %s. Skip daemon stop.', host.name)
    return
  if not _HasSudoAccess():
    raise ActionableError(
        'The root privileges are required to stop MTT daemon. '
        'Please consider run MTT CLI with sudo access. '
        'If you are running MTT Lab CLI, please consider adding flags '
        ' --sudo_user or/and --ask_sudo_password.')
  logger.info('Stopping MTT daemon on %s.', host.name)
  # Stop mttd.service immediately.
  host.context.Run(['systemctl', 'stop', 'mttd.service'])
  # Unregister mttd.service, so that it does not start on system reboot.
  host.context.Run(['systemctl', 'disable', 'mttd.service'])


def _PullUpdate(args, host):
  """Pull the latest version of the image.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  Returns:
    True if container need to be restarted.
    False otherwise.
  """
  if args.force_update:
    logger.info('force_update==True, updating.')
    return True
  if args.image_name:
    host.config = host.config.SetDockerImage(args.image_name)
  image_name = _GetDockerImageName(host.config.docker_image)
  docker_server = args.docker_server or host.config.docker_server
  logger.debug('Using image %s.', image_name)
  docker_context = command_util.DockerContext(
      host.context,
      docker_server=docker_server,
      service_account_json_key_path=host.config.service_account_json_key_path)
  docker_helper = command_util.DockerHelper(docker_context, image_name)
  # docker doesn't provide a command to inspect remote image directly.
  # And to use docker repository http API:
  # https://docs.docker.com/registry/spec/api/, the authenticating will
  # be difficult, especially we have 2 different authentication ways.
  # Here we are checking the remote image is the same as the running container's
  # image or not. Logically the following 2 ways are the same:
  # 1. pull the image, compare the remote image with running container,
  #    update if they are not the same.
  # 2. compare the remote image with runnint container, pull and update
  #    if they are not the same.
  # Here we do 1, since it's much simpler. Pull will be slow when the images
  # are different, but it will be cheap if the images are the same, so there
  # should be no performance concerns.
  docker_helper.Pull()
  if not docker_helper.IsContainerRunning(args.name):
    logger.info('%s is not running, will start %s with %s.',
                args.name, args.name, image_name)
    return True
  logger.info('%s is running.', args.name)
  container_image_id = docker_helper.GetImageIdForContainer(args.name)
  container_image_remote_digest = (
      docker_helper.GetRemoteImageDigest(container_image_id))
  image_remote_digest = docker_helper.GetRemoteImageDigest(image_name)
  if container_image_remote_digest == image_remote_digest:
    logger.info('%s is already using the same image as remote, skip.',
                args.name)
    return False
  if host.config.enable_ui_update or host.config.enable_autoupdate:
    if (host.config.max_concurrent_update_percentage and
        not host.metadata.get(_ALLOW_TO_UPDATE_KEY, False)):
      logger.info(
          'Pending to kick-off the update of currently running container '
          'until getting sign-off from control server, '
          'because max_concurrent_update_percentage was '
          'limited to %d%% in the physical cluster.',
          host.config.max_concurrent_update_percentage)
      return False
  host.control_server_client.SubmitHostUpdateStateChangedEvent(
      host.config.hostname, host_util.HostUpdateState.SYNCING,
      target_image=host.config.docker_image)
  docker_helper.CleanupUnusedImages()
  logger.info(
      '%s != %s, should restart.',
      container_image_remote_digest, image_remote_digest)
  return True


def Update(args, host=None):
  """Execute 'mtt update [OPTION] ...' on the local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  host = host or host_util.CreateHost(args)
  _StopMttDaemon(host)
  if host.config.enable_autoupdate:
    _StartMttDaemon(args, host)
    return
  if host.config.enable_ui_update:
    host.control_server_client.PatchTestHarnessImageToHostMetadata(
        host.config.hostname, host.config.docker_image)
    _StartMttDaemon(args, host)
    return
  _UpdateMttNode(args, host)


def _UpdateMttNode(args, host):
  """Update mtt node on the local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  if not _PullUpdate(args, host):
    return
  logger.info('Restarting %s.', args.name)
  try:
    _StopMttNode(args, host)
    _StartMttNode(args, host)
  except Exception as e:      host.control_server_client.SubmitHostUpdateStateChangedEvent(
        host.config.hostname,
        host_util.HostUpdateState.ERRORED,
        display_message=str(e),
        target_image=host.config.docker_image)
    raise e
  host.control_server_client.SubmitHostUpdateStateChangedEvent(
      host.config.hostname, host_util.HostUpdateState.SUCCEEDED,
      target_image=host.config.docker_image)


def Restart(args, host=None):
  """Execute 'mtt restart [OPTION] ...' on the local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  host = host or host_util.CreateHost(args)
  _StopMttDaemon(host)
  _StopMttNode(args, host)
  if host.config.enable_autoupdate:
    _StartMttDaemon(args, host)
    return
  if host.config.enable_ui_update:
    host.control_server_client.PatchTestHarnessImageToHostMetadata(
        host.config.hostname, host.config.docker_image)
    _StartMttDaemon(args, host)
    return
  _StartMttNode(args, host)


def RunDaemon(args, host=None):
  """Run MTT daemon on the local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  while True:
    _RunDaemonIteration(args, host=host)
    time.sleep(_DAEMON_UPDATE_INTERVAL_SEC)


def _RunDaemonIteration(args, host=None):
  """Run one iteration of daemon task.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  """
  if not args.no_check_update:
    try:
      new_path = cli_util.CheckAndUpdateTool(
          args.cli_path,
          cli_update_url=args.cli_update_url)
      if new_path:
        logger.debug('CLI is updated.')
        os.execv(new_path, [new_path] + sys.argv[1:])
    except Exception as e:        logger.warning('Failed to check/update tool: %s', e)
  host = host or host_util.CreateHost(args)
  if (host.config.secret_project_id and
      host.config.service_account_key_secret_id and
      host.config.service_account_json_key_path):
    _UpdateServiceAccountKeyFile(
        host.config.secret_project_id,
        host.config.service_account_key_secret_id,
        host.config.service_account_json_key_path)
  if host.config.enable_autoupdate:
    logger.debug('Auto-update enabled.')
    _UpdateMttNode(args, host)
    return
  if host.config.enable_ui_update:
    logger.debug('Update from UI enabled.')
    host.metadata = host.control_server_client.GetHostMetadata(
        host.config.hostname)
    test_harness_image = host.metadata.get(_TEST_HARNESS_IMAGE_KEY)
    logger.debug('Refreshed host metadata: %s.', host.metadata)
    if test_harness_image:
      logger.debug('Pinned to image: %s.', test_harness_image)
      host.config = host.config.SetDockerImage(test_harness_image)
    else:
      logger.warning(
          'No test_harness_image is found in HostMetadata, updating with '
          'image from lab config file.')
    _UpdateMttNode(args, host)


def _CreateImageArgParser():
  """Create argparser for docker image relate operations."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--image_name', help='The docker image to use.')
  parser.add_argument('--tag', help='A tag for a new image.')
  return parser


def _CreateContainerArgParser():
  """Create argparser for docker container relate operations."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--name', default=_MTT_CONTAINER_NAME,
                      help='Docker container name.')
  return parser


def _CreateStartArgParser():
  """Create argparser for Start."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--force_update', action='store_true')
  parser.add_argument('--port', type=int, default=_MTT_CONTROL_SERVER_PORT)
  parser.add_argument(
      '--server_log_level',
      help='Server Log level',
      default='info',
      choices=['debug', 'info', 'warn', 'error', 'critical'])
  parser.add_argument(
      '--docker_server',
      help='Docker server to login when using a service account.')
  # TODO: delete service_account_json_key_path arg.
  parser.add_argument(
      '--service_account_json_key_path', help='Service account json key path.')
  parser.add_argument('--custom_adb_path', help='Path to custom ADB tool')
  parser.add_argument(
      '--adb_server_port', type=int,
      help='Adb server port exposed by the container',
      default=_ADB_SERVER_PORT)
  parser.add_argument(
      '--max_local_virtual_devices', type=int, default=0,
      help='Maximum number of virtual devices on local host (experimental).')
  parser.add_argument(
      '--extra_docker_args', action='append',
      help='Extra docker args passing to container.')
  parser.add_argument('--extra_ca_cert', help='Extra CA cert file for SSL.')
  parser.add_argument('--mount_local_path', action='append',
                      help='Additional path to mount in the local file store.')
  parser.add_argument(
      '--use_host_network',
      help='Use host networking for the container.',
      action='store_true')
  parser.add_argument(
      '--use_host_adb',
      help=(
          'Use host ADB server. This is useful when accessing virtual devices '
          'running outside Docker container.'),
      action='store_true')
  parser.add_argument(
      '--operation_mode',
      default=lab_config_pb2.OperationMode.Name(
          lab_config_pb2.OperationMode.UNKNOWN),
      choices=lab_config_pb2.OperationMode.keys(),
      help='Run ATS in a certain operation mode.')
  parser.add_argument(
      '--control_server_url',
      default=None,
      help=('Control server url is required for workers in ON_PREMISE mode.'
            'This field can also be set by yaml config.'))
  parser.add_argument(
      '--control_file_server_url',
      default=None,
      help=(
          'Set in ON_PREMISE mode if file server URL cannot be inferred '
          'from the control server URL.'
      ))
  parser.set_defaults(func=Start)
  return parser


def _CreateStopArgParser():
  """Create argparser for Stop."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--wait', action='store_true')
  parser.set_defaults(func=Stop)
  return parser


def _CreateRestartArgParser():
  """Create argparser for Restart."""
  parser = argparse.ArgumentParser(
      add_help=False, parents=[_CreateStartArgParser(), _CreateStopArgParser()])
  parser.set_defaults(func=Restart)
  return parser


def _CreateUpdateArgParser():
  """Create argparser for Update."""
  parser = argparse.ArgumentParser(
      add_help=False, parents=[_CreateStartArgParser(), _CreateStopArgParser()])
  parser.set_defaults(func=Update)
  return parser


def _CreateDaemonCommandArgParser():
  parser = argparse.ArgumentParser(
      add_help=False, parents=[_CreateUpdateArgParser()])
  parser.set_defaults(func=RunDaemon)
  return parser


def _CreateLabConfigArgParser():
  """Create argparser for lab config path arg."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument(
      'lab_config_path', metavar='lab_config_path', type=str, nargs='?',
      help='Lab config path to use.')
  return parser


def _UpdateServiceAccountKeyFile(
    secret_project_id, secret_id, local_service_account_key_path):
  """Update local service account key path."""
  try:
    with open(local_service_account_key_path) as f:
      local_service_account_key = f.read()
    local_sa_key_dict = json.loads(local_service_account_key)
    # Only read secret when local is old.
    credentials = google_auth_util.CreateCredentialFromServiceAccount(
        local_service_account_key_path, [google_auth_util.AUTH_SCOPE])
    service_account_key = google_auth_util.GetSecret(
        secret_project_id, secret_id, credentials=credentials)
    sa_key_dict = json.loads(service_account_key)
    if (local_sa_key_dict.get(_PRIVATE_KEY_ID_KEY) ==
        sa_key_dict.get(_PRIVATE_KEY_ID_KEY)):
      logger.debug('Local service account key is the same as remote.')
      return False
    logger.debug(
        'Local service account key %s is different from remote %s. Updating %s',
        local_sa_key_dict.get(_PRIVATE_KEY_ID_KEY),
        sa_key_dict.get(_PRIVATE_KEY_ID_KEY),
        local_service_account_key_path)
    with open(local_service_account_key_path, 'w') as f:
      f.write(service_account_key.decode())
    return True
  except Exception:      logger.exception(
        'Fail to update service account key %s.',
        local_service_account_key_path)
    return False


def CreateParser():
  """Creates an argument parser.

  Returns:
    an argparse.ArgumentParser object.
  """
  parser = argparse.ArgumentParser(
      parents=[cli_util.CreateLoggingArgParser(),
               cli_util.CreateCliUpdateArgParser()])
  subparsers = parser.add_subparsers(title='Actions', dest='action')

  # Commands for users
  subparsers.add_parser(
      'start', help='Start a MTT instance on the local host.',
      parents=[_CreateLabConfigArgParser(), _CreateImageArgParser(),
               _CreateContainerArgParser(), _CreateStartArgParser()])
  subparsers.add_parser(
      'stop', help='Stop a MTT instance on the local host.',
      parents=[_CreateLabConfigArgParser(), _CreateContainerArgParser(),
               _CreateStopArgParser()])
  subparsers.add_parser(
      'restart', help='Retart a MTT instance on the local host.',
      parents=[
          _CreateLabConfigArgParser(), _CreateImageArgParser(),
          _CreateContainerArgParser(), _CreateRestartArgParser()])
  subparsers.add_parser(
      'update', help='Update a MTT instance on the local host.',
      parents=[
          _CreateLabConfigArgParser(), _CreateImageArgParser(),
          _CreateContainerArgParser(), _CreateUpdateArgParser()])
  subparsers.add_parser(
      'daemon', help='Run MTT daemon process.',
      parents=[
          _CreateLabConfigArgParser(), _CreateImageArgParser(),
          _CreateContainerArgParser(), _CreateDaemonCommandArgParser()])

  subparser = subparsers.add_parser(
      'version', help='Print the version of MTT CLI.')
  subparser.set_defaults(func=cli_util.PrintVersion)
  return parser


def Main():
  """The entry point function for CLI."""
  parser = CreateParser()
  args = parser.parse_args()
  args.cli_path = os.environ.get('PEX', os.path.realpath(sys.argv[0]))
  global logger
  logger = cli_util.CreateLogger(args)
  if not args.no_check_update:
    try:
      new_path = cli_util.CheckAndUpdateTool(
          args.cli_path,
          cli_update_url=args.cli_update_url)
      if new_path:
        logger.debug('CLI is updated.')
        os.execv(new_path, [new_path] + sys.argv[1:])
    except Exception as e:        logger.warning('Failed to check/update tool: %s', e)
  try:
    if args.action == 'version':
      cli_util.PrintVersion()
    elif hasattr(args, 'func'):
      args.func(args)
    else:
      parser.print_usage()
  except command_util.DockerNotFoundError:
    logger.error(
        'Docker is not installed on the host. Please install Docker Engine'
        '(http://www.docker.com/) and try again.')
    sys.exit(-1)
  except command_util.FabricNotFoundError:
    logger.error(
        'Running remote commands requires Fabric. Please install Fabric'
        '(http://www.fabfile.org/) and try again.')
    sys.exit(-1)
  except command_util.GCloudNotFoundError:
    logger.error(
        'gcloud is not found on the host. Please install Google Cloud SDK'
        '(https://cloud.google.com/sdk/downloads) and try again.')
    sys.exit(-1)
  except host_util.ExecutionError:
    # The information should already be printed.
    sys.exit(-1)
  except ActionableError as e:
    logger.error(e.message)
    sys.exit(-1)


if __name__ == '__main__':
  Main()
