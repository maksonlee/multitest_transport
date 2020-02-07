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

BASE_CONFIG_PATH = 'config.yaml'


def Load():
  """Load MTT configuration."""
  logging.info('Loading %s...', BASE_CONFIG_PATH)
  with open(BASE_CONFIG_PATH) as f:
    content = f.read()
  config_set = config_encoder.Decode(content)
  config_set.node_config = None  # Do not load node_config automatically
  config_encoder.Load(config_set)
