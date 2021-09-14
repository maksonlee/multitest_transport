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
      name: remove_file
      value: True

  operation:
    type: DELETE
"""
import distutils.util
import pathlib

from multitest_transport.models import messages
from multitest_transport.models import ndb_models
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

  def __init__(self, remove_file: str = 'True'):
    super().__init__()
    self.remove_file = distutils.util.strtobool(remove_file)

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


Operations = {
    ndb_models.FileCleanerOperationType.ARCHIVE: Archive,
    ndb_models.FileCleanerOperationType.DELETE: Delete
}


def BuildOperation(config: messages.FileCleanerOperation) -> 'Operation':
  """Factory function to build the Operation according to the config.

  Args:
    config: operation config.

  Returns:
    Operation
  """
  return Operations[config.type](
      **messages.ConvertNameValuePairsToDict(config.params))
