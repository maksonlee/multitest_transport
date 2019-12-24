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

import * as moment from 'moment';

import {AppData} from '../services/app_data';
import * as MttModels from '../services/mtt_models';
import * as TfcModels from '../services/tfc_models';

// CONSTANTS;
const ADB_VERSION = '12.3.4-5678901';
const ANALYTICS_TRACKING_ID = 'analyticstrackingid';
const ATTEMPT_ID = 'attemptid789';
const BUILD_CHANNEL_ID = 'test_build_channel_id';
const BUILD_CHANNEL_NAME = 'test_build_channel_name';
const BUILD_CHANNEL_PROVIDER_NAME = 'Partner Android Build';
const BUILD_ITEM_NAME = 'test_build_item_name';
const CLUSTER = 'cluster1';
const COMMAND_ID = 'commandid456';
const COMMAND_STATE = TfcModels.CommandState.RUNNING;
const DATE = new Date().toISOString();
const DATE_FUTURE = addTime(DATE, 0, 5, 0);  // 5 minutes later
const DEVICE_ACTION_ID = 'reset';
const DEVICE_ACTION_NAME = 'Factory Reset';
const DEVICE_BUILD_ID = 'B12.34.56';
const DEVICE_PRODUCT = 'fish';
const DEVICE_SERIAL = 'D12345';
const FAILED_TEST_COUNT = 13;
const FILE_BROWSE_URL = '/file/browse/url';
const FILE_OPEN_URL = '/file/open/url';
const FILE_SERVER_ROOT = '/file/server/root';
const MTT_VERSION = '01012000';
const OPTION_DEF_NAME = 'test_name';
const PREVIOUS_TEST_RUN_ID = '12345678';
const REQUEST_ID = 'requestid123';
const REQUEST_STATE = TfcModels.RequestState.RUNNING;
const RUN_TARGET_LIST = ['target1', 'target2'];
const RUN_TARGET_STRING = RUN_TARGET_LIST.join(';');
const TARGET_PREPARER_CLASS_NAME = 'test_class_name';
const TEST_GROUP_STATUS_NAME = 'testgroupstatusname';
const TEST_ID = 'testid123';
const TEST_NAME = 'test456';
const TEST_RESOURCE_DEF_NAME = 'testname';
const TEST_RESOURCE_DEF_DEFAULT_DOWNLOAD_URL = 'url';
const TEST_RESOURCE_TYPE = MttModels.TestResourceType.TEST_PACKAGE;
const TEST_RUN_ID = 'id123';
const TEST_RUN_OUTPUT_LINES = [
  'Invocation finished in 100s. PASSED: 42, FAILED: 13, MODULES: 2 of 2\n',
  'Saved log to /tmp/tradefed_global_log_123456789.txt\n',
  '06-12 10:38:07 I/CommandScheduler: All done\n'
];
const TEST_RUN_STATE = MttModels.TestRunState.RUNNING;
const TEST_PACKAGE_NAME = 'CTS 8.1';
const TEST_PACKAGE_VERSION = 'r11';
const TEST_PLAN_ID = 'test_plan_id';
const TEST_PLAN_NAME = 'test_plan_name';
const TOTAL_TEST_COUNT = 42;

/*******************************************
 * Functions to create mock MTT API objects
 *******************************************/

/** Create a new Build Channel */
export function newMockBuildChannel(
    id = BUILD_CHANNEL_ID, name = BUILD_CHANNEL_NAME) {
  return {
    id,
    name,
    provider_name: 'Local File Store',
    user_upload_url: 'user/upload/url',
    auth_state: MttModels.BuildChannelAuthState.AUTHORIZED,
    need_auth: false,
  };
}

/** Create a new Build Channel Config */
export function newMockBuildChannelConfig(
    id = BUILD_CHANNEL_ID, name = BUILD_CHANNEL_NAME,
    providerName = BUILD_CHANNEL_PROVIDER_NAME) {
  return {
    id,
    name,
    provider_name: providerName,
    options: [{name: 'account_id', value: '3333333'}]
  };
}

