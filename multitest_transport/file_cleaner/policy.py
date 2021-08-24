# Copyright 2021 Google LLC
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
# limitations under the License
"""Cleanup policies.

YAML config example:

  policies:
  - name: archive  # required, unique
    target: DIRECTORY  # optional, DIRECTORY or FILE(default)
    operation:  # required
      ...
    criteria:  # optional
    - ...
    - ...
"""
import os
from typing import Any, Dict

from multitest_transport.file_cleaner import criterion
from multitest_transport.file_cleaner import operation


class Policy(object):
  """Cleanup policies."""

  def __init__(self, config: Dict[str, Any]):
    self.name = config['name']
    self.target = config.get('target')
    self.criteria = [
        criterion.BuildCriterion(criterion_config)
        for criterion_config in config.get('criteria', [])
    ]
    self.operation = operation.BuildOperation(config['operation'])

  def _ApplyToTarget(self, path: str):
    if all([item.Apply(path) for item in self.criteria]):
      self.operation.Apply(path)

  def Apply(self, path: str):
    """Applies the policy to files/directories.

    Args:
      path: root path
    """
    if not os.path.exists(path):
      return

    for root, dirs, files in os.walk(path):
      targets = dirs if self.target == 'DIRECTORY' else files
      for name in targets:
        target_path = os.path.join(root, name)
        self._ApplyToTarget(target_path)
      if self.target == 'DIRECTORY':
        break
