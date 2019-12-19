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

"""Cleans up files in GCS based on policies."""

import datetime
import logging

from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import env
from multitest_transport.util import gcs_util

RECENT_TEST_RUN_WINDOW_DAYS = 7
MAX_TEMP_FILE_AGE_DAYS = 7


def Start():
  """Cleanup GCS."""
  _CleanupTestResourceCache()
  _CleanupTempFiles()


def _CleanupTestResourceCache():
  """Cleanup test resource cache."""
  now = datetime.datetime.utcnow()
  min_create_time = (now - datetime.timedelta(days=RECENT_TEST_RUN_WINDOW_DAYS))
  logging.info(
      'Cleaning up test resource cache: deleting ones not used since %s (UTC)',
      min_create_time)
  query = ndb_models.TestRun.query(
      ndb_models.TestRun.create_time >= min_create_time)
  test_resource_urls = []
  for test_run in query:
    test_resource_urls.extend([r.url for r in test_run.test_resources if r.url])
  files_to_keep = set([
      download_util.GetCacheFilename(url)
      for url in test_resource_urls
  ])
  gcs_util.DeleteFiles(
      download_util.TEST_RESOURCE_CACHE_PATH,
      files_to_keep=files_to_keep,
      max_file_age_seconds=datetime.timedelta(
          days=RECENT_TEST_RUN_WINDOW_DAYS).total_seconds())


def _CleanupTempFiles():
  """Cleanup temp files."""
  logging.info(
      'Cleaning up temp files: deleting files older than %s days',
      MAX_TEMP_FILE_AGE_DAYS)
  gcs_util.DeleteFiles(
      env.GCS_TEMP_PATH,
      max_file_age_seconds=datetime.timedelta(
          days=MAX_TEMP_FILE_AGE_DAYS).total_seconds())
