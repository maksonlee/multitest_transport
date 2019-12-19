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

"""Unit tests for cron_kicker."""

import datetime
import os
import pickle
import urllib2



import mock
import pytz
import webtest

from google.appengine.api.modules import modules
from google.appengine.ext import testbed
from absl.testing import absltest
from multitest_transport.core import cron_kicker


class CronKickerTest(absltest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.testbed.init_taskqueue_stub(root_path=os.path.dirname(__file__))
    self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    self.addCleanup(self.testbed.deactivate)

  @mock.patch.object(urllib2, 'urlopen')
  @mock.patch.object(modules, 'get_hostname')
  def testKick(self, mock_get_hostname, mock_urlopen):
    now = datetime.datetime.utcnow()
    cron_job = cron_kicker.CronJob(
        url='/foo', schedule='schedule', target='target', next_run_time=now)
    mock_get_hostname.return_value = 'localhost'

    cron_kicker.Kick(cron_job)

    mock_get_hostname.assert_called_with(module='target')
    mock_urlopen.assert_called_with('http://localhost/foo')
    self.assertIsNone(cron_job.next_run_time)

  @mock.patch.object(cron_kicker, '_GetCurrentTime')
  def testScheduleNextKick(self, mock_get_current_time):
    next_run_time = datetime.datetime(2000, 1, 1, 1, 0, 0)
    mock_get_current_time.return_value = next_run_time - datetime.timedelta(
        hours=1)
    cron_job = cron_kicker.CronJob(
        url='/foo', schedule='every 1 hours', target='target',
        next_run_time=None)

    cron_kicker.ScheduleNextKick(cron_job)

    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=[cron_kicker.CRON_KICKER_QUEUE])
    self.assertEqual(1, len(tasks))
    task = tasks[0]
    self.assertEqual(pytz.UTC.localize(next_run_time), task.eta)
    new_cron_job = pickle.loads(task.payload)
    self.assertEqual(cron_job.url, new_cron_job.url)
    self.assertEqual(cron_job.schedule, new_cron_job.schedule)
    self.assertEqual(cron_job.target, new_cron_job.target)
    self.assertEqual(next_run_time, new_cron_job.next_run_time)


class TaskHandlerTest(absltest.TestCase):

  def setUp(self):
    self.app = webtest.TestApp(cron_kicker.APP)

  @mock.patch.object(cron_kicker, 'ScheduleNextKick')
  @mock.patch.object(cron_kicker, 'Kick')
  def testTaskHandler(self, mock_kick, mock_schedule_next_kick):
    cron_job = cron_kicker.CronJob(
        url='/foo', schedule='every 1 hours', target='target',
        next_run_time=None)

    self.app.post(
        '/_ah/queue/%s' % cron_kicker.CRON_KICKER_QUEUE, pickle.dumps(cron_job))

    mock_kick.assert_called_with(cron_job)
    mock_schedule_next_kick.assert_called_with(cron_job)

if __name__ == '__main__':
  absltest.main()

