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

"""Tests for analytics."""
from absl.testing import absltest
import mock
from six.moves import urllib

from google.appengine.ext import deferred
from google.appengine.ext import testbed

from multitest_transport.models import ndb_models
from multitest_transport.util import analytics
from multitest_transport.util import env


class AnalyticsTest(absltest.TestCase):

  def setUp(self):
    super(AnalyticsTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    env.VERSION = 'version'
    env.IS_GOOGLE = True
    analytics.TRACKING_ID = 'tracking_id'
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.server_uuid = 'server'
    private_node_config.metrics_enabled = False
    private_node_config.put()

  def assertValidEvent(self, data, server, category, action):
    """Confirms the base event information is present."""
    self.assertEqual(analytics._API_VERSION, data['v'])
    self.assertEqual(analytics._TRACKING_ID, data['tid'])
    self.assertEqual(server, data['cid'])
    self.assertEqual(analytics._EVENT_TYPE, data['t'])
    self.assertEqual(category, data['ec'])
    self.assertEqual(action, data['ea'])
    self.assertEqual(env.VERSION, data['cd1'])
    self.assertIn(data['cd6'], [True, 'True'])

  @mock.patch.object(deferred, 'defer')
  def testLog_enabled(self, mock_defer):
    """Tests that events are logged when metrics are enabled."""
    private_node_config = ndb_models.GetPrivateNodeConfig()
    private_node_config.metrics_enabled = True
    private_node_config.put()
    analytics.Log('category', 'action')
    mock_defer.assert_called_with(
        analytics._Send, analytics._Event('server', 'category', 'action'))

  @mock.patch.object(deferred, 'defer')
  def testLog_disabled(self, mock_defer):
    """Tests that events are not logged when metrics are disabled."""
    analytics.Log('category', 'action')
    mock_defer.assert_not_called()

  @mock.patch.object(urllib.request, 'urlopen')
  def testSend(self, urlopen):
    """Tests that events can be encoded and sent to GA."""
    event = analytics._Event('server', 'category', 'action')
    analytics._Send(event)

    request = urlopen.call_args[0][0]
    data = dict(urllib.parse.parse_qsl(request.data))
    self.assertEqual(analytics._GA_ENDPOINT, request.get_full_url())
    self.assertValidEvent(data, 'server', 'category', 'action')

  def testEvent_simple(self):
    """Tests that simple events can be constructed."""
    event = analytics._Event('server', 'category', 'action')
    data = dict(event)
    self.assertValidEvent(data, 'server', 'category', 'action')
    self.assertLen(data, 8)  # no additional fields

  def testEvent_complex(self):
    """Tests that complex events can be constructed."""
    event = analytics._Event('server', 'category', 'action',
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
    self.assertLen(data, 18)  # ten additional fields
    self.assertEqual('name', data['cd2'])
    self.assertEqual('version', data['cd3'])
    self.assertEqual('COMPLETED', data['cd4'])
    self.assertEqual(True, data['cd5'])
    self.assertEqual(0, data['cm1'])
    self.assertEqual(1, data['cm2'])
    self.assertEqual(2, data['cm3'])
    self.assertEqual(3, data['cm4'])
    self.assertEqual(4, data['cm5'])
    self.assertEqual(5, data['cm6'])


if __name__ == '__main__':
  absltest.main()
