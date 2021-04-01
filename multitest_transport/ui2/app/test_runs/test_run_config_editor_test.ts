/**
 * Copyright 2020 Google LLC
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

import {DevicePicker} from '../devices/device_picker';
import {APP_DATA} from '../services/app_data';
import {DeviceInfoService} from '../services/device_info_service';
import {MttClient} from '../services/mtt_client';
import {MttObjectMap, MttObjectMapService, newMttObjectMap} from '../services/mtt_object_map';
import {DeviceInfo} from '../services/tfc_models';
import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';
import {newMockDeviceAction, newMockTest, newMockTestRunConfig} from '../testing/mtt_mocks';

import {TestRunConfigEditor, TestRunConfigEditorData} from './test_run_config_editor';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunConfigEditor', () => {
  let testRunConfigEditor: TestRunConfigEditor;
  let testRunConfigEditorFixture: ComponentFixture<TestRunConfigEditor>;
  let devicePicker: DevicePicker;
  let deviceInfoService: jasmine.SpyObj<DeviceInfoService>;
  let el: DebugElement;
  let mttClient: jasmine.SpyObj<MttClient>;
  let mttObjectMapService: jasmine.SpyObj<MttObjectMapService>;
  let device1: DeviceInfo;
  let device2: DeviceInfo;

  const test = newMockTest('test_id_1', 'test_name_1');
  const testRunConfig =
      newMockTestRunConfig(test.id, 'command', 'retry_command', '');
  const testRunConfigEditorData: TestRunConfigEditorData = {
    editMode: false,
    testRunConfig,
  };
  const dialogRefSpy =
      jasmine.createSpyObj('MatDialogRef', ['close', 'backdropClick']);

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getTest']);
    mttClient.getTest.and.returnValue(observableOf(test));
    mttObjectMapService = jasmine.createSpyObj(['getMttObjectMap']);
    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(newMttObjectMap()));
    dialogRefSpy.backdropClick.and.returnValue(observableOf({}));
    deviceInfoService = jasmine.createSpyObj<DeviceInfoService>({
      getDeviceInfos: observableOf([]),
      isInitialized: true,
      deviceSpecsToDeviceTypes: new Set<string>(),
    });

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, NoopAnimationsModule, TestRunsModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: {}},
        {provide: MatDialogRef, useValue: dialogRefSpy},
        {provide: MAT_DIALOG_DATA, useValue: testRunConfigEditorData},
        {provide: MttClient, useValue: mttClient},
        {provide: DeviceInfoService, useValue: deviceInfoService},
        {provide: MttObjectMapService, useValue: mttObjectMapService},
      ],
    });

    testRunConfigEditorFixture = TestBed.createComponent(TestRunConfigEditor);
    el = testRunConfigEditorFixture.debugElement;
    testRunConfigEditor = testRunConfigEditorFixture.componentInstance;
    testRunConfigEditorFixture.detectChanges();

    device1 = newMockDeviceInfo('device1Id');
    device2 = newMockDeviceInfo('device2Id');
    devicePicker = el.query(By.directive(DevicePicker)).componentInstance;
    devicePicker.deviceInfos = [];
  });

  function reload(objectMap: MttObjectMap) {
    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(newMttObjectMap()));
    testRunConfigEditor.load();
    testRunConfigEditorFixture.detectChanges();
  }

  it('initializes a component', () => {
    expect(testRunConfigEditor).toBeTruthy();
  });

  it('should return device specs correctly', () => {
    const testedDevices = [device1, device2];
    devicePicker.deviceInfos = testedDevices;
    expect(testRunConfigEditor.data.testRunConfig.device_specs).toEqual([]);
    devicePicker.toggleSelection();
    expect(testRunConfigEditor.data.testRunConfig.device_specs)
        .toEqual(testedDevices.map(
            (device) => `device_serial:${device.device_serial}`));
    devicePicker.toggleSelection();
    expect(testRunConfigEditor.data.testRunConfig.device_specs).toEqual([]);
    devicePicker.toggleSelection();
  });

  it('should create new test run config correctly on submit', () => {
    testRunConfigEditor.data.editMode = false;
    spyOn(testRunConfigEditor.configSubmitted, 'emit');
    testRunConfigEditor.submit();
    expect(testRunConfigEditor.configSubmitted.emit)
        .toHaveBeenCalledWith(testRunConfigEditor.data.testRunConfig);
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('can update the selected device action ids', () => {
    const objectMap = newMttObjectMap();
    const deviceAction = newMockDeviceAction('action.id');
    objectMap.deviceActionMap = {'action.id': deviceAction};
    reload(objectMap);

    expect(
        testRunConfigEditor.data.testRunConfig.before_device_action_ids!.length)
        .toEqual(0);
    testRunConfigEditor.selectedDeviceActions = [deviceAction];
    testRunConfigEditor.updateConfigDeviceActionIds();
    expect(testRunConfigEditor.data.testRunConfig.before_device_action_ids!)
        .toEqual(['action.id']);
  });

  it('should update test run config correctly on submit', () => {
    testRunConfigEditor.data.editMode = true;
    const testedDevices =
        [newMockDeviceInfo('device1Id'), newMockDeviceInfo('device2Id')];
    devicePicker.deviceInfos = testedDevices;
    devicePicker.toggleSelection();
    testRunConfigEditor.submit();
    expect(testRunConfigEditor.data.testRunConfig.device_specs)
        .toEqual(testedDevices.map(
            (device) => `device_serial:${device.device_serial}`));
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
