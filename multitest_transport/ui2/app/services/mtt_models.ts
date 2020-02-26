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
  /** The url for this build item */
  origin_url: string;
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
 * Build channel authorization states
 */
export enum BuildChannelAuthState {
  NOT_AUTHORIZED = 'NOT_AUTHORIZED',
  AUTHORIZED = 'AUTHORIZED'
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
  auth_state: BuildChannelAuthState;
  need_auth: boolean;
}

/**
 * A list of the IDs for the default build channels that shouldn't be editable
 */
export const DEFAULT_BUILD_CHANNEL_IDS =
    ['local_file_store', 'google_drive', 'google_cloud_storage'];

/**
 * Check whether a build channel is available
 */
export function isBuildChannelAvailable(buildChannel: BuildChannel): boolean {
  return !(
      buildChannel.need_auth &&
      buildChannel.auth_state === BuildChannelAuthState.NOT_AUTHORIZED);
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
 * A device action.
 *
 * id: a device action id
 * name: a device action name.
 * description: a description.
 * test_resource_defs: a list of test resource definitions.
 * tradefed_target_preparers: a list of Tradefed target preparers.
 */
export declare interface DeviceAction {
  id: string;
  name: string;
  description?: string;
  test_resource_defs?: TestResourceDef[];
  tradefed_target_preparers?: TradefedConfigObject[];
}

/** initialize a device action */
export function newDeviceAction(): Partial<DeviceAction> {
  return {
    test_resource_defs: [],
    tradefed_target_preparers: [],
  };
}

/**
 * A list of device actions
 */
export declare interface DeviceActionList {
  device_actions: DeviceAction[];
}

/**
 * An Endpoint Error object
 */
export declare interface EndpointError {
  /** Detailed Error message */
  message: string;
  /** Domain information */
  domain: string;
  /** Error type (e.g. Bad request) */
  reason: string;
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
  /** proxy configuration. */
  proxy_config?: ProxyConfig;
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

/**
 * A list of periodic time type use in ScheduleTimeForm component as dropdown
 * options.
 */
export enum PeriodicTimeType {
  MINUTE = 'Minute',
  HOUR = 'Hour',
  DAY = 'Day',
  WEEK = 'Week',
  MONTH = 'Month',
  YEAR = 'Year'
}

/** Non-shareable node configs */
export declare interface PrivateNodeConfig {
  /** True to collect usage metrics. */
  metrics_enabled?: boolean;
  /** If false, trigger the setup wizard */
  setup_wizard_completed?: boolean;
}

/**
 *   Proxy config
 */
export declare interface ProxyConfig {
  /** a proxy server for HTTP traffic. */
  http_proxy?: string;
  /** a proxy server for HTTPS traffic. */
  https_proxy?: string;
  /** a proxy server for FTP traffic. */
  ftp_proxy?: string;
  /**
   * patterns for IP addresses or domain names that shouldn't use the
   *  proxy.
   */
  no_proxy?: string;
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
  /** remote test run file */
  context_filename?: string;
}

/**
 * A list of schedule time type use in ScheduleTimeForm component as dropdown
 * options.
 */
export enum ScheduleTimeType {
  MANUAL = 'Manual',
  PERIODIC = 'Periodic',
  CUSTOM = 'Custom'
}

/**
 * Test config options
 */
export declare interface Test {
  /** Auto-generated id */
  id?: string;
  /** Name for the Test */
  name: string;
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
}

/** Initialize a test */
export function initTest(): Partial<Test> {
  return {
    test_resource_defs: [],
    env_vars: [],
    output_file_patterns: [],
    setup_scripts: [],
    jvm_options: [],
    java_properties: [],
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
  test_run_configs?: TestRunConfig[];
  test_resource_pipes?: TestResourcePipe[];
  before_device_action_ids?: string[];
  last_run_time?: string;
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
 */
export declare interface TestResourceDef {
  /** a test resource name. (e.g. bootloader.img) */
  name: string;
  /** default value for the download url */
  default_download_url?: string;
  /** a test resource type. (e.g. DEVICE_IMAGE) */
  test_resource_type: TestResourceType;
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
  };
}

/**
 * A list of test resource types
 */
export enum TestResourceType {
  UNKNOWN = 'UNKNOWN',
  DEVICE_IMAGE = 'DEVICE_IMAGE',
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
  /** Device selection rules */
  run_target: string;
  /** Number of times the test was run */
  run_count: number;
  /** Number of shards used */
  shard_count: number;
  /** Tradefed sharding mode */
  sharding_mode?: TFShardingMode;
  /** Extra command line arguments */
  extra_args?: string;
  /** Additional arguments to use when retrying */
  retry_extra_args?: string;
  /** Max number of retries */
  max_retry_on_test_failures?: number;
  /** Timeout second when waiting in queue */
  queue_timeout_seconds: number;
  /** how long a test run's output can be idle before attempting recovery */
  output_idle_timeout_seconds?: number;
  /** List of ids for the device actions */
  before_device_action_ids?: string[];
  /** List of test run action IDs */
  test_run_action_ids?: string[];
}

/** initialize a new test run config */
export function initTestRunConfig(): Partial<TestRunConfig> {
  return {
    cluster: DEFAULT_CLUSTER,
    run_count: DEFAULT_RUN_COUNT,
    run_target: '',
    shard_count: DEFAULT_SHARD_COUNT,
    sharding_mode: TFShardingMode.RUNNER,
    extra_args: '',
    retry_extra_args: '',
    max_retry_on_test_failures: DEFAULT_MAX_RETRY_ON_TEST_FAILURES,
    queue_timeout_seconds: DEFAULT_QUEUE_TIMEOUT_SECONDS,
    output_idle_timeout_seconds: DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS,
    before_device_action_ids: [],
  };
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
  /** test context from the previous test run */
  prev_test_context?: TestContextObj;
  /** test context generated from this test run */
  next_test_context?: TestContextObj;
}

/** Partial test run information. */
export declare interface TestRunSummary {
  /** Auto-generated id */
  id?: string;
  /** Test run */
  test_name?: string;
  /** Configs used for the run */
  run_target?: string;
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
