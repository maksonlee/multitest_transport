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
  - type: LAST_MODIFIED_TIME  # required
    params:  # optional
    - name: ttl
      value: '7 days'
  - type: NAME_MATCH
    params:
    - name: pattern
      value: 'zip'
"""
import os
import re
import time

from pytimeparse import timeparse

from multitest_transport.models import messages
from multitest_transport.models import ndb_models

DEFAULT_TTL = '7 days'
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


class LastModifiedTime(Criterion):
  """Whether the file is expired according to last modified time."""

  def __init__(self, ttl: str = DEFAULT_TTL):
    super().__init__()
    self.ttl_seconds = timeparse.timeparse(ttl)

  def Apply(self, path: str) -> bool:
    return time.time() - os.path.getmtime(path) > self.ttl_seconds


class NameMatch(Criterion):
  """Whether the file name matches the given regex pattern."""

  def __init__(self, pattern: str = DEFAULT_NAME_PATTERN):
    super().__init__()
    self.pattern = re.compile(pattern)

  def Apply(self, path: str) -> bool:
    return bool(self.pattern.search(path))


Criteria = {
    ndb_models.FileCleanerCriterionType.LAST_MODIFIED_TIME: LastModifiedTime,
    ndb_models.FileCleanerCriterionType.NAME_MATCH: NameMatch
}


def BuildCriterion(config: messages.FileCleanerCriterion) -> 'Criterion':
  """Factory function to build the Criterion according to the config.

  Args:
    config: criterion config.

  Returns:
    Criterion
  """
  return Criteria[config.type](
      **messages.ConvertNameValuePairsToDict(config.params))
