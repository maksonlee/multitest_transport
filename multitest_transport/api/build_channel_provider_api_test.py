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

"""Tests for build channel provider APIs."""

from absl.testing import absltest
from protorpc import protojson

from multitest_transport.api import api_test_util
from multitest_transport.api import build_channel_provider_api
from multitest_transport.models import messages
from multitest_transport.plugins import base as plugins


class MockBuildProvider(plugins.BuildProvider):
  """Dummy build provider for testing."""
  name = 'Mock'

  def __init__(self):
    super(MockBuildProvider, self).__init__()
    self.AddOptionDef('mock_option')


class BuildChannelProviderApiTest(api_test_util.TestCase):

  def setUp(self):
    super(BuildChannelProviderApiTest,
          self).setUp(build_channel_provider_api.BuildChannelProviderApi)

  def testList(self):
    response = self.app.get('/_ah/api/mtt/v1/build_channel_providers')
    res = protojson.decode_message(messages.BuildChannelProviderList,
                                   response.body)
    self.assertLen(res.build_channel_providers, 1)
    provider_names = [provider.name for provider in res.build_channel_providers]
    self.assertEqual(['Mock'], provider_names)

  def testGet(self):
    response = self.app.get('/_ah/api/mtt/v1/build_channel_providers/Mock')
    res = protojson.decode_message(messages.BuildChannelProvider, response.body)
    self.assertEqual(res.name, 'Mock')
    self.assertLen(res.option_defs, 1)
    self.assertEqual(res.option_defs[0].name, 'mock_option')


if __name__ == '__main__':
  absltest.main()
