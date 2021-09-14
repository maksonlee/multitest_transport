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
"""Tests for multitest_transport.file_cleaner.operation.py."""
import os

from absl.testing import absltest
from pyfakefs import fake_filesystem_unittest

from multitest_transport.file_cleaner import operation
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.util import env


class OperationTest(fake_filesystem_unittest.TestCase):
  """Tests Operation functionality."""

  def setUp(self):
    super(OperationTest, self).setUp()
    self.setUpPyfakefs()
    env.STORAGE_PATH = '/test'

  def testArchive(self):
    """Tests files can be archived and removed."""
    self.fs.create_file('/test/file')

    archive = operation.BuildOperation(
        messages.FileCleanerOperation(
            type=ndb_models.FileCleanerOperationType.ARCHIVE))
    archive.Apply('/test/file')

    self.assertTrue(os.path.exists('/test/file.zip'))
    self.assertFalse(os.path.exists('/test/file'))

  def testArchive_notRemoved(self):
    """Tests files can be archived and not removed."""
    self.fs.create_file('/test/file')

    archive = operation.BuildOperation(
        messages.FileCleanerOperation(
            type=ndb_models.FileCleanerOperationType.ARCHIVE,
            params=[messages.NameValuePair(name='remove_file', value='False')]))

    archive.Apply('/test/file')

    self.assertTrue(os.path.exists('/test/file.zip'))
    self.assertTrue(os.path.exists('/test/file'))

  def testDelete_file(self):
    """Tests files can be deleted."""
    self.fs.create_file('/test/file')

    delete = operation.BuildOperation(
        messages.FileCleanerOperation(
            type=ndb_models.FileCleanerOperationType.DELETE))
    delete.Apply('/test/file')

    self.assertFalse(os.path.exists('/test/file'))

  def testDelete_dir(self):
    """Tests directories can be deleted."""
    self.fs.create_dir('/test/dir')

    delete = operation.BuildOperation(
        messages.FileCleanerOperation(
            type=ndb_models.FileCleanerOperationType.DELETE))
    delete.Apply('/test/dir')

    self.assertFalse(os.path.exists('/test/dir'))


if __name__ == '__main__':
  absltest.main()
