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
"""Cleanup criteria.

YAML config example:

  criteria:
  - type: LAST_MODIFIED_DAYS  # required
    params:  # optional
      ttl_days: 7
  - type: NAME_MATCH
    params:
      pattern: 'zip'
"""
import os
import re
import time

from typing import Any, Dict

DAY_IN_SECS = 24 * 60 * 60
DEFAULT_TTL_DAYS = 7
DEFAULT_NAME_PATTERN = '.^'  # does not match anything


class Criterion(object):
  """Interface for cleanup criteria."""

  def Apply(self, path: str) -> bool:
    """Applies the criterion.

    Args:
      path: file path

    Returns:
      Bool, whether the file meets the criterion.
    """
    raise NotImplementedError


class LastModifiedDays(Criterion):
  """Whether the file exists more than ttl days."""

  def __init__(self, ttl_days: int = DEFAULT_TTL_DAYS):
    super().__init__()
    self.ttl_seconds = ttl_days * DAY_IN_SECS

  def Apply(self, path: str) -> bool:
    return time.time() - os.path.getmtime(path) > self.ttl_seconds


class NameMatch(Criterion):
  """Whether the file name matches the given regex pattern."""

  def __init__(self, pattern: str = DEFAULT_NAME_PATTERN):
    super().__init__()
    self.pattern = re.compile(pattern)

  def Apply(self, path: str) -> bool:
    return bool(self.pattern.search(path))


Criteria = {'LAST_MODIFIED_DAYS': LastModifiedDays, 'NAME_MATCH': NameMatch}


def BuildCriterion(config: Dict[str, Any]) -> 'Criterion':
  """Factory function to build the Criterion according to the config.

  Args:
    config: criterion config.

  Returns:
    Criterion
  """
  assert config['type'] in Criteria.keys()
  return Criteria[config['type']](**config.get('params', {}))
