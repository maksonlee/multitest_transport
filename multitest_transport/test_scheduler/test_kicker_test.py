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

"""Unit tests for test_kicker module."""
import json
import os
import uuid
from absl.testing import absltest

import mock
from tradefed_cluster import api_messages
from tradefed_cluster import common
import webtest

from google.appengine.ext import testbed
from multitest_transport.models import messages
from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.test_scheduler import download_util
from multitest_transport.test_scheduler import test_kicker
from multitest_transport.util import analytics
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client


class TestKickerTest(absltest.TestCase):

  def setUp(self):
    super(TestKickerTest, self).setUp()
    root_path = os.path.dirname(__file__)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.testbed.init_taskqueue_stub(root_path=root_path)
    self.testapp = webtest.TestApp(test_kicker.APP)
    self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    self.hostname = 'HOST:8000'
    os.environ['DEFAULT_VERSION_HOSTNAME'] = self.hostname

  def tearDown(self):
    super(TestKickerTest, self).tearDown()
    self.testbed.deactivate()

  def testCreateTestRun(self):
    test = ndb_models.Test(
        name='test', command='command', test_resource_defs=[
            ndb_models.TestResourceDef(
                name='foo', default_download_url='default_download_url'),
            ndb_models.TestResourceDef(
                name='bar', default_download_url='default_download_url'),
        ])
    test.put()
    test_run_config = ndb_models.TestRunConfig(
        test_key=test.key, cluster='cluster', run_target='run_target')
    test_resources = [
        ndb_models.TestResourceObj(
            name='foo', url='origin_url', cache_url='cache_url'),
    ]

    test_run = test_kicker.CreateTestRun(
        ['label'], test_run_config, test_resources)

    test_run = ndb_models.TestRun.get_by_id(test_run.key.id())
    self.assertEqual(test, test_run.test)
    self.assertEqual(['label'], test_run.labels)
    self.assertEqual(test_run_config, test_run.test_run_config)
    self.assertCountEqual([
        ndb_models.TestResourceObj(
            name='bar', url='default_download_url'),
        ndb_models.TestResourceObj(
            name='foo', url='origin_url', cache_url='cache_url'),
    ], test_run.test_resources)
    self.assertEqual(ndb_models.TestRunState.PENDING, test_run.state)
    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=[test_kicker.TEST_KICKER_QUEUE])
    self.assertEqual(1, len(tasks))
    task = tasks[0]
    data = json.loads(task.payload)
    self.assertEqual(test_run.key.id(), data['test_run_id'])

  def testCreateTestRun_withNodeConfig(self):
    test = ndb_models.Test(
        name='test', command='command', test_resource_defs=[
            ndb_models.TestResourceDef(
                name='abc', default_download_url='default_download_url'),
            ndb_models.TestResourceDef(
                name='def', default_download_url='default_download_url'),
            ndb_models.TestResourceDef(
                name='xyz', default_download_url='default_download_url'),
        ])
    test.put()
    node_config = ndb_models.GetNodeConfig()
    node_config.env_vars.append(
        ndb_models.NameValuePair(name='foo', value='bar'))
    node_config.test_resource_default_download_urls = [
        ndb_models.NameValuePair(name='def', value='default_download_url2'),
        ndb_models.NameValuePair(name='xyz', value='default_download_url2'),
    ]
    node_config.put()
    test_run_config = ndb_models.TestRunConfig(
        test_key=test.key, cluster='cluster', run_target='run_target')
    test_resources = [
        ndb_models.TestResourceObj(
            name='xyz', url='origin_url', cache_url='cache_url'),
    ]

    test_run = test_kicker.CreateTestRun(
        ['label'], test_run_config, test_resources)

    test_run = ndb_models.TestRun.get_by_id(test_run.key.id())
    self.assertEqual(test, test_run.test)
    self.assertEqual(node_config.env_vars, test.env_vars)
    self.assertEqual(['label'], test_run.labels)
    self.assertEqual(test_run_config, test_run.test_run_config)
    self.assertCountEqual([
        ndb_models.TestResourceObj(
            name='abc', url='default_download_url'),
        ndb_models.TestResourceObj(
            name='def', url='default_download_url2'),
        ndb_models.TestResourceObj(
            name='xyz', url='origin_url', cache_url='cache_url'),
    ], test_run.test_resources)
    self.assertEqual(ndb_models.TestRunState.PENDING, test_run.state)
    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=[test_kicker.TEST_KICKER_QUEUE])
    self.assertEqual(1, len(tasks))
    task = tasks[0]
    data = json.loads(task.payload)
    self.assertEqual(test_run.key.id(), data['test_run_id'])

  def _CreateMockTestRun(
      self,
      test_name='test',
      command='command',
      retry_command_line=None,
      runner_sharding_args=None,
      extra_args=None,
      retry_extra_args=None,
      run_target='run_target',
      shard_count=1,
      sharding_mode=ndb_models.ShardingMode.RUNNER):
    test = ndb_models.Test(
        name=test_name,
        command=command,
        retry_command_line=retry_command_line,
        runner_sharding_args=runner_sharding_args)
    test.put()
    test_run_config = ndb_models.TestRunConfig(
        test_key=test.key, cluster='cluster', run_target=run_target,
        shard_count=shard_count, sharding_mode=sharding_mode,
        extra_args=extra_args,
        retry_extra_args=retry_extra_args)
    test_resources = [
        ndb_models.TestResourceObj(name='foo', url='http://foo_origin_url'),
        ndb_models.TestResourceObj(name='bar', url='https://bar_origin_url'),
    ]
    test_run = ndb_models.TestRun(
        id=str(uuid.uuid4()),
        test=test, labels=['label'], test_run_config=test_run_config,
        test_resources=test_resources, state=ndb_models.TestRunState.PENDING)
    test_run.put()
    return test_run

  def testGetRerunInfo_empty(self):
    # no rerun info without context
    self.assertEqual((None, None), test_kicker._GetRerunInfo(None, None))
    # no rerun info for empty context
    self.assertEqual((None, None),
                     test_kicker._GetRerunInfo(None, messages.RerunContext()))

  def testGetRerunInfo_local(self):
    # create local test run to rerun
    prev_test_run = self._CreateMockTestRun()
    prev_test_run.next_test_context = ndb_models.TestContextObj(
        test_resources=[ndb_models.TestResourceObj(name='bar', url='zzz')])
    prev_test_run.put()

    # determine rerun info using parent ID
    prev_run_key, prev_test_context = test_kicker._GetRerunInfo(
        None, messages.RerunContext(test_run_id=prev_test_run.key.id()))

    # test run key found and next_test_context used
    self.assertEqual(prev_test_run.key, prev_run_key)
    self.assertEqual(prev_test_run.next_test_context, prev_test_context)

  @mock.patch.object(download_util, 'DownloadResource')
  def testGetRerunInfo_remote(self, mock_download):
    test = ndb_models.Test(context_file_dir='context/')
    mock_download.return_value = 'url'

    # determine rerun info using parent ID
    prev_run_key, prev_test_context = test_kicker._GetRerunInfo(
        test, messages.RerunContext(context_filename='file'))

    # no test run key and test context contains provided file
    expected_context = ndb_models.TestContextObj(test_resources=[
        ndb_models.TestResourceObj(name='context/file', url='url')])
    self.assertIsNone(prev_run_key)
    self.assertEqual(expected_context, prev_test_context)

  def _CheckNewRequestMessage(
      self, msg, test_run, command_line=None, retry_command_line=None,
      run_target=None, shard_count=1):
    """Compare a new request message to its associated test run."""
    test = test_run.test
    test_run_config = test_run.test_run_config
    # compare general options
    self.assertEqual(api_messages.RequestType.MANAGED, msg.type)
    self.assertEqual(command_line, msg.command_line)
    self.assertEqual(test_run_config.cluster, msg.cluster)
    self.assertEqual(
        run_target or test_run_config.run_target, msg.run_target)
    self.assertEqual(test_run_config.run_count, msg.run_count)
    self.assertEqual(
        shard_count or test_run_config.shard_count, msg.shard_count)
    self.assertEqual(
        test_run_config.max_retry_on_test_failures,
        msg.max_retry_on_test_failures)
    # compare test environment
    self.assertTrue(msg.test_environment.use_subprocess_reporting)
    self.assertEqual(
        test.context_file_pattern,
        msg.test_environment.context_file_pattern)
    self.assertEqual([test_kicker.METADATA_FILE],
                     msg.test_environment.extra_context_files)
    self.assertEqual(
        retry_command_line, msg.test_environment.retry_command_line)
    self.assertEqual(common.LogLevel.INFO, msg.test_environment.log_level)
    # compare test resources, including additional metadata file
    test_resources = [api_messages.TestResource(name=r.name, url='cache_url')
                      for r in test_run.test_resources]
    metadata_url = test_kicker.METADATA_API_FORMAT % (self.hostname,
                                                      test_run.key.id())
    test_resources.append(api_messages.TestResource(
        name=test_kicker.METADATA_FILE, url=metadata_url))
    self.assertEqual(test_resources, msg.test_resources)
    # compare previous test context
    if test_run.prev_test_context:
      self.assertIsNotNone(msg.prev_test_context)
      self.assertEqual([
          api_messages.KeyValuePair(key=p.name, value=p.value)
          for p in test_run.prev_test_context.env_vars
      ], msg.prev_test_context.env_vars)
      self.assertEqual([
          api_messages.TestResource(name=r.name, url=r.url)
          for r in test_run.prev_test_context.test_resources
      ], msg.prev_test_context.test_resources)

  @mock.patch.object(test_kicker, '_TrackTestRun')
  @mock.patch.object(tfc_client, 'NewRequest', autospec=True)
  @mock.patch.object(download_util, 'DownloadResource', autospec=True)
  def testKickTestRun(
      self, mock_download_resource, mock_new_request, mock_track_test_run):
    test_run = self._CreateMockTestRun(
        command='command', extra_args='extra_args')
    test_run_id = test_run.key.id()
    mock_download_resource.return_value = 'cache_url'
    mock_request = api_messages.RequestMessage(id='request_id')
    mock_new_request.return_value = mock_request

    test_kicker.KickTestRun(test_run_id)

    mock_download_resource.assert_has_calls([
        mock.call(r.url) for r in test_run.test_resources
    ])
    mock_new_request.assert_called()
    msg = mock_new_request.call_args[0][0]
    self._CheckNewRequestMessage(
        msg, test_run, command_line='command extra_args')
    test_run = ndb_models.TestRun.get_by_id(test_run_id)
    self.assertEqual(mock_request.id, test_run.request_id)
    self.assertEqual(ndb_models.TestRunState.QUEUED, test_run.state)
    # metrics tracked
    mock_track_test_run.assert_called_with(test_run)

  @mock.patch.object(tfc_client, 'NewRequest', autospec=True)
  @mock.patch.object(download_util, 'DownloadResource', autospec=True)
  def testKickTestRun_runnerSharding(
      self, mock_download_resource, mock_new_request):
    test_run = self._CreateMockTestRun(
        command='command',
        runner_sharding_args='--shard-count ${TF_SHARD_COUNT}',
        extra_args='extra_args',
        run_target='run_target;run_target',
        shard_count=2,
        sharding_mode=ndb_models.ShardingMode.RUNNER)
    test_run_id = test_run.key.id()
    mock_download_resource.return_value = 'cache_url'
    mock_request = api_messages.RequestMessage(id='request_id')
    mock_new_request.return_value = mock_request

    test_kicker.KickTestRun(test_run_id)

    mock_download_resource.assert_has_calls([
        mock.call(r.url) for r in test_run.test_resources
    ])
    mock_new_request.assert_called()
    msg = mock_new_request.call_args[0][0]
    self._CheckNewRequestMessage(
        msg,
        test_run,
        command_line='command extra_args --shard-count 2',
        run_target='run_target;run_target',
        shard_count=1)
    test_run = ndb_models.TestRun.get_by_id(test_run_id)
    self.assertEqual(mock_request.id, test_run.request_id)
    self.assertEqual(ndb_models.TestRunState.QUEUED, test_run.state)

  @mock.patch.object(tfc_client, 'NewRequest', autospec=True)
  @mock.patch.object(download_util, 'DownloadResource', autospec=True)
  def testKickTestRun_withPrevTestContext(
      self, mock_download_resource, mock_new_request):
    test_run = self._CreateMockTestRun(
        command='command',
        retry_command_line='retry_command_line',
        retry_extra_args='extra_args',
        runner_sharding_args='--shard-count ${TF_SHARD_COUNT}',
        shard_count=6)
    test_run.prev_test_context = ndb_models.TestContextObj(
        command_line='prev_command_line',
        env_vars=[],
        test_resources=[ndb_models.TestResourceObj(name='bar', url='zzz')])
    test_run.put()
    test_run_id = test_run.key.id()
    mock_download_resource.return_value = 'cache_url'
    mock_request = api_messages.RequestMessage(id='request_id')
    mock_new_request.return_value = mock_request

    test_kicker.KickTestRun(test_run_id)

    mock_download_resource.assert_has_calls([
        mock.call(r.url) for r in test_run.test_resources
    ])
    mock_new_request.assert_called()
    msg = mock_new_request.call_args[0][0]
    self._CheckNewRequestMessage(
        msg,
        test_run,
        command_line='command --shard-count 6',
        retry_command_line='retry_command_line extra_args --shard-count 6',
        shard_count=1)
    # prev_test_context's command_line should be replaced.
    self.assertEqual(
        'retry_command_line extra_args --shard-count 6',
        msg.prev_test_context.command_line)
    test_run = ndb_models.TestRun.get_by_id(test_run_id)
    self.assertEqual(mock_request.id, test_run.request_id)
    self.assertEqual(ndb_models.TestRunState.QUEUED, test_run.state)

  @mock.patch.object(tfc_client, 'NewRequest', autospec=True)
  @mock.patch.object(test_run_hook, 'ExecuteHooks', autospec=True)
  @mock.patch.object(download_util, 'DownloadResource', autospec=True)
  def testKickTestRun_withTestRunHookConfigs(
      self, mock_download_resource, mock_execute_hooks, mock_new_request):
    # Create hook config with two TF result reporters
    hook_config = ndb_models.TestRunHookConfig(
        name='Foo',
        hook_class_name='foo',
        tradefed_result_reporters=[
            ndb_models.TradefedConfigObject(
                class_name='com.android.foo',
                option_values=[ndb_models.NameMultiValuePair(
                    name='test-run-id', values=['${MTT_TEST_RUN_ID}'])]
            ),
            ndb_models.TradefedConfigObject(class_name='com.android.bar'),
        ])
    hook_config.put()
    # Create test run with hook config
    test_run = self._CreateMockTestRun(command='command')
    test_run.hook_configs = [hook_config]
    test_run.put()
    test_run_id = test_run.key.id()
    # Mock responses
    mock_download_resource.return_value = 'cache_url'
    mock_request = api_messages.RequestMessage(id='request_id')
    mock_new_request.return_value = mock_request

    test_kicker.KickTestRun(test_run_id)
    # Resources downloaded, hooks executed, and new TFC request created
    mock_download_resource.assert_called()
    mock_execute_hooks.assert_called_with(
        test_run_id, ndb_models.TestRunPhase.BEFORE_RUN)
    mock_new_request.assert_called()
    msg = mock_new_request.call_args[0][0]
    self._CheckNewRequestMessage(msg, test_run, command_line='command')

    # TFC request has two TF result reporters with right class names and options
    tradefed_config_objects = msg.test_environment.tradefed_config_objects
    self.assertLen(tradefed_config_objects, 2)
    self.assertEqual(api_messages.TradefedConfigObjectType.RESULT_REPORTER,
                     tradefed_config_objects[0].type)
    self.assertEqual('com.android.foo', tradefed_config_objects[0].class_name)
    self.assertEqual('test-run-id',
                     tradefed_config_objects[0].option_values[0].key)
    self.assertEqual([str(test_run_id)],
                     tradefed_config_objects[0].option_values[0].values)
    self.assertEqual(api_messages.TradefedConfigObjectType.RESULT_REPORTER,
                     tradefed_config_objects[1].type)
    self.assertEqual('com.android.bar', tradefed_config_objects[1].class_name)
    self.assertEmpty(tradefed_config_objects[1].option_values)

    # Test run now queued
    test_run = ndb_models.TestRun.get_by_id(test_run_id)
    self.assertEqual(mock_request.id, test_run.request_id)
    self.assertEqual(ndb_models.TestRunState.QUEUED, test_run.state)

  @mock.patch.object(test_kicker, 'KickTestRun')
  def testEnqueueTestRun(self, mock_kick_test_run):
    test_run_id = 1000
    test_kicker.EnqueueTestRun(test_run_id)
    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=test_kicker.TEST_KICKER_QUEUE)
    self.assertEqual(1, len(tasks))
    response = self.testapp.post(
        '/_ah/queue/%s' % test_kicker.TEST_KICKER_QUEUE, tasks[0].payload,
        headers=tasks[0].headers)
    self.assertEqual('200 OK', response.status)
    mock_kick_test_run.assert_called_with(test_run_id)

  @mock.patch.object(download_util, 'DownloadResource', autospec=True)
  @mock.patch.object(file_util, 'GetTestSuiteInfo')
  @mock.patch.object(file_util, 'FileHandle')
  def testPrepareTestResources(
      self, mock_file_handle, mock_get_suite_info, mock_download_resource):
    test_run = self._CreateMockTestRun(
        command='command', extra_args='extra_args')
    test_run.test_resources = [
        ndb_models.TestResourceObj(
            name='foo',
            url='http://foo_origin_url',
            test_resource_type=ndb_models.TestResourceType.TEST_PACKAGE)
    ]
    test_run.put()
    test_run_id = test_run.key.id()
    mock_download_resource.return_value = 'foo_cache_url'
    mock_file_handle.Get.return_value = 'filehandle'
    test_suite_info = file_util.TestSuiteInfo(
        'build_number', 'target_architecture', 'name', 'fullname', 'version')
    mock_get_suite_info.return_value = test_suite_info

    test_kicker._PrepareTestResources(test_run_id)
    test_run = ndb_models.TestRun.get_by_id(test_run.key.id())

    # Resource downloaded and cached, and its test package info was read
    mock_download_resource.assert_called_with('http://foo_origin_url')
    self.assertEqual(test_run.test_resources[0].cache_url, 'foo_cache_url')
    mock_file_handle.Get.assert_called_with('foo_cache_url')
    self.assertEqual(
        test_run.test_package_info.build_number, test_suite_info.build_number)
    self.assertEqual(
        test_run.test_package_info.target_architecture,
        test_suite_info.target_architecture)
    self.assertEqual(
        test_run.test_package_info.name, test_suite_info.name)
    self.assertEqual(
        test_run.test_package_info.fullname, test_suite_info.fullname)
    self.assertEqual(
        test_run.test_package_info.version, test_suite_info.version)

  @mock.patch.object(analytics, 'Log')
  def testTrackTestRun(self, mock_log):
    # configure test run
    test_run = self._CreateMockTestRun()
    test_run.test_package_info = ndb_models.TestPackageInfo(
        name='name', version='version')

    # check that right data was logged
    test_kicker._TrackTestRun(test_run)
    mock_log.assert_called_with(analytics.TEST_RUN_CATEGORY,
                                analytics.START_ACTION,
                                test_name='name',
                                test_version='version',
                                is_rerun=False)

if __name__ == '__main__':
  absltest.main()
