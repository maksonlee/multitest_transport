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

"""A module to load MTT configuration during application start."""

import logging

from multitest_transport.models import config_encoder
from multitest_transport.util import env
from multitest_transport.util import file_util

BASE_CONFIG_PATH = 'config.yaml'
EXTERNAL_CONFIG_ROOT = 'config'


def _ReadBaseConfig():
  """Read base configuration file."""
  logging.info('Loading %s...', BASE_CONFIG_PATH)
  with open(BASE_CONFIG_PATH) as f:
    return f.read()


def _ReadAdditionalConfigs():
  """Read additional configuration files from local storage."""
  config_dir = file_util.DownloadDirectory(
      env.FILE_SERVER_URL, EXTERNAL_CONFIG_ROOT)
  if not config_dir:
    return

  # iterate over files (sorted as the CLI preserves the user-specified ordering
  # by renaming the files 1.yaml, 2.yaml, and so on), extract and read content
  for file_name in sorted(config_dir.getnames()):
    tar_file = config_dir.extractfile(file_name)
    if tar_file:
      logging.info('Loading %s...', file_name)
      yield tar_file.read()


def Load():
  """Load MTT configuration files."""
  file_contents = [_ReadBaseConfig()] + list(_ReadAdditionalConfigs())
  config_set = config_encoder.Decode(file_contents)
  config_set.node_config = None  # Do not load node_config automatically
  config_encoder.Load(config_set)