/** Create a new Build Channel Provider */
export function newMockBuildChannelProvider(
    name = BUILD_CHANNEL_NAME, optionDefs?: MttModels.OptionDef[]) {
  if (optionDefs === undefined) {
    return {name};
  }
  return {name, option_defs: optionDefs};
}

/** Create a new Build Channel Provider List */
export function newMockBuildChannelProviderList() {
  return [
    newMockBuildChannelProvider(
        'Test Storage', [newMockOptionDef('test_name')]),
    newMockBuildChannelProvider(
        'Google Cloud Storage', [newMockOptionDef('bucket_name')]),
    newMockBuildChannelProvider('Android'),
    newMockBuildChannelProvider('Local File Store'),
    newMockBuildChannelProvider(
        'Partner Android Build', [newMockOptionDef('account_id')])
  ];
}

/** Create a mock buildItem */
export function newMockBuildItem(name = BUILD_ITEM_NAME) {
  return {
    name,
    path: 'build/item/path',
    is_file: true,
    size: 0,
    timestamp: DATE,
    origin_url: 'fake_url',
    description: 'this is description'
  };
}

/** Create a mock buildItemList */
export function newMockBuildItemList() {
  return {
    build_items:
        [newMockBuildItem('a'), newMockBuildItem('b'), newMockBuildItem('c')],
    next_page_token: 'fake_token'
  };
}

/** Creates a new Device given serial and product */
export function newMockDevice(
    deviceSerial = DEVICE_SERIAL, product = DEVICE_PRODUCT,
    state = 'Available') {
  return {
    battery_level: '85',
    build_id: DEVICE_BUILD_ID,
    device_serial: deviceSerial,
    device_type: product,
    product,
    state,
    timestamp: DATE,
  };
}

/** Creates a new Device Action */
export function newMockDeviceAction(
    id = DEVICE_ACTION_ID, name = DEVICE_ACTION_NAME) {
  return {id, name};
}

/** Create a list of Device Action */
export function newMockDeviceActionList() {
  return [
    newMockDeviceAction('id1', 'name1'),
    newMockDeviceAction('id2', 'name2'),
    newMockDeviceAction('id3', 'name3'),
  ];
}

/** Creates a new mock invocation status object */
export function newMockInvocationStatus() {
  return {
    test_group_statuses: [
      newMockTestGroupStatus('Passing Module', 3, 0, true, 50),
      newMockTestGroupStatus('Failing Module', 29, 13, true, 12345, 'msg 2'),
    ]
  };
}

/** Creates a new NameMultiValuePair object */
export function newMockNameMultiValuePair(name: string) {
  return {
    name,
    values: ['a', 'b', 'c'],
  };
}

/** Creates a list of NameMultiValuePair object */
export function newMockNameMultiValuePairList() {
  return [
    newMockNameMultiValuePair('testa'),
    newMockNameMultiValuePair('testb'),
    newMockNameMultiValuePair('testc'),
    newMockNameMultiValuePair('testd'),
  ];
}

/** Creates a Name Value Pair object */
export function newMockNameValuePair(name: string, value?: string) {
  return {name, value};
}

/** Creates a list of Name Value Pair object */
export function newMockNameValuePairList() {
  return [
    newMockNameValuePair('pair1', 'value1'),
    newMockNameValuePair('pair2', 'value2'),
    newMockNameValuePair('pair3', 'value3'),
  ];
}

/** Create a new Test Run Request */
export function newMockNewTestRunRequest() {
  return {
    prev_test_run_id: PREVIOUS_TEST_RUN_ID,
    test_run_config: newMockTestRunConfig(TEST_ID),
  };
}

/** Create a mock a node config object */
export function newMockNodeConfig() {
  return {proxy_config: newMockProxyConfig()};
}

/** Create new build channel provider option definition */
export function newMockOptionDef(name = OPTION_DEF_NAME) {
  return {name, value_type: 'str', choices: [], default: ''};
}

/** Create a mock ProxyConfig object */
export function newMockProxyConfig() {
  return {http_proxy: 'sample http proxy', no_proxy: 'sample no proxy'};
}

