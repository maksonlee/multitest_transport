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

import {HttpClient, HttpParams} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {EMPTY, from, Observable, of as observableOf} from 'rxjs';
import {map, switchMap} from 'rxjs/operators';

import {AnalyticsParams} from './analytics_service';
import {AuthService, REDIRECT_URI} from './auth_service';
import {readBlobAsText} from './file_service';
import * as model from './mtt_models';

/** URL for MTT API methods */
export const MTT_API_URL = '/_ah/api/mtt/v1';

/** Client for MTT API access */
@Injectable({
  providedIn: 'root',
})
export class MttClient {
  readonly testRunActions: TestRunActionClient;
  readonly testResults: TestResultClient;

  constructor(
      private readonly http: HttpClient, private readonly auth: AuthService) {
    // TODO: Reorganize MttClient methods
    this.testRunActions = new TestRunActionClient(http, auth);
    this.testResults = new TestResultClient();
  }

  /**
   * Authorizes a build channel using an authorization code.
   * @param buildChannelId: build channel to authorize
   */
  authorizeBuildChannel(buildChannelId: string): Observable<void> {
    return this.getBuildChannelAuthorizationInfo(buildChannelId)
        .pipe(switchMap(authInfo => this.auth.getAuthorizationCode(authInfo)))
        .pipe(switchMap(code => {
          if (!code) {
            return EMPTY;
          }
          return this.sendBuildChannelAuthorizationCode(buildChannelId, code);
        }));
  }

  /** Sends build channel authorization code to complete flow. */
  private sendBuildChannelAuthorizationCode(
      buildChannelId: string, code: string): Observable<void> {
    const params = new AnalyticsParams('build_channels', 'authorize');
    return this.http.post<void>(
        `${MTT_API_URL}/build_channels/${
            encodeURIComponent(buildChannelId)}/auth`,
        {'redirect_uri': REDIRECT_URI, 'code': code}, {params});
  }

  /** Fetches a build channel's authorization information to start flow. */
  private getBuildChannelAuthorizationInfo(buildChannelId: string):
      Observable<model.AuthorizationInfo> {
    const params = new HttpParams().set('redirect_uri', REDIRECT_URI);
    return this.http.get<model.AuthorizationInfo>(
        `${MTT_API_URL}/build_channels/${
            encodeURIComponent(buildChannelId)}/auth`,
        {params});
  }

  /** Authorizes a build channel with a service account JSON key. */
  authorizeBuildChannelWithServiceAccount(buildChannelId: string, key: Blob):
      Observable<void> {
    return from(readBlobAsText(key)).pipe(switchMap(data => {
      const params = new AnalyticsParams('build_channels', 'authorize');
      return this.http.put<void>(
          `${MTT_API_URL}/build_channels/${
              encodeURIComponent(buildChannelId)}/auth`,
          {value: data}, {params});
    }));
  }

  /** Revokes a build channel's authorization. */
  unauthorizeBuildChannel(buildChannelId: string): Observable<void> {
    const params = new AnalyticsParams('build_channels', 'unauthorize');
    return this.http.delete<void>(
        `${MTT_API_URL}/build_channels/${
            encodeURIComponent(buildChannelId)}/auth`,
        {params});
  }

  lookupBuildItem(url: string):
      Observable<model.BuildItem> {
    const params = new HttpParams().set('url', url);
    return this.http.get<model.BuildItem>(
        `${MTT_API_URL}/build_channels/build_item_lookup`, {params});
  }

  listBuildItems(id: string, path: string, pageToken?: string):
      Observable<model.BuildItemList> {
    let params = new HttpParams().set('path', path);
    if (pageToken) {
      params = params.set('page_token', pageToken);
    }
    return this.http.get<model.BuildItemList>(
        `${MTT_API_URL}/build_channels/${encodeURIComponent(id)}/build_items`,
        {params});
  }

  deleteBuildItem(id: string, path: string) {
    const params = new AnalyticsParams('build_channels', 'delete_build_item')
        .set('path', path);
    return this.http.delete(
        `${MTT_API_URL}/build_channels/${encodeURIComponent(id)}/build_items`,
        {params});
  }

  getBuildChannelProviders(): Observable<model.BuildChannelProviderList> {
    return this.http.get<model.BuildChannelProviderList>(
        `${MTT_API_URL}/build_channel_providers`);
  }

