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

"""A lab management CLI for MTT."""
import argparse
import atexit
import datetime
import json
import logging
import os
import shlex
import shutil
import sys
import tempfile
import zipfile

import dateutil

from multitest_transport.cli import cli_util
from multitest_transport.cli import google_auth_util
from multitest_transport.cli import host_util

logger = logging.getLogger(__name__)

_MTT_BINARY_FILE = 'mtt_binary'
_REMOTE_MTT_BINARY_FORMAT = '/tmp/%s/mtt'
_REMOTE_CONFIG_FILE_FORMAT = '/tmp/%s/mtt_host_config.yaml'
_REMOTE_KEY_FILE_FORMAT = '/tmp/%s/keyfile/key.json'

_PRIVATE_KEY_ID_KEY = 'private_key_id'
_CLIENT_EMAIL_KEY = 'client_email'
_VALID_AFTER_TIME_KEY = 'validAfterTime'

# By default service account key is valid for 90 days.
# And at most 10 keys can be created for a service account.
# So we need to renew > 9 days (in theory we can remove old keys,
# but that requires some work to delete keys properly), so that
# we will not create more than 10 keys.
_SERVICE_ACCOUNT_KEY_RENEW_TIME_IN_DAYS = 14
_SECRET_VERSION_DISABLE_BEFORE_DAYS = 14 * 2


def _CreateLabCommandArgParser():
  """Create argparser for lab related commands."""
  parser = argparse.ArgumentParser(
      add_help=False, parents=[
          cli_util.CreateSSHArgParser(),
          cli_util.CreateMultiHostCommandArgParser()])
  parser.add_argument(
      'lab_config_path', type=str, help='Lab to manage.')
  parser.add_argument(
      'hosts_or_clusters', metavar='hosts_or_clusters', type=str, nargs='*',
      help='Only manage these hosts or clusters that configured in the lab.')
  return parser


def _CreateServiceAccountArgParser():
  """Create argparser for service account key file."""
  parser = argparse.ArgumentParser(add_help=False)
  # TODO: delete service_account_json_key_path arg.
  parser.add_argument(
      '--service_account_json_key_path', help='Service account json key path.')
  return parser


def _SetupMTTBinary(args, host):
  """Setup the remote host properly.

  Copy mtt binary to the remote host.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  """
  remote_mtt_binary = _REMOTE_MTT_BINARY_FORMAT % host.context.user
  logger.info('Setting up MTT binary on %s.', host.name)
  host.execution_state = 'Setting up MTT Binary'
  tmp_folder = tempfile.mkdtemp()
  try:
    with zipfile.ZipFile(args.cli_path, 'r') as cli_zip:
      mtt_binary_path = cli_zip.extract(_MTT_BINARY_FILE, tmp_folder)
    host.context.CopyFile(mtt_binary_path, remote_mtt_binary)
    host.context.Run(['chmod', '+x', remote_mtt_binary])
  except zipfile.BadZipfile:
    logger.error('%s is not a zip file.', args.cli_path)
    raise
  except KeyError:
    logger.error('No %s in %s.', _MTT_BINARY_FILE, args.cli_path)
    raise
  finally:
    if tmp_folder:
      shutil.rmtree(tmp_folder)


def _SetupHostConfig(host):
  """Setup the remote host config properly.

  Args:
    host: a Host.
  """
  remote_config_file = _REMOTE_CONFIG_FILE_FORMAT % host.context.user
  logger.info('Setting up host config on %s.', host.name)
  host.execution_state = 'Setting up host config'
  config_file = tempfile.NamedTemporaryFile(suffix='.yaml')
  try:
    host.config.Save(config_file.name)
    host.context.CopyFile(config_file.name, remote_config_file)
  finally:
    config_file.close()


def _SetupServiceAccountKey(args, host):
  """Setup service account key in remote a host.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  """
  remote_key_file = _REMOTE_KEY_FILE_FORMAT % host.context.user
  service_account_json_key_path = (
      args.service_account_json_key_path or
      host.config.service_account_json_key_path)
  if not service_account_json_key_path:
    logger.debug('No service account set up.')
    return
  logger.info('Setting up service account key on %s.', host.name)
  host.execution_state = 'Setting up service account key'
  # Using service account key file in args or config.
  host.context.CopyFile(
      service_account_json_key_path, remote_key_file)
  host.config = host.config.SetServiceAccountJsonKeyPath(remote_key_file)


