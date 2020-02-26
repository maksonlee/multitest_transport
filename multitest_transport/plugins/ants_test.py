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

"""Unit tests for ants."""
from absl.testing import absltest
import mock

from tradefed_cluster import api_messages
from google.appengine.ext import testbed

from multitest_transport.models import ndb_models
from multitest_transport.plugins import ants
from multitest_transport.plugins import base as plugins


class AntsHookTest(absltest.TestCase):

  def setUp(self):
    super(AntsHookTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    # Initialize mock API client and hook under test
    self.client_patcher = mock.patch.object(ants.AntsHook, '_GetClient')
    self.client = self.client_patcher.start()()
    self.hook = ants.AntsHook(build_id='build_id', build_target='build_target')

  def tearDown(self):
    self.testbed.deactivate()
    super(AntsHookTest, self).tearDown()
    self.client_patcher.stop()

  def testCreateInvocation(self):
    """Tests that invocations can be created."""
    test_run = ndb_models.TestRun()
    test_run.put()
    self.client.invocation().insert().execute.return_value = {
        'invocationId': 'invocation_id'
    }

    # Inserts a new invocation and stores the ID
    self.hook._CreateInvocation(test_run)
    self.client.invocation().insert().execute.assert_called_once()
    self.assertEqual('invocation_id', test_run.hook_data[ants.INVOCATION_ID])

  def testCreateInvocation_alreadyCreated(self):
    """Tests that creation is skipped if invocation ID already defined."""
    test_run = ndb_models.TestRun(
        hook_data={ants.INVOCATION_ID: 'invocation_id'})
    test_run.put()

    # Skips sending insert invocation request
    self.hook._CreateInvocation(test_run)
    self.client.invocation().insert().execute.assert_not_called()

  def testCreateWorkUnit(self):
    """Tests that work units can be created."""
    test_run = ndb_models.TestRun(
        hook_data={ants.INVOCATION_ID: 'invocation_id'})
    test_run.put()
    task = plugins.TestRunTask(None, None, None, {})
    self.client.workunit().insert().execute.return_value = {
        'id': 'work_unit_id'
    }

    # Created a work unit and stored its ID
    self.hook._CreateWorkUnit(test_run, task)
    self.client.workunit().insert().execute.assert_called_once()
    self.assertEqual('work_unit_id', test_run.hook_data[ants.WORK_UNIT_ID])
    # Injected additional task options
    self.assertEqual(['build_id'], task.extra_options['cluster:build-id'])
    self.assertEqual(['build_target'],
                     task.extra_options['cluster:build-target'])
    self.assertEqual(
        ['invocation_id=invocation_id', 'work_unit_id=work_unit_id'],
        task.extra_options['invocation-data'])

  def testUpdateWorkUnit(self):
    """Tests that work units can be updated."""
    test_run = ndb_models.TestRun(
        hook_data={ants.WORK_UNIT_ID: 'work_unit_id'})
    test_run.put()
    attempt = api_messages.CommandAttemptMessage(
        request_id='id',
        command_id='id',
        attempt_id='id',
        task_id='id',
        state=api_messages.CommandState.ERROR)
    work_unit = {}
    self.client.workunit().get().execute.return_value = work_unit

    # Updates the work unit by adding a state field
    self.hook._UpdateWorkUnit(test_run, attempt)
    self.client.workunit().get().execute.assert_called_once()
    self.client.workunit().update().execute.assert_called_once()
    self.assertEqual('ERROR', work_unit['state'])

  def testUpdateInvocation(self):
    """Tests that invocations can be updated."""
    test_run = ndb_models.TestRun(
        state=ndb_models.TestRunState.COMPLETED,
        hook_data={ants.INVOCATION_ID: 'invocation_id'})
    test_run.put()
    invocation = {}
    self.client.invocation().get().execute.return_value = invocation

    # Updates the invocation by adding a schedulerState field
    self.hook._UpdateInvocation(test_run)
    self.client.invocation().get().execute.assert_called_once()
    self.client.invocation().update().execute.assert_called_once()
    self.assertEqual('COMPLETED', invocation['schedulerState'])


if __name__ == '__main__':
  absltest.main()