/** Creates a new Test */
export function newMockTest(id = TEST_ID, name = TEST_NAME) {
  return {id, name};
}

/** Creates a new mock test group status */
export function newMockTestGroupStatus(
    name = TEST_GROUP_STATUS_NAME, failedTestCount?: number,
    passedTestCount?: number, isCompleted?: boolean, elapsedTime?: number,
    failureMessage?: string) {
  return {
    name,
    failed_test_count: failedTestCount,
    passed_test_count: passedTestCount,
    is_completed: isCompleted,
    elapsed_time: elapsedTime,
    failure_message: failureMessage,
  };
}

/** Creates a new Test Package Info object */
export function newMockTestPackageInfo(
    name = TEST_PACKAGE_NAME, version = TEST_PACKAGE_VERSION) {
  return {name, version};
}

/** Creates a new Test Plan */
export function newMockTestPlan(id = TEST_PLAN_ID, name = TEST_PLAN_NAME) {
  return {id, name, test_run_configs: [], labels: [], cron_exp: '* * * * *'};
}

/** Creates a list of new test resource def object */
export function newMockTestResourceDefs(): MttModels.TestResourceDef[] {
  return [
    newMockTestResourceDef(
        'name1', 'url1', MttModels.TestResourceType.DEVICE_IMAGE),
    newMockTestResourceDef('name2', 'url2', MttModels.TestResourceType.UNKNOWN),
  ];
}

/** Creates a new test resource def object */
export function newMockTestResourceDef(
    name = TEST_RESOURCE_DEF_NAME,
    defaultDownloadUrl = TEST_RESOURCE_DEF_DEFAULT_DOWNLOAD_URL,
    testResourceType: MttModels.TestResourceType): MttModels.TestResourceDef {
  return {
    name,
    default_download_url: defaultDownloadUrl,
    test_resource_type: testResourceType
  };
}

/** Creates a new mock test resource object */
export function newMockTestResourceObj(
    name = TEST_RESOURCE_DEF_NAME, url = TEST_RESOURCE_DEF_DEFAULT_DOWNLOAD_URL,
    cacheUrl = TEST_RESOURCE_DEF_DEFAULT_DOWNLOAD_URL,
    testResourceType = TEST_RESOURCE_TYPE): MttModels.TestResourceObj {
  return {
    name,
    url,
    cache_url: cacheUrl,
    test_resource_type: testResourceType,
  };
}

/** Creates a list of new test resource objects */
export function newMockTestResourceObjs(): MttModels.TestResourceObj[] {
  return [
    newMockTestResourceObj(
        'name1', 'url1', 'cacheUrl1', MttModels.TestResourceType.DEVICE_IMAGE),
    newMockTestResourceObj(
        'name2', 'url2', 'cacheUrl2', MttModels.TestResourceType.UNKNOWN),
  ];
}

/** Creates a new Test Run given an id and test (state is optional) */
export function newMockTestRun(
    test: MttModels.Test, id = TEST_RUN_ID, state = TEST_RUN_STATE,
    testResources: MttModels.TestResourceObj[] = [],
    testPackageInfo?: MttModels.TestPackageInfo,
    testDevices?: TfcModels.DeviceInfo[], failedTestCount = FAILED_TEST_COUNT,
    totalTestCount = TOTAL_TEST_COUNT) {
  return {
    id,
    test,
    test_package_info: testPackageInfo,
    test_devices: testDevices,
    test_resources: testResources,
    test_run_config: newMockTestRunConfig(test.id!),
    state,
    failed_test_count: FAILED_TEST_COUNT,
    total_test_count: TOTAL_TEST_COUNT,
    create_time: DATE,
    update_time: DATE,
  };
}

/** Creates a new Test Run Config given a testid */
export function newMockTestRunConfig(testId: string) {
  return {
    test_id: testId,
    cluster: CLUSTER,
    run_target: RUN_TARGET_STRING,
    run_count: 1,
    shard_count: 1,
    extra_args: '',
    queue_timeout_seconds: 100,
    sharding_mode: MttModels.TFShardingMode.RUNNER,
    before_device_action_ids: [],
    result_report_action_ids: [],
  };
}

