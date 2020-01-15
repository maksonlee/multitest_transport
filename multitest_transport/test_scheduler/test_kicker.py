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

"""A test kicker module."""
import json
import logging
import os
import string
import uuid

from googleapiclient.errors import HttpError
from protorpc import messages
from tradefed_cluster import api_messages
from tradefed_cluster import common
import webapp2

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.test_scheduler import download_util
from multitest_transport.test_scheduler import test_run_manager

from multitest_transport.util import analytics
from multitest_transport.util import env
from multitest_transport.util import errors
from multitest_transport.util import file_util
from multitest_transport.util import gcs_util
from multitest_transport.util import tfc_client


TEST_KICKER_QUEUE = 'test-kicker-queue'
TEST_RUN_OUTPUT_PATH_FORMAT = '/%s/test_runs/%%s/output/' % env.GCS_BUCKET_NAME
MAX_RETRY_COUNT = 7
METADATA_FILE = 'mtt.json'
METADATA_API_FORMAT = 'http://%s/_ah/api/mtt/v1/test_runs/%s/metadata'


def CreateTestRun(labels,
                  test_run_config,
                  test_resources,
                  test_output_upload_configs=None,
                  test_plan_key=None,
                  rerun_context=None):
  """Creates a test run.

  Args:
    labels: labels for the test run
    test_run_config: a ndb_models.TestRunConfig object.
    test_resources: a list of ndb_models.TestResourceObj objects.
    test_output_upload_configs: a list of ndb_models.TestOutputUploadConfig.
    test_plan_key: a ndb_models.TestPlan key.
    rerun_context: rerun parameters containing parent ID or context filename.
  Returns:
    a ndb_models.TestRun object.
  Raises:
    ValueError: if a given test is not found in DB.
    errors.TestResourceError: if some of test resources don't have URLs.
  """
  test_output_upload_configs = test_output_upload_configs or []

  test = test_run_config.test_key.get()
  if not test:
    raise ValueError('cannot find test %s' % test_run_config.test_key)

  node_config = ndb_models.GetNodeConfig()
  test.env_vars.extend(node_config.env_vars)

  # Store snapshot of test run's actions
  before_device_actions = [
      key.get() for key in test_run_config.before_device_action_keys
  ]
  if not all(before_device_actions):
    raise ValueError(
        'Cannot find some device actions: %s -> %s' % (
            test_run_config.before_device_action_keys, before_device_actions))
  hook_configs = [key.get() for key in test_run_config.hook_config_keys]
  if not all(hook_configs):
    raise ValueError(
        'Cannot find some test run hooks: %s -> %s' % (
            test_run_config.hook_config_keys, hook_configs))

  test_resource_defs = test.test_resource_defs[:]
  for device_action in before_device_actions:
    test_resource_defs += device_action.test_resource_defs
  # Initialize test_resource_maps based on test_resource_defs.
  test_resource_map = {
      d.name: ndb_models.TestResourceObj(
          name=d.name,
          url=d.default_download_url,
          test_resource_type=d.test_resource_type)
      for d in test_resource_defs
  }
  # Override test resource URLs based on
  # node_config.test_resource_default_download_urls.
  for pair in node_config.test_resource_default_download_urls:
    if pair.name not in test_resource_map:
      continue
    test_resource_map[pair.name].url = pair.value
  for r in test_resources:
    if r.name not in test_resource_map:
      logging.warn(
          'Test resource %s is not needed for this test run; ignoring', r)
      continue
    test_resource_map[r.name].url = r.url
    test_resource_map[r.name].cache_url = r.cache_url
  # Check every test resource has a valid URL.
  for test_resource in test_resource_map.itervalues():
    if not test_resource.url:
      raise errors.TestResourceError(
          'No URL for test resource %s' % test_resource.name)

  # Determine previous test context from previous test run
  prev_test_run_key, prev_test_context = _GetRerunInfo(test, rerun_context)

  # Create and enqueue test run
  test_run = ndb_models.TestRun(
      id=str(uuid.uuid4()),
      prev_test_run_key=prev_test_run_key,
      labels=labels,
      test_plan_key=test_plan_key,
      test=test,
      test_run_config=test_run_config,
      test_resources=test_resource_map.values(),
      test_output_upload_configs=test_output_upload_configs,
      prev_test_context=prev_test_context,
      state=ndb_models.TestRunState.PENDING,
      before_device_actions=before_device_actions,
      hook_configs=hook_configs)
  test_run.put()
  test_run_id = test_run.key.id()
  logging.info('test run %s created', test_run_id)
  EnqueueTestRun(test_run_id)
  return test_run


