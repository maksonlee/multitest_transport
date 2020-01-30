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
import {Inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';

import {AnalyticsParams} from './analytics_service';
import {APP_DATA, AppData} from './app_data';
import * as model from './mtt_models';
import {CommandAttempt, isFinalCommandState} from './tfc_models';

/** URL for MTT API methods */
export const MTT_API_URL = '/_ah/api/mtt/v1';

/** Client for MTT API access */
@Injectable({
  providedIn: 'root',
})
export class MttClient {
  constructor(
      @Inject(APP_DATA) private readonly appData: AppData,
      private readonly http: HttpClient) {}

  /**
   * Authorizes a build channel using an authorization code.
   * @param code: authorization code to use
   * @param buildChannelId: build channel to authorize
   * @param redirectUri: authorization redirect URI
   */
  authorizeBuildChannel(code: string, buildChannelId: string,
                        redirectUri: string): Observable<void> {
    const params = new AnalyticsParams('build_channels', 'authorize');
    return this.http.post<void>(
        `${MTT_API_URL}/build_channels/${buildChannelId}/auth_return`,
        {'redirect_uri': redirectUri, 'code': code}, {params});
  }

  /**
   * Determine a build channel's authorization information.
   * @param buildChannelId: build channel to authorize
   * @param redirectUri: authorization redirect URI
   * @return authorization flow and URL to use
   */
  getBuildChannelAuthorizationInfo(buildChannelId: string, redirectUri: string):
      Observable<model.AuthorizationInfo> {
    const params = new HttpParams().set('redirect_uri', redirectUri);
    return this.http.get<model.AuthorizationInfo>(
        `${MTT_API_URL}/build_channels/${buildChannelId}/auth`, {params});
  }

  listBuildItems(id: string, path: string, pageToken?: string):
      Observable<model.BuildItemList> {
    let params = new HttpParams().set('build_channel_id', id).set('path', path);
    if (pageToken) {
      params = params.set('page_token', pageToken);
    }
    return this.http.get<model.BuildItemList>(
        `${MTT_API_URL}/build_channels/${id}/build_items`, {params});
  }

  deleteBuildItem(id: string, path: string) {
    const params = new AnalyticsParams('build_channels', 'delete_build_item');
    return this.http.post(
        `${MTT_API_URL}/build_channels/${id}/build_items/delete`, {path},
        {params});
  }

  getBuildChannelProviders(): Observable<model.BuildChannelProviderList> {
    return this.http.get<model.BuildChannelProviderList>(
        `${MTT_API_URL}/build_channel_providers`);
  }

  getBuildChannelProvider(id: string) {
    return this.http.get(`${MTT_API_URL}/build_channel_providers/${id}`);
  }

  createBuildChannel(buildChannelConfig: model.BuildChannelConfig) {
    const params = new AnalyticsParams('build_channels', 'create');
    return this.http.post(
        `${MTT_API_URL}/build_channels`, buildChannelConfig, {params});
  }

  getBuildChannel(id: string) {
    return this.http.get<model.BuildChannelConfig>(
        `${MTT_API_URL}/build_channels/${id}`);
  }

  getBuildChannels(): Observable<model.BuildChannelList> {
    return this.http.get<model.BuildChannelList>(
        `${MTT_API_URL}/build_channels`);
  }

  updateBuildChannel(
      buildChannelId: string, buildChannelConfig: model.BuildChannelConfig) {
    const params = new AnalyticsParams('build_channels', 'update');
    return this.http.put(
        `${MTT_API_URL}/build_channels/${buildChannelId}`, buildChannelConfig,
        {params});
  }

  deleteBuildChannel(id: string) {
    const params = new AnalyticsParams('build_channels', 'delete');
    return this.http.post(
        `${MTT_API_URL}/build_channels/${id}/delete`, null, {params});
  }

  getConfigSetBuildChannels(): Observable<model.BuildChannelList> {
    return this.http.get(`${MTT_API_URL}/config_sets/build_channels`);
  }

  getConfigSetInfos(includeRemote = false):
      Observable<model.ConfigSetInfoList> {
    const params = new HttpParams().set('include_remote', `${includeRemote}`);
    return this.http.get<model.ConfigSetInfoList>(
        `${MTT_API_URL}/config_sets`, {params});
  }

  importConfigSet(url = '', contents = ''): Observable<model.ConfigSetInfo> {
    return this.http.post<model.ConfigSetInfo>(
        `${MTT_API_URL}/config_sets/import`,
        {'url': url, 'contents': contents});
  }

  getDeviceAction(id: string): Observable<model.DeviceAction> {
    return this.http.get<model.DeviceAction>(
        `${MTT_API_URL}/device_actions/${id}`);
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
    return this.http.post(
        `${MTT_API_URL}/device_actions/${id}`, deviceAction, {params});
  }

  deleteDeviceAction(id: string) {
    const params = new AnalyticsParams('device_actions', 'delete');
    return this.http.post(
        `${MTT_API_URL}/device_actions/${id}/delete`, null, {params});
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
    return this.http.post(`${MTT_API_URL}/node_config`, nodeConfig, {params});
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
    return this.http.post(
        `${MTT_API_URL}/private_node_config`, privateNodeConfig, {params});
  }

  createTest(test: model.Test) {
    const params = new AnalyticsParams('tests', 'create');
    return this.http.post(`${MTT_API_URL}/tests`, test, {params});
  }

  getTest(id: string): Observable<model.Test> {
    return this.http.get<model.Test>(`${MTT_API_URL}/tests/${id}`);
  }

  getTests(): Observable<model.TestList> {
    return this.http.get<model.TestList>(`${MTT_API_URL}/tests`);
  }

  updateTest(testId: string, test: model.Test) {
    const params = new AnalyticsParams('tests', 'update');
    return this.http.post(`${MTT_API_URL}/tests/${testId}`, test, {params});
  }

  deleteTest(id: string) {
    const params = new AnalyticsParams('tests', 'delete');
    return this.http.post(`${MTT_API_URL}/tests/${id}/delete`, null, {params});
  }

  createTestPlan(testPlan: model.TestPlan) {
    const params = new AnalyticsParams('test_plans', 'create');
    return this.http.post<model.TestPlan>(
        `${MTT_API_URL}/test_plans`, testPlan, {params});
  }

  updateTestPlan(testPlanId: string, testPlan: model.TestPlan) {
    const params = new AnalyticsParams('test_plans', 'update');
    return this.http.post<model.TestPlan>(
        `${MTT_API_URL}/test_plans/${testPlanId}`, testPlan, {params});
  }

  getTestPlan(id: string): Observable<model.TestPlan> {
    return this.http.get<model.TestPlan>(`${MTT_API_URL}/test_plans/${id}`);
  }

  getTestPlans(): Observable<model.TestPlanList> {
    return this.http.get<model.TestPlanList>(`${MTT_API_URL}/test_plans`);
  }

  runTestPlan(id: string) {
    const params = new AnalyticsParams('test_plans', 'run');
    return this.http.post(
        `${MTT_API_URL}/test_plans/${id}/run`, null, {params});
  }

  deleteTestPlan(id: string) {
    const params = new AnalyticsParams('test_plans', 'delete');
    return this.http.post(
        `${MTT_API_URL}/test_plans/${id}/delete`, null, {params});
  }

  getTestRun(id: string): Observable<model.TestRun> {
    return this.http.get<model.TestRun>(`${MTT_API_URL}/test_runs/${id}`);
  }

  cancelTestRun(id: string) {
    const params = new AnalyticsParams('test_runs', 'cancel');
    return this.http.post(
        `${MTT_API_URL}/test_runs/${id}/cancel`, null, {params});
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

  getTestRunOutput(
      testRunId: string, attemptId: string, path: string,
      offset?: number): Observable<model.TestRunOutput> {
    let params =
        new HttpParams().set('attempt_id', attemptId).set('path', path);
    if (typeof offset !== 'undefined') {
      params = params.set('offset', String(offset));
    }

    return this.http.get<model.TestRunOutput>(
        `${MTT_API_URL}/test_runs/${testRunId}/output`, {params});
  }

  /**
   * Determine a test run output file's URL.
   * @param testRun related test run
   * @param attempt related TFC attempt
   * @param path relative file path
   * @return file URL
   */
  getTestRunFileUrl(
      testRun: model.TestRun, attempt: CommandAttempt, path: string): string {
    if (isFinalCommandState(attempt.state)) {
      // Completed run files are stored in the configured output location.
      const outputUrl = testRun.output_url || '';
      return joinPath(outputUrl, attempt.command_id, attempt.attempt_id, path);
    }
    // Active run files are stored in a local temporary location.
    return joinPath(
        'file:///', this.getFileServerRoot(), 'tmp', attempt.attempt_id, path);
  }

  /**
   * Returns a URL for viewing a file stored in MTT
   */
  getFileBrowseUrl(fileUrl: string): string {
    const fileServerPath = this.getFileServerPath(fileUrl);
    if (!fileServerPath) {
      return fileUrl;
    }
    return joinPath(this.appData.fileBrowseUrl || '', fileServerPath);
  }

  /**
   * Returns a URL for opening a file stored in MTT
   */
  getFileOpenUrl(fileUrl: string): string {
    // TODO: Refactor file functions
    const fileServerPath = this.getFileServerPath(fileUrl);
    if (!fileServerPath) {
      return fileUrl;
    }
    return joinPath(this.appData.fileOpenUrl || '', fileServerPath);
  }

  /**
   * Returns the base path to MTT's file server
   */
  getFileServerPath(fileUrl: string): string|null {
    const fileServerRoot = this.getFileServerRoot();
    if (!fileServerRoot) {
      return null;
    }
    const parser = document.createElement('a');
    parser.href = fileUrl;
    if (parser.protocol !== 'file:' ||
        !parser.pathname.startsWith(fileServerRoot)) {
      return null;
    }
    return parser.pathname.substring(fileServerRoot.length);
  }

  getFileServerRoot(): string {
    return this.appData.fileServerRoot || '';
  }
}

/**
 * Joins filepaths
 *
 * TODO: use shared/utils.ts joinPath after removing shared
 *                    dependencies on services
 */
export function joinPath(...paths: string[]): string {
  const tokens = [];
  for (const path of paths) {
    tokens.push(path.replace(/^\/|\/$/g, ''));
  }
  return tokens.join('/');
}
