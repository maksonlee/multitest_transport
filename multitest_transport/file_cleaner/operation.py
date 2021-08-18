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
"""Cleanup operations.

YAML config example:

  operation:
    type: ARCHIVE  # required
    params:  # optional
      remove_file: True

  operation:
    type: DELETE
"""
import pathlib
from typing import Any, Dict

from multitest_transport.util import file_util


class Operation(object):
  """Interface for cleanup operations."""

  def Apply(self, path: str):
    """Executes the cleanup operation.

    Args:
      path: file path
    """
    raise NotImplementedError


class Archive(Operation):
  """Archive operation."""

  def __init__(self, remove_file: bool = True):
    super().__init__()
    self.remove_file = remove_file

  def Apply(self, path: str):
    file_handle = file_util.FileHandle.Get(pathlib.Path(path).as_uri())
    file_handle.Archive(self.remove_file)


class Delete(Operation):
  """Delete operation."""

  def Apply(self, path: str):
    file_handle = file_util.FileHandle.Get(pathlib.Path(path).as_uri())
    info = file_handle.Info()
    if info:
      if info.is_file:
        file_handle.Delete()
      else:
        file_handle.DeleteDir()


Operations = {'ARCHIVE': Archive, 'DELETE': Delete}


def BuildOperation(config: Dict[str, Any]) -> 'Operation':
  """Factory function to build the Operation according to the config.

  Args:
    config: operation config.

  Returns:
    Operation
  """
  assert config['type'] in Operations.keys()
  return Operations[config['type']](**config.get('params', {}))