def _GetRerunInfo(test, rerun_context):
  """Determine parent run key and test context for reruns.

  Args:
    test: ndb_models.Test that will be executed.
    rerun_context: rerun parameters containing parent ID or context filename.
  Returns:
    previous test run key and previous test context to use during rerun
  """
  # TODO: support directly fetching rerun context from remote MTT
  if rerun_context and rerun_context.test_run_id:
    # local rerun - fetch key and test context from DB
    logging.info('Rerunning local test run %s', rerun_context.test_run_id)
    prev_test_run_key = ndb.Key(ndb_models.TestRun, rerun_context.test_run_id)
    prev_test_run = prev_test_run_key.get()
    if not prev_test_run:
      raise ValueError(
          'Previous test run %s not found' % prev_test_run_key.id())
    return prev_test_run_key, prev_test_run.next_test_context

  if rerun_context and rerun_context.context_filename:
    # remote rerun - construct test context from locally uploaded file
    logging.info('Rerunning test run from %s', rerun_context.context_filename)
    if not test.context_file_dir:
      raise ValueError(
          'No context file directory configured for test %s' % test.name)
    remote_test_context = ndb_models.TestContextObj(test_resources=[
        ndb_models.TestResourceObj(
            name=test.context_file_dir + rerun_context.context_filename,
            # TODO: determine filename without calling DownloadResource
            url=download_util.DownloadResource(
                'gs:/%s/%s' %
                (env.GCS_TEMP_PATH, rerun_context.context_filename)))
    ])
    return None, remote_test_context

  # no rerun information
  return None, None


def EnqueueTestRun(test_run_id):
  """Push the exist test run to the task queue.

  Args:
    test_run_id: a test run ID.
  """
  task_name = str(test_run_id)
  payload = json.dumps({
      'test_run_id': test_run_id
  })
  task = taskqueue.Task(name=task_name, payload=payload, target='default')
  task.add(queue_name=TEST_KICKER_QUEUE)


def KickTestRun(test_run_id):
  """Kick off a test run.

  Args:
    test_run_id: a test run ID.
  """
  _PrepareTestResources(test_run_id)
  test_run_hook.ExecuteHooks(test_run_id, ndb_models.TestRunPhase.BEFORE_RUN)
  _CreateTFCRequest(test_run_id)


def _PrepareTestResources(test_run_id):
  """Prepare test resources.

  Args:
    test_run_id: a test run ID.
  """
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if test_run.state == ndb_models.TestRunState.CANCELED:
    logging.info(
        'Test run %s is CANCELED; aborting _PrepareTestResources()',
        test_run_id)
    return
  assert test_run.state == ndb_models.TestRunState.PENDING

  logging.info(
      'Preparing test resources for test run %s: test_resources=%s',
      test_run_id, test_run.test_resources)
  num_test_resources = len(test_run.test_resources)
  for i, r in enumerate(test_run.test_resources):
    logging.info('Checking %s: %s... (%d of %d)', r.name, r.url, i + 1,
                 num_test_resources)
    # If the resource is already downloaded and still up-to-date, this will
    # simply return its cache URL. Otherwise, it will be (re-)downloaded.
    cache_url = download_util.DownloadResource(r.url)
    test_package_info = None
    if r.test_resource_type == ndb_models.TestResourceType.TEST_PACKAGE:
      test_package_info = _GetTestPackageInfo(cache_url)
    _UpdateTestResource(test_run_id, r.name, cache_url, test_package_info)
  logging.info('Done preparing test resources for test run %s', test_run_id)


def _GetTestPackageInfo(cache_url):
  """Retrieve the test package information at a specified resource URL."""
  handle = file_util.FileHandle.Get(cache_url)
  test_suite_info = file_util.GetTestSuiteInfo(handle)
  if test_suite_info:
    return ndb_models.TestPackageInfo(
        build_number=test_suite_info.build_number,
        target_architecture=test_suite_info.target_architecture,
        name=test_suite_info.name,
        fullname=test_suite_info.fullname,
        version=test_suite_info.version)


