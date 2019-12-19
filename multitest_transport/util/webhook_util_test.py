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

"""Tests for webhook_util."""
import urllib2



import mock
from protorpc import messages

from absl.testing import absltest
from multitest_transport.util import webhook_util


class HttpMethod(messages.Enum):
  """HTTP methods."""
  GET = 0
  POST = 1


class WebhookUtilTest(absltest.TestCase):

  @mock.patch.object(urllib2, 'urlopen')
  @mock.patch.object(urllib2, 'Request')
  def testInvokeWebhook(self, mock_request_ctor, mock_urlopen):
    webhook = mock.MagicMock(
        url='http://abc.com/xyz',
        http_method=HttpMethod.POST,
        data='foo ${BAR} ${ZZZ}')
    mock_req = mock_request_ctor.return_value
    mock_res = mock_urlopen.return_value

    webhook_util.InvokeWebhook(webhook, context={'BAR': 'bar', 'ZZZ': 'zzz'})

    mock_request_ctor.assert_called_with(url=webhook.url, data='foo bar zzz')
    mock_urlopen.assert_called_with(mock_req)
    self.assertEqual('POST', mock_req.get_method())
    mock_res.read.assert_called_with()

if __name__ == '__main__':
  absltest.main()
