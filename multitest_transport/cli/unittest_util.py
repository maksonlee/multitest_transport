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

"""A module for unit test utilities in multitest_trasport/cli library."""
import collections
import zipfile

import six


File = collections.namedtuple('File', ['filename', 'content'])


def CreateZipFile(zipfile_path, files):
  """Create a zip file with a collection of files.

  Args:
    zipfile_path: a string, the path of created zip file.
    files: a collection of unittest_util.File tuples, filename and content are
      both strings.
  """
  with zipfile.ZipFile(zipfile_path, 'w') as zip_file:
    for name, content in files:
      zip_file.writestr(name, six.ensure_str(content))
