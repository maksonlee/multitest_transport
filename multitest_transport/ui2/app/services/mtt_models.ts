/**
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Property names match those in models/ndb_models.py.
// tslint:disable:enforce-name-casing
import {DeviceInfo} from './tfc_models';

/** Default queue timeout seconds, used in new test plan, and new test run */
export const DEFAULT_QUEUE_TIMEOUT_SECONDS = 24 * 60 * 60;  // one day
/**
 * Default invocation timeout seconds, used in new test plan, and new test
 * run pages
 */
export const DEFAULT_INVOCATION_TIMEOUT_SECONDS = 0;  // no timeout
/**
 * Default output idle timeout seconds, used in new test plan, and new test
 * run pages
 */
export const DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS = 3600;  // one hour
/**
 * Default max retry on test failures, used in new test plan, and new test
 * run pages
 */
export const DEFAULT_MAX_RETRY_ON_TEST_FAILURES = 1;
/** Default run count. used in new test plan, and new test run */
export const DEFAULT_RUN_COUNT = 1;
/** Default shard count, used in new test plan, and new test run */
export const DEFAULT_SHARD_COUNT = 0;
/** Default cluster name */
const DEFAULT_CLUSTER = 'default';

/** OAuth2 authorization information. */
export declare interface AuthorizationInfo {
  /** An authorization url. */
  url: string;
  /**
   * A boolean value which tell us to start automatic or
   * manual copy/paste flow
   */
  is_manual: boolean;
}

/** Authorization states (for build channels or test run actions). */
export enum AuthorizationState {
  NOT_APPLICABLE = 'NOT_APPLICABLE',
  AUTHORIZED = 'AUTHORIZED',
  UNAUTHORIZED = 'UNAUTHORIZED',
}

/** Authorization methods. */
export enum AuthorizationMethod {
  OAUTH2_AUTHORIZATION_CODE = 'OAUTH2_AUTHORIZATION_CODE',
  OAUTH2_SERVICE_ACCOUNT = 'OAUTH2_SERVICE_ACCOUNT',
}

/**
 * A Simple String Message containing a value
 */
export declare interface SimpleMessage {
  /** Simple string message. */
  value: string;
}
/**
 * A build item
 */
export declare interface BuildItem {
  /** A build name */
  name: string;
  /** A build item's path */
  path: string;
  /** Builditem can be folder or file */
  is_file: boolean;
  /** Size of this build item (bytes) */
  size: number;
  /** Created time of this build item */
  timestamp: string;
  /** The description of this build item */
  description: string;
}

/**
 * A list of build item
 */
export declare interface BuildItemList {
  /** A list of builditem */
  build_items?: BuildItem[];
  /** Next page token */
  next_page_token: string;
}

/**
 * Information for user or service account credentials
 */
export declare interface CredentialsInfo {
  /** Email for the user or service account */
  email?: string;
}

/**
 * A build channel, which combines channel config and provider properties.
 *
 * id: build channel id
 * name: build channel name
 * provider_name: channel provider name (e.g. google drive, local file store)
 */
export declare interface BuildChannel {
  id: string;
  name: string;
  provider_name: string;
  auth_state: AuthorizationState;
  auth_methods?: AuthorizationMethod[];
  credentials?: CredentialsInfo;
}

/**
 * A list of the IDs for the default build channels that shouldn't be editable
 */
export const DEFAULT_BUILD_CHANNEL_IDS =
    ['android_ci', 'google_cloud_storage', 'google_drive'];

/**
 * Check whether a build channel is available
 */
export function isBuildChannelAvailable(buildChannel: BuildChannel): boolean {
  return buildChannel.auth_state !== AuthorizationState.UNAUTHORIZED;
}

/**
 * Returns true if the build channel is a default build channel
 */
export function isDefaultBuildChannel(buildChannel: BuildChannel): boolean {
  // TODO: Find a more reliable way to determine default configs
  return DEFAULT_BUILD_CHANNEL_IDS.includes(buildChannel.id);
}

/**
 * A BuildChannelConfig Object
 */
