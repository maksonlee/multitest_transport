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

"""Tests for tfc_client."""
import threading

from absl.testing import absltest
import apiclient.discovery
import mock

from google.appengine.api import modules
from google.appengine.ext import testbed

from multitest_transport.util import tfc_client


class TfcClientTest(absltest.TestCase):

  def setUp(self):
    super(TfcClientTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)
    tfc_client._tls = threading.local()

  @mock.patch.object(apiclient.discovery, 'build')
  def testGetAPIClient(self, mock_build):
    hostname = modules.get_hostname('default')

    api_client = tfc_client._GetAPIClient()

    mock_build.assert_called_with(
        tfc_client.API_NAME, tfc_client.API_VERSION,
        discoveryServiceUrl=tfc_client.API_DISCOVERY_URL_FORMAT % (
            hostname, tfc_client.API_NAME, tfc_client.API_VERSION))
    self.assertEqual(mock_build(), api_client)


if __name__ == '__main__':
  absltest.main()
