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
import {Component, DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {FileService} from '../services/file_service';
import {MttClient, TestRunActionClient} from '../services/mtt_client';
import {Test, TestRun} from '../services/mtt_models';
import {TfcClient} from '../services/tfc_client';
import {DeviceInfo} from '../services/tfc_models';
import {getEl} from '../testing/jasmine_util';
import {newMockDevice, newMockNodeConfig, newMockTest, newMockTestRun} from '../testing/test_util';

import {NewTestRunPage} from './new_test_run_page';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

@Component({selector: 'device-list', template: ''})
class DeviceListStubComponent {
}

describe('NewTestRunPage', () => {
  let newTestRunPage: NewTestRunPage;
  let newTestRunPageFixture: ComponentFixture<NewTestRunPage>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let tfcClient: jasmine.SpyObj<TfcClient>;

  let el: DebugElement;
  let connectedDevice: DeviceInfo;
  let test: Test;
  let testRun: TestRun;

  beforeEach(() => {
    connectedDevice = newMockDevice('connectedDevice123');
    test = newMockTest();
    testRun = newMockTestRun(test);

    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);

    mttClient = {
      ...jasmine.createSpyObj([
        'getBuildChannels', 'getDeviceActionList', 'getNodeConfig', 'getTests'
      ]),
      testRunActions:
          jasmine.createSpyObj<TestRunActionClient>({list: observableOf([])}),
    } as jasmine.SpyObj<MttClient>;

    mttClient.getBuildChannels.and.returnValue(observableOf([]));
    mttClient.getDeviceActionList.and.returnValue(observableOf([]));
    mttClient.getNodeConfig.and.returnValue(observableOf(newMockNodeConfig()));
    mttClient.getTests.and.returnValue(observableOf([test]));

    tfcClient = jasmine.createSpyObj('tfcClient', ['getDeviceInfos']);
    tfcClient.getDeviceInfos.and.returnValue(
        observableOf({device_infos: [connectedDevice]}));

    TestBed.configureTestingModule({
      declarations: [DeviceListStubComponent],
      imports: [TestRunsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: FileService, useValue: {}},
        {provide: MttClient, useValue: mttClient},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });
    newTestRunPageFixture = TestBed.createComponent(NewTestRunPage);
    newTestRunPageFixture.detectChanges();
    el = newTestRunPageFixture.debugElement;
    newTestRunPage = newTestRunPageFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(newTestRunPage).toBeTruthy();
  });

  it('displays and announces a loading mask', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    expect(liveAnnouncer.announce)
        .toHaveBeenCalledWith('Test run loaded', 'assertive');
  });

  it('loads previous test run data', () => {
    newTestRunPage.loadPrevTestRun(testRun);
    expect(newTestRunPage.testRunConfig.test_id).toBe(test.id!);
  });

  it('adds labels', () => {
    newTestRunPage.labels = [];
    newTestRunPage.addLabel(
        {input: document.createElement('input'), value: ' label1  '});
    expect(newTestRunPage.labels).toEqual(['label1']);
    newTestRunPage.addLabel(
        {input: document.createElement('input'), value: 'label2'});
    expect(newTestRunPage.labels).toEqual(['label1', 'label2']);

    // Should not add duplicate label
    newTestRunPage.addLabel(
        {input: document.createElement('input'), value: ' label1  '});
    expect(newTestRunPage.labels).toEqual(['label1', 'label2']);
  });

  it('removes labels', () => {
    newTestRunPage.labels = ['label1', 'label2', 'label3'];
    newTestRunPage.removeLabel('label2');
    expect(newTestRunPage.labels).toEqual(['label1', 'label3']);
    newTestRunPage.removeLabel('label3');
    expect(newTestRunPage.labels).toEqual(['label1']);
    newTestRunPage.removeLabel('label4');
    expect(newTestRunPage.labels).toEqual(['label1']);
    newTestRunPage.removeLabel('label1');
    expect(newTestRunPage.labels).toEqual([]);
    newTestRunPage.removeLabel('label1');
    expect(newTestRunPage.labels).toEqual([]);
  });

  describe('back button', () => {
    it('should display correct aria-label and tooltip', () => {
      const backButton = getEl(el, '#back-button');
      expect(backButton).toBeTruthy();
      expect(backButton.getAttribute('aria-label'))
          .toBe('Return to test suites page');
      expect(backButton.getAttribute('mattooltip'))
          .toBe('Return to test suites page');
    });
  });
});
