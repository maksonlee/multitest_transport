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

from absl.testing import absltest
import mock
from tradefed_cluster import api_common
from tradefed_cluster import testbed_dependent_test

from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import file_util


class DownloadUtilTest(testbed_dependent_test.TestbedDependentTest):

  def setUp(self):
    super(DownloadUtilTest, self).setUp()
    # Prevent auto-updating timestamp
    ndb_models.TestResourceTracker.update_time._auto_now = False

  def CreateMockTracker(self, url, timedelta):
    """Create a placeholder resource tracker."""
    update_time = datetime.datetime.utcnow() + timedelta
    tracker = ndb_models.TestResourceTracker(
        id=url, download_progress=0.0, update_time=update_time)
    tracker.put()
    return tracker

  @mock.patch.object(download_util, 'DownloadResource')
  @mock.patch.object(api_common, 'with_ndb_context')
  def testDownloadResources(self, mock_ndb_wrapper, mock_download):
    """Tests that multiple resources can be downloaded in parallel."""
    def _MockDownload(url, **_):
      return {'a': 'cached_a', 'b': 'cached_b'}[url]
    mock_download.side_effect = _MockDownload
    def _MockWrapper(method):
      return method
    mock_ndb_wrapper.side_effect = _MockWrapper
    # Resources are downloaded and a map of urls to cache_urls is returned
    cached_urls = download_util.DownloadResources(['a', 'b'])
    self.assertEqual({'a': 'cached_a', 'b': 'cached_b'}, cached_urls)
    mock_download.assert_has_calls([
        mock.call('a', test_run=None),
        mock.call('b', test_run=None),
    ], any_order=True)

  @mock.patch.object(download_util, 'DownloadResource')
  @mock.patch.object(api_common, 'with_ndb_context')
  def testDownloadResources_error(self, mock_ndb_wrapper, mock_download):
    """Tests that errors are handled when downloading multiple resources."""
    def _MockDownload(url, **_):
      if url == 'a':
        return 'cached_a'
      raise ValueError()
    mock_download.side_effect = _MockDownload
    def _MockWrapper(method):
      return method
    mock_ndb_wrapper.side_effect = _MockWrapper
    # Resources are downloaded and the first error is raised
    with self.assertRaises(ValueError):
      download_util.DownloadResources(['a', 'b'])
    mock_download.assert_has_calls([
        mock.call('a', test_run=None),
        mock.call('b', test_run=None),
    ], any_order=True)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource(self, mock_handle_factory, mock_download_file):
    # Source URL and mock handle
    url = 'http://www.foo.com/bar/zzz.ext'
    src_handle = mock.MagicMock()
    # Destination URL and mock handle (not cached and tracks writing)
    dst_url = download_util.GetCacheUrl(url)
    dst_file = mock.MagicMock()
    dst_handle = mock.MagicMock()
    dst_handle.Info.return_value = None
    dst_handle.Open.return_value.__enter__.return_value = dst_file
    # Return right handle based on URL
    mock_handle_factory.side_effect = {url: src_handle, dst_url: dst_handle}.get
    # File downloaded in two chunks
    mock_download_file.return_value = [
        file_util.FileChunk(data=b'hello', offset=5, total_size=10),
        file_util.FileChunk(data=b'world', offset=10, total_size=10),
    ]

    cache_url = download_util.DownloadResource(url)
    self.assertEqual(dst_url, cache_url)
    # File downloaded, written to destination, and tracker updated
    mock_download_file.assert_called_with(url)
    dst_file.write.assert_has_calls([mock.call(b'hello'), mock.call(b'world')])
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    self.assertEqual(1.0, tracker.download_progress)
    self.assertTrue(tracker.completed)

  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(build, 'FindBuildChannel')
  def testDownloadResource_fromBuildChannel(self, mock_find_build_channel,
                                            mock_handle_factory):
    # Source URL, path, and mock build channel
    url = 'mtt:///build_channel_id/build_item_path'
    src_path = 'build_item_path'
    mock_build_channel = mock.MagicMock()
    mock_build_channel.GetBuildItem.return_value = build.BuildItem(
        name='name', path=src_path, is_file=True)
    mock_find_build_channel.return_value = mock_build_channel, src_path
    # Destination URL and mock handle (not cached and tracks writing)
    dst_url = download_util.GetCacheUrl(url)
    dst_file = mock.MagicMock()
    dst_handle = mock.MagicMock()
    dst_handle.Open.return_value.__enter__.return_value = dst_file
    mock_handle_factory.side_effect = {dst_url: dst_handle}.get
    # File downloaded in two chunks
    mock_build_channel.DownloadFile.return_value = [
        file_util.FileChunk(data=b'hello', offset=5, total_size=10),
        file_util.FileChunk(data=b'world', offset=10, total_size=10),
    ]

    cache_url = download_util.DownloadResource(url)
    self.assertEqual(dst_url, cache_url)
    # File downloaded from channel, written to destination, and tracker updated
    mock_find_build_channel.assert_called_with(url)
    mock_build_channel.DownloadFile.assert_called_with(src_path)
    dst_file.write.assert_has_calls([mock.call(b'hello'), mock.call(b'world')])
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    self.assertEqual(1.0, tracker.download_progress)
    self.assertTrue(tracker.completed)

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_existingFile(self, mock_handle_factory,
                                        mock_download_file):
    # Source URL nad mock handle (with size and timestamp)
    url = 'http://www.foo.com/bar/zzz.ext'
    src_handle = mock.MagicMock()
    src_handle.Info.return_value = file_util.FileInfo(
        url=url, total_size=123, timestamp=datetime.datetime(1990, 1, 1))
    # Destination URL and mock handle (valid size and up-to-date timestamp)
    dst_url = download_util.GetCacheUrl(url)
    dst_handle = mock.MagicMock()
    dst_handle.Info.return_value = file_util.FileInfo(
        url=dst_url, total_size=123, timestamp=datetime.datetime(1990, 1, 1))
    # Return right handle based on URL
    mock_handle_factory.side_effect = {url: src_handle, dst_url: dst_handle}.get

    cache_url = download_util.DownloadResource(url)
    self.assertEqual(dst_url, cache_url)
    # Download skipped due to cached file
    mock_download_file.assert_not_called()

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_outOfDate(self, mock_handle_factory,
                                     mock_download_file):
    # Source URL nad mock handle (with size and timestamp)
    url = 'http://www.foo.com/bar/zzz.ext'
    src_handle = mock.MagicMock()
    src_handle.Info.return_value = file_util.FileInfo(
        123, 'type', datetime.datetime(2000, 1, 1))
    # Destination URL and mock handle (timestamp out of date)
    dst_url = download_util.GetCacheUrl(url)
    dst_handle = mock.MagicMock()
    dst_handle.Info.return_value = file_util.FileInfo(
        123, 'type', datetime.datetime(1990, 1, 1))
    # Return right handle based on URL
    mock_handle_factory.side_effect = {url: src_handle, dst_url: dst_handle}.get

    cache_url = download_util.DownloadResource(url)
    self.assertEqual(dst_url, cache_url)
    # downloaded file despite cached file
    mock_download_file.assert_called_with(url)

  @mock.patch.object(download_util.TestResourceDownloader, '_WaitForDownload')
  @mock.patch.object(download_util.TestResourceDownloader,
                     '_TryAcquireDownloadLock')
  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_alreadyDownloading(self, mock_handle_factory,
                                              mock_download_file,
                                              mock_acquire_lock, mock_wait):
    # Source and destination URLs and handles
    url = 'http://www.foo.com/bar/zzz.ext'
    src_handle = mock.MagicMock()
    dst_url = download_util.GetCacheUrl(url)
    dst_handle = mock.MagicMock()
    dst_handle.Info.return_value = None
    mock_handle_factory.side_effect = {url: src_handle, dst_url: dst_handle}.get
    # Did not acquire download lock
    mock_acquire_lock.return_value = False

    cache_url = download_util.DownloadResource(url)
    self.assertEqual(dst_url, cache_url)
    # Waited for download instead of downloading
    mock_download_file.assert_not_called()
    mock_wait.assert_called_once()

  @mock.patch.object(file_util, 'DownloadFile')
  @mock.patch.object(file_util.FileHandle, 'Get')
  def testDownloadResource_error(self, mock_handle_factory, mock_download_file):
    # Source and destination URLs and handles
    url = 'http://www.foo.com/bar/zzz.ext'
    src_handle = mock.MagicMock()
    dst_url = download_util.GetCacheUrl(url)
    dst_handle = mock.MagicMock()
    dst_handle.Info.return_value = None
    mock_handle_factory.side_effect = {url: src_handle, dst_url: dst_handle}.get
    # Download will encounter an error
    mock_download_file.side_effect = RuntimeError('download error')

    # Error is propagated
    with self.assertRaises(RuntimeError):
      download_util.DownloadResource(url)
    # Download tracker has error message
    tracker = ndb_models.TestResourceTracker.get_by_id(url)
    error = tracker.error
    self.assertEqual('download error', error)

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testTryAcquireDownloadLock(self, mock_handle_factory):
    mock_handle_factory.return_value = mock.MagicMock()
    downloader = download_util.TestResourceDownloader('url')

    # lock acquired if tracker does not exist
    self.assertTrue(downloader._TryAcquireDownloadLock())

    # tracker was created
    self.assertIsNotNone(ndb_models.TestResourceTracker.get_by_id('url'))

    # lock not acquired from subsequent attempts
    self.assertFalse(downloader._TryAcquireDownloadLock())

    # lock re-acquired if tracker has an error, and error is cleared
    downloader._UpdateTracker(0.0, error='test')
    self.assertTrue(downloader._TryAcquireDownloadLock())
    tracker = ndb_models.TestResourceTracker.get_by_id('url')
    self.assertIsNone(tracker.error)

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testIsDownloadComplete(self, mock_handle_factory):
    mock_handle_factory.return_value = mock.MagicMock()
    downloader = download_util.TestResourceDownloader('url')

    # throws if download tracker not found
    with self.assertRaises(RuntimeError):
      downloader._IsDownloadComplete()

    # create download tracker, initially not complete
    downloader._TryAcquireDownloadLock()
    self.assertFalse(downloader._IsDownloadComplete())

    # can mark download as complete
    downloader._UpdateTracker(1.0, completed=True)
    self.assertTrue(downloader._IsDownloadComplete())

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

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testCleanTestResourceCache(self, mock_handle_factory):
    """Tests that cached test resources can be deleted."""
    mock_handle_factory.return_value.ListFiles.return_value = [
        file_util.FileInfo(
            url='url',
            is_file=True,
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1))
    ]
    # File is deleted
    download_util.CleanTestResourceCache()
    mock_handle_factory.return_value.Delete.assert_called()

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testCleanTestResourceCache_directory(self, mock_handle_factory):
    """Tests that directories are ignored when cleaning cache."""
    mock_handle_factory.return_value.ListFiles.return_value = [
        file_util.FileInfo(
            url='url',
            is_file=False,
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1))
    ]
    # Directory is not deleted
    download_util.CleanTestResourceCache()
    mock_handle_factory.return_value.Delete.assert_not_called()

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testCleanTestResourceCache_recentlyUpdated(self, mock_handle_factory):
    """Tests that recently updated files are ignored when cleaning cache."""
    mock_handle_factory.return_value.ListFiles.return_value = [
        file_util.FileInfo(
            url='url', is_file=True, timestamp=datetime.datetime.utcnow())
    ]
    # Recently updated file is not deleted (timestamp > min_access_time)
    min_access_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    download_util.CleanTestResourceCache(min_access_time=min_access_time)
    mock_handle_factory.return_value.Delete.assert_not_called()

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testCleanTestResourceCache_recentlyUsed(self, mock_handle_factory):
    """Tests that recently used files are ignored when cleaning cache."""
    test_run = ndb_models.TestRun(test_resources=[
        ndb_models.TestResourceObj(name='resource', url='resource_url')
    ])
    test_run.put()
    # Cached resource is old but recently referenced
    mock_handle_factory.return_value.ListFiles.return_value = [
        file_util.FileInfo(
            url=download_util.GetCacheUrl('resource_url'),
            is_file=True,
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=1))
    ]
    # Recently used file is not deleted (test_run > min_access_time)
    min_access_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    download_util.CleanTestResourceCache(min_access_time=min_access_time)
    mock_handle_factory.return_value.Delete.assert_not_called()


if __name__ == '__main__':
  absltest.main()
