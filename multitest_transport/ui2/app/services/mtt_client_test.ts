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
import {of as observableOf} from 'rxjs';

import * as testUtil from '../testing/test_util';

import {MTT_API_URL, MttClient} from './mtt_client';
import {BuildChannelList, TestPlanList, TestRun} from './mtt_models';
import {CommandAttempt, CommandState} from './tfc_models';

describe('MttClient', () => {
  let httpClientSpy: jasmine.SpyObj<HttpClient>;
  let mttClient: MttClient;

  beforeEach(() => {
    httpClientSpy = jasmine.createSpyObj<HttpClient>(
        'HttpClient', ['get', 'post', 'put', 'delete']);
    mttClient = new MttClient(testUtil.newMockAppData(), httpClientSpy);
  });

  describe('getBuildChannelAuthorizationInfo', () => {
    const mockAuthorizedInfo = {url: 'http://localhost/auth', is_manual: false};
    const BUILD_CHANNEL_ID = 'test_id';
    const REDIRECT_URI = 'http://localhost:8000/ui2/setting';

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(mockAuthorizedInfo));
    });

    it('calls API correctly', () => {
      mttClient.getBuildChannelAuthorizationInfo(
          BUILD_CHANNEL_ID, REDIRECT_URI);
      const params = new HttpParams().set('redirect_uri', REDIRECT_URI);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              '/_ah/api/mtt/v1/build_channels/test_id/auth', {params});
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
    });

    it('parses API response correctly', () => {
      mttClient.getBuildChannelAuthorizationInfo(BUILD_CHANNEL_ID, REDIRECT_URI)
          .subscribe(response => {
            expect(response).toEqual(
                jasmine.objectContaining(mockAuthorizedInfo));
          });
    });
  });

  describe('authorizeBuildChannel', () => {
    const mockCodeString = '4/123123123';
    const BUILD_CHANNEL_ID = 'test_id';
    const REDIRECT_URI = 'http://localhost:8000/ui2/setting';

    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf());
    });

    it('calls API correctly on valid input', () => {
      mttClient.authorizeBuildChannel(
          mockCodeString, BUILD_CHANNEL_ID, REDIRECT_URI);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `/_ah/api/mtt/v1/build_channels/test_id/auth_return`,
              {'redirect_uri': REDIRECT_URI, 'code': mockCodeString},
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('listBuildItem', () => {
    const BUILD_ITEM_LIST = testUtil.newMockBuildItemList();

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(BUILD_ITEM_LIST));
    });

    it('calls API and parses response correctly', () => {
      const id = 'test_id';
      const path = 'test_path';
      const observable = mttClient.listBuildItems(id, path);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/build_channels/${id}/build_items`,
              jasmine.any(Object));
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(BUILD_ITEM_LIST));
      });
    });
  });

  describe('deleteBuildItem', () => {
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf({}));
    });

    it('calls API correctly', () => {
      const id = 'build_channel_id';
      const path = 'path';
      const observable = mttClient.deleteBuildItem(id, path);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/build_channels/${id}/build_items/delete`, {path},
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual({});
      });
    });
  });

  describe('getBuildChannels', () => {
    const BUILD_CHANNELS:
        BuildChannelList = {build_channels: [testUtil.newMockBuildChannel()]};
    const url = `${MTT_API_URL}/build_channels`;

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(BUILD_CHANNELS));
    });

    it('calls API correctly', () => {
      mttClient.getBuildChannels();
      expect(httpClientSpy.get).toHaveBeenCalledWith(url);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
    });

    it('parses API response correctly', () => {
      const observable = mttClient.getBuildChannels();
      observable.subscribe((response) => {
        expect(response).toEqual(BUILD_CHANNELS);
      });
    });
  });

  describe('getDeviceActionList', () => {
    const DEVICE_ACTION_LIST = testUtil.newMockDeviceActionList();

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(
          observableOf({device_actions: DEVICE_ACTION_LIST}));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getDeviceActionList();
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/device_actions`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(
            jasmine.objectContaining({device_actions: DEVICE_ACTION_LIST}));
      });
    });
  });

  describe('getDeviceAction', () => {
    const DEVICE_ACTION = testUtil.newMockDeviceAction();

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(DEVICE_ACTION));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getDeviceAction(DEVICE_ACTION.id);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/device_actions/${DEVICE_ACTION.id}`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(DEVICE_ACTION));
      });
    });
  });

  describe('createDeviceAction', () => {
    const DEVICE_ACTION = testUtil.newMockDeviceAction();

    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(DEVICE_ACTION));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.createDeviceAction(DEVICE_ACTION);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/device_actions`, DEVICE_ACTION,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(DEVICE_ACTION));
      });
    });
  });

  describe('updateDeviceAction', () => {
    const DEVICE_ACTION = testUtil.newMockDeviceAction();

    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(DEVICE_ACTION));
    });

    it('calls API and parses response correctly', () => {
      const observable =
          mttClient.updateDeviceAction(DEVICE_ACTION.id, DEVICE_ACTION);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/device_actions/${DEVICE_ACTION.id}`,
              DEVICE_ACTION, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(DEVICE_ACTION));
      });
    });
  });

  describe('createNewTestRunRequest', () => {
    const newtestRun = testUtil.newMockNewTestRunRequest();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(newtestRun));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.createNewTestRunRequest(newtestRun);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_runs`, newtestRun, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(newtestRun));
      });
    });
  });

  describe('getNodeConfig', () => {
    const nodeConfig = testUtil.newMockNodeConfig();
    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(nodeConfig));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getNodeConfig();
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/node_config`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(nodeConfig);
      });
    });
  });

  describe('updateNodeConfig', () => {
    const nodeConfig = testUtil.newMockNodeConfig();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(nodeConfig));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.updateNodeConfig(nodeConfig);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/node_config`, nodeConfig, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(nodeConfig));
      });
    });
  });

  describe('importNodeConfig', () => {
    const fileContent = 'random';
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf());
    });

    it('calls API and parses response correctly', () => {
      mttClient.importNodeConfig('random');
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/node_config/import`, {'value': fileContent},
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('exportNodeConfig', () => {
    const simpleMessage = {'value': '123'};
    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(simpleMessage));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.exportNodeConfig();
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/node_config/export`, jasmine.any(Object));
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(simpleMessage));
      });
    });
  });

  describe('getPrivateNodeConfig', () => {
    const privateNodeConfig = testUtil.newMockPrivateNodeConfig();
    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(privateNodeConfig));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getPrivateNodeConfig();
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/private_node_config`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(privateNodeConfig);
      });
    });
  });

  describe('updatePrivateNodeConfig', () => {
    const privateNodeConfig = testUtil.newMockPrivateNodeConfig();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(privateNodeConfig));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.updatePrivateNodeConfig(privateNodeConfig);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/private_node_config`, privateNodeConfig,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(privateNodeConfig));
      });
    });
  });

  describe('createTest', () => {
    const TEST = testUtil.newMockTest();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(TEST));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.createTest(TEST);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/tests`, TEST, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(TEST));
      });
    });
  });

  describe('getTest', () => {
    const TEST = testUtil.newMockTest();
    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(TEST));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getTest(TEST.id);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/tests/${TEST.id}`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(TEST));
      });
    });
  });

  describe('updateTest', () => {
    const TEST = testUtil.newMockTest();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(TEST));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.updateTest(TEST.id, TEST);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/tests/${TEST.id}`, TEST, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(TEST));
      });
    });
  });

  describe('getTestPlan', () => {
    const TEST_PLAN = testUtil.newMockTestPlan();
    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(TEST_PLAN));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getTestPlan(TEST_PLAN.id);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/test_plans/${TEST_PLAN.id}`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(TEST_PLAN));
      });
    });
  });

  describe('runTestPlan', () => {
    const TEST_PLAN = testUtil.newMockTestPlan();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(null));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.runTestPlan(TEST_PLAN.id);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_plans/${TEST_PLAN.id}/run`, null,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toBeNull();
      });
    });
  });

  describe('getTestPlans', () => {
    const TEST_PLANS: TestPlanList = {
      test_plans: [
        testUtil.newMockTestPlan('test_plan_id_1', 'test_plan_name_1'),
        testUtil.newMockTestPlan('test_plan_id_2', 'test_plan_name_2')
      ]
    };

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(TEST_PLANS));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getTestPlans();
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/test_plans`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(TEST_PLANS);
      });
    });
  });

  describe('deleteTestPlan', () => {
    const TEST_PLAN = testUtil.newMockTestPlan();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(null));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.deleteTestPlan(TEST_PLAN.id);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_plans/${TEST_PLAN.id}/delete`, null,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toBeNull();
      });
    });
  });

  describe('createTestPlan', () => {
    const testPlan = testUtil.newMockTestPlan();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(testPlan));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.createTestPlan(testPlan);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_plans`, testPlan, jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(testPlan));
      });
    });
  });

  describe('updateTestPlan', () => {
    const testPlan = testUtil.newMockTestPlan();
    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(testPlan));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.updateTestPlan(testPlan.id, testPlan);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_plans/${testPlan.id}`, testPlan,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(testPlan));
      });
    });
  });

  describe('getTestRun', () => {
    const testRun = testUtil.newMockTestRun(testUtil.newMockTest());

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(testRun));
    });

    it('calls API and parses response correctly', () => {
      const observable = mttClient.getTestRun(testRun.id);
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${MTT_API_URL}/test_runs/${testRun.id}`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(testRun);
      });
    });
  });

  describe('cancelTestRun', () => {
    const testRun = testUtil.newMockTestRun(testUtil.newMockTest());

    beforeEach(() => {
      httpClientSpy.post.and.returnValue(observableOf(null));
    });

    it('calls API and parses response correctly', () => {
      mttClient.cancelTestRun(testRun.id);
      expect(httpClientSpy.post)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_runs/${testRun.id}/cancel`, null,
              jasmine.any(Object));
      expect(httpClientSpy.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('getTestRunOutput', () => {
    const test = testUtil.newMockTest();
    const testRun = testUtil.newMockTestRun(test);
    const testRunOutput = testUtil.newMockTestRunOutput();
    const attemptId = 'attemptId';
    const path = 'log/path';
    const offset = 3;

    beforeEach(() => {
      httpClientSpy.get.and.returnValue(observableOf(testRunOutput));
    });

    it('calls API correctly', () => {
      const observable =
          mttClient.getTestRunOutput(testRun.id, attemptId, path, offset);
      const params = new HttpParams()
                         .set('attempt_id', attemptId)
                         .set('path', path)
                         .set('offset', String(offset));

      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              `${MTT_API_URL}/test_runs/${testRun.id}/output`, {params});
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      observable.subscribe((response) => {
        expect(response).toEqual(jasmine.objectContaining(testRunOutput));
      });
    });
  });

  describe('getFileUrl', () => {
    let testRun: TestRun;

    beforeEach(() => {
      testRun = {output_url: 'output_url'} as TestRun;
    });

    it('can get URL for active attempts', () => {
      const attempt = {
        command_id: 'command_id',
        attempt_id: 'attempt_id',
        state: CommandState.RUNNING
      } as CommandAttempt;
      const path = 'path/to/file';
      const expected = 'file:///file/server/root/tmp/attempt_id/path/to/file';
      expect(mttClient.getTestRunFileUrl(testRun, attempt, path))
          .toEqual(expected);
    });

    it('can get URL for completed attempts', () => {
      const attempt = {
        command_id: 'command_id',
        attempt_id: 'attempt_id',
        state: CommandState.COMPLETED
      } as CommandAttempt;
      const path = 'path/to/file';
      const expected = 'output_url/command_id/attempt_id/path/to/file';
      expect(mttClient.getTestRunFileUrl(testRun, attempt, path))
          .toEqual(expected);
    });
  });

  describe('getFileServerPath', () => {
    it('converts the file server paths correctly', () => {
      const fileUrl = 'file:///file/server/root/app_default_bucket/test_runs/' +
          'command_id/output/106001/attempt_id';
      const serverPath = '/app_default_bucket/test_runs/' +
          'command_id/output/106001/attempt_id';
      const result = mttClient.getFileServerPath(fileUrl);
      expect(result).toEqual(serverPath);
    });
  });
});
