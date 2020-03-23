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

"""Utilities for downloading test resources."""
import datetime
import logging
import time
import urllib2

import cloudstorage as gcs
import webapp2

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from multitest_transport.models import build
from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import gcs_util

TEST_RESOURCE_CACHE_PATH = env.GCS_ROOT_PATH + '/test_resources'
TEST_RESOURCE_CACHE_FILENAME_FORMAT = TEST_RESOURCE_CACHE_PATH + '/%s'
TEMP_FILENAME_FORMAT = env.GCS_TEMP_PATH + '/test_scheduler.download_util/{key}'


def GetCacheFilename(url):
  """Get a GCS cache filename for a remote resource.

  Args:
    url: a resource URL.
  Returns:
    a GCS filename.
  """
  if url.startswith('gs:/' + env.GCS_ROOT_PATH):
    # URL is already in local GCS, use it directly.
    return url[4:]
  return TEST_RESOURCE_CACHE_FILENAME_FORMAT % urllib2.quote(url, safe='')


def DownloadResource(url, test_run=None):
  """Download resource(s) to Google Cloud Storage.

  If a url starts with mtt://, this function tries to download a file from
  one of registered build channel via a corresponding build provider. Otherwise,
  it will use urllib2 to download a file.

  Args:
    url: resource URL.
    test_run: optional related test run
  Returns:
    a GCS download URL.
  """
  if url.startswith('file://'):
    return url  # Skip downloading local files

  logging.info('Downloading resource %s', url)
  downloader, src_path, dst_path, timestamp = _CreateDownloadContext(url)

  # Check if file already downloaded
  if gcs_util.Exists(dst_path):
    cache_timestamp = gcs.stat(dst_path).st_ctime
    if (timestamp and cache_timestamp and
        datetime.datetime.utcfromtimestamp(cache_timestamp) >= timestamp):
      logging.info('Resource already in local GCS: %s', dst_path)
      return gcs_util.GetDownloadUrl(dst_path)
    logging.info('Cached resource is out of date: %s', dst_path)

  # Download file or wait for another thread to download it
  if _TryAcquireDownloadLock(url):
    # TODO: enqueue all download tasks in parallel
    _PerformDownload(url, downloader, src_path, dst_path)
  else:
    # TODO: notify test run instead of waiting
    _WaitForDownload(url)

  if test_run:
    event_log.Info(test_run, 'Downloaded resource \'%s\'' % url)
  return gcs_util.GetDownloadUrl(dst_path)


def _CreateDownloadContext(url):
  """Determines the download context.

  Args:
    url: resource URL
  Returns:
    downloader: resource download function
    src_path: path to download from
    dst_path: path to download to
    timestamp: last modification datetime
  """
  build_channel, build_item_path = build.FindBuildChannel(url)
  if not build_channel:
    # URL does not match any build channel, use default download context
    info = file_util.FileHandle.Get(url).Info()
    timestamp = info.timestamp if info else None
    return file_util.DownloadFile, url, GetCacheFilename(url), timestamp

  # Corresponding build channel found, use that channel
  build_item = build_channel.GetBuildItem(build_item_path)
  if build_item and build_item.origin_url:
    url = build_item.origin_url
  timestamp = build_item.timestamp if build_item else None
  return build_channel.DownloadFile, build_item_path, GetCacheFilename(
      url), timestamp


@ndb.transactional()
def _TryAcquireDownloadLock(url):
  """Attempt to acquire a download lock.

  Either fetch an existing download tracker (lock not acquired and current
  thread should wait for download to complete), or create a new download tracker
  (lock acquired and current thread should perform the download).

  Args:
    url: resource URL
  Returns:
    True if lock was acquired
  """
  tracker = ndb_models.TestResourceTracker.get_by_id(url)
  if tracker and not tracker.error:
    return False
  tracker = ndb_models.TestResourceTracker(id=url)
  tracker.put()
  return True


def _WaitForDownload(url, poll_interval=10):
  """Wait for a download to complete."""
  logging.info('Waiting for download of %s to complete', url)
  while not _IsDownloadComplete(url):
    time.sleep(poll_interval)


def _IsDownloadComplete(url):
  """Check whether a download has completed."""
  return _GetTracker(url).completed


def _PerformDownload(url, downloader, src_path, dst_path):
  """Executes the download and updates the download progress."""
  try:
    logging.info('Starting download of %s', url)
    urlfetch.set_default_fetch_deadline(env.GCS_FETCH_DEADLINE_SECONDS)
    # Download file to temporary location
    tmp_path = TEMP_FILENAME_FORMAT.format(key=time.time())
    with gcs.open(tmp_path, 'w') as tmp_file:
      for data, offset, total_size in downloader(src_path):
        tmp_file.write(data)
        progress = float(offset) / float(total_size)
        _UpdateTracker(url, progress)
        # TODO: re-queue download task if taking too long

    logging.info('Finishing download of %s', url)
    # Move to final destination
    gcs.copy2(tmp_path, dst_path)
    gcs.delete(tmp_path)

    logging.info('Downloading %s completed', url)
    # Mark download as completed
    _UpdateTracker(url, 1.0, completed=True)
  except Exception as e:      logging.error('Failed to download %s: %s', url, e)
    _UpdateTracker(url, 0.0, error=str(e))
    raise e


@ndb.transactional()
def _UpdateTracker(url, download_progress, completed=False, error=None):
  """Update an existing download tracker."""
  tracker = _GetTracker(url)
  tracker.download_progress = download_progress
  tracker.completed = completed
  tracker.error = error
  tracker.put()


def _GetTracker(url):
  """Locate a download tracker and check its validity."""
  tracker = ndb_models.TestResourceTracker.get_by_id(url)
  if tracker is None:
    # Download tracker unexpectedly not found
    raise RuntimeError('Test resource tracker %s not found' % url)
  if tracker.error:
    # Error was encountered during download
    raise RuntimeError(tracker.error)
  return tracker


def ReleaseDownloadLocks(min_update_time=None):
  """Deletes resource trackers to release the download locks.

  Args:
    min_update_time: latest update timestamp to delete, or None to delete all
  """
  if min_update_time is None:
    min_update_time = datetime.datetime.utcnow()
  logging.info(
      'Cleaning up resource trackers not updated since %s (UTC)',
      min_update_time)
  keys_to_delete = ndb_models.TestResourceTracker.query(
      ndb_models.TestResourceTracker.update_time < min_update_time
  ).fetch(keys_only=True)
  ndb.delete_multi(keys_to_delete)


class TestResourceTrackerCleaner(webapp2.RequestHandler):
  """Request handler which periodically releases idle resource trackers."""

  def get(self):
    min_update_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    ReleaseDownloadLocks(min_update_time=min_update_time)