export declare interface BuildChannelConfig {
  /** A buildChannelConfig id */
  id: string;
  /** A buildChannel name */
  name: string;
  /** provider name for this build_channel (e.g. Android, Google Drive) */
  provider_name: string;
  /** A list of NameValuePair */
  options?: NameValuePair[];
}

/**
 * A list of build channels.
 *
 * build_channels: a list of BuildChannel object
 */
export declare interface BuildChannelList {
  build_channels?: BuildChannel[];
}

/**
 * Information about a build channel provider.
 */
export declare interface BuildChannelProvider {
  /** A build channel provider name */
  name: string;
  /** A list of OptionDef object */
  option_defs?: OptionDef[];
}

/**
 * A list of build channel providers.
 */
export declare interface BuildChannelProviderList {
  /** build_channel_providers: a list of BuildChannelProvider object */
  build_channel_providers?: BuildChannelProvider[];
}

/**
 * Import and update status of a ConfigSet
 */
export enum ConfigSetStatus {
  NOT_IMPORTED = 'NOT_IMPORTED',
  IMPORTED = 'IMPORTED',
  UPDATABLE = 'UPDATABLE',
}

/**
 * Metadata for an MTT configuration file
 */
export declare interface ConfigSetInfo {
  /** URL where the config file can be downloaded from */
  url: string;
  /** SHA hash of the file contents */
  hash?: string;
  /** Display name for the config set */
  name: string;
  /** Short description of the contents */
  description?: string;
  /** Last time the config set was imported */
  last_update_time?: string;
  /** Import and updatable status of the config set */
  status: ConfigSetStatus;
}

/**
 * A list of config set infos
 */
export declare interface ConfigSetInfoList {
  config_set_infos: ConfigSetInfo[];
}

/**
 * Separates the config set namespace from the object id
 */
export const NAMESPACE_SEPARATOR = '::';

/**
 * Returns the namespace from a given id, or empty string if no namespace
 */
export function getNamespaceFromId(id: string): string {
  const split = id.split(NAMESPACE_SEPARATOR);
  if (split.length < 2) {
    return '';
  }
  return split[0];
}

/**
 * A device action.
 *
 * id: a device action id
 * name: a device action name.
 * description: a description.
 * test_resource_defs: a list of test resource definitions.
 * tradefed_target_preparers: a list of Tradefed target preparers.
 * device_type: the type of the devices that require the device action.
 * tradefed_options: key-value pairs to be added to Tradefed configuration.
 */
export declare interface DeviceAction {
  id: string;
  name: string;
  description?: string;
  test_resource_defs?: TestResourceDef[];
  tradefed_target_preparers?: TradefedConfigObject[];
  device_type?: string;
  tradefed_options?: NameMultiValuePair[];
}

/** initialize a device action */
export function newDeviceAction(): Partial<DeviceAction> {
  return {
    test_resource_defs: [],
    tradefed_target_preparers: [],
    tradefed_options: [],
  };
}

/**
 * A list of device actions
 */
export declare interface DeviceActionList {
  device_actions: DeviceAction[];
}

/** Add or remove the device actions according to the device types */
export function updateSelectedDeviceActions(
    selectedDeviceActions: readonly DeviceAction[],
    allDeviceActions: readonly DeviceAction[],
    deviceTypes: Set<string>): DeviceAction[] {
  const updatedDeviceActions: DeviceAction[] = [];

  // Exclude the auto-selected DeviceActions that have device type field but do
  // not match any device.
  for (const selectedAction of selectedDeviceActions) {
    const deviceType = selectedAction.device_type;
    if (!deviceType || deviceTypes.has(deviceType)) {
      updatedDeviceActions.push(selectedAction);
    }
  }

  // Add the DeviceActions that match any device.
  for (const action of allDeviceActions) {
    const deviceType = action.device_type;
    if (deviceType && deviceTypes.has(deviceType) &&
        !updatedDeviceActions.some(
            (selectedAction) => selectedAction === action)) {
      updatedDeviceActions.push(action);
    }
  }
  return updatedDeviceActions;
}

/** Event log levels. */
export enum EventLogLevel {
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
}

/** Event log entry. */
export declare interface EventLogEntry {
  create_time: string;
  level: EventLogLevel;
  message: string;
}