@ndb.transactional()
def _UpdateTestResource(test_run_id, resource_name, cache_url,
                        test_package_info):
  """Update a test resource to persist its cache URL and test package info."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run or test_run.state != ndb_models.TestRunState.PENDING:
    return
  resource = next(r for r in test_run.test_resources if r.name == resource_name)
  resource.cache_url = cache_url
  if test_package_info:
    test_run.test_package_info = test_package_info
  test_run.put()


def _CreateTFCRequest(test_run_id):
  """Creates a TFC request.

  Args:
    test_run_id: a test run ID.
  """
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if test_run.state == ndb_models.TestRunState.CANCELED:
    logging.info(
        'Test run %s is CANCELED; aborting _CreateTFCRequest()',
        test_run_id)
    return
  assert test_run.state == ndb_models.TestRunState.PENDING

  logging.info(
      'Creating a TFC request: test=%s, test_run_config=%s',
      test_run.test, test_run.test_run_config)
  test_run.output_path = TEST_RUN_OUTPUT_PATH_FORMAT % test_run_id
  if env.STORAGE_PATH:
    # Standalone mode
    test_run.output_storage = file_util.FileStorage.LOCAL_FILE_SYSTEM
    output_upload_url = 'file://%s%s' % (env.STORAGE_PATH, test_run.output_path)
  else:
    test_run.output_storage = file_util.FileStorage.GOOGLE_CLOUD_STORAGE
    output_upload_url = gcs_util.GetUploadUrl(test_run.output_path)

  # Construct command
  command_line = test_run.test.command
  if test_run.test_run_config.extra_args:
    command_line = ' '.join([command_line, test_run.test_run_config.extra_args])

  # Construct retry command
  retry_command_line = test_run.test.retry_command_line
  if retry_command_line and test_run.test_run_config.retry_extra_args:
    retry_command_line = ' '.join([retry_command_line,
                                   test_run.test_run_config.retry_extra_args])

  # Append sharding arguments
  sharding_mode = (
      test_run.test_run_config.sharding_mode or ndb_models.ShardingMode.RUNNER)
  run_target = test_run.test_run_config.run_target
  shard_count = test_run.test_run_config.shard_count
  if sharding_mode == ndb_models.ShardingMode.RUNNER:
    if shard_count > 1 and test_run.test.runner_sharding_args:
      tmpl = string.Template(test_run.test.runner_sharding_args)
      sharding_args = tmpl.safe_substitute({
          'TF_SHARD_COUNT': str(shard_count)
      })
      command_line = ' '.join([command_line, sharding_args])
      if retry_command_line:
        retry_command_line = ' '.join([retry_command_line, sharding_args])
    shard_count = 1

  tradefed_config_objects = _GetTradefedConfigObjects(test_run)

  prev_test_context = None
  if test_run.prev_test_context:
    prev_test_context = api_messages.TestContext(
        env_vars=[
            api_messages.KeyValuePair(key=p.name, value=p.value)
            for p in test_run.prev_test_context.env_vars
        ],
        test_resources=[
            api_messages.TestResource(name=r.name, url=r.url)
            for r in test_run.prev_test_context.test_resources
        ])
    # TODO: consider removing command_line from TestContext.
    if not prev_test_context.test_resources:
      prev_test_context.command_line = command_line
    else:
      prev_test_context.command_line = retry_command_line

  test_resources = [api_messages.TestResource(name=r.name, url=r.cache_url)
                    for r in test_run.test_resources]

  # add metadata URL to the test resources
  hostname = os.environ['DEFAULT_VERSION_HOSTNAME']
  metadata_url = METADATA_API_FORMAT % (hostname, test_run.key.id())
  test_resources.append(
      api_messages.TestResource(name=METADATA_FILE, url=metadata_url))

  # determine context file pattern
  context_file_pattern = None
  if test_run.test.context_file_dir and test_run.test.context_file_pattern:
    context_file_pattern = (test_run.test.context_file_dir +
                            test_run.test.context_file_pattern)

  # Record metrics
  _TrackTestRun(test_run)

  new_request_msg = api_messages.NewRequestMessage(
      type=api_messages.RequestType.MANAGED,
      user='test_kicker',
      command_line=command_line,
      cluster=test_run.test_run_config.cluster,
      run_target=run_target,
      run_count=test_run.test_run_config.run_count,
      shard_count=shard_count,
      max_retry_on_test_failures=(
          test_run.test_run_config.max_retry_on_test_failures),
      queue_timeout_seconds=test_run.test_run_config.queue_timeout_seconds,
      test_environment=api_messages.TestEnvironment(
          env_vars=[
              api_messages.KeyValuePair(key=p.name, value=p.value)
              for p in test_run.test.env_vars
          ],
          setup_scripts=test_run.test.setup_scripts,
          output_file_upload_url=output_upload_url,
          output_file_patterns=test_run.test.output_file_patterns,
          use_subprocess_reporting=True,
          output_idle_timeout_millis=(
              1000 * test_run.test_run_config.output_idle_timeout_seconds),
          jvm_options=test_run.test.jvm_options,
          java_properties=[
              api_messages.KeyValuePair(key=p.name, value=p.value)
              for p in test_run.test.java_properties
          ],
          context_file_pattern=context_file_pattern,
          extra_context_files=[METADATA_FILE],  # append metadata to context
          retry_command_line=retry_command_line,
          log_level=common.LogLevel.INFO,
          tradefed_config_objects=tradefed_config_objects),
      test_resources=test_resources,
      prev_test_context=prev_test_context)
  logging.info('new_request_msg=%s', new_request_msg)
  request = tfc_client.NewRequest(new_request_msg)
  logging.info('TFC request %s is created', request.id)
  test_run.request_id = request.id
  test_run.state = ndb_models.TestRunState.QUEUED
  test_run.put()


def _GetTradefedConfigObjects(test_run):
  """Return a list of Tradefed config objects for a test run.

  Args:
    test_run: a ndb_models.TestRun object.
  Returns:
    a list of api_messages.TradefedConfigObjects.
  """
  objs = []
  for action in test_run.before_device_actions:
    for target_preparer in action.tradefed_target_preparers:
      obj = api_messages.TradefedConfigObject(
          type=api_messages.TradefedConfigObjectType.TARGET_PREPARER,
          class_name=target_preparer.class_name,
          option_values=[
              api_messages.KeyMultiValuePair(key=o.name, values=o.values)
              for o in target_preparer.option_values
          ])
      objs.append(obj)
  for hook_config in test_run.hook_configs:
    for result_reporter in hook_config.tradefed_result_reporters:
      obj = api_messages.TradefedConfigObject(
          type=api_messages.TradefedConfigObjectType.RESULT_REPORTER,
          class_name=result_reporter.class_name,
          option_values=[
              api_messages.KeyMultiValuePair(key=o.name, values=o.values)
              for o in result_reporter.option_values
          ])
      objs.append(obj)

  ctx = test_run.GetContext()
  for obj in objs:
    for pair in obj.option_values:
      pair.values = [
          string.Template(v).safe_substitute(ctx)
          for v in pair.values
      ]
  return objs


def _TrackTestRun(test_run):
  """Generate and send test run analytics information before start."""
  package = test_run.test_package_info
  analytics.Log(analytics.TEST_RUN_CATEGORY, analytics.START_ACTION,
                test_name=package.name if package else None,
                test_version=package.version if package else None,
                is_rerun=test_run.prev_test_run_key is not None)


class TaskHandler(webapp2.RequestHandler):
  """A web request handler to handle tasks from the test kicker queue."""

  def post(self):
    """Process a request message."""
    retry_count = int(
        self.request.headers.get('X-AppEngine-TaskRetryCount', MAX_RETRY_COUNT))
    payload = json.loads(self.request.body)
    test_run_id = payload['test_run_id']
    try:
      KickTestRun(test_run_id)
    except Exception as e:        if isinstance(e, messages.ValidationError):
        logging.exception('Non retriable error %s, no retry needed', e)
      elif isinstance(e, HttpError) and e.resp.status == 400:
        logging.exception('Non retriable error %s, no retry needed', e)
      elif retry_count < MAX_RETRY_COUNT:
        logging.exception(
            'Fail to kick test run %s, retry_count = %d',
            test_run_id, retry_count + 1)
        raise
      else:
        logging.exception(
            'Fail to kick test run %s after %d retries', test_run_id,
            MAX_RETRY_COUNT)
      test_run_manager.SetTestRunState(
          test_run_id=test_run_id,
          state=ndb_models.TestRunState.ERROR,
          error_reason=str(e))


APP = webapp2.WSGIApplication([
    ('/.*', TaskHandler),
], debug=True)
