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

"""Datastore model classes."""

import collections
import datetime
import uuid

from protorpc import messages
from tradefed_cluster import common

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import oauth2_util

NODE_CONFIG_ID = 1


class BuildChannelAuthState(messages.Enum):
  """Build channel authorization states."""
  NOT_AUTHORIZED = 0
  AUTHORIZED = 1


class NameValuePair(ndb.Model):
  """A generic name-value pair to store an option.

  Attributes:
    name: a name.
    value: a value.
  """
  name = ndb.StringProperty(required=True)
  value = ndb.StringProperty()

  @classmethod
  def FromDict(cls, d):
    return [cls(name=k, value=v) for k, v in d.iteritems()]

  @classmethod
  def ToDict(cls, pairs):
    d = collections.OrderedDict()
    for pair in pairs:
      d[pair.name] = pair.value
    return d


class NameMultiValuePair(ndb.Model):
  """A generic name-multi value pair to store an option.

  Attributes:
    name: a name.
    values: a list of values.
  """
  name = ndb.StringProperty(required=True)
  values = ndb.StringProperty(repeated=True)

  @classmethod
  def FromDict(cls, d):
    return [cls(name=k, values=v) for k, v in d.iteritems()]

  @classmethod
  def ToDict(cls, pairs):
    d = collections.OrderedDict()
    for pair in pairs:
      d[pair.name] = pair.values
    return d


class AuthorizationState(messages.Enum):
  """Authorization states."""
  NOT_APPLICABLE = 0  # Does not require authorization
  AUTHORIZED = 1  # Requires authorization and has credentials
  UNAUTHORIZED = 2  # Requires authorization and no credentials found


class BuildChannelConfig(ndb.Model):
  """A build channel config."""
  name = ndb.StringProperty(required=True)
  provider_name = ndb.StringProperty(required=True)
  options = ndb.StructuredProperty(NameValuePair, repeated=True)
  credentials = oauth2_util.CredentialsProperty()


class ConfigSetStatus(messages.Enum):
  NOT_IMPORTED = 0
  IMPORTED = 1
  UPDATABLE = 2


class ConfigSetInfo(ndb.Model):
  """Metadata for a config set.

  Attributes:
    url: origin url where this config can be downloaded from
    hash: SHA value of the file, used for comparing two files
    name: name to display to the user
    description: describes the contents of the file
    last_update_time: timestamp when the file was last imported
  """
  url = ndb.StringProperty(required=True)
  hash = ndb.StringProperty()
  name = ndb.StringProperty(required=True)
  description = ndb.StringProperty()
  last_update_time = ndb.StringProperty()


class ConfigSetInfoList(ndb.Model):
  """A list of ConfigSetInfos."""
  config_set_infos = ndb.StructuredProperty(ConfigSetInfo, repeated=True)


class TestResourceType(messages.Enum):
  UNKNOWN = 0
  DEVICE_IMAGE = 1
  TEST_PACKAGE = 2


class TestResourceDef(ndb.Model):
  """A test resource definition.

  Attributes:
    name: a test resource name.
    default_download_url: a default download URL.
    test_resource_type: a test resource type.
  """
  name = ndb.StringProperty(required=True)
  default_download_url = ndb.StringProperty()
  test_resource_type = msgprop.EnumProperty(TestResourceType)