/** A Name Value Pair */
export declare interface NameValuePair {
  name: string;
  value?: string;
}

/** A Name Value-Array Pair */
export declare interface NameMultiValuePair {
  name: string;
  values?: string[];
}

/**
 * A new test run request object
 */
export declare interface NewTestRunRequest {
  /** A list of labels */
  labels?: string[];
  /** A TestRunConfig Object */
  test_run_config?: TestRunConfig;
  /** A list of TestResourcePipe */
  test_resource_pipes?: TestResourcePipe[];
  /** Previous Test Run's Id */
  rerun_context?: RerunContext;
  /** List of configs to retry with */
  rerun_configs?: TestRunConfig[];
}

/**
 *  Node config
 */
export declare interface NodeConfig {
  /** default environment vars. */
  env_vars?: NameValuePair[];
  /**
   * default download URLs for test resources. (e.g) [{name: 'android-ct
   * s.zip', value: 'some url'}]. When creating a new test run, testResourceDefs
   * would be prefilled with the url if supplied here.
   */
  test_resource_default_download_urls?: NameValuePair[];
}

/**
 * A build channel provider option definition.
 */
export declare interface OptionDef {
  /** An option definition name */
  name: string;
  /** An option definition value type */
  value_type: string;
  /**  List of possible values */
  choices?: string[];
  /** A default value for choices */
  default?: string;
}

/** Non-shareable node configs */
export declare interface PrivateNodeConfig {
  /** True to collect usage metrics. */
  metrics_enabled?: boolean;
  /** If false, trigger the setup wizard */
  setup_wizard_completed?: boolean;
  /** default service account credentials */
  default_credentials?: CredentialsInfo;
}

/**
 * Previous test run context used for rerun.
 *
 * Represents either a local test run (ID provided) or a remote test run
 * (context file already uploaded to local file storage and filename provided).
 */
export declare interface RerunContext {
  /** local test run id */
  test_run_id?: string;
  /** remote test run filename */
  context_filename?: string;
  /** remote test run file URL */
  context_file_url?: string;
}

/**
 * Test run parameter.
 */
export declare interface TestRunParameters {
  /** Default max retry on test failures. */
  max_retry_on_test_failures?: number;
  /** Default invocation timeout in seconds. */
  invocation_timeout_seconds?: number;
  /** Default output idle timeout in seconds. */
  output_idle_timeout_seconds?: number;
}

/**
 * Test config options
 */
export declare interface Test {
  /** Auto-generated id */
  id?: string;
  /** Name for the Test */
  name: string;
  /** Description for the Test */
  description?: string;
  /** A list of test resource def obj */
  test_resource_defs?: TestResourceDef[];
  /** Command to execute the test run */
  command?: string;
  /** Environment variables */
  env_vars?: NameValuePair[];
  /** Output files to copy to retrieve with MTT */
  output_file_patterns?: string[];
  /** Result File */
  result_file?: string;
  /** Scripts to run before executing the test */
  setup_scripts?: string[];
  /** JVM options */
  jvm_options?: string[];
  /** Java environment variables */
  java_properties?: NameValuePair[];
  /**
   * Directory where the context file that needs to be passed across attempts
   * is located
   */
  context_file_dir?: string;
  /**
   * A regex pattern for the filename of the context file which needs to be
   *  passed across attempts
   */
  context_file_pattern?: string;
  /** Command to retry the test */
  retry_command_line?: string;
  /** Sharding option */
  runner_sharding_args?: string;
  /** Default test run parameter */
  default_test_run_parameters?: TestRunParameters;
}

/** Initialize a test */
export function initTest(): Partial<Test> {
  return {
    test_resource_defs: [],
    env_vars: [],
    output_file_patterns: [],
    setup_scripts: [],
    jvm_options: [],
    java_properties: []
  };
}

/** Initialize a test */
export function initTestPlan(): Partial<TestPlan> {
  return {
    name: '',
    labels: [],
    cron_exp: '',
    test_run_configs: [],
    test_resource_pipes: [],
    before_device_action_ids: [],
  };
}

