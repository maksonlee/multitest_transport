# Copyright 2020 Google LLC
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

"""Base file upload hook."""
import re

from multitest_transport.plugins import base
from multitest_transport.util import file_util


class AbstractFileUploadHook(base.TestRunHook):
  """Base class for hooks that upload files during a test run."""

  def __init__(self, file_pattern=None, upload_prefix=None, **_):
    if not file_pattern:
      raise ValueError('file_pattern is required')
    self.file_pattern = re.compile('^' + file_pattern + '$')
    self.upload_prefix = upload_prefix or ''

  def Execute(self, context):
    """Upload output files that match the file pattern."""
    test_run = context.test_run
    attempt = context.latest_attempt
    if not attempt:
      raise ValueError('No attempt found for test run %s' % test_run.key.id())
    filenames = file_util.GetOutputFilenames(test_run, attempt)
    # Iterate over filenames to find those that match the file pattern
    for filename in filenames:
      if not self.file_pattern.match(filename):
        continue
      src = file_util.GetOutputFileUrl(test_run, attempt, filename)
      dest = self.upload_prefix + filename
      self.UploadFile(src, dest)

  def UploadFile(self, source_url, dest_file_path):
    """Uploads a file.

    Args:
      source_url: source URL
      dest_file_path: destination path
    """
    raise NotImplementedError('UploadFile() is not implemented.')
