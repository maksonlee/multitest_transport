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
import logging
import os
import os.path
import re
import shutil
import socket
import sys
import tempfile
import time
import zipfile

import six

from multitest_transport.cli import cli_util
from multitest_transport.cli import command_util
from multitest_transport.cli import config
from multitest_transport.cli import gcs_file_util
from multitest_transport.cli import google_auth_util
from multitest_transport.cli import host_util

_MTT_CONTAINER_NAME = 'mtt'
_MTT_PROJECT = 'android-mtt'
_MTT_SERVER_WAIT_TIME_SECONDS = 120

_MTT_LIB_DIR = '/var/lib/mtt'
_MTT_LOG_DIR = '/var/log/mtt'
_TMP_DIR = '/tmp'
_KEY_FILE = os.path.join(_MTT_LIB_DIR, 'keyfile', 'key.json')
_TMP_KEY_FILE = os.path.join(_TMP_DIR, 'keyfile', 'key.json')
# Permanent MTT binary path has to match the one in mttd.service file.
_MTT_BINARY = os.path.join(_MTT_LIB_DIR, 'mtt')
_HOST_CONFIG = os.path.join(_MTT_LIB_DIR, 'mtt_host_config.yaml')
_ZIPPED_MTTD_FILE = 'multitest_transport/mttd.service'
_MTTD_FILE = '/etc/systemd/system/mttd.service'
_CONFIG_ROOT = 'config'
_VERSION_FILE = 'VERSION'
_UNKNOWN_VERSION = 'unknown'
_DEFAULT_DOCKERIZED_TF_IMAGE = 'gcr.io/dockerized-tradefed/tradefed:golden'
_DEFAULT_MTT_IMAGE = 'gcr.io/android-mtt/mtt:prod'
_DAEMON_UPDATE_INTERVAL_SEC = 60
_CLI_UPDATE_URL_TEMPLATE = 'gs://android-mtt.appspot.com/%s/mtt'

# Tradefed accept TSTP signal as 'quit', which will finish all running tests.
_TF_QUIT = 'TSTP'

PACKAGE_LOGGER_NAME = 'multitest_transport.cli'
logger = logging.getLogger(__name__)


def Configure(_):
  """Configures the common settings."""
  config.config.Prompt()
  config.config.Save()


def _WaitForServer(url, timeout):
  """Wait for a server to be ready.

  Args:
    url: a server url.
    timeout: max wait time.
  Returns:
    True if the service is ready. Otherwise False.
  """
  end_time = time.time() + timeout
  while time.time() < end_time:
    time.sleep(0.1)
    try:
      six.moves.urllib.request.urlopen(url, timeout=1)
      return True
    except (socket.error, six.moves.urllib.error.URLError):
      pass
  return False


def _GetDockerImageName(image_name, tag=None, master_url=None):
  """Get a MTT image name to use.

  Args:
    image_name: an image name.
    tag: an image tag (optional).
    master_url: master url to determine to use dockerized tf or mtt.
  Returns:
    a Docker image name.
  """
  if not image_name:
    if master_url:
      image_name = _DEFAULT_DOCKERIZED_TF_IMAGE
    else:
      image_name = _DEFAULT_MTT_IMAGE
  if tag:
    image_name = image_name.split(':', 2)[0] + ':' + tag
  return image_name


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
    host.config.service_account_json_key_path = _KEY_FILE
  host.config.Save(_HOST_CONFIG)


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
  _StartMttNode(args, host)