class Test(ndb.Model):
  """A test.

  Attributes:
    name: a test name.
    test_resource_defs: a list of test resource definitions.
    command: a TF command line.
    env_vars: a dict of environment variables to set before running a test.
    output_file_patterns: a list of file patterns to collect after a test run.
    result_file: XML result file path.
    setup_scripts: a list of scripts to run before running a test.
    jvm_options: a list of JVM options to be passed to TF.
    java_properties: a dict of Java properties to be passed to TF.
    context_file_dir: directory where the context file which needs to be
        passed across attempts is located.
    context_file_pattern: a regex pattern for the filename of the context file
        which needs to be passed across attempts.
    retry_command_line: a command line to use in retry invocations.
        attempts.
    runner_sharding_args: extra args to enable runner sharding. It can contain
        a reference to a desired shard count (e.g. ${TF_SHARD_COUNT})
  """
  name = ndb.StringProperty(required=True)
  test_resource_defs = ndb.StructuredProperty(TestResourceDef, repeated=True)
  command = ndb.StringProperty(required=True)
  env_vars = ndb.StructuredProperty(NameValuePair, repeated=True)
  output_file_patterns = ndb.StringProperty(repeated=True)
  result_file = ndb.StringProperty()
  setup_scripts = ndb.StringProperty(repeated=True)
  jvm_options = ndb.StringProperty(repeated=True)
  java_properties = ndb.StructuredProperty(NameValuePair, repeated=True)
  context_file_dir = ndb.StringProperty()
  context_file_pattern = ndb.StringProperty()
  retry_command_line = ndb.StringProperty()
  runner_sharding_args = ndb.StringProperty()


class ShardingMode(messages.Enum):
  RUNNER = 0  # Let a test runner to take care of sharding.
  SCHEDULER = 1  # Schedule each shard as a separate command.


class TradefedConfigObject(ndb.Model):
  """A Tradefed object and its options.

  Attributes:
    class_name: a Tradefed config class name.
    option_values: a list of option name and value pairs.
  """
  class_name = ndb.StringProperty(required=True)
  option_values = ndb.LocalStructuredProperty(NameMultiValuePair, repeated=True)


class DeviceAction(ndb.Model):
  """A device action.

  Attributes:
    name: a device action name.
    description: a description.
    test_resource_defs: a list of test resource definitions.
    tradefed_target_preparers: a list of Tradefed target preparers.
  """
  name = ndb.StringProperty(required=True)
  description = ndb.StringProperty()
  test_resource_defs = ndb.LocalStructuredProperty(
      TestResourceDef, repeated=True)
  tradefed_target_preparers = ndb.LocalStructuredProperty(
      TradefedConfigObject, repeated=True)


class TestRunPhase(messages.Enum):
  """Test run phases."""
  UNKNOWN = 0  # Invalid phase
  BEFORE_RUN = 1  # Before run is started (but is created)
  BEFORE_ATTEMPT = 2  # Before an attempt is created (task not sent to runner)
  AFTER_ATTEMPT = 3  # After an attempt is completed (successfully or not)
  AFTER_RUN = 4  # After run is completed (successfully or not)
  ON_SUCCESS = 5  # After run is completed successfully (may have test failures)
  ON_ERROR = 6  # After run fails to complete due to errors


class TestRunAction(ndb.Model):
  """Test run action, describes a specific hook execution.

  Attributes:
    name: action name.
    description: action description.
    hook_class_name: run hook class identifier.
    phases: phases during which hook should be triggered.
    options: key-value pairs to use when configuring the hook.
    tradefed_result_reporters: list of TF result reporters.
    credentials: stored OAuth2 credentials.
  """
  name = ndb.StringProperty(required=True)
  description = ndb.StringProperty()
  hook_class_name = ndb.StringProperty(required=True)
  phases = msgprop.EnumProperty(TestRunPhase, repeated=True)
  options = ndb.LocalStructuredProperty(NameValuePair, repeated=True)
  tradefed_result_reporters = ndb.LocalStructuredProperty(
      TradefedConfigObject, repeated=True)
  credentials = oauth2_util.CredentialsProperty()


class TestRunActionRef(ndb.Model):
  """Test run action reference, with additional overridden options.

  Attributes:
    action_key: test run action to execute.
    options: additional key-value pairs to use when configuring the hook.
  """
  action_key = ndb.KeyProperty(TestRunAction, required=True)
  options = ndb.LocalStructuredProperty(NameValuePair, repeated=True)

  def ToAction(self):
    """Converts this ref into a test run action."""
    action = self.action_key.get()
    if not action:
      raise ValueError('Test run action %s not found' % self.action_key)
    options = NameValuePair.ToDict(action.options or [])
    options.update(NameValuePair.ToDict(self.options or []))
    action.options = NameValuePair.FromDict(options)
    return action


