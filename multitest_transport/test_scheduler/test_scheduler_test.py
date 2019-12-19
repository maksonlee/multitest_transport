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

"""Unit tests for test_scheduler module."""

import datetime

import mock

from google.appengine.ext import testbed
from absl.testing import absltest
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_kicker
from multitest_transport.test_scheduler import test_scheduler


class TestSchedulerTest(absltest.TestCase):
  """Unit tests for test_scheduler module."""

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

  def tearDown(self):
    self.testbed.deactivate()

  def _CreateTestRun(self, state=None, create_time=None):
    """Creates a test run.

    Args:
      state: a test run state.
      create_time: a test run create time.
    Returns:
      a ndb_models.TestRun object.
    """
    test = ndb_models.Test(name='test', command='command')
    test.put()
    test_run_config = ndb_models.TestRunConfig(
        test_key=test.key, cluster='cluster', run_target='run_target')
    test_resources = [
        ndb_models.TestResourceObj(name='foo', url='http://foo_origin_url'),
        ndb_models.TestResourceObj(name='bar', url='https://bar_origin_url'),
    ]
    test_run = ndb_models.TestRun(
        labels=['label'],
        test=test,
        test_run_config=test_run_config,
        test_resources=test_resources,
        state=state or ndb_models.TestRunState.PENDING,
        create_time=create_time)
    test_run.put()
    return test_run

  @mock.patch.object(test_kicker, 'EnqueueTestRun')
  def testCheckPendingTestRuns_less_than_24hr(self, mock_enqueue_test_run):
    test_run = self._CreateTestRun(
        state=ndb_models.TestRunState.PENDING,
        create_time=datetime.datetime.utcnow())
    test_scheduler.CheckPendingTestRuns()
    mock_enqueue_test_run.assert_called_with(test_run.key.id())

  def testCheckPendingTestRuns_more_than_24hr(self):
    create_time = datetime.datetime.utcnow() - datetime.timedelta(
        seconds=(test_scheduler._PENDING_TEST_RUN_TTL + 1))
    test_run = self._CreateTestRun(
        state=ndb_models.TestRunState.PENDING,
        create_time=create_time)
    test_scheduler.CheckPendingTestRuns()
    self.assertEqual(ndb_models.TestRunState.CANCELED, test_run.state)

if __name__ == '__main__':
  absltest.main()
