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

"""Unit tests for web_hook."""
from unittest import mock

from absl.testing import absltest
from six.moves import urllib

from tradefed_cluster import testbed_dependent_test

from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.plugins.web_hook import WebHook


class WebHookTest(testbed_dependent_test.TestbedDependentTest):

  @mock.patch.object(urllib.request, 'urlopen')
  @mock.patch.object(urllib.request, 'Request')
  def testExecute(self, mock_request_ctor, mock_urlopen):
    webhook = WebHook(
        url='http://abc.com/xyz',
        http_method='POST',
        data='foo ${BAR} ${ZZZ}')
    mock_test_run = mock.MagicMock()
    mock_test_run.GetContext.return_value = {'BAR': 'bar', 'ZZZ': 'zzz'}
    mock_request = mock_request_ctor.return_value
    mock_response = mock_urlopen.return_value

    hook_context = plugins.TestRunHookContext(
        test_run=mock_test_run, phase=ndb_models.TestRunPhase.BEFORE_RUN)
    webhook.Execute(hook_context)

    mock_request_ctor.assert_called_with(
        url=webhook.url, data='foo bar zzz', headers={'X-MTT-HOST': mock.ANY})
    mock_urlopen.assert_called_with(mock_request)
    self.assertEqual('POST', mock_request.get_method())
    mock_response.read.assert_called_with()


if __name__ == '__main__':
  absltest.main()
