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
"""Tests for multitest_transport.file_cleaner.criterion.py."""
import time

from absl.testing import absltest
from pyfakefs import fake_filesystem_unittest

from multitest_transport.file_cleaner import criterion
from multitest_transport.models import ndb_models
from multitest_transport.models import messages


class CriterionTest(fake_filesystem_unittest.TestCase):
  """Tests Criterion functionality."""

  def setUp(self):
    super(CriterionTest, self).setUp()
    self.setUpPyfakefs()

  def _createFileWithMtime(self, file_name, days):
    self.fs.create_file(file_name)
    now = time.time()
    timestamp = now - days * 24 * 60 * 60
    self.fs.utime(file_name, times=(now, timestamp))

  def testLastModifiedTime(self):
    """Tests last modified time can be checked."""
    self._createFileWithMtime('/test/file_1', 8)
    self._createFileWithMtime('/test/file_2', 10)

    last_modified_time = criterion.BuildCriterion(
        messages.FileCleanerCriterion(
            type=ndb_models.FileCleanerCriterionType.LAST_MODIFIED_TIME,
            params=[messages.NameValuePair(name='ttl', value='9 days')]))

    self.assertFalse(last_modified_time.Apply('/test/file_1'))
    self.assertTrue(last_modified_time.Apply('/test/file_2'))

  def testNameMatch(self):
    """Tests names can match given pattern."""
    name_match = criterion.BuildCriterion(
        messages.FileCleanerCriterion(
            type=ndb_models.FileCleanerCriterionType.NAME_MATCH,
            params=[messages.NameValuePair(name='pattern', value='zip')]))
    self.assertTrue(name_match.Apply('/test/path/file.zip'))
    self.assertFalse(name_match.Apply('/test/path/file.txt'))
    self.assertFalse(name_match.Apply(''))

  def testNameMatch_defaultPattern(self):
    """Tests no name can match default pattern."""
    name_match = criterion.BuildCriterion(
        messages.FileCleanerCriterion(
            type=ndb_models.FileCleanerCriterionType.NAME_MATCH))
    self.assertFalse(name_match.Apply('file.txt'))
    self.assertFalse(name_match.Apply(''))

if __name__ == '__main__':
  absltest.main()
