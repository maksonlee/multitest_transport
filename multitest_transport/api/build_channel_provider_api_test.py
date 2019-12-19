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


from protorpc import protojson

from absl.testing import absltest

from multitest_transport.api import api_test_util
from multitest_transport.api import build_channel_provider_api
from multitest_transport.models import build
from multitest_transport.models import messages


class BuildChannelProviderApiTest(api_test_util.TestCase):

  def setUp(self):
    super(BuildChannelProviderApiTest,
          self).setUp(build_channel_provider_api.BuildChannelProviderApi)

  def testList(self):
    response = self.app.get('/_ah/api/mtt/v1/build_channel_providers')
    res = protojson.decode_message(messages.BuildChannelProviderList,
                                   response.body)
    build_channel_providers = res.build_channel_providers
    provider_names = build.ListBuildProviderNames()
    self.assertEqual(len(provider_names), len(build_channel_providers))
    for build_channel_provider in build_channel_providers:
      self.assertIn(build_channel_provider.name, provider_names)

  def testGet(self):
    response = self.app.get('/_ah/api/mtt/v1/build_channel_providers/Android')
    res = protojson.decode_message(messages.BuildChannelProvider, response.body)
    option_defs = res.option_defs
    self.assertEqual(0, len(option_defs))
    self.assertEqual(res.name, 'Android')

    response = self.app.get(
        '/_ah/api/mtt/v1/build_channel_providers/Google%20Cloud%20Storage')
    res = protojson.decode_message(messages.BuildChannelProvider, response.body)
    option_defs = res.option_defs
    self.assertEqual(0, len(option_defs))
    self.assertEqual(res.name, 'Google Cloud Storage')


if __name__ == '__main__':
  absltest.main()