def _BuildBaseMTTCmd(args, host):
  """Build base MTT cmd."""
  remote_mtt_binary = _REMOTE_MTT_BINARY_FORMAT % host.context.user
  remote_cmd = [remote_mtt_binary]
  if args.very_verbose:
    remote_cmd += ['-vv']
  elif args.verbose:
    remote_cmd += ['-v']
  # We copy the mtt binary inside mtt_lab to remote host,
  # there is not need to update the mtt binary on the remote host.
  remote_cmd += ['--no_check_update']
  return remote_cmd


def Start(args, host):
  """Start MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to start.
  """
  remote_config_file = _REMOTE_CONFIG_FILE_FORMAT % host.context.user
  _SetupMTTBinary(args, host)
  _SetupServiceAccountKey(args, host)
  _SetupHostConfig(host)

  logger.info('Starting mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args, host) + ['start', remote_config_file]
  use_sudo = bool(args.sudo_user) or args.ask_sudo_password
  host.execution_state = 'Running start'
  host.context.Run(remote_cmd, sudo=use_sudo)
  logger.info('Started mtt on %s.', host.name)


def Stop(args, host):
  """Stop MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to start.
  """
  logger.info('Stopping mtt on %s.', host.name)
  _SetupMTTBinary(args, host)
  remote_cmd = _BuildBaseMTTCmd(args, host) + ['stop']
  use_sudo = bool(args.sudo_user) or args.ask_sudo_password
  host.execution_state = 'Running stop'
  host.context.Run(remote_cmd, sudo=use_sudo)
  logger.info('Stopped mtt on %s.', host.name)


def Restart(args, host):
  """Restart MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to restart.
  """
  remote_config_file = _REMOTE_CONFIG_FILE_FORMAT % host.context.user
  _SetupMTTBinary(args, host)
  _SetupServiceAccountKey(args, host)
  _SetupHostConfig(host)

  logger.info('Restarting mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args, host) + ['restart', remote_config_file]
  use_sudo = bool(args.sudo_user) or args.ask_sudo_password
  host.execution_state = 'Running restart'
  host.context.Run(remote_cmd, sudo=use_sudo)
  logger.info('Restarted mtt on %s.', host.name)


def Update(args, host):
  """Update MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to update.
  """
  remote_config_file = _REMOTE_CONFIG_FILE_FORMAT % host.context.user
  _SetupMTTBinary(args, host)
  _SetupServiceAccountKey(args, host)
  _SetupHostConfig(host)

  logger.info('Updating mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args, host) + ['update', remote_config_file]
  use_sudo = bool(args.sudo_user) or args.ask_sudo_password
  host.execution_state = 'Running update'
  host.context.Run(remote_cmd, sudo=use_sudo)
  logger.info('Updated mtt on %s.', host.name)


def RunCmd(args, host):
  """Run command line on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  """
  logger.info('Run "%s" on %s.', args.cmd, host.name)
  tokens = shlex.split(args.cmd)
  use_sudo = bool(args.sudo_user) or args.ask_sudo_password
  host.execution_state = 'Running cmd'
  res = host.context.Run(tokens, sudo=use_sudo)
  logger.info(res.stdout)
  logger.info('Finished "%s" on %s.', args.cmd, host.name)


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
  subparser = subparsers.add_parser(
      'version', help='Print the version of MTT CLI.')

  subparser = subparsers.add_parser(
      'start', help='Start a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(host_func=Start)

  subparser = subparsers.add_parser(
      'restart', help='Restart a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(host_func=Restart)

  subparser = subparsers.add_parser(
      'update', help='Update a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(host_func=Update)

  subparser = subparsers.add_parser(
      'stop', help='Stop a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(host_func=Stop)

  subparser = subparsers.add_parser(
      'run_cmd', help='Run command line on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.add_argument('--cmd', type=str, help='Command line to run.')
  subparser.set_defaults(host_func=RunCmd)
  return parser


def _GetServiceAccountKeyFilePath(secret_project_id, secret_id):
  service_account_key = _GetServiceAccountKeyFromSecretManager(
      secret_project_id, secret_id)
  tmp_service_account_key_file = tempfile.NamedTemporaryFile(suffix='.json')
  tmp_service_account_key_file.write(service_account_key)
  tmp_service_account_key_file.flush()
  # Key file will be deleted at exit.
  atexit.register(tmp_service_account_key_file.close)
  return tmp_service_account_key_file.name


def _GetServiceAccountKeyFromSecretManager(secret_project_id, secret_id):
  """Get service account key based on lab config path."""
  service_account_key = google_auth_util.GetSecret(
      secret_project_id, secret_id)
  sa_key_dict = json.loads(service_account_key)
  sa_email = sa_key_dict[_CLIENT_EMAIL_KEY]
  if not google_auth_util.CanCreateKey(sa_email):
    logger.info('No permission to create service account key, skip renew')
    return service_account_key
  if not google_auth_util.CanUpdateSecret(secret_project_id, secret_id):
    logger.info('No permission to create service account key, skip renew')
    return service_account_key
  if not _ShouldRenewServiceAccountKey(sa_key_dict):
    logger.debug('The service account key is new, no need to renew.')
    return service_account_key
  new_sa_key_dict = google_auth_util.CreateKey(sa_email)
  new_service_account_key = json.dumps(new_sa_key_dict).encode()
  version = google_auth_util.UpdateSecret(
      secret_project_id, secret_id, new_service_account_key)
  google_auth_util.DisableSecretVersions(
      secret_project_id, secret_id,
      exclude_versions=[version],
      days_before=_SECRET_VERSION_DISABLE_BEFORE_DAYS)
  return new_service_account_key


def _ShouldRenewServiceAccountKey(sa_key_dict):
  """Check if we need to renew the service account key or not."""
  sa_key_id = sa_key_dict[_PRIVATE_KEY_ID_KEY]
  sa_email = sa_key_dict[_CLIENT_EMAIL_KEY]
  key_info = google_auth_util.GetServiceAccountKeyInfo(sa_email, sa_key_id)
  logger.debug('Get %s key %s info: %s.', sa_email, sa_key_id, key_info)
  create_time = dateutil.parser.parse(key_info[_VALID_AFTER_TIME_KEY])
  renew_time = create_time + datetime.timedelta(
      days=_SERVICE_ACCOUNT_KEY_RENEW_TIME_IN_DAYS)
  now = datetime.datetime.now(tz=datetime.timezone.utc)
  if now > renew_time:
    logger.info(
        'The service account key %s is created at %s (>%s days ago),'
        ' try to renew.',
        sa_key_id, create_time, _SERVICE_ACCOUNT_KEY_RENEW_TIME_IN_DAYS)
    return True
  logger.info(
      'The service account key %s is created at %s, skip renew.',
      sa_key_id, create_time)
  return False


def _WarnIfDev():
  """Warn before proceed with dev-built binary.

  This method aims to reduce the risk of copying dev binaries to remote hosts.
  The dev version hosts does not auto-update itself, and may lead to unexpected
  behavior on remote hosts.
  """
  _, build_environment = cli_util.GetVersion()
  if build_environment != 'dev':
    return
  print(f'{cli_util.OUTPUT_RED}'
        'MTT Lab CLI was built in dev environment, '
        'and will copy dev version MTT CLI to remote hosts. '
        'Would you like to continue(Y/n):'
        f'{cli_util.OUTPUT_NOCOLOR}')
  answer = input()
  if answer == 'Y':
    return
  if answer == 'n':
    sys.exit(0)
  raise ValueError('Please enter Y or n.')


def Main():
  """The entry point function for lab CLI."""
  parser = CreateParser()
  args = parser.parse_args()
  args.cli_path = os.path.realpath(sys.argv[0])
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
  if not args.action:
    parser.print_usage()
    return
  if args.action == 'version':
    cli_util.PrintVersion()
    return

  _WarnIfDev()

  lab_config_pool = host_util.BuildLabConfigPool(args.lab_config_path)
  lab_config = lab_config_pool.GetLabConfig()
  service_account_key_path = None
  # Use service account in secret first, since this is the most secure way.
  if lab_config.secret_project_id and lab_config.service_account_key_secret_id:
    service_account_key_path = _GetServiceAccountKeyFilePath(
        lab_config.secret_project_id,
        lab_config.service_account_key_secret_id)
  service_account_key_path = (
      service_account_key_path or
      lab_config.service_account_json_key_path or
      args.service_account_json_key_path)
  if service_account_key_path:
    logger = cli_util.CreateLogger(args, service_account_key_path)
  else:
    logger.warning('There is no service account key secret or path set.')
  args.service_account_json_key_path = service_account_key_path
  host_util.Execute(args, lab_config_pool)


if __name__ == '__main__':
  Main()