/** Creates a new Test Run Output object */
export function newMockTestRunOutput(
    lines = TEST_RUN_OUTPUT_LINES, offset = 0) {
  return {
    length: (lines.join('')).length,
    lines,
    offset,
  };
}

/** Creates a new TradefedConfigObject */
export function newMockTradefedConfigObject(
    className = TARGET_PREPARER_CLASS_NAME) {
  return {
    class_name: className,
    option_values: [],
  };
}

/** Creates a list of TradefedConfigObject */
export function newMockTradefedConfigObjectList() {
  return [
    newMockTradefedConfigObject('className1'),
    newMockTradefedConfigObject('className2'),
    newMockTradefedConfigObject('className3'),
  ];
}

/** Creates a new PrivateNodeConfig */
export function newMockPrivateNodeConfig(
    metricsEnabled = true, setupWizardCompleted = true) {
  return {
    metrics_enabled: metricsEnabled,
    setup_wizard_completed: setupWizardCompleted
  };
}

/*******************************************
 * Functions to create mock TFC API objects
 *******************************************/

/** Creates a new Command */
export function newMockCommand(
    id = COMMAND_ID, requestId = REQUEST_ID,
    state = COMMAND_STATE): TfcModels.Command {
  return {
    id,
    request_id: requestId,
    state,
  };
}

/** Creates a new Command Attempt */
export function newMockCommandAttempt(
    failedTestCount?: number, passedTestCount?: number, requestId = REQUEST_ID,
    commandId = COMMAND_ID, attemptId = ATTEMPT_ID, state = COMMAND_STATE,
    startTime = DATE, endTime = DATE_FUTURE): TfcModels.CommandAttempt {
  return {
    request_id: requestId,
    command_id: commandId,
    attempt_id: attemptId,
    state,
    failed_test_count: failedTestCount,
    passed_test_count: passedTestCount,
    start_time: startTime,
    end_time: endTime,
  };
}

/** Creates a new Request */
export function newMockRequest(
    commands: TfcModels.Command[] = [],
    commandAttempts: TfcModels.CommandAttempt[] = [], id = REQUEST_ID,
    state = REQUEST_STATE): TfcModels.Request {
  return {id, state, commands, command_attempts: commandAttempts};
}

/*****************************************
 * Functions to create other mock objects
 *****************************************/

/** Create a new mock app data */
export function newMockAppData(
    fileServerRoot = FILE_SERVER_ROOT, fileBrowseUrl = FILE_BROWSE_URL,
    fileOpenUrl = FILE_OPEN_URL, analyticsTrackingId = ANALYTICS_TRACKING_ID,
    mttVersion = MTT_VERSION, adbVersion = ADB_VERSION): AppData {
  return {
    adbVersion,
    analyticsTrackingId,
    fileBrowseUrl,
    fileOpenUrl,
    fileServerRoot,
    mttVersion,
  };
}

/**
 * Make a File object with custom text content
 * @param text Custom text content
 */
export function newMockFile(text: string, fileName: string) {
  return new File([new Blob([text], {type: 'text/plain'})], fileName);
}

/*******************
 * Helper functions
 *******************/

/**
 * Adds time to a Date
 *
 * @param date the starting date
 * @param hours number of hours to add
 * @param minutes number of minutes to add
 * @param seconds number of seconds to add
 * @return a new Date with the inputted amount of time added
 */
export function addTime(
    date: string, hours: number, minutes: number, seconds: number) {
  return moment(date)
      .add(hours, 'hours')
      .add(minutes, 'minutes')
      .add(seconds, 'seconds')
      .toISOString();
}

/**
 * Convert a string to title case (e.g. abc abc -> Abc Abc, ABC ABC -> Abc Abc)
 *
 * @param str a string that needs to be converted
 * @return a converted string
 */
export function toTitleCase(str: string) {
  return str.replace(
      /\w+/g,
      (word) =>
          `${word.charAt(0).toUpperCase()}${word.substr(1).toLowerCase()}`);
}