/** The context of a test run */
export declare interface TestContextObj {
  /** Command used to execute the test run */
  command_line: string;
  /** List of environment variables set */
  env_vars?: NameValuePair[];
  /** List of test resources used */
  test_resources?: TestResourceObj[];
}

/** List of Tests */
export declare interface TestList {
  tests?: Test[];
  next_page_token?: string;
}

/**
 * Information on the test package
 */
export declare interface TestPackageInfo {
  /** Test package build number. */
  build_number?: string;
  /** Test package architecture. */
  target_architecture?: string;
  /** A short name of test package. */
  name?: string;
  /** A full name of test package. */
  full_name?: string;
  /** Test package version */
  version?: string;
}

/**
 * Test plan info
 */
export declare interface TestPlan {
  id?: string;
  name: string;
  labels?: string[];
  cron_exp?: string;
  cron_exp_timezone?: string;
  test_run_configs?: TestRunConfig[];
  test_resource_pipes?: TestResourcePipe[];
  before_device_action_ids?: string[];
  test_run_action_refs?: TestRunActionRef[];
  last_run_time?: string;
  last_run_ids?: string[];
  last_run_error?: string;
  next_run_time?: string;
}

/** List of Test plans */
export declare interface TestPlanList {
  test_plans?: TestPlan[];
}

/** Information on the test resource pipe */
export declare interface TestResourcePipe {
  name: string;
  url: string;
  test_resource_type: TestResourceType;
}

/**
 * A test resource definition.
 *
 *  name: a test resource name. (e.g. bootloader.img)
 *  default_download_url: a default download URL.
 *  test_resource_type: a test resource type. (e.g. DEVICE_IMAGE)
 *  decompress: whether the host should decompress the downloaded file.
 *  decompress_dir: the directory where the host decompresses the file.
 */
export declare interface TestResourceDef {
  /** a test resource name. (e.g. bootloader.img) */
  name: string;
  /** default value for the download url */
  default_download_url?: string;
  /** a test resource type. (e.g. DEVICE_IMAGE) */
  test_resource_type: TestResourceType;
  /** whether the host should decompress the downloaded file */
  decompress?: boolean;
  /** the directory where the host decompresses the file */
  decompress_dir?: string;
}

/**
 * A test resource object.
 * The "Obj" suffix was added to avoid name collision with TFC
 * TestResource.
 */
export declare interface TestResourceObj {
  /** a test resource name. */
  name?: string;
  /** a URL. */
  url?: string;
  /** a URL for a cached copy. */
  cache_url?: string;
  /** a test resource type. */
  test_resource_type?: TestResourceType;
  /** whether the host should decompress the downloaded file. */
  decompress?: boolean;
  /** the directory where the host decompresses the file. */
  decompress_dir?: string;
}

/**
 * Converts a TestResourceDef into a TestResourceObj
 */
export function testResourceDefToObj(testResourceDef: TestResourceDef):
    TestResourceObj {
  return {
    name: testResourceDef.name,
    url: testResourceDef.default_download_url,
    test_resource_type: testResourceDef.test_resource_type,
    decompress: testResourceDef.decompress,
  };
}

/**
 * A list of test resource types
 */
export enum TestResourceType {
  UNKNOWN = 'UNKNOWN',
  DEVICE_IMAGE = 'DEVICE_IMAGE',
  SYSTEM_IMAGE = 'SYSTEM_IMAGE',
  TEST_PACKAGE = 'TEST_PACKAGE'
}

/** TradeFed Sharding Mode */
export enum TFShardingMode {
  RUNNER,
  SCHEDULER,
}

/**
 * Run-time config options for a test run
 */
