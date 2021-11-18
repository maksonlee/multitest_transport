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

"""MTT base integration tests."""
import logging

from absl.testing import absltest
import requests

from multitest_transport.integration_test import integration_util


class BaseIntegrationTest(integration_util.DockerContainerTest):
  """"Tests that MTT can be launched and initialized successfully."""

  def testServer(self):
    """Tests that the MTT server was started."""
    requests.get(self.container.base_url).raise_for_status()

  def testInitialState_runs(self):
    """Tests that there are no test runs initially."""
    response = requests.get(self.container.mtt_api_url + '/test_runs')
    response.raise_for_status()
    test_runs = response.json().get('test_runs', [])
    self.assertEmpty(test_runs)

  def testInitialState_tests(self):
    """Tests that the default tests are loaded from config.yaml."""
    response = requests.get(self.container.mtt_api_url + '/tests')
    response.raise_for_status()
    tests = response.json().get('tests', [])
    self.assertNotEmpty(tests)
    test_ids = [test['id'] for test in tests]
    self.assertIn('noop', test_ids)
    self.assertIn('android.cts.8_0.arm', test_ids)
    self.assertIn('android.cts.10_0.arm', test_ids)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  absltest.main()
