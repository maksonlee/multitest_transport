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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';

import {DeviceInfo} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';

import {DevicePicker} from './device_picker';
import {DevicesModule} from './devices_module';
import {DevicesModuleNgSummary} from './devices_module.ngsummary';

describe('DevicePicker', () => {
  let devicePicker: DevicePicker;
  let devicePickerFixture: ComponentFixture<DevicePicker>;
  let el: DebugElement;

  let testedDevice: DeviceInfo;

  beforeEach(() => {
    testedDevice = newMockDeviceInfo('testedDevice456');

    TestBed.configureTestingModule({
      imports: [DevicesModule],
      aotSummaries: DevicesModuleNgSummary,
    });

    devicePickerFixture = TestBed.createComponent(DevicePicker);
    el = devicePickerFixture.debugElement;
    devicePicker = devicePickerFixture.componentInstance;
    devicePickerFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(devicePicker).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    expect(getEl(el, 'mat-header-cell')).toBeTruthy();
  });

  it('correctly displays a given empty list', () => {
    devicePicker.deviceInfos = [];
    devicePickerFixture.detectChanges();
    expect(getTextContent(el)).toContain('No devices found.');
  });

  it('correctly displays a given device list', () => {
    devicePicker.deviceInfos = [testedDevice];
    devicePickerFixture.detectChanges();
    expect(getTextContent(el)).toContain(testedDevice.device_serial);
    expect(getTextContent(el)).toContain(testedDevice.sim_operator as string);
  });

  it('displayed correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Device Picker');
  });
});
