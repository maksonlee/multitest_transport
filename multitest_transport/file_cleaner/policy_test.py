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
"""Tests for multitest_transport.file_cleaner.policy.py."""
import os

from absl.testing import absltest
from multitest_transport.file_cleaner import policy
from multitest_transport.util import env
from pyfakefs import fake_filesystem_unittest


class PolicyTest(fake_filesystem_unittest.TestCase):
  """Tests Policy functionality."""

  def setUp(self):
    super(PolicyTest, self).setUp()
    self.setUpPyfakefs()
    env.STORAGE_PATH = '/test'

  def testPolicy_file(self):
    """Tests policy for files."""
    self.fs.create_dir('/test/path/dir')
    self.fs.create_file('/test/path/dir/file1.zip')
    self.fs.create_file('/test/path/dir/file2')
    self.fs.create_file('/test/path/dir/output.zip')
    self.fs.create_file('/test/path/file.zip')

    policy.Policy({
        'name':
            'name',
        'target':
            'FILE',
        'operation': {
            'type': 'DELETE'
        },
        'criteria': [{
            'type': 'NAME_MATCH',
            'params': {
                'pattern': 'file'
            }
        }, {
            'type': 'NAME_MATCH',
            'params': {
                'pattern': 'zip'
            }
        }]
    }).Apply('/test/path')

    self.assertTrue(os.path.exists('/test/path/dir'))
    self.assertFalse(os.path.exists('/test/path/dir/file1.zip'))
    self.assertTrue(os.path.exists('/test/path/dir/file2'))
    self.assertTrue(os.path.exists('/test/path/dir/output.zip'))
    self.assertFalse(os.path.exists('/test/path/file.zip'))

  def testPolicy_dir(self):
    """Tests policy for directories."""
    self.fs.create_dir('/test/path/dir_match_1')
    self.fs.create_dir('/test/path/dir_match_1/subdir')
    self.fs.create_dir('/test/path/dir_2')
    self.fs.create_dir('/test/path/dir_2/subdir_match')
    self.fs.create_file('/test/path/file_match')

    policy.Policy({
        'name': 'name',
        'target': 'DIRECTORY',
        'operation': {
            'type': 'ARCHIVE'
        },
        'criteria': [{
            'type': 'NAME_MATCH',
            'params': {
                'pattern': 'match'
            }
        }]
    }).Apply('/test/path')

    self.assertFalse(os.path.exists('/test/path/dir_match_1'))
    self.assertFalse(os.path.exists('/test/path/dir_match_1/subdir'))
    self.assertTrue(os.path.exists('/test/path/dir_match_1.zip'))
    self.assertTrue(os.path.exists('/test/path/dir_2'))
    self.assertTrue(os.path.exists('/test/path/dir_2/subdir_match'))
    self.assertTrue(os.path.exists('/test/path/file_match'))

  def testPolicy_noCriteria(self):
    """Tests policy without criteria."""
    self.fs.create_dir('/test/path/dir')
    self.fs.create_file('/test/path/dir/file1.zip')
    self.fs.create_file('/test/path/dir/file2')
    self.fs.create_file('/test/path/dir/output.zip')
    self.fs.create_file('/test/path/file.zip')

    policy.Policy({
        'name': 'name',
        'target': 'FILE',
        'operation': {
            'type': 'DELETE'
        }
    }).Apply('/test/path')

    self.assertFalse(os.path.exists('/test/path/dir/file1.zip'))
    self.assertFalse(os.path.exists('/test/path/dir/file2'))
    self.assertFalse(os.path.exists('/test/path/dir/output.zip'))
    self.assertFalse(os.path.exists('/test/path/file.zip'))


if __name__ == '__main__':
  absltest.main()
