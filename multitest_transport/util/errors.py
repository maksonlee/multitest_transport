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


class TestResourceError(Exception):
  """Test resource related errors."""


class BuildProviderError(Exception):
  """The Base Error Class for MTT Plugin."""


class FileNotFoundError(BuildProviderError):
  """An Error indicating that file is not found."""


class InvalidFileNameError(BuildProviderError):
  """An Error indicating that file name is not valid."""


class DuplicatedNameError(BuildProviderError):
  """An MTT Google Drive Error.

  A Google Drive Error indicating that there exists folders or files that
  shared the same name resides under the same directory
  """


class InvalidParamError(BuildProviderError):
  """An MTT Google Drive Error.

  A Google Drive Error indicating that requested parameters are invalid
  """