  getBuildChannelProvider(id: string) {
    return this.http.get(
        `${MTT_API_URL}/build_channel_providers/${encodeURIComponent(id)}`);
  }

  createBuildChannel(buildChannelConfig: model.BuildChannelConfig) {
    const params = new AnalyticsParams('build_channels', 'create');
    return this.http.post(
        `${MTT_API_URL}/build_channels`, buildChannelConfig, {params});
  }

  getBuildChannel(id: string) {
    return this.http.get<model.BuildChannelConfig>(
        `${MTT_API_URL}/build_channels/${encodeURIComponent(id)}`);
  }

  getBuildChannels(): Observable<model.BuildChannelList> {
    return this.http.get<model.BuildChannelList>(
        `${MTT_API_URL}/build_channels`);
  }

  updateBuildChannel(
      buildChannelId: string, buildChannelConfig: model.BuildChannelConfig) {
    const params = new AnalyticsParams('build_channels', 'update');
    return this.http.put(
        `${MTT_API_URL}/build_channels/${encodeURIComponent(buildChannelId)}`,
        buildChannelConfig, {params});
  }

  deleteBuildChannel(id: string) {
    const params = new AnalyticsParams('build_channels', 'delete');
    return this.http.delete(
        `${MTT_API_URL}/build_channels/${encodeURIComponent(id)}`, {params});
  }

  getConfigSetBuildChannels(): Observable<model.BuildChannelList> {
    return this.http.get(`${MTT_API_URL}/config_sets/build_channels`);
  }

  getConfigSetInfos(
      includeRemote = false, statuses: model.ConfigSetStatus[] = []):
      Observable<model.ConfigSetInfoList> {
    const params = new HttpParams({
      fromObject: {
        'include_remote': `${includeRemote}`,
        'statuses': statuses,
      }
    });
    return this.http.get<model.ConfigSetInfoList>(
        `${MTT_API_URL}/config_sets`, {params});
  }

  importConfigSet(url = '', content = ''): Observable<model.ConfigSetInfo> {
    const params = new AnalyticsParams('config_sets', 'import');
    if (!url) {
      url = 'local';
    }
    return this.http.post<model.ConfigSetInfo>(
        `${MTT_API_URL}/config_sets/import/${encodeURIComponent(url)}`,
        {'content': content}, {params});
  }

  deleteConfigSet(url: string) {
    const params = new AnalyticsParams('config_sets', 'delete');
    return this.http.delete(
        `${MTT_API_URL}/config_sets/${encodeURIComponent(url)}`, {params});
  }

  getDeviceAction(id: string): Observable<model.DeviceAction> {
    return this.http.get<model.DeviceAction>(
        `${MTT_API_URL}/device_actions/${encodeURIComponent(id)}`);
  }

  getDeviceActionList(): Observable<model.DeviceActionList> {
    return this.http.get<model.DeviceActionList>(
        `${MTT_API_URL}/device_actions`);
  }

  createDeviceAction(deviceAction: model.DeviceAction) {
    const params = new AnalyticsParams('device_actions', 'create');
    return this.http.post(
        `${MTT_API_URL}/device_actions`, deviceAction, {params});
  }

  updateDeviceAction(id: string, deviceAction: model.DeviceAction) {
    const params = new AnalyticsParams('device_actions', 'update');
    return this.http.put(
        `${MTT_API_URL}/device_actions/${encodeURIComponent(id)}`, deviceAction,
        {params});
  }

  deleteDeviceAction(id: string) {
    const params = new AnalyticsParams('device_actions', 'delete');
    return this.http.delete(
        `${MTT_API_URL}/device_actions/${encodeURIComponent(id)}`, {params});
  }

  createNewTestRunRequest(newtestRun: model.NewTestRunRequest):
      Observable<model.TestRun> {
    const params = new AnalyticsParams('test_runs', 'create');
    return this.http.post<model.TestRun>(
        `${MTT_API_URL}/test_runs`, newtestRun, {params});
  }

  getNodeConfig(): Observable<model.NodeConfig> {
    return this.http.get<model.NodeConfig>(`${MTT_API_URL}/node_config`);
  }

  updateNodeConfig(nodeConfig: model.NodeConfig) {
    const params = new AnalyticsParams('node_config', 'update');
    return this.http.put(`${MTT_API_URL}/node_config`, nodeConfig, {params});
  }