export declare interface TestRunConfig {
  /** Id of the Test used */
  test_id: string;
  /** Host cluster */
  cluster: string;
  /** Command to execute the test suite */
  command: string;
  /** Command to retry a test run */
  retry_command: string;
  /** Device requirements */
  device_specs?: string[];
  /** Number of times the test was run */
  run_count: number;
  /** Number of shards used */
  shard_count: number;
  /** Tradefed sharding mode */
  sharding_mode?: TFShardingMode;
  /** Max number of retries */
  max_retry_on_test_failures?: number;
  /** Invocation timeout in seconds */
  invocation_timeout_seconds?: number;
  /** how long a test run's output can be idle before attempting recovery */
  output_idle_timeout_seconds?: number;
  /** Timeout second when waiting in queue */
  queue_timeout_seconds: number;
  /** List of ids for the device actions */
  before_device_action_ids?: string[];
  /** List of test run action refs */
  test_run_action_refs?: TestRunActionRef[];
  /** List of test resource pipes */
  test_resource_objs?: TestResourceObj[];
  /** Whether to setup devices in parallel */
  use_parallel_setup?: boolean;
}

/** initialize a new test run config */
export function initTestRunConfig(test?: Test): Partial<TestRunConfig> {
  const config = {
    test_id: '',
    cluster: DEFAULT_CLUSTER,
    run_count: DEFAULT_RUN_COUNT,
    command: '',
    retry_command: '',
    device_specs: [],
    shard_count: DEFAULT_SHARD_COUNT,
    sharding_mode: TFShardingMode.RUNNER,
    max_retry_on_test_failures: DEFAULT_MAX_RETRY_ON_TEST_FAILURES,
    queue_timeout_seconds: DEFAULT_QUEUE_TIMEOUT_SECONDS,
    invocation_timeout_seconds: DEFAULT_INVOCATION_TIMEOUT_SECONDS,
    output_idle_timeout_seconds: DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS,
    before_device_action_ids: [],
    test_resource_objs: [],
    use_parallel_setup: true,
  };

  if (test) {
    // Load test defaults
    config.test_id = test.id || '';
    config.command = test.command || '';
    config.retry_command = test.retry_command_line || '';

    const parameters = test.default_test_run_parameters;
    if (parameters) {
      config.max_retry_on_test_failures =
          parameters.max_retry_on_test_failures ||
          DEFAULT_MAX_RETRY_ON_TEST_FAILURES;
      config.invocation_timeout_seconds =
          parameters.invocation_timeout_seconds ||
          DEFAULT_INVOCATION_TIMEOUT_SECONDS;
      config.output_idle_timeout_seconds =
          parameters.output_idle_timeout_seconds ||
          DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS;
    }
  }

  return config;
}

/** A list of test run configs to be scheduled as retries. */
export declare interface TestRunSequence {
  id: string;
  test_run_configs: TestRunConfig[];
  finished_test_run_ids: string[];
}

/** States for Test Runs */
export enum TestRunState {
  UNKNOWN = 'UNKNOWN',
  PENDING = 'PENDING',      // Downloading test resources
  QUEUED = 'QUEUED',        // Waiting for available devices
  RUNNING = 'RUNNING',      // Tests being run
  COMPLETED = 'COMPLETED',  // All tests completed
  // Test run started but cancelled (by user, or automatically)
  CANCELED = 'CANCELED',
  ERROR = 'ERROR',  // An error occurred during the test run
}

/** States that are final for a test run. */
export const FINAL_TEST_RUN_STATES: TestRunState[] = [
  TestRunState.COMPLETED,
  TestRunState.CANCELED,
  TestRunState.ERROR,
];

/** Returns true if the status is considered final, false otherwise */
export function isFinalTestRunState(state: TestRunState) {
  return FINAL_TEST_RUN_STATES.includes(state);
}

/**
 * Test run info and results (includes retries)
 */
export declare interface TestRun {
  /** Auto-generated id */
  id?: string;
  /** Test suite */
  test?: Test;
  /** Configs used for the run */
  test_run_config?: TestRunConfig;
  /** List of strings to filter test runs */
  labels?: string[];
  /** State of the test run */
  state: TestRunState;
  /** Additional state information */
  state_info?: TestRunState;
  /** Link to output files folder */
  output_url?: string;
  /** Information on the test package */
  test_package_info?: TestPackageInfo;
  /** List of snapshots of devices that were tested */
  test_devices?: DeviceInfo[];
  /** List of the test resource files used for this test run */
  test_resources?: TestResourceObj[];
  /** Tradefed request id */
  request_id?: string;
  /** Total tests run */
  total_test_count?: number;
  /** Total tests failed */
  failed_test_count?: number;
  /** Total modules failed */
  failed_test_run_count?: number;
  /** Time test started running */
  create_time?: string;
  /** Last time results were updated */
  update_time?: string;
  /** Id for the previous test run */
  prev_test_run_id?: string;
  /** test context from the previous test run */
  prev_test_context?: TestContextObj;
  /** test context generated from this test run */
  next_test_context?: TestContextObj;
  /** Test run log entries */
  log_entries?: EventLogEntry[];
  /** Id of the TestRunSequence this config belongs to */
  sequence_id?: string;
}

