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

"""Unit tests for ndb_upgrader."""

from absl.testing import absltest
from tradefed_cluster.util import ndb_test_lib

from multitest_transport.core import ndb_upgrader
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models


class NdbUpgraderTest(ndb_test_lib.NdbWithContextTest):

  # Mocking functions
  def _CreateMockTest(self, test_id='test.id', name='test name'):
    """Creates a mock ndb_models.Test object."""
    test = ndb_models.Test(name=name, command='command')
    test.key = mtt_messages.ConvertToKey(ndb_models.Test, test_id)
    test.put()
    return test

  def _CreateMockTestRunConfig(self, test, device_action_keys=None,
                               cluster='cluster'):
    """Creates a mock ndb_models.TestRunConfig object."""
    config = ndb_models.TestRunConfig(
        test_key=test.key, before_device_action_keys=device_action_keys,
        cluster=cluster, run_target='run_target')
    return config

  def _CreateMockTestPlan(self, configs, device_action_keys=None,
                          test_resource_pipes=None):
    """Creates a mock ndb_models.TestPlan object."""
    test_plan = ndb_models.TestPlan(
        test_run_configs=configs, name='name',)
    test_plan.put()
    return test_plan

  # Update function tests
  def testUpdate25001(self):
    test = self._CreateMockTest()
    config_1 = self._CreateMockTestRunConfig(test, [], 'cluster1')
    config_2 = self._CreateMockTestRunConfig(test, [], 'cluster2')
    test_plan = self._CreateMockTestPlan([config_1, config_2], [], [])

    ndb_upgrader.Update25001()

    updated_test_plan = test_plan.key.get()
    sequences = updated_test_plan.test_run_sequences
    self.assertEqual(len(sequences), 2)
    self.assertEqual(len(sequences[0].test_run_configs), 1)
    self.assertEqual(len(sequences[1].test_run_configs), 1)
    self.assertEqual(sequences[0].test_run_configs[0].cluster, 'cluster1')
    self.assertEqual(sequences[1].test_run_configs[0].cluster, 'cluster2')


if __name__ == '__main__':
  absltest.main()