class TestRunConfig(ndb.Model):
  """A test run config.

  Attributes:
    test_key: a Test key.
    cluster: a cluster to run a test in.
    run_target: a run target.
    run_count: a run count.
    shard_count: a shard count.
    sharding_mode: a sharding mode.
    extra_args: a string containing extra arguments.
    retry_extra_args: extra arguments used when retrying.
    max_retry_on_test_failures: the max number of retry on test failure.
    queue_timeout_seconds: how long a test run can stay in QUEUED state before
        being cancelled
    output_idle_timeout_seconds: how long a test run's output can be idle before
        attempting recovery
    before_device_action_keys: device actions to execute before running a test.
    test_run_action_refs: test run actions to execute during a test.
  """
  test_key = ndb.KeyProperty(kind=Test, required=True)
  cluster = ndb.StringProperty(required=True)
  run_target = ndb.StringProperty(required=True)
  run_count = ndb.IntegerProperty(required=True, default=1)
  shard_count = ndb.IntegerProperty(required=True, default=1)
  sharding_mode = msgprop.EnumProperty(
      ShardingMode, default=ShardingMode.RUNNER)
  extra_args = ndb.StringProperty()
  retry_extra_args = ndb.StringProperty()
  max_retry_on_test_failures = ndb.IntegerProperty()
  queue_timeout_seconds = ndb.IntegerProperty(
      required=True, default=env.DEFAULT_QUEUE_TIMEOUT_SECONDS)
  output_idle_timeout_seconds = ndb.IntegerProperty(
      default=env.DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS)
  before_device_action_keys = ndb.KeyProperty(DeviceAction, repeated=True)
  test_run_action_refs = ndb.LocalStructuredProperty(
      TestRunActionRef, repeated=True)


class TestResourcePipe(ndb.Model):
  """A pipe which defines where to get test resources from.

  Attributes:
    name: a test resource name.
    url: a url.
    test_resource_type: a test resource type.
  """
  name = ndb.StringProperty(required=True)
  url = ndb.StringProperty()
  test_resource_type = msgprop.EnumProperty(TestResourceType)


class TestPlan(ndb.Model):
  """A test plan.

  Attributes:
    name: a test resource name.
    labels: list of strings users can use to categorize test runs and plans.
    cron_exp: a CRON expression.
    test_run_configs: a list of test run configs.
    test_resource_pipes: a list of test resource pipes.
    before_device_action_keys: common before device actions for tests.
  """
  name = ndb.StringProperty(required=True)
  labels = ndb.StringProperty(repeated=True)
  cron_exp = ndb.StringProperty()
  test_run_configs = ndb.LocalStructuredProperty(TestRunConfig, repeated=True)
  test_resource_pipes = ndb.LocalStructuredProperty(
      TestResourcePipe, repeated=True)
  before_device_action_keys = ndb.KeyProperty(DeviceAction, repeated=True)


class TestPlanStatus(ndb.Model):
  """A test plan status."""
  last_run_time = ndb.DateTimeProperty()
  next_run_time = ndb.DateTimeProperty()
  next_run_task_name = ndb.StringProperty()


class TestRunState(messages.Enum):
  """Test run state values."""
  UNKNOWN = 0  # this is an invalid state
  PENDING = 1  # A test run is waiting to be kicked-off.
  QUEUED = 2  # A test run is queued by a runner.
  RUNNING = 3  # A test run is running by a runner.
  COMPLETED = 4  # A test run is completed.
  CANCELED = 5  # A test run is canceled.
  ERROR = 6  # A test run is finished with an error.

FINAL_TEST_RUN_STATES = {
    TestRunState.COMPLETED,
    TestRunState.CANCELED,
    TestRunState.ERROR
}


