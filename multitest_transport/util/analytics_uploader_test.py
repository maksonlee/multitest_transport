# Copyright 2020 Google LLC
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

"""Tests for analytics_uploader."""
from absl.testing import absltest
import mock
import six
from six.moves import urllib
from tradefed_cluster import testbed_dependent_test

from multitest_transport.models import ndb_models
from multitest_transport.util import analytics_uploader
from multitest_transport.util import env


class AnalyticsUploaderTest(testbed_dependent_test.TestbedDependentTest):

  def setUp(self):
    super(AnalyticsUploaderTest, self).setUp()
    env.VERSION = 'version'
    env.IS_GOOGLE = True
    analytics_uploader._UPLOAD_ERROR_COUNT.value = 0
    analytics_uploader._TRACKING_ID = 'tracking_id'
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.server_uuid = 'server'
    private_node_config.metrics_enabled = True
    private_node_config.gms_client_id = 'test_user_tag'
    private_node_config.put()

  def assertValidEvent(self, data, server, category, action):
    """Confirms the base event information is present."""
    self.assertEqual(analytics_uploader._API_VERSION, data['v'])
    self.assertEqual(analytics_uploader._TRACKING_ID, data['tid'])
    self.assertEqual(server, data['cid'])
    self.assertEqual(analytics_uploader._EVENT_TYPE, data['t'])
    self.assertEqual(category, data['ec'])
    self.assertEqual(action, data['ea'])
    self.assertEqual(env.VERSION, data['cd1'])
    self.assertIn(data['cd6'], [True, 'True'])

  @mock.patch.object(urllib.request, 'urlopen')
  def testUploadEvent(self, mock_urlopen):
    """Tests that events are sent to GA when metrics are enabled."""
    uploaded = analytics_uploader._UploadEvent('category', 'action')
    self.assertTrue(uploaded)
    request = mock_urlopen.call_args[0][0]
    data = dict(urllib.parse.parse_qsl(six.ensure_text(request.data)))
    self.assertEqual(analytics_uploader._GA_ENDPOINT, request.get_full_url())
    self.assertValidEvent(data, 'server', 'category', 'action')

  @mock.patch.object(urllib.request, 'urlopen')
  def testUploadEvent_disabled(self, mock_urlopen):
    """Tests that events are not sent when metrics are disabled."""
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.metrics_enabled = False
    private_node_config.put()
    uploaded = analytics_uploader._UploadEvent('category', 'action')
    self.assertFalse(uploaded)
    mock_urlopen.assert_not_called()

  @mock.patch.object(urllib.request, 'urlopen')
  def testUploadEvent_tooManyErrors(self, mock_urlopen):
    """Tests that events are not sent after too many upload errors."""
    mock_urlopen.side_effect = RuntimeError()
    # Should fail up to the maximum consecutive error count
    for _ in range(analytics_uploader.MAX_CONSECUTIVE_UPLOAD_ERRORS):
      with self.assertRaises(RuntimeError):
        analytics_uploader._UploadEvent('category', 'action')
    # Next calls will be ignored (metrics upload disabled)
    uploaded = analytics_uploader._UploadEvent('category', 'action')
    self.assertFalse(uploaded)

  def testEvent_simple(self):
    """Tests that simple events can be constructed."""
    event = analytics_uploader._Event('server', 'category', 'action')
    data = dict(event)
    self.assertValidEvent(data, 'server', 'category', 'action')
    self.assertLen(data, 9)  # no additional fields

  def testEvent_complex(self):
    """Tests that complex events can be constructed."""
    event = analytics_uploader._Event('server', 'category', 'action',
                                      test_name='name',
                                      test_version='version',
                                      state='COMPLETED',
                                      is_rerun=True,
                                      duration_seconds=0,
                                      device_count=1,
                                      attempt_count=2,
                                      failed_module_count=3,
                                      test_count=4,
                                      failed_test_count=5)
    data = dict(event)
    self.assertValidEvent(data, 'server', 'category', 'action')
    self.assertLen(data, 19)  # ten additional fields
    self.assertEqual('name', data['cd2'])
    self.assertEqual('version', data['cd3'])
    self.assertEqual('COMPLETED', data['cd4'])
    self.assertEqual(True, data['cd5'])
    self.assertEqual('test_user_tag', data['cd14'])
    self.assertEqual(0, data['cm1'])
    self.assertEqual(1, data['cm2'])
    self.assertEqual(2, data['cm3'])
    self.assertEqual(3, data['cm4'])
    self.assertEqual(4, data['cm5'])
    self.assertEqual(5, data['cm6'])


if __name__ == '__main__':
  absltest.main()
