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
import logging
import os
import shlex
import shutil
import sys
import tempfile
import zipfile

from multitest_transport.cli import cli_util
from multitest_transport.cli import config
from multitest_transport.cli import host_util

logger = logging.getLogger(__name__)

_MTT_BINARY_FILE = 'mtt_binary'
_REMOTE_MTT_BINARY = '/tmp/mtt'
_REMOTE_CONFIG_FILE = '/tmp/mtt_host_config.yaml'
_REMOTE_KEY_DIR = '/tmp/keyfile'
_REMOTE_KEY_FILE = os.path.join(_REMOTE_KEY_DIR, 'key.json')


def _CreateLabCommandArgParser():
  """Create argparser for lab related commands."""
  parser = argparse.ArgumentParser(
      add_help=False, parents=[
          cli_util.CreateSSHArgParser(),
          cli_util.CreateMultiHostCommandArgParser()])
  parser.add_argument('lab_config_path', type=str, help='Lab to manage.')
  parser.add_argument(
      'hosts_or_clusters', metavar='hosts_or_clusters', type=str, nargs='*',
      help='Only manage these hosts or clusters that configured in the lab.')
  parser.set_defaults(
      command_executor_factory=host_util.LabExecutor)
  return parser


def _CreateServiceAccountArgParser():
  """Create argparser for service account key file."""
  parser = argparse.ArgumentParser(add_help=False)
  # TODO: delete service_account_json_key_path arg.
  parser.add_argument(
      '--service_account_json_key_path',
      default=config.config.service_account_json_key_path,
      help='Service account json key path.')
  return parser


def _SetupMTTBinary(args, host):
  """Setup the remote host properly.

  Copy mtt binary to the remote host.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  """
  logger.info('Setting up MTT binary on %s.', host.name)
  host.execution_state = 'Setting up MTT Binary'
  tmp_folder = tempfile.mkdtemp()
  try:
    with zipfile.ZipFile(args.cli_path, 'r') as cli_zip:
      mtt_binary_path = cli_zip.extract(_MTT_BINARY_FILE, tmp_folder)
    host.context.CopyFile(mtt_binary_path, _REMOTE_MTT_BINARY)
    host.context.Run(['chmod', '+x', _REMOTE_MTT_BINARY])
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
  logger.info('Setting up host config on %s.', host.name)
  host.execution_state = 'Setting up host config'
  config_file = tempfile.NamedTemporaryFile(suffix='.yaml')
  try:
    host.config.Save(config_file.name)
    host.context.CopyFile(config_file.name, _REMOTE_CONFIG_FILE)
  finally:
    config_file.close()


def _SetupServiceAccountKey(host, service_account_json_key_path):
  """Setup service account key in remote a host.

  Args:
    host: an instance of host_util.Host.
    service_account_json_key_path: a string, path of the source key file.
  """
  logger.info('Setting up service account key on %s.', host.name)
  host.execution_state = 'Setting up service account key'
  host.context.CopyFile(
      service_account_json_key_path, _REMOTE_KEY_FILE)
  host.config.service_account_json_key_path = _REMOTE_KEY_FILE


def _BuildBaseMTTCmd(args):
  """Build base MTT cmd."""
  remote_cmd = [_REMOTE_MTT_BINARY]
  if args.very_verbose:
    remote_cmd += ['-vv']
  elif args.verbose:
    remote_cmd += ['-v']
  return remote_cmd


def Start(args, host):
  """Start MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to start.
  """
  _SetupMTTBinary(args, host)

  service_account_json_key_path = (
      args.service_account_json_key_path
      or host.config.service_account_json_key_path)
  if service_account_json_key_path:
    _SetupServiceAccountKey(host, service_account_json_key_path)

  _SetupHostConfig(host)

  logger.info('Starting mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args) + ['start', _REMOTE_CONFIG_FILE]
  host.execution_state = 'Running start'
  host.context.Run(remote_cmd, sudo=args.ask_sudo_password)
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
  remote_cmd = _BuildBaseMTTCmd(args) + ['stop']
  host.execution_state = 'Running stop'
  host.context.Run(remote_cmd, sudo=args.ask_sudo_password)
  logger.info('Stopped mtt on %s.', host.name)


def Restart(args, host):
  """Restart MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to restart.
  """
  _SetupMTTBinary(args, host)

  service_account_json_key_path = (
      args.service_account_json_key_path
      or host.config.service_account_json_key_path)
  if service_account_json_key_path:
    _SetupServiceAccountKey(host, service_account_json_key_path)

  _SetupHostConfig(host)

  logger.info('Restarting mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args) + ['restart', _REMOTE_CONFIG_FILE]
  host.execution_state = 'Running restart'
  host.context.Run(remote_cmd, sudo=args.ask_sudo_password)
  logger.info('Restarted mtt on %s.', host.name)


def Update(args, host):
  """Update MTT node on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  Raises:
    RuntimeError: if a MTT node fails to update.
  """
  _SetupMTTBinary(args, host)

  service_account_json_key_path = (
      args.service_account_json_key_path
      or host.config.service_account_json_key_path)
  if service_account_json_key_path:
    _SetupServiceAccountKey(host, service_account_json_key_path)

  _SetupHostConfig(host)

  logger.info('Updating mtt on %s.', host.name)
  remote_cmd = _BuildBaseMTTCmd(args) + ['update', _REMOTE_CONFIG_FILE]
  host.execution_state = 'Running update'
  host.context.Run(remote_cmd, sudo=args.ask_sudo_password)
  logger.info('Updated mtt on %s.', host.name)


def RunCmd(args, host):
  """Run command line on remote hosts.

  Args:
    args: a parsed argparse.Namespace object.
    host: a Host.
  """
  logger.info('Run "%s" on %s.', args.cmd, host.name)
  tokens = shlex.split(args.cmd)
  host.execution_state = 'Running cmd'
  res = host.context.Run(tokens, sudo=args.ask_sudo_password)
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
  subparsers = parser.add_subparsers(title='Actions')
  # Commands for users
  subparser = subparsers.add_parser(
      'version', help='Print the version of MTT CLI.')
  subparser.set_defaults(func=cli_util.PrintVersion)

  subparser = subparsers.add_parser(
      'start', help='Start a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(func=Start)

  subparser = subparsers.add_parser(
      'restart', help='Restart a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(func=Restart)

  subparser = subparsers.add_parser(
      'update', help='Update a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser(), _CreateServiceAccountArgParser()])
  subparser.set_defaults(func=Update)

  subparser = subparsers.add_parser(
      'stop', help='Stop a MTT instance on a remote host.',
      parents=[_CreateLabCommandArgParser()])
  subparser.set_defaults(func=Stop)

  subparser = subparsers.add_parser(
      'run_cmd', help='Run command line on a remote host.',
      parents=[_CreateLabCommandArgParser()])
  subparser.add_argument('--cmd', type=str, help='Command line to run.')
  subparser.set_defaults(func=RunCmd)
  return parser


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
  try:
    if (hasattr(args, 'command_executor_factory') and
        args.command_executor_factory):
      executor = args.command_executor_factory(args)
      executor.Execute()
    elif hasattr(args, 'func'):
      args.func(args)
    else:
      parser.print_usage()
  except host_util.ExecutionError:
    # The information should already be printed.
    sys.exit(-1)


if __name__ == '__main__':
  Main()
