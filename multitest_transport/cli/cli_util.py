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

"""Utils for cli."""
from __future__ import print_function
import argparse
import logging
import zipfile

import six

logger = logging.getLogger(__name__)
_UNKNOWN = 'unknown'
_VERSION_FILE = 'VERSION'
_LOG_FORMAT = '%(asctime)s |%(levelname)s| %(module)s:%(lineno)s| %(message)s'
_SIMPLE_LOG_FORMAT = '%(message)s'
_PACKAGE_LOGGER_NAME = 'multitest_transport.cli'


def PrintVersion(args):
  """Print the version of MTT CLI."""
  version, _ = GetVersion(args.cli_path)
  print('Version: %s' % version)


def GetVersion(cli_path):
  """Get the version and build environment of MTT CLI."""
  version = _UNKNOWN
  build_environment = _UNKNOWN
  try:
    with zipfile.ZipFile(cli_path, 'r') as mtt_zip:
      try:
        parser = six.moves.configparser.SafeConfigParser()
        parser.readfp(six.StringIO(six.ensure_str(mtt_zip.read(_VERSION_FILE))))
        version = parser.get('version', 'VERSION')
        build_environment = parser.get('version', 'BUILD_ENVIRONMENT')
      except KeyError:
        logger.error('No %s in MTT Cli.', _VERSION_FILE)
  except zipfile.BadZipfile:
    logger.error('%s is not a zip file.', cli_path)
  return version, build_environment


def CreateLoggingArgParser():
  """Create argparser for logging."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--logtostderr', action='store_true')
  parser.add_argument(
      '-v', dest='verbose', action='store_true',
      help='Log logs from multitest_transport.cli package at DEBUG level.')
  parser.add_argument(
      '-vv', dest='very_verbose', action='store_true',
      help='Log all logs from all package at DEBUG level.')
  parser.add_argument(
      '--log_file', dest='log_file', type=str, default=None,
      help='Path to log file.')
  return parser


def CreateLogger(args):
  """Create logger.

  All sub package should use logger.getLogger(__name__) to get module logger,
  instead of using logging directly.

  Args:
    args: parsed args for logging.
  Returns:
    a logging.Logger
  """
  if args.very_verbose:
    new_logger = logging.getLogger()
  else:
    new_logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    # Avoid to logging through root.
    if new_logger.root:
      for handler in new_logger.root.handlers[:] or []:
        new_logger.root.removeHandler(handler)
      new_logger.root.addHandler(logging.NullHandler())

  logger_level = (logging.DEBUG if args.verbose or args.very_verbose
                  else logging.INFO)
  log_format = (_LOG_FORMAT if args.verbose or args.very_verbose
                else _SIMPLE_LOG_FORMAT)
  new_logger.setLevel(logger_level)

  if args.logtostderr and not new_logger.handlers:
    new_logger.addHandler(logging.StreamHandler())
  if args.log_file:
    new_logger.addHandler(logging.FileHandler(filename=args.log_file))
  if not new_logger.handlers:
    new_logger.addHandler(logging.StreamHandler())

  log_formatter = logging.Formatter(log_format)
  for handler in new_logger.handlers:
    handler.setFormatter(log_formatter)
  return new_logger


def CreateMultiHostCommandArgParser():
  """Create argparser for executing on multiple hosts."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument(
      '--parallel', action='store_true')
  parser.add_argument(
      '--exit_on_error', action='store_true')
  return parser


def CreateSSHArgParser():
  """Create argparser for ssh to remote host."""
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument(
      '--ssh_key', help='Use ssh key file.')
  parser.add_argument(
      '--ask_sudo_password', default=False,
      action='store_true', dest='ask_sudo_password')
  parser.add_argument(
      '--sudo_user', dest='sudo_user')
  return parser
