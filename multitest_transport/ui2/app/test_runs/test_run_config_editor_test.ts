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

import {HttpClientTestingModule} from '@angular/common/http/testing';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {DeviceList} from '../devices/device_list';
import {APP_DATA} from '../services/app_data';
import {MttClient} from '../services/mtt_client';
import {newMockDevice, newMockTest, newMockTestRunConfig} from '../testing/test_util';

import {TestRunConfigEditor, TestRunConfigEditorData} from './test_run_config_editor';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunConfigEditor', () => {
  let testRunConfigEditor: TestRunConfigEditor;
  let testRunConfigEditorFixture: ComponentFixture<TestRunConfigEditor>;
  let deviceList: DeviceList;
  let el: DebugElement;
  let mttClient: jasmine.SpyObj<MttClient>;

  const test = newMockTest('test_id_1', 'test_name_1');
  const testRunConfig = newMockTestRunConfig(test.id);
  const testRunConfigEditorData: TestRunConfigEditorData = {
    editMode: false,
    testRunConfig,
    testMap: {[test.id]: test}
  };
  const dialogRefSpy =
      jasmine.createSpyObj('MatDialogRef', ['close', 'backdropClick']);

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getTest']);
    mttClient.getTest.and.returnValue(observableOf(test));
    dialogRefSpy.backdropClick.and.returnValue(observableOf({}));
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, NoopAnimationsModule, TestRunsModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: {}},
        {provide: MatDialogRef, useValue: dialogRefSpy},
        {provide: MAT_DIALOG_DATA, useValue: testRunConfigEditorData},
        {provide: MttClient, useValue: mttClient},
      ],
    });
    testRunConfigEditorFixture = TestBed.createComponent(TestRunConfigEditor);
    el = testRunConfigEditorFixture.debugElement;
    testRunConfigEditor = testRunConfigEditorFixture.componentInstance;
    testRunConfigEditorFixture.detectChanges();
    deviceList = el.query(By.directive(DeviceList)).componentInstance;
    deviceList.deviceInfos = [];
  });

  it('initializes a component', () => {
    expect(testRunConfigEditor).toBeTruthy();
  });

  it('should return run target device correctly', () => {
    const testedDevices =
        [newMockDevice('device1Id'), newMockDevice('device2Id')];
    deviceList.deviceInfos = testedDevices;
    // All devices are pre-selected because testRunConfig.run_target includes
    // them. Try flip-floping.
    deviceList.toggleSelection();
    deviceList.toggleSelection();
    expect(testRunConfigEditor.data.testRunConfig.run_target)
        .toBe(testedDevices.map((device) => device.device_serial).join(';'));
  });

  it('should create new test run config correctly on submit', () => {
    testRunConfigEditor.data.editMode = false;
    spyOn(testRunConfigEditor.configSubmitted, 'emit');
    testRunConfigEditor.submit();
    expect(testRunConfigEditor.configSubmitted.emit)
        .toHaveBeenCalledWith(testRunConfig);
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('should update test run config correctly on submit', () => {
    testRunConfigEditor.data.editMode = true;
    const testedDevices =
        [newMockDevice('device1Id'), newMockDevice('device2Id')];
    deviceList.deviceInfos = testedDevices;
    // All devices are pre-selected because testRunConfig.run_target includes
    // them. Try flip-floping.
    deviceList.toggleSelection();
    deviceList.toggleSelection();
    testRunConfigEditor.submit();
    expect(testRunConfigEditor.data.testRunConfig.run_target)
        .toBe(testedDevices.map((device) => device.device_serial).join(';'));
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
