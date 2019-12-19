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

"""Unit tests for download_util."""
import datetime


import cloudstorage as gcs
import mock

from google.appengine.ext import testbed
from absl.testing import absltest
from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import file_util
from multitest_transport.util import gcs_util


class DownloadUtilTest(absltest.TestCase):

  def setUp(self):
    super(DownloadUtilTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)
    # Prevent auto-updating timestamp
    ndb_models.TestResourceTracker.update_time._auto_now = False

  def CreateMockTracker(self, url, timedelta):
    """Create a dummy resource tracker."""
    update_time = datetime.datetime.utcnow() + timedelta
    tracker = ndb_models.TestResourceTracker(id=url,
                                             download_progress=0.0,
                                             update_time=update_time)
    tracker.put()
    return tracker

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource(self, mock_handler_factory, mock_download_file):
    url = 'http://www.foo.com/bar/zzz.ext'
    dst_path = download_util.GetCacheFilename(url)
    mock_handler_factory.return_value = mock.MagicMock()

    def MockDownload(_):
      yield 'hello', 5, 10
      yield 'world', 5, 10
    mock_download_file.side_effect = MockDownload

    cache_url = download_util.DownloadResource(url)

    # downloader called with right arguments, and tracker updated
    mock_download_file.assert_called_with(url)
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    self.assertEqual(1.0, tracker.download_progress)
    self.assertTrue(tracker.completed)

    # file downloaded to local GCS
    self.assertEqual(gcs_util.GetDownloadUrl(dst_path), cache_url)
    stat = gcs.stat(dst_path)
    self.assertIsNotNone(stat)
    self.assertEqual(10, stat.st_size)

  @mock.patch.object(build, 'FindBuildChannel')
  def testDownloadResource_fromBuildChannel(self, mock_find_build_channel):
    url = 'mtt:///build_channel_id/build_item_path'
    src_path = 'build_item_path'
    dst_path = download_util.GetCacheFilename(url)
    mock_build_channel = mock.MagicMock()
    mock_build_channel.GetBuildItem.return_value = build.BuildItem(
        name='name',
        path=src_path,
        is_file=True)
    mock_find_build_channel.return_value = mock_build_channel, src_path

    def MockDownload(_):
      yield 'hello', 5, 10
      yield 'world', 5, 10
    mock_build_channel.DownloadFile.side_effect = MockDownload

    cache_url = download_util.DownloadResource(url)

    # build channel downloader called with right arguments, and tracker updated
    mock_find_build_channel.assert_called_with(url)
    mock_build_channel.DownloadFile.assert_called_with(src_path)
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    self.assertEqual(1.0, tracker.download_progress)
    self.assertTrue(tracker.completed)

    # file downloaded to local GCS
    self.assertEqual(gcs_util.GetDownloadUrl(dst_path), cache_url)
    stat = gcs.stat(dst_path)
    self.assertIsNotNone(stat)
    self.assertEqual(10, stat.st_size)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(gcs, 'stat')
  def testDownloadResource_existingFile(self, mock_stat, mock_handler_factory,
                                        mock_download_file):
    url = 'http://www.foo.com/bar/zzz.ext'
    dst_path = download_util.GetCacheFilename(url)
    # cached file is still valid
    mock_stat.return_value = mock.MagicMock(st_ctime=631152000)
    mock_handler = mock.MagicMock()
    mock_handler.Info.return_value = file_util.FileInfo(
        0, 'type', datetime.datetime(1990, 1, 1))
    mock_handler_factory.return_value = mock_handler

    cache_url = download_util.DownloadResource(url)

    # download skipped due to cached file
    mock_stat.assert_called_with(dst_path)
    mock_download_file.assert_not_called()
    self.assertEqual(gcs_util.GetDownloadUrl(dst_path), cache_url)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(gcs, 'stat')
  def testDownloadResource_outOfDate(self, mock_stat, mock_handler_factory,
                                     mock_download_file):
    url = 'http://www.foo.com/bar/zzz.ext'
    dst_path = download_util.GetCacheFilename(url)
    # cached file is out of date
    mock_stat.return_value = mock.MagicMock(st_ctime=631152000)
    mock_handler = mock.MagicMock()
    mock_handler.Info.return_value = file_util.FileInfo(
        0, 'type', datetime.datetime(2000, 1, 1))
    mock_handler_factory.return_value = mock_handler

    cache_url = download_util.DownloadResource(url)

    # downloaded file despite cached file
    mock_download_file.assert_called_with(url)
    self.assertEqual(gcs_util.GetDownloadUrl(dst_path), cache_url)

  @mock.patch.object(download_util, '_WaitForDownload')
  @mock.patch.object(download_util, '_TryAcquireDownloadLock')
  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_alreadyDownloading(self, mock_handler_factory,
                                              mock_download_file,
                                              mock_acquire_lock, mock_wait):
    url = 'http://www.foo.com/bar/zzz.ext'
    dst_path = download_util.GetCacheFilename(url)
    mock_handler_factory.return_value = mock.MagicMock()
    # did not acquire download lock
    mock_acquire_lock.return_value = False

    cache_url = download_util.DownloadResource(url)

    # waited for download instead of downloading
    mock_download_file.assert_not_called()
    mock_wait.assert_called_with(url)
    self.assertEqual(gcs_util.GetDownloadUrl(dst_path), cache_url)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_error(self, mock_handler_factory,
                                 mock_download_file):
    url = 'http://www.foo.com/bar/zzz.ext'
    mock_handler_factory.return_value = mock.MagicMock()
    # download will encounter an error
    mock_download_file.side_effect = RuntimeError('download error')

    # error is propagated
    with self.assertRaises(RuntimeError):
      download_util.DownloadResource(url)

    # download tracker has error message
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    error = tracker.error
    self.assertEqual('download error', error)

  def testTryAcquireDownloadLock(self):
    # lock acquired if tracker does not exist
    self.assertTrue(download_util._TryAcquireDownloadLock('url'))

    # tracker was created
    self.assertIsNotNone(ndb_models.TestResourceTracker.get_by_id('url'))

    # lock not acquired from subsequent attempts
    self.assertFalse(download_util._TryAcquireDownloadLock('url'))

    # lock re-acquired if tracker has an error, and error is cleared
    download_util._UpdateTracker('url', 0.0, error='test')
    self.assertTrue(download_util._TryAcquireDownloadLock('url'))
    tracker = ndb_models.TestResourceTracker.get_by_id('url')
    self.assertIsNone(tracker.error)

  def testIsDownloadComplete(self):
    # throws if download tracker not found
    with self.assertRaises(RuntimeError):
      download_util._IsDownloadComplete('url')

    # create download tracker, initially not complete
    download_util._TryAcquireDownloadLock('url')
    self.assertFalse(download_util._IsDownloadComplete('url'))

    # can mark download as complete
    download_util._UpdateTracker('url', 1.0, completed=True)
    self.assertTrue(download_util._IsDownloadComplete('url'))

  def testReleaseDownloadLocks(self):
    # create trackers with varying update times
    self.CreateMockTracker('1', datetime.timedelta(hours=0))
    self.CreateMockTracker('2', datetime.timedelta(hours=-1))

    # all should be deleted if min_update_time is not specified
    download_util.ReleaseDownloadLocks()
    self.assertIsNone(ndb_models.TestResourceTracker.get_by_id('1'))
    self.assertIsNone(ndb_models.TestResourceTracker.get_by_id('2'))

  def testReleaseDownloadLocks_minUpdateTime(self):
    # create trackers with varying update times
    self.CreateMockTracker('1', datetime.timedelta(minutes=0))
    self.CreateMockTracker('2', datetime.timedelta(minutes=-40))
    self.CreateMockTracker('3', datetime.timedelta(minutes=-80))
    self.CreateMockTracker('4', datetime.timedelta(minutes=-120))

    # only those updated before the min_update_time should be deleted
    min_update_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    download_util.ReleaseDownloadLocks(min_update_time=min_update_time)
    self.assertIsNotNone(ndb_models.TestResourceTracker.get_by_id('1'))
    self.assertIsNotNone(ndb_models.TestResourceTracker.get_by_id('2'))
    self.assertIsNone(ndb_models.TestResourceTracker.get_by_id('3'))
    self.assertIsNone(ndb_models.TestResourceTracker.get_by_id('4'))


if __name__ == '__main__':
  absltest.main()
