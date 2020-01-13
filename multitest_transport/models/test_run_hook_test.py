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

"""Unit tests for run_hook."""
from absl.testing import absltest
import mock

from google.appengine.ext import testbed

from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.plugins import base as plugins


class MockHook(plugins.TestRunHook):
  name = 'mock'


class RunHookTest(absltest.TestCase):

  def setUp(self):
    super(RunHookTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  @mock.patch.object(test_run_hook, '_ExecuteHook')
  def testExecuteHooks(self, mock_execute_hook):
    """Tests that relevant hooks can be found and executed."""
    before_hook = ndb_models.TestRunHookConfig(
        hook_name='mock', phases=[ndb_models.TestRunPhase.BEFORE_RUN])
    after_hook = ndb_models.TestRunHookConfig(
        hook_name='mock', phases=[ndb_models.TestRunPhase.AFTER_RUN])
    # Create test run with two hooks
    test_run = ndb_models.TestRun(hook_configs=[before_hook, after_hook])
    test_run.put()
    # Execute after run hooks and verify
    test_run_hook.ExecuteHooks(test_run.key.id(),
                               ndb_models.TestRunPhase.AFTER_RUN)
    mock_execute_hook.assert_called_with(test_run,
                                         ndb_models.TestRunPhase.AFTER_RUN,
                                         after_hook)

  @mock.patch.object(test_run_hook, '_ExecuteHook')
  def testExecuteHooks_notFound(self, mock_execute_hook):
    """Tests that no hooks are executed if run not found."""
    test_run_hook.ExecuteHooks('unknown', ndb_models.TestRunPhase.AFTER_RUN)
    mock_execute_hook.assert_not_called()

  @mock.patch.object(MockHook, 'Execute')
  @mock.patch.object(MockHook, '__init__')
  def testExecuteHook(self, mock_init, mock_execute):
    """Tests that a hook can be constructed and executed."""
    mock_init.return_value = None
    test_run = ndb_models.TestRun()
    hook_config = ndb_models.TestRunHookConfig(
        hook_name='mock',
        options=[ndb_models.NameValuePair(name='ham', value='eggs')])
    test_run_hook._ExecuteHook(test_run, ndb_models.TestRunPhase.UNKNOWN,
                               hook_config)
    mock_init.assert_called_with(ham='eggs')
    mock_execute.assert_called_with(test_run, ndb_models.TestRunPhase.UNKNOWN)


if __name__ == '__main__':
  absltest.main()