class TestResourceObj(ndb.Model):
  """A test resource object.

  The "Obj" suffix was added to avoid name collistion with TFC TestResource.

  Attributes:
    name: a test resource name.
    url: a URL.
    cache_url: a URL for a cached copy.
    test_resource_type: a test resource type.
  """
  name = ndb.StringProperty(required=True)
  url = ndb.StringProperty()
  cache_url = ndb.StringProperty()
  test_resource_type = msgprop.EnumProperty(TestResourceType)


class TestContextObj(ndb.Model):
  """A test context object.

  The "Obj" suffix was added to avoid name collision with TFC TestContext.

  Attributes:
    command_line: a command line.
    env_vars: environment variables.
    test_resources: a list of TestResourceObj objects.
  """
  command_line = ndb.StringProperty()
  env_vars = ndb.LocalStructuredProperty(NameValuePair, repeated=True)
  test_resources = ndb.LocalStructuredProperty(TestResourceObj, repeated=True)


def ToTimestamp(dt):
  return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())


class TestPackageInfo(ndb.Model):
  """A test package info.

  Attributes
    build_number: test package build number.
    target_architecture: test package arch.
    name: A short name of test package.
    full_name: A full name of test package.
    version: test package version
  """
  build_number = ndb.StringProperty()
  target_architecture = ndb.StringProperty()
  name = ndb.StringProperty()
  fullname = ndb.StringProperty()
  version = ndb.StringProperty()


class TestDeviceInfo(ndb.Model):
  """A test package info.

  Attributes
    device_serial: Serial identifying the device. It should be unique.
    hostname: The name of the host this device is connected to.
    run_target: Run target for the device.
    build_id: Current build ID in the device.
    product: Device product (Eg.: flounder).
    sdk_version: SDK version of the device's build.
  """
  device_serial = ndb.StringProperty()
  hostname = ndb.StringProperty()
  run_target = ndb.StringProperty()
  build_id = ndb.StringProperty()
  product = ndb.StringProperty()
  sdk_version = ndb.StringProperty()