def _StartMttNode(args, host):
  """Start MTT node on local hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.
  Raises:
    RuntimeError: if a MTT node fails to start.
  """
  master_url = host.config.master_url
  image_name = _GetDockerImageName(
      host.config.docker_image or args.image_name,
      master_url=master_url,
      tag=args.tag)
  logger.info('Using image %s.', image_name)
  docker_context = command_util.DockerContext(
      host.context,
      service_account_json_key_path=host.config.service_account_json_key_path)
  docker_helper = command_util.DockerHelper(docker_context, image_name)

  if docker_helper.IsContainerRunning(args.name):
    logger.error('MTT is already running.')
    return

  if args.force_update:
    docker_helper.Pull()

  if master_url:
    docker_helper.AddEnv('MTT_MASTER_URL', master_url)
  else:
    logger.info('mtt_master_url is not set; starting a standalone node.')
    docker_helper.AddEnv('MTT_MASTER_PORT', args.port)
  if host.config.lab_name:
    docker_helper.AddEnv('LAB_NAME', host.config.lab_name)
  if host.config.cluster_name:
    docker_helper.AddEnv('CLUSTER', host.config.cluster_name)
  if host.config.tf_global_config_path:
    docker_helper.AddEnv(
        'TF_GLOBAL_CONFIG_PATH',
        host.config.tf_global_config_path)

  docker_helper.AddEnv('USER', os.environ.get('USER'))

  # Copy proxy settings if exists
  docker_helper.CopyEnv('http_proxy')
  docker_helper.CopyEnv('https_proxy')
  docker_helper.CopyEnv('ftp_proxy')
  if os.environ.get('no_proxy'):
    os.environ['no_proxy'] = os.environ.get('no_proxy') + ',127.0.0.1'
  docker_helper.CopyEnv('no_proxy')

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
    host.context.CopyFile(
        host.config.service_account_json_key_path,
        _TMP_KEY_FILE)
    docker_helper.AddVolume('mtt-key', os.path.dirname(_TMP_KEY_FILE))
    docker_helper.AddFile(_TMP_KEY_FILE, _TMP_KEY_FILE)
    docker_helper.AddEnv('JSON_KEY_PATH', _TMP_KEY_FILE)
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

  if config.config.config_files:
    # Copy config files into container and notify MTT using env variable
    docker_files = []
    for config_file in filter(None, config.config.config_files.split(',')):
      config_path = os.path.abspath(config_file)
      docker_file = '/' + config_path[1::].replace(os.path.sep, '$')
      docker_files.append(docker_file)
      # Copy instead of mounting to ensure MTT has access
      # TODO: support GCS files
      docker_helper.AddFile(config_path, docker_file)
    docker_helper.AddEnv('MTT_CONFIG_FILES', ','.join(docker_files))

  custom_sdk_dir = None
  if config.config.custom_adb_path:
    # Create temp directory for custom SDK tools, will be copied over to ensure
    # MTT has access, and will be cleaned up on next start
    custom_sdk_dir = tempfile.mkdtemp()
    docker_helper.AddFile(custom_sdk_dir, '/tmp/custom_sdk_tools')
    # TODO: support GCS files
    shutil.copy(config.config.custom_adb_path, '%s/adb' % custom_sdk_dir)

  docker_helper.Run(args.name)

  # Delete temp tools directory
  if custom_sdk_dir:
    shutil.rmtree(custom_sdk_dir)

  hostname = host.name
  if host.context.IsLocal():
    # We change hostname to localhost since
    # MTT's build channel authorization only works when accessed with
    # localhost URL.
    hostname = 'localhost'
  if master_url:
    logger.info('MTT slave is running.')
  else:
    url = 'http://%s:%s' % (hostname, args.port)
    if not _WaitForServer(url, timeout=_MTT_SERVER_WAIT_TIME_SECONDS):
      raise RuntimeError(
          'MTT server failed to start in %ss' % _MTT_SERVER_WAIT_TIME_SECONDS)
    logger.info('MTT is serving at %s', url)


def _StartMttDaemon(args, host):
  """Start MTT daemon on local host.

  Args:
    args: a parsed argparse.Namespace object.
    host: an instance of host_util.Host.

  Raises:
    RuntimeError: when failing to run command on host.
  """
  logger.info('Starting MTT daemon on %s.', host.name)
  if _IsDaemonActive(host):
    logger.warn('MTT daemon is already running on %s.', host.name)
    return
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
  docker_context = command_util.DockerContext(host.context, login=False)
  docker_helper = command_util.DockerHelper(docker_context)
  if docker_helper.IsContainerRunning(args.name):
    logger.info('Stopping running container %s.', args.name)
    if host.config.graceful_shutdown or args.wait:
      logger.info('Wait all tests to finish.')
      docker_helper.Kill([args.name], _TF_QUIT)
      res_shutdown = docker_helper.Wait([args.name])
    else:
      docker_helper.Stop([args.name])
      res_shutdown = docker_helper.Wait([args.name])
    if res_shutdown.return_code != 0:
      logger.warn('The docker container failed to shut down.')
      _ForceKillMttNode(host, docker_helper, args.name)
  logger.info('Container %s stopped.', args.name)
  res_inspect = docker_helper.Inspect(args.name)
  if res_inspect.return_code != 0:
    logger.info('No container %s.', args.name)
    return
  logger.info('Remove container %s.', args.name)
  docker_helper.RemoveContainers([args.name])


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
  """
  if not _IsDaemonActive(host):
    logger.debug('MTT daemon is not active on %s. Skip daemon stop.', host.name)
    return
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
  image_name = _GetDockerImageName(
      host.config.docker_image or args.image_name,
      tag=args.tag,
      master_url=host.config.master_url)
  logger.debug('Using image %s.', image_name)
  docker_context = command_util.DockerContext(
      host.context,
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
  docker_helper.CleanupDanglingImages()
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
  if host.config.enable_autoupdate:
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
  _StopMttNode(args, host)
  _StartMttNode(args, host)


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
  _StartMttNode(args, host)


def RunDaemon(args):
  """Run MTT daemon on the local host.

  Args:
    args: a parsed argparse.Namespace object.
  """
  while True:
    host = host_util.CreateHost(args)
    _UpdateMttNode(args, host)
    time.sleep(_DAEMON_UPDATE_INTERVAL_SEC)


def _CreateImageArgParser():
  """Create argparser for docker image relate operations."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--image_name',
                      default=config.config.docker_image,
                      help='The docker image to use.')
  parser.add_argument('--tag',
                      help='A tag for a new image.')
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
  parser.add_argument('--port', type=int, default=8000)
  # TODO: delete service_account_json_key_path arg.
  parser.add_argument(
      '--service_account_json_key_path',
      default=config.config.service_account_json_key_path,
      help='Service account json key path.')
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


