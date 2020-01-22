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

"""Unit tests for test_plan_kicker module."""

import datetime
import json
import os.path

from absl.testing import absltest
import mock
import pytz

from google.appengine.ext import testbed

from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_kicker
from multitest_transport.test_scheduler import test_plan_kicker


class TestPlanKickerTest(absltest.TestCase):

  def setUp(self):
    root_path = os.path.dirname(__file__)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.testbed.init_taskqueue_stub(root_path=root_path)
    self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

  def tearDown(self):
    self.testbed.deactivate()

  @mock.patch.object(test_plan_kicker, '_GetCurrentTime', autospec=True)
  def testScheduleCronKick(self, get_current_time):
    now = datetime.datetime(1970, 1, 1, 0, 30, 0)
    get_current_time.return_value = now
    test_plan = ndb_models.TestPlan(name='foo', cron_exp='0 0 * * *')
    test_plan.put()
    test_plan_id = test_plan.key.id()
    next_run_time = datetime.datetime(1970, 1, 2, 0, 0, 0)

    test_plan_kicker.ScheduleCronKick(test_plan_id)

    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=[test_plan_kicker.TEST_PLAN_KICKER_QUEUE])
    self.assertEqual(1, len(tasks))
    task = tasks[0]
    self.assertEqual(pytz.UTC.localize(next_run_time), task.eta)
    data = json.loads(task.payload)
    self.assertEqual(test_plan_id, data['test_plan_id'])
    self.assertTrue(data['is_cron'])

  @mock.patch.object(test_plan_kicker, 'ScheduleCronKick', autospec=True)
  @mock.patch.object(test_kicker, 'CreateTestRun', autospec=True)
  def testKickTestPlan(self, create_test_run, schedule_cron_kick):
    test = ndb_models.Test(
        name='test',
        command='command',
        test_resource_defs=[
            ndb_models.TestResourceDef(name='res_1')
        ])
    test.put()
    test_device_action = ndb_models.DeviceAction(name='test_device_action')
    test_device_action.put()
    plan_device_action = ndb_models.DeviceAction(name='plan_device_action')
    plan_device_action.put()
    test_plan = ndb_models.TestPlan(
        name='test_plan',
        labels=['label'],
        cron_exp='0 0 * * *',
        test_run_configs=[
            ndb_models.TestRunConfig(
                test_key=test.key,
                cluster='cluster',
                run_target='run_target',
                before_device_action_keys=[test_device_action.key]),
        ],
        test_resource_pipes=[
            ndb_models.TestResourcePipe(name='res_1', url='url_1'),
            ndb_models.TestResourcePipe(name='res_2', url='url_2'),
        ],
        before_device_action_keys=[plan_device_action.key])
    test_plan.put()

    test_plan_kicker.KickTestPlan(test_plan.key.id())

    create_test_run.assert_called_with(
        labels=['label'],
        test_plan_key=test_plan.key,
        test_run_config=ndb_models.TestRunConfig(
            test_key=test_plan.test_run_configs[0].test_key,
            cluster=test_plan.test_run_configs[0].cluster,
            run_target=test_plan.test_run_configs[0].run_target,
            before_device_action_keys=[
                plan_device_action.key, test_device_action.key
            ]),
        test_resources=[
            ndb_models.TestResourceObj(name='res_1', url='url_1'),
            ndb_models.TestResourceObj(name='res_2', url='url_2'),
        ])
    schedule_cron_kick.assert_not_called()

  @mock.patch.object(test_plan_kicker, 'ScheduleCronKick', autospec=True)
  @mock.patch.object(test_kicker, 'CreateTestRun', autospec=True)
  @mock.patch.object(build, 'GetBuildChannel', autospec=True)
  def testKickTestPlan_withWildcardFilenames(
      self, get_build_channel, create_test_run, schedule_cron_kick):
    test = ndb_models.Test(
        name='test',
        command='command',
        test_resource_defs=[
            ndb_models.TestResourceDef(name='res_1')
        ])
    test.put()
    test_plan = ndb_models.TestPlan(
        name='test_plan',
        labels=['label'],
        cron_exp='0 0 * * *',
        test_run_configs=[
            ndb_models.TestRunConfig(
                test_key=test.key, cluster='cluster', run_target='run_target'),
        ],
        test_resource_pipes=[
            ndb_models.TestResourcePipe(
                name='res_1', url='mtt:///foo/bar/*.zip'),
        ])
    test_plan.put()
    mock_build_channel = mock.MagicMock()
    get_build_channel.return_value = mock_build_channel
    mock_build_item = build.BuildItem(name='bar', path='bar', is_file=False)
    mock_build_channel.GetBuildItem.return_value = mock_build_item
    mock_build_channel.ListBuildItems.return_value = ([
        build.BuildItem(name='zzz.dat', path='bar/zzz.dat', is_file=True),
        build.BuildItem(name='zzz.txt', path='bar/zzz.txt', is_file=True),
        build.BuildItem(name='zzz.zip', path='bar/zzz.zip', is_file=True),
    ], None)

    test_plan_kicker.KickTestPlan(test_plan.key.id())

    get_build_channel.assert_called_with('foo')
    mock_build_channel.GetBuildItem.assert_called_with('bar')
    mock_build_channel.ListBuildItems.assert_called_with(
        'bar', page_token=None, item_type=build.BuildItemType.FILE)
    create_test_run.assert_called_with(
        labels=['label'],
        test_plan_key=test_plan.key,
        test_run_config=ndb_models.TestRunConfig(
            test_key=test_plan.test_run_configs[0].test_key,
            cluster=test_plan.test_run_configs[0].cluster,
            run_target=test_plan.test_run_configs[0].run_target),
        test_resources=[
            ndb_models.TestResourceObj(
                name='res_1',
                url='mtt:///foo/bar/zzz.zip'),
        ])
    schedule_cron_kick.assert_not_called()

  @mock.patch.object(test_plan_kicker, 'ScheduleCronKick', autospec=True)
  @mock.patch.object(test_plan_kicker, '_GetCurrentTime', autospec=True)
  def testCheckTestPlanNextRuns(self, get_current_time, schedule_cron_kick):
    now = datetime.datetime(1970, 1, 1, 0, 30, 0)
    get_current_time.return_value = now
    test_plan = ndb_models.TestPlan(name='foo', cron_exp='0 0 * * *')
    test_plan.put()
    test_plan_status = ndb_models.TestPlanStatus(
        parent=test_plan.key,
        next_run_time=datetime.datetime(1970, 1, 1, 0, 0, 0))
    test_plan_status.put()

    test_plan_kicker.CheckTestPlanNextRuns()

    schedule_cron_kick.assert_called_with(test_plan.key.id(), next_run_time=now)

if __name__ == '__main__':
  absltest.main()
