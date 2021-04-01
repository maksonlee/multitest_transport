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
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {AnalyticsService} from '../services/analytics_service';
import {FileService} from '../services/file_service';
import {MttClient} from '../services/mtt_client';
import {Test, TestPackageInfo, TestRun, TestRunState} from '../services/mtt_models';
import {TfcClient} from '../services/tfc_client';
import {CommandAttempt, DeviceInfo, InvocationStatus, Request} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';
import * as testUtil from '../testing/mtt_mocks';
import {toTitleCase} from '../testing/mtt_mocks';

import {TestRunDetail} from './test_run_detail';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunDetail', () => {
  let testRunDetail: TestRunDetail;
  let testRunDetailFixture: ComponentFixture<TestRunDetail>;
  let fs: jasmine.SpyObj<FileService>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  let invocationStatus: InvocationStatus;
  let attempt: CommandAttempt;
  let request: Request;
  let test: Test;
  let testDevices: DeviceInfo[];
  let testPackageInfo: TestPackageInfo;
  let testRun: TestRun;
  let retryRun: TestRun;

  beforeEach(() => {
    test = testUtil.newMockTest();
    testDevices = [newMockDeviceInfo()];
    testPackageInfo = testUtil.newMockTestPackageInfo();
    testRun = testUtil.newMockTestRun(
        test, 'tridcomp123', TestRunState.COMPLETED, [], testPackageInfo,
        testDevices);
    retryRun = testUtil.newMockTestRun(test);
    retryRun.prev_test_run_id = testRun.id;
    attempt = testUtil.newMockCommandAttempt();
    request = testUtil.newMockRequest();
    invocationStatus = testUtil.newMockInvocationStatus();

    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    fs = jasmine.createSpyObj(['getTestRunFileUrl', 'getFileBrowseUrl']);
    fs.getFileBrowseUrl.and.returnValue('browse_url');
    mttClient = jasmine.createSpyObj(['getTestRun', 'getReruns']);
    mttClient.getTestRun.and.returnValue(observableOf(testRun));
    mttClient.getReruns.and.returnValue(observableOf({test_runs: [retryRun]}));
    tfcClient =
        jasmine.createSpyObj('tfcClient', ['getDeviceInfos', 'getRequest']);
    tfcClient.getDeviceInfos.and.returnValue(observableOf(testDevices));
    tfcClient.getRequest.and.returnValue(observableOf(request));

    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
        {provide: MttClient, useValue: mttClient},
        {provide: TfcClient, useValue: tfcClient},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: AnalyticsService, useValue: {}},
      ],
    });
    testRunDetailFixture = TestBed.createComponent(TestRunDetail);
    testRunDetail = testRunDetailFixture.componentInstance;
    el = testRunDetailFixture.debugElement;
    testRunDetail.testRunId = testRun.id as string;
    testRunDetailFixture.detectChanges();
  });

  it('gets initialized and calls the API', () => {
    expect(testRunDetail).toBeTruthy();
    expect(mttClient.getTestRun).toHaveBeenCalled();
  });

  it('displays the correct test run values', () => {
    const textContent = getTextContent(el);
    const device = testRun.test_devices![0];
    expect(textContent).toContain(testRun.id!);
    expect(textContent).toContain(test.name);
    expect(textContent)
        .toContain(`${testPackageInfo.name} ${testPackageInfo.version}`);
    expect(textContent).toContain(toTitleCase(testRun.state));
    expect(textContent).toContain(device.build_id!);
    expect(textContent).toContain(device.product);
  });

  it('display previous runs and reruns', () => {
    const prevRunId = 'prev_run';
    testRunDetail.testRun!.prev_test_run_id = prevRunId;
    testRunDetailFixture.detectChanges();

    const textContent = getTextContent(el);
    expect(textContent).toContain(prevRunId);
    expect(textContent).toContain(retryRun.id!);
  });

  it('displays and announces a loading mask', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
  });

  it('shows the latest output files button when available', () => {
    // No output files yet
    testRunDetail.request = testUtil.newMockRequest();
    testRunDetail.updateOutputFilesUrl();
    testRunDetailFixture.detectChanges();
    let textContent = getTextContent(el);
    expect(textContent).not.toContain('View Output Files');
    expect(testRunDetail.outputFilesUrl).toBeUndefined();

    // Output files ready
    testRunDetail.request = testUtil.newMockRequest([], [attempt]);
    testRunDetail.updateOutputFilesUrl();
    testRunDetailFixture.detectChanges();
    textContent = getTextContent(el);
    expect(textContent).toContain('View Working Directory');
    expect(testRunDetail.outputFilesUrl).toEqual('browse_url');
  });

  describe('back button', () => {
    it('should display correct aria-label and tooltip', () => {
      const backButton = getEl(el, '#back-button');
      expect(backButton).toBeTruthy();
      expect(backButton.getAttribute('aria-label'))
          .toBe('Return to test results page');
      expect(backButton.getAttribute('mattooltip'))
          .toBe('Return to test results page');
    });
  });
});