def CreateParser():
  """Creates an argument parser.

  Returns:
    an argparse.ArgumentParser object.
  """
  parser = argparse.ArgumentParser(
      parents=[cli_util.CreateLoggingArgParser()])
  parser.add_argument(
      '--cli_update_url', type=str,
      help='Remote url to download the latest version command line.')
  parser.add_argument(
      '--no_check_update', action='store_true',
      help='Enable command line auto update or not.')
  subparsers = parser.add_subparsers(title='Actions')

  subparser = subparsers.add_parser(
      'configure', help='Configure basic settings')
  subparser.set_defaults(func=Configure)

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


def _CheckAndUpdateTool(local_path, cli_update_url=None):
  """Check the remote version, if it's different, update the local CLI."""
  if not cli_update_url or not cli_update_url.strip():
    _, build_environment = cli_util.GetVersion(local_path)
    if build_environment == 'dev':
      logger.debug('CLI from dev and no "cli_update_url" set, not update CLI.')
      return None
    cli_update_url = _CLI_UPDATE_URL_TEMPLATE % build_environment
    logger.debug('Command auto update enabled, '
                 'but there is no cli_update_url set. '
                 'Using the default: %s.', cli_update_url)
  cli_update_url = cli_update_url.strip()
  if not cli_update_url.startswith('gs://'):
    logger.warn('cli_update_url only Support Google Cloud Storage path.')
    return None
  if os.path.basename(local_path) != os.path.basename(cli_update_url):
    logger.debug(
        '%s is not %s, not update.',
        os.path.basename(local_path), os.path.basename(cli_update_url))
    return None
  try:
    cred = google_auth_util.GetGCloudCredential(
        command_util.CommandContext())
    gcs_client = gcs_file_util.CreateGCSClient(_MTT_PROJECT, cred)
    blob = gcs_file_util.GetGCSBlob(gcs_client, cli_update_url)
  except gcs_file_util.GCSError as e:
    logger.warn(e)
    return None
  local_md5hash = gcs_file_util.CalculateMd5Hash(local_path)
  if six.ensure_text(blob.md5_hash) == local_md5hash:
    logger.debug('Local is the same as remote, not update.')
    return
  logger.info(
      'There is a newer version %s on %s, updating.',
      os.path.basename(local_path), cli_update_url)
  try:
    os.rename(
        local_path,
        gcs_file_util.CreateBackupFilePath(local_path))
    blob.download_to_filename(local_path)
    os.chmod(local_path, 0o770)
    return local_path
  except OSError as e:
    logger.warn('No write access to %s: %s.', os.path.dirname(local_path), e)


def Main():
  """The entry point function for CLI."""
  parser = CreateParser()
  args = parser.parse_args()
  args.cli_path = os.path.realpath(sys.argv[0])
  global logger
  logger = cli_util.CreateLogger(args)
  if not args.no_check_update:
    try:
      new_path = _CheckAndUpdateTool(
          args.cli_path,
          cli_update_url=args.cli_update_url)
      if new_path:
        os.execv(new_path, [new_path] + sys.argv[1:])
    except Exception as e:        logger.warn('Failed to check/update tool: %s', e)
  try:
    args.func(args)
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


if __name__ == '__main__':
  Main()