class TestRun(ndb.Model):
  """A test run.

  Attributes:
    prev_test_run_key: previous (parent) test run key.
    user: a user who scheduled a test run.
    labels: list of strings users can use to categorize test runs.
    test_plan_key: a test plan key.
    test: a Test object copy made at the test run schedule time.
    test_run_config: a TestRunConfig object.
    test_resources: a list of TestResourceObj objects.
    state: a test run state.
    is_finalized: True if post-run handlers were executed.
    output_storage: a storage to store test outputs in.
    output_path: a path to store test outputs to.
    output_url: a test output URL.
    prev_test_context: a previous test context object.
    next_test_context: a test context object from this test run.
    test_package_info: a test package information
    test_devices: a list of TestDeviceInfo of DUTs
    request_id: a TFC request ID.
    total_test_count: the number of total test cases.
    failed_test_count: the number of failed test cases.
    failed_test_run_count: the number of test modules that failed to execute.
    create_time: time a test run is created.
    update_time: time a test run is last updated.
    before_device_actions: device actions used during the run.
    test_run_actions: test run actions executed during the run.
    hook_data: additional data used by hooks
    cancel_reason: cancellation reason
    error_reason: error reason
  """
  prev_test_run_key = ndb.KeyProperty(kind='TestRun')
  user = ndb.StringProperty()
  labels = ndb.StringProperty(repeated=True)
  test_plan_key = ndb.KeyProperty(TestPlan)
  test = ndb.StructuredProperty(Test)
  test_run_config = ndb.StructuredProperty(TestRunConfig)
  test_resources = ndb.StructuredProperty(TestResourceObj, repeated=True)
  state = msgprop.EnumProperty(TestRunState, default=TestRunState.UNKNOWN)
  is_finalized = ndb.BooleanProperty()
  output_storage = msgprop.EnumProperty(
      file_util.FileStorage, default=file_util.FileStorage.LOCAL_CLOUD_STORAGE)
  output_path = ndb.StringProperty()
  output_url = ndb.StringProperty()
  prev_test_context = ndb.LocalStructuredProperty(TestContextObj)
  next_test_context = ndb.LocalStructuredProperty(TestContextObj)
  test_package_info = ndb.StructuredProperty(TestPackageInfo)
  test_devices = ndb.StructuredProperty(TestDeviceInfo, repeated=True)
  request_id = ndb.StringProperty()
  total_test_count = ndb.IntegerProperty()
  failed_test_count = ndb.IntegerProperty()
  failed_test_run_count = ndb.IntegerProperty()

  create_time = ndb.DateTimeProperty(auto_now_add=True)
  update_time = ndb.DateTimeProperty(auto_now_add=True)

  # TODO improve action versioning
  # Snapshot of the actions executed by the run
  before_device_actions = ndb.LocalStructuredProperty(
      DeviceAction, repeated=True)
  test_run_actions = ndb.LocalStructuredProperty(TestRunAction, repeated=True)
  hook_data = ndb.JsonProperty(default={})

  cancel_reason = msgprop.EnumProperty(common.CancelReason)
  error_reason = ndb.StringProperty()

  @classmethod
  def get_by_id(cls, id_, **kwargs):
    try:
      # support numeric (legacy) and uuid identifiers
      id_ = int(id_)
    except ValueError:
      pass
    return TestRun._get_by_id(id_, **kwargs)

  def _post_put_hook(self, future):
    self.ToSummary().put()

  @classmethod
  def _post_delete_hook(cls, key, future):
    ndb.Key(TestRunSummary, key.id()).delete()

  def ToSummary(self):
    return TestRunSummary(
        parent=self.key,
        id=self.key.id(),
        labels=self.labels,
        test_name=self.test.name if self.test else None,
        run_target=(self.test_run_config.run_target
                    if self.test_run_config else None),
        state=self.state,
        test_package_info=self.test_package_info,
        test_devices=self.test_devices,
        total_test_count=self.total_test_count,
        failed_test_count=self.failed_test_count,
        failed_test_run_count=self.failed_test_run_count,
        create_time=self.create_time,
        update_time=self.update_time)

  def IsFinal(self):
    """Returns whether a test run is in a final state.

    Returns:
      True if a test run is in a final state. Otherwise false.
    """
    return self.state in FINAL_TEST_RUN_STATES

  def IsRerun(self):
    """Checks whether this is a rerun of another test run."""
    return self.prev_test_context is not None

  def IsLocalRerun(self):
    """Checks whether this is a rerun using a local test run ID."""
    return self.prev_test_run_key is not None

  def IsRemoteRerun(self):
    """Checks whether this is a rerun using an uploaded context file."""
    return self.IsRerun() and not self.IsLocalRerun()

  def GetRerunContextFile(self):
    """Fetches the rerun context file if it exists."""
    if not self.prev_test_context or not self.prev_test_context.test_resources:
      return None
    return self.prev_test_context.test_resources[0]

  def GetContext(self):
    """Returns a test run context dictionary."""
    url_map = {
        r.test_resource_type: r.url
        for r in self.test_resources if r.test_resource_type
    }
    ctx = {
        'MTT_USER': env.USER,
        'MTT_HOSTNAME': env.HOSTNAME,
        'MTT_VERSION': env.VERSION,
        'MTT_TEST_RUN_ID': self.key.id(),
        'MTT_TEST_ID': self.test_run_config.test_key.id(),
        'MTT_TEST_NAME': self.test.name,
        'MTT_TEST_PLAN_NAME': (
            self.test_plan_key.get().name if self.test_plan_key else ''),
        'MTT_TEST_RUN_CREATE_TIMESTAMP': ToTimestamp(self.create_time),
        'MTT_TEST_RUN_CREATE_TIMESTAMP_MILLIS':
            ToTimestamp(self.create_time) * 1000,
        'MTT_DEVICE_IMAGE_URL': url_map.get(TestResourceType.DEVICE_IMAGE, ''),
        'MTT_TEST_PACKAGE_URL': url_map.get(TestResourceType.TEST_PACKAGE, ''),
    }
    for k, v in url_map.iteritems():
      ctx['MTT_%s_URL' % k.name] = v
    return ctx


