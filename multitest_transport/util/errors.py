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

"""Error types."""
from typing import Optional


class BaseError(Exception):
  """Base MTT error class."""

  def __init__(self, message: str, http_status: Optional[int] = None):
    super(BaseError, self).__init__(message)
    if not hasattr(self, 'message'):
      self.message = message
    if http_status:
      self.http_status = http_status


class PluginError(BaseError):
  """Base MTT plugin error class.

  Signals that a plugin (build provider or test run hook) operation could not
  be completed successfully.
  """
  http_status = 500


class TestResourceError(BaseError):
  """Signals that a required test resource was invalid."""
  http_status = 400


class FileNotFoundError(BaseError):
  """Signals that the requested file could not be found."""
  http_status = 404


class FilePermissionError(BaseError):
  """Signals that the caller does not have access to the requested file."""
  http_status = 403