  exportNodeConfig(): Observable<model.SimpleMessage> {
    const params = new AnalyticsParams('node_config', 'export');
    return this.http.get<model.SimpleMessage>(
        `${MTT_API_URL}/node_config/export`, {params});
  }

  importNodeConfig(value: string): Observable<void> {
    const params = new AnalyticsParams('node_config', 'import');
    return this.http.post<void>(
        `${MTT_API_URL}/node_config/import`, {'value': value}, {params});
  }

  getPrivateNodeConfig(): Observable<model.PrivateNodeConfig> {
    return this.http.get<model.PrivateNodeConfig>(
        `${MTT_API_URL}/private_node_config`);
  }

  updatePrivateNodeConfig(privateNodeConfig: model.PrivateNodeConfig) {
    const params = new AnalyticsParams('private_node_config', 'update');
    return this.http.put(
        `${MTT_API_URL}/private_node_config`, privateNodeConfig, {params});
  }

  setDefaultServiceAccount(key: Blob): Observable<void> {
    return from(readBlobAsText(key)).pipe(switchMap(data => {
      const params = new AnalyticsParams(
          'private_node_config', 'set_default_service_account');
      return this.http.put<void>(
          `${MTT_API_URL}/private_node_config/default_service_account`,
          {value: data}, {params});
    }));
  }

  removeDefaultServiceAccount() {
    const params = new AnalyticsParams(
        'private_node_config', 'remove_default_service_account');
    return this.http.delete(
        `${MTT_API_URL}/private_node_config/default_service_account`, {params});
  }

  createTest(test: model.Test) {
    const params = new AnalyticsParams('tests', 'create');
    return this.http.post(`${MTT_API_URL}/tests`, test, {params});
  }

  getTest(id: string): Observable<model.Test> {
    return this.http.get<model.Test>(
        `${MTT_API_URL}/tests/${encodeURIComponent(id)}`);
  }

  getTests(): Observable<model.TestList> {
    return this.http.get<model.TestList>(`${MTT_API_URL}/tests`);
  }

  updateTest(testId: string, test: model.Test) {
    const params = new AnalyticsParams('tests', 'update');
    return this.http.put(
        `${MTT_API_URL}/tests/${encodeURIComponent(testId)}`, test, {params});
  }

  deleteTest(id: string) {
    const params = new AnalyticsParams('tests', 'delete');
    return this.http.delete(
        `${MTT_API_URL}/tests/${encodeURIComponent(id)}`, {params});
  }

  createTestPlan(testPlan: model.TestPlan) {
    const params = new AnalyticsParams('test_plans', 'create');
    return this.http.post<model.TestPlan>(
        `${MTT_API_URL}/test_plans`, testPlan, {params});
  }

  updateTestPlan(testPlanId: string, testPlan: model.TestPlan) {
    const params = new AnalyticsParams('test_plans', 'update');
    return this.http.put<model.TestPlan>(
        `${MTT_API_URL}/test_plans/${encodeURIComponent(testPlanId)}`, testPlan,
        {params});
  }

  getTestPlan(id: string): Observable<model.TestPlan> {
    return this.http.get<model.TestPlan>(
        `${MTT_API_URL}/test_plans/${encodeURIComponent(id)}`);
  }

  getTestPlans(): Observable<model.TestPlanList> {
    return this.http.get<model.TestPlanList>(`${MTT_API_URL}/test_plans`);
  }

  runTestPlan(id: string) {
    const params = new AnalyticsParams('test_plans', 'run');
    return this.http.post(
        `${MTT_API_URL}/test_plans/${encodeURIComponent(id)}/run`, null,
        {params});
  }

  deleteTestPlan(id: string) {
    const params = new AnalyticsParams('test_plans', 'delete');
    return this.http.delete(
        `${MTT_API_URL}/test_plans/${encodeURIComponent(id)}`, {params});
  }

  getTestRun(id: string): Observable<model.TestRun> {
    return this.http.get<model.TestRun>(
        `${MTT_API_URL}/test_runs/${encodeURIComponent(id)}`);
  }

  cancelTestRun(id: string) {
    const params = new AnalyticsParams('test_runs', 'cancel');
    return this.http.post(
        `${MTT_API_URL}/test_runs/${encodeURIComponent(id)}/cancel`, null,
        {params});
  }