class TestRunSummary(ndb.Model):
  """Partial test run information.

  Attributes:
    labels: list of strings users can use to categorize test runs.
    test_name: name of the Test to run.
    run_target: run target.
    state: a test run state.
    test_package_info: a test package information
    test_devices: a list of TestDeviceInfo of DUTs
    total_test_count: the number of total test cases.
    failed_test_count: the number of failed test cases.
    failed_test_run_count: the number of test modules that failed to execute.
    create_time: time a test run is created.
    update_time: time a test run is last updated.
  """
  labels = ndb.StringProperty(repeated=True)
  test_name = ndb.StringProperty()
  run_target = ndb.StringProperty()
  state = msgprop.EnumProperty(TestRunState, default=TestRunState.UNKNOWN)
  test_package_info = ndb.StructuredProperty(TestPackageInfo)
  test_devices = ndb.StructuredProperty(TestDeviceInfo, repeated=True)
  total_test_count = ndb.IntegerProperty()
  failed_test_count = ndb.IntegerProperty()
  failed_test_run_count = ndb.IntegerProperty()
  create_time = ndb.DateTimeProperty()
  update_time = ndb.DateTimeProperty()


class ProxyConfig(ndb.Model):
  """A proxy configuration.

  Attributes:
    http_proxy: a proxy server for HTTP traffic.
    https_proxy: a proxy server for HTTPS traffic.
    ftp_proxy: a proxy server for FTP traffic.
    no_proxy: patterns for IP addresses or domain names that shouldn't use the
        proxy.
  """
  http_proxy = ndb.StringProperty()
  https_proxy = ndb.StringProperty()
  ftp_proxy = ndb.StringProperty()
  no_proxy = ndb.StringProperty()


class NodeConfig(ndb.Model):
  """A MTT node configuration.

  Attributes:
    env_vars: default environment vars.
    test_resource_default_download_urls: default download URLs for test
        resources.
    proxy_config: proxy configuration.
  """
  env_vars = ndb.LocalStructuredProperty(NameValuePair, repeated=True)
  test_resource_default_download_urls = ndb.LocalStructuredProperty(
      NameValuePair, repeated=True)
  proxy_config = ndb.LocalStructuredProperty(ProxyConfig)


def GetNodeConfig():
  """Returns a node config object.

  Returns:
    a NodeConfig object.
  """
  obj = ndb.Key(NodeConfig, NODE_CONFIG_ID).get()
  if not obj:
    obj = NodeConfig(id=NODE_CONFIG_ID)
    obj.put()
  return obj


class PrivateNodeConfig(ndb.Model):
  """Non-shareable node configs.

  Attributes:
    metrics_enabled: True to collect usage metrics.
    setup_wizard_completed: If false, trigger the setup wizard on startup
    server_uuid: node's unique identifier.
  """
  metrics_enabled = ndb.BooleanProperty()
  setup_wizard_completed = ndb.BooleanProperty()
  server_uuid = ndb.StringProperty(required=True, default=str(uuid.uuid4()))


def GetPrivateNodeConfig():
  """Returns a private node config object.

  Returns:
    a PrivateNodeConfig object.
  """
  obj = PrivateNodeConfig.query().get()
  if obj is None:
    obj = PrivateNodeConfig()
    obj.put()
  return obj


class TestResourceTracker(ndb.Model):
  """Test resource download tracker.

  Serves as a lock to determine the thread that should perform the download, and
  holds the download metadata.

  Attributes
    update_time: Latest update timestamp.
    download_progress: Download progress (between 0 and 1).
    completed: True if download is finished.
    error: Optional error encountered during download.
  """
  _use_cache = False
  _use_memcache = False
  update_time = ndb.DateTimeProperty(auto_now=True)
  download_progress = ndb.FloatProperty(required=True, default=0.0)
  completed = ndb.BooleanProperty()
  error = ndb.StringProperty()