/** Partial test run information. */
export declare interface TestRunSummary {
  /** Auto-generated id */
  id?: string;
  /** Test run */
  test_name?: string;
  /** Device requirements */
  device_specs?: string[];
  /** State of the test run */
  state: TestRunState;
  /** Information on the test package */
  test_package_info?: TestPackageInfo;
  /** List of snapshots of devices that were tested */
  test_devices?: DeviceInfo[];
  /** Total tests run */
  total_test_count?: number;
  /** Total tests failed */
  failed_test_count?: number;
  /** Total modules failed */
  failed_test_run_count?: number;
  /** Time test started running */
  create_time?: string;
  /** Last time results were updated */
  update_time?: string;
}

/** List of test run summaries. */
export declare interface TestRunSummaryList {
  test_runs?: TestRunSummary[];
  next_page_token?: string;
  prev_page_token?: string;
}

/** Output log of Test Runs, displayed in the test run details console */
export declare interface TestRunOutput {
  /** Number of lines */
  length: number;
  /** Array of output strings */
  lines?: string[];
  /** Line offset */
  offset: number;
}

/** Test run execution phases. */
export enum TestRunPhase {
  UNKNOWN = 'UNKNOWN',
  BEFORE_RUN = 'BEFORE_RUN',
  AFTER_ATTEMPT = 'AFTER_ATTEMPT',
  AFTER_RUN = 'AFTER_RUN',
  ON_SUCCESS = 'ON_SUCCESS',
  ON_ERROR = 'ON_ERROR',
}

/** Test run action. */
export declare interface TestRunAction {
  id: string;
  name: string;
  description?: string;
  hook_class_name: string;
  phases?: TestRunPhase[];
  options?: NameValuePair[];
  tradefed_result_reporters?: TradefedConfigObject[];
  authorization_state?: AuthorizationState;
}

/** List of test run actions. */
export declare interface TestRunActionList {
  actions: TestRunAction[];
}

/** Test run action reference. */
export declare interface TestRunActionRef {
  action_id: string;
  options?: NameValuePair[];
}

/**
 * Module-level results for a test run.
 * Reference to /models/message.py:TestModuleResult
 */
export declare interface TestModuleResult {
  id: string;
  attempt_id: string;
  name: string;
  complete: boolean;
  passed_tests: number;
  failed_tests: number;
  total_tests: number;
  error_message?: string;  // Incomplete modules will have an error message
}

/** Paginated list of TestModuleResult. */
export declare interface TestModuleResultList {
  results?: TestModuleResult[];
  next_page_token?: string;
}

/** Test outcome. */
export enum TestStatus {
  UNKNOWN = 'UNKNOWN',
  PASS = 'PASS',
  FAIL = 'FAIL',
  IGNORED = 'IGNORED',
  ASSUMPTION_FAILURE = 'ASSUMPTION_FAILURE',
}

/** TestCase-level results for a test run. */
export declare interface TestCaseResult {
  id: string;
  module_id: string;
  name: string;
  status: TestStatus;
  result: string;
  error_message: string;
  stack_trace: string;
}

/** Paginated list of TestCaseResult. */
export declare interface TestCaseResultList {
  results?: TestCaseResult[];
  next_page_token?: string;
}

/**
 * A Tradefed object and its options.
 */
export declare interface TradefedConfigObject {
  /** a Tradefed config class name. */
  class_name: string;
  /** a list of option name and value pairs. */
  option_values?: NameMultiValuePair[];
}

/** Table column */
export interface TableColumn {
  fieldName: string;
  displayName: string;
  removable: boolean;
  show: boolean;
}