  getTestRuns(
      maxResults?: number, pageToken?: string, backwards = false,
      filterQueries: string[] = [],
      state: model.TestRunState[] = []): Observable<model.TestRunSummaryList> {
    const params = new HttpParams({
      fromObject: {
        'max_results': maxResults ? String(maxResults) : '',
        'page_token': pageToken || '',
        'backwards': String(backwards),
        'filter_query': filterQueries,
        'state': state,
      }
    });

    return this.http.get<model.TestRunSummaryList>(
        `${MTT_API_URL}/test_runs`, {params});
  }

  getReruns(id: string) {
    const params = new HttpParams({fromObject: {'prev_test_run_id': id}});
    return this.http.get<model.TestRunSummaryList>(
        `${MTT_API_URL}/test_runs`, {params});
  }

  getTestRunOutput(
      testRunId: string, attemptId: string, path: string,
      offset?: number): Observable<model.TestRunOutput> {
    let params =
        new HttpParams().set('attempt_id', attemptId).set('path', path);
    if (typeof offset !== 'undefined') {
      params = params.set('offset', String(offset));
    }

    return this.http.get<model.TestRunOutput>(
        `${MTT_API_URL}/test_runs/${encodeURIComponent(testRunId)}/output`,
        {params});
  }
}

/** Provides access to the test run action API. */
export class TestRunActionClient {
  /** Backend path which serves test run action data. */
  static readonly PATH = `${MTT_API_URL}/test_run_actions`;

  constructor(
      private readonly http: HttpClient, private readonly auth: AuthService) {}

  /** Lists all test run actions. */
  list(): Observable<model.TestRunAction[]> {
    return this.http.get<model.TestRunActionList>(TestRunActionClient.PATH)
        .pipe(map(result => result.actions || []));
  }

