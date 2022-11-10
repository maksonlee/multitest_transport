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
import {ComponentFixture, TestBed, inject} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';
import {MatDialog} from '@angular/material/dialog';

import {AnalyticsService} from '../services/analytics_service';
import {FileService} from '../services/file_service';
import {MttClient, TestResultClient, TestRunActionClient} from '../services/mtt_client';
import {Test, TestPackageInfo, TestRun, TestRunState, TestRunPhase, TestRunAction} from '../services/mtt_models';
import {TfcClient} from '../services/tfc_client';
import {Command, CommandAttempt, DeviceInfo, Request} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';
import * as testUtil from '../testing/mtt_mocks';
import {toTitleCase} from '../testing/mtt_mocks';
import {TestRunActionPickerDialog, TestRunActionPickerDialogData} from '../test_run_actions/test_run_action_picker_dialog';

import {TestRunDetail} from './test_run_detail';
import {TestRunsModule} from './test_runs_module';

describe('TestRunDetail', () => {
  let testRunDetail: TestRunDetail;
  let testRunDetailFixture: ComponentFixture<TestRunDetail>;
  let fs: jasmine.SpyObj<FileService>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let testResultClient: jasmine.SpyObj<TestResultClient>;
  let testRunActionClient: jasmine.SpyObj<TestRunActionClient>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  let command: Command;
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
    command = testUtil.newMockCommand();
    attempt = testUtil.newMockCommandAttempt();
    request = testUtil.newMockRequest();

    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    fs = jasmine.createSpyObj(['getTestRunFileUrl', 'getFileBrowseUrl']);
    fs.getFileBrowseUrl.and.returnValue('browse_url');

    testResultClient =
        jasmine.createSpyObj('testResultClient', ['listModules']);
    testResultClient.listModules.and.returnValue(observableOf({}));
    testRunActionClient = jasmine.createSpyObj(
        'testRunActionsClient', ['list', 'executeTestRunActions']);
    testRunActionClient.list.and.returnValue(observableOf([]));
    testRunActionClient.executeTestRunActions.and.returnValue(observableOf({}));

    mttClient = {
      ...jasmine.createSpyObj('mttClient', ['getTestRun', 'getReruns']),
      testResults: testResultClient,
      testRunActions: testRunActionClient,
    };
    mttClient.getTestRun.and.returnValue(observableOf(testRun));
    mttClient.getReruns.and.returnValue(observableOf({test_runs: [retryRun]}));

    tfcClient = jasmine.createSpyObj(
        'tfcClient', ['getCommandStateStats', 'getDeviceInfos', 'getRequest']);
    tfcClient.getCommandStateStats.and.returnValue(observableOf(
        {state_stats: [], create_time: '2021-09-15T01:47:28.430076+00:00'}));
    tfcClient.getDeviceInfos.and.returnValue(observableOf(testDevices));
    tfcClient.getRequest.and.returnValue(observableOf(request));

    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule, RouterTestingModule],
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
    testRunDetail.request = testUtil.newMockRequest([command], [attempt]);
    testRunDetail.updateOutputFilesUrl();
    testRunDetailFixture.detectChanges();
    textContent = getTextContent(el);
    expect(textContent).toContain('View Working Directory');
    expect(testRunDetail.outputFilesUrl).toEqual('browse_url');
  });

  it('shows the execute test run action button when there are manual actions',
     () => {
       let textContent = getTextContent(el);
       expect(textContent).not.toContain('Execute Test Run Actions');
       testRunActionClient.list.and.returnValue(observableOf(
           [{id: 'id', name: 'action', phases: [TestRunPhase.MANUAL]}]));

       // Reload the page
       testRunDetail.loadTestRun();
       testRunDetailFixture.detectChanges();

       textContent = getTextContent(el);
       expect(textContent).toContain('Execute Test Run Actions');
     });

  it('opens the test run action picker dialog and executes successfully',
     inject([MatDialog], (dialog: MatDialog) => {
       const manualAction: TestRunAction = {
         id: 'id',
         name: 'action',
         hook_class_name: 'hook',
         phases: [TestRunPhase.MANUAL],
       };
       testRunActionClient.list.and.returnValue(observableOf([manualAction]));
       testRunDetail.loadTestRun();
       testRunDetailFixture.detectChanges();
       spyOn(dialog, 'open').and.returnValue({
         componentInstance: {confirm: observableOf([{action_id: 'id'}])}
       });
       mttClient.getTestRun.calls.reset();

       getEl(el, '.execute-test-run-actions-button').click();

       // Open the dialog
       expect(dialog.open).toHaveBeenCalledTimes(1);
       const testRunActionPickerDialogData: TestRunActionPickerDialogData = {
         actions: [manualAction],
         selectedActionRefs: [],
       };
       expect(dialog.open).toHaveBeenCalledWith(TestRunActionPickerDialog, {
         panelClass: 'test-run-action-picker-dialog',
         data: testRunActionPickerDialogData,
       });
       // Execute test run actions
       expect(testRunActionClient.executeTestRunActions)
           .toHaveBeenCalledWith('tridcomp123', {refs: [{action_id: 'id'}]});
       // Reload test run
       expect(mttClient.getTestRun).toHaveBeenCalledTimes(1);
     }));

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
