"""Tests for google3.third_party.py.multitest_transport.sidekicks.main."""

from absl.testing import absltest
import mock
import webtest

from multitest_transport.sidekicks import main
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import analytics


class MainTest(absltest.TestCase):
  """Unit test for main."""

  def setUp(self):
    super(MainTest, self).setUp()
    self.testapp = webtest.TestApp(main.APP)

  @mock.patch.object(analytics, 'Log')
  def testHeartbeatSender(self, mock_log):
    response = self.testapp.get('/sidekicks/heartbeat_sender')
    self.assertEqual('200 OK', response.status)
    mock_log.assert_called_once_with(
        analytics.SYSTEM_CATEGORY, analytics.HEARTBEAT_ACTION)

  @mock.patch.object(download_util, 'CleanTestResourceCache')
  def testTestResourceCacheCleaner(self, mock_clean_test_resource_cache):
    response = self.testapp.get('/sidekicks/test_resource_cache_cleaner')
    self.assertEqual('200 OK', response.status)
    self.assertTrue(mock_clean_test_resource_cache.called)

  @mock.patch.object(download_util, 'ReleaseDownloadLocks')
  def testTestResourceTrackerCleaner(self, mock_release_download_locks):
    response = self.testapp.get('/sidekicks/test_resource_tracker_cleaner')
    self.assertEqual('200 OK', response.status)
    self.assertTrue(mock_release_download_locks.called)


if __name__ == '__main__':
  absltest.main()