  /** Returns a test run action using its ID. */
  get(id: string): Observable<model.TestRunAction> {
    return this.http.get<model.TestRunAction>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}`);
  }

  /** Creates a new test run action. */
  create(data: model.TestRunAction): Observable<model.TestRunAction> {
    const params = new AnalyticsParams('test_run_actions', 'create');
    return this.http.post<model.TestRunAction>(
        TestRunActionClient.PATH, data, {params});
  }

  /** Updates an existing test run action. */
  update(id: string, data: model.TestRunAction):
      Observable<model.TestRunAction> {
    const params = new AnalyticsParams('test_run_actions', 'update');
    return this.http.put<model.TestRunAction>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}`, data,
        {params});
  }

  /** Deletes a test run action. */
  delete(id: string): Observable<void> {
    const params = new AnalyticsParams('test_run_actions', 'delete');
    return this.http.delete<void>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}`, {params});
  }

  /** Authorizes a test run action. */
  authorize(id: string): Observable<void> {
    return this.getAuthorizationInfo(id)
        .pipe(switchMap(authInfo => this.auth.getAuthorizationCode(authInfo)))
        .pipe(switchMap(
            code => code ? this.sendAuthorizationCode(id, code) : EMPTY));
  }

  /** Authorizes a test run action with a service account JSON key. */
  authorizeWithServiceAccount(id: string, key: Blob): Observable<void> {
    return from(readBlobAsText(key)).pipe(switchMap(data => {
      const params = new AnalyticsParams('test_run_actions', 'authorize');
      return this.http.put<void>(
          `${TestRunActionClient.PATH}/${encodeURIComponent(id)}/auth`,
          {value: data}, {params});
    }));
  }

  /** Revokes a test run action's authorization. */
  unauthorize(id: string): Observable<void> {
    const params = new AnalyticsParams('test_run_actions', 'unauthorize');
    return this.http.delete<void>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}/auth`, {params});
  }

  // Fetches authorization information to start authorization flow.
  private getAuthorizationInfo(id: string):
      Observable<model.AuthorizationInfo> {
    const params = new HttpParams().set('redirect_uri', REDIRECT_URI);
    return this.http.get<model.AuthorizationInfo>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}/auth`, {params});
  }

  // Sends authorization code to complete authorization flow.
  private sendAuthorizationCode(id: string, code: string): Observable<void> {
    const params = new AnalyticsParams('test_run_actions', 'authorize');
    return this.http.post<void>(
        `${TestRunActionClient.PATH}/${encodeURIComponent(id)}/auth`,
        {'redirect_uri': REDIRECT_URI, 'code': code}, {params});
  }
}

/** Provides access to the test results API. */
export class TestResultClient {
  /** Backend path which serves test run action data. */
  static readonly PATH = `${MTT_API_URL}/test_result`;
  static readonly PAGE_SIZE = 20;

  // TODO: Remove once API is implemented

  createMockModuleResult(
      name = 'module_name', passed = 0, failed = 0, total = 0,
      errorMessage?: string): model.TestModuleResult {
    return {
      id: 'module_id',
      attempt_id: 'attempt_id',
      name,
      complete: !!errorMessage,
      passed_tests: passed,
      failed_tests: failed,
      total_tests: total,
      error_message: errorMessage,
    } as model.TestModuleResult;
  }

  // TODO: Remove once API is implemented
  createMockTestCaseResult(
      moduleId = 'module_id', name = 'testName', status = model.TestStatus.PASS,
      errorMessage = 'failure message',
      stackTrace = 'some stack trace'): model.TestCaseResult {
    return {
      id: 'test_id',
      module_id: moduleId,
      name,
      status,
      error_message: errorMessage,
      stack_trace: stackTrace,
    } as model.TestCaseResult;
  }

  /** Lists all modules. */
  listModules(
      testRunId: string, pageToken?: string,
      pageSize = TestResultClient.PAGE_SIZE):
      Observable<model.TestModuleResultList> {
    // TODO: Replace with actual API call later
    // TODO: Add pagination and filtering
    const module1 = this.createMockModuleResult(
        'module1', 12345, 67890, 98765, 'lorem ipsum');
    const module2 = this.createMockModuleResult(
        'module.2', 0, 0, 0,
        'some super super super super super super super super super super super super super super long text');
    const module3 = this.createMockModuleResult(
        'module_3_with_really_really_really_really_really_long_name',
    );
    const fillerModule = this.createMockModuleResult();

    if (!pageToken) {
      const results = [module1, module2, module3];
      for (let i = 0; i < pageSize - 3; i++) {
        results.push(fillerModule);
      }
      return observableOf({results, next_page_token: 'a'});
    }

    // Stop after 5 additional pages have been loaded
    if (pageToken.length === 5) {
      return observableOf({results: [fillerModule]});
    }

    // Otherwise, return list of filler test cases and increase token length
    const results = [];
    for (let i = 0; i < pageSize; i++) {
      results.push(fillerModule);
    }
    return observableOf({results, next_page_token: pageToken + 'a'});
  }

  listTestCases(
      testRunId: string, moduleId: string, pageToken?: string,
      pageSize = TestResultClient.PAGE_SIZE):
      Observable<model.TestCaseResultList> {
    // TODO: Replace with actual API call later
    // TODO: Add filtering
    const testCase1 = this.createMockTestCaseResult(
        moduleId, 'test_case.1', model.TestStatus.PASS, '', '');
    const testCase2 = this.createMockTestCaseResult(
        moduleId, 'test_case2', model.TestStatus.FAIL, 'some failure message',
        'some stack trace');
    const testCase3 = this.createMockTestCaseResult(
        moduleId, 'really_really_long.test.case.name_with_lots_of_text',
        model.TestStatus.ASSUMPTION_FAILURE,
        'some other failure message that is really really really long',
        'some really really really really really really really really really really really really long stack trace');
    const testCase4 = this.createMockTestCaseResult(
        moduleId, 'test.case.Four', model.TestStatus.UNKNOWN, '', '');
    const testCase5 = this.createMockTestCaseResult(
        moduleId, 'another_really_really_long.test.case.name_with_lots_of_text',
        model.TestStatus.IGNORED,
        'some other failure message that is really really really long',
        'some really really really really really really really really really really really really long stack trace');
    const fillerTestCase = this.createMockTestCaseResult();

    // Return first page of test cases
    if (!pageToken) {
      const results = [testCase1, testCase2, testCase3, testCase4, testCase5];
      for (let i = 0; i < pageSize - 5; i++) {
        results.push(fillerTestCase);
      }
      return observableOf({results, next_page_token: 'a'});
    }

    // Stop after 5 additional pages have been loaded
    if (pageToken.length === 5) {
      return observableOf({results: [fillerTestCase]});
    }

    // Otherwise, return list of filler test cases and increase token length
    const results = [];
    for (let i = 0; i < pageSize; i++) {
      results.push(fillerTestCase);
    }
    return observableOf({results, next_page_token: pageToken + 'a'});
  }
}
