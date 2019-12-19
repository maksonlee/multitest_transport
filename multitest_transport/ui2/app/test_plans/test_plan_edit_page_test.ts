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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Params} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf, Subject} from 'rxjs';

import {APP_DATA} from '../services/app_data';
import {MttClient} from '../services/mtt_client';
import {DeviceAction, Test, TestResourceType} from '../services/mtt_models';
import {getEl} from '../testing/jasmine_util';
import {newMockDeviceAction, newMockTest, newMockTestPlan, newMockTestResourceDef, newMockTestResourceDefs} from '../testing/test_util';

import {TestPlanEditPage} from './test_plan_edit_page';
import {TestPlansModule} from './test_plans_module';
import {TestPlansModuleNgSummary} from './test_plans_module.ngsummary';

describe('TestPlanEditPage', () => {
  const testPlan = newMockTestPlan('test_plan_id_1', 'test_plan_name_1');
  let test: Test;
  let el: DebugElement;
  let testPlanEditPage: TestPlanEditPage;
  let testPlanEditPageFixture: ComponentFixture<TestPlanEditPage>;

  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let routeParams: Subject<Params>;
  let buildChannelsSpy: jasmine.Spy;
  let deviceActionListSpy: jasmine.Spy;
  let nodeConfigSpy: jasmine.Spy;
  let testsSpy: jasmine.Spy;
  let testPlanSpy: jasmine.Spy;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj('mttClient', [
      'getBuildChannels', 'getDeviceActionList', 'getNodeConfig', 'getTests',
      'getTestPlan'
    ]);
    routeParams = new Subject<Params>();

    buildChannelsSpy =
        mttClient.getBuildChannels.and.returnValue(observableOf([]));
    deviceActionListSpy =
        mttClient.getDeviceActionList.and.returnValue(observableOf([]));
    nodeConfigSpy = mttClient.getNodeConfig.and.returnValue(observableOf([]));
    testsSpy = mttClient.getTests.and.returnValue(observableOf({}));
    testPlanSpy = mttClient.getTestPlan.and.returnValue(observableOf(testPlan));

    test = newMockTest();

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        RouterTestingModule,
        TestPlansModule,
      ],
      aotSummaries: TestPlansModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: {}},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: MttClient, useValue: mttClient},
        {provide: ActivatedRoute, useValue: {params: routeParams}},
      ],
    });

    testPlanEditPageFixture = TestBed.createComponent(TestPlanEditPage);
    testPlanEditPageFixture.detectChanges();
    el = testPlanEditPageFixture.debugElement;
    testPlanEditPage = testPlanEditPageFixture.componentInstance;
  });

  it('should get initialized correctly', () => {
    expect(testPlanEditPage).toBeTruthy();
  });

  it('should call load data correctly', () => {
    routeParams.next({'id': testPlan.id});
    expect(testPlanEditPage.editMode).toBeTruthy();
    expect(mttClient.getDeviceActionList).toHaveBeenCalledTimes(1);
    expect(mttClient.getBuildChannels).toHaveBeenCalledTimes(1);
    expect(mttClient.getNodeConfig).toHaveBeenCalledTimes(1);
    expect(mttClient.getTests).toHaveBeenCalledTimes(1);
    expect(mttClient.getTestPlan).toHaveBeenCalledWith(testPlan.id);
    expect(mttClient.getTestPlan).toHaveBeenCalledTimes(1);
  });

  it('displays and announces a loading mask', () => {
    testPlanEditPage.loadData(testPlan.id);
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
      expect(liveAnnouncer.announce)
          .toHaveBeenCalledWith('Test plan loaded', 'assertive');
  });

  it('should set test plan correctly', () => {
    testPlanEditPage.loadTestPlan(testPlan);
    expect(testPlanEditPage.data).toEqual(testPlan);
  });

  it('should update and display test resource pipes correctly', () => {
    test.test_resource_defs = newMockTestResourceDefs();

    const deviceAction: DeviceAction = newMockDeviceAction();
    deviceAction.test_resource_defs = newMockTestResourceDefs();
    deviceAction.test_resource_defs.push(
        newMockTestResourceDef('name3', 'url3', TestResourceType.DEVICE_IMAGE));

    testPlanEditPage.nodeConfigTestResourceUrls =
        [{name: 'name3', value: 'node_url'}];
    testPlanEditPage.selectedDeviceActions = [deviceAction];

    testPlanEditPage.data = testPlan;
    testPlanEditPage.updateTestResources();
    expect(testPlanEditPage.testResourceObjs.length).toEqual(3);

    const lastTestResourceObj =
        testPlanEditPage
            .testResourceObjs[testPlanEditPage.testResourceObjs.length - 1];
    expect(lastTestResourceObj.url).toEqual('node_url');
  });

  it('should add labels correctly', () => {
    testPlanEditPage.data.labels = [];
    testPlanEditPage.addLabel(
        {input: document.createElement('input'), value: ' label1  '});
    expect(testPlanEditPage.data.labels).toEqual(['label1']);
    testPlanEditPage.addLabel(
        {input: document.createElement('input'), value: 'label2'});
    expect(testPlanEditPage.data.labels).toEqual(['label1', 'label2']);

    // Should not add duplicate label
    testPlanEditPage.addLabel(
        {input: document.createElement('input'), value: ' label1  '});
    expect(testPlanEditPage.data.labels).toEqual(['label1', 'label2']);
  });

  it('should remove labels correctly', () => {
    testPlanEditPage.data.labels = ['label1', 'label2', 'label3'];
    testPlanEditPage.removeLabel('label2');
    expect(testPlanEditPage.data.labels).toEqual(['label1', 'label3']);
    testPlanEditPage.removeLabel('label3');
    expect(testPlanEditPage.data.labels).toEqual(['label1']);
    testPlanEditPage.removeLabel('label4');
    expect(testPlanEditPage.data.labels).toEqual(['label1']);
    testPlanEditPage.removeLabel('label1');
    expect(testPlanEditPage.data.labels).toEqual([]);
    testPlanEditPage.removeLabel('label1');
    expect(testPlanEditPage.data.labels).toEqual([]);
  });

  describe('back button', () => {
    it('should display correct aria-label and tooltip', () => {
      const backButton = getEl(el, '#back-button');
      expect(backButton).toBeTruthy();
      expect(backButton.getAttribute('aria-label'))
          .toBe('Return to test plans page');
      expect(backButton.getAttribute('mattooltip'))
          .toBe('Return to test plans page');
    });
  });
});
