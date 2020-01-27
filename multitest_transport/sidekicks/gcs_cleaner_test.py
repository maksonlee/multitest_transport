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

"""Unit tests for gcs_cleaner."""
import datetime

from absl.testing import absltest
import mock

from google.appengine.ext import testbed

from multitest_transport.models import ndb_models
from multitest_transport.sidekicks import gcs_cleaner
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import env
from multitest_transport.util import gcs_util


class GcsCleanerTest(absltest.TestCase):

  def setUp(self):
    super(GcsCleanerTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)

  @mock.patch.object(gcs_util, 'DeleteFiles', autospec=True)
  def testCleanupTestResourceCache(self, mock_delete_files):
    test_run = ndb_models.TestRun(
        test_resources=[
            ndb_models.TestResourceObj(url='foo'),
            ndb_models.TestResourceObj(url='bar'),
        ])
    test_run.put()
    test_run2 = ndb_models.TestRun(
        test_resources=[
            ndb_models.TestResourceObj(url='bar'),
            ndb_models.TestResourceObj(url='zzz'),
        ],
        create_time=datetime.datetime.utcnow() - datetime.timedelta(days=14))
    test_run2.put()
    files_to_keep = set([
        download_util.GetCacheFilename(obj.url)
        for obj in test_run.test_resources
    ])

    gcs_cleaner._CleanupTestResourceCache()

    mock_delete_files.assert_called_with(
        download_util.TEST_RESOURCE_CACHE_PATH,
        files_to_keep=files_to_keep,
        max_file_age_seconds=gcs_cleaner.RECENT_TEST_RUN_WINDOW_DAYS * 86400)

  @mock.patch.object(gcs_util, 'DeleteFiles', autospec=True)
  def testCleanupTempFiles(self, mock_delete_files):
    gcs_cleaner._CleanupTempFiles()

    mock_delete_files.assert_called_with(
        env.GCS_TEMP_PATH,
        max_file_age_seconds=gcs_cleaner.MAX_TEMP_FILE_AGE_DAYS * 86400)

if __name__ == '__main__':
  absltest.main()
