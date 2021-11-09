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
  let testedDevice2: DeviceInfo;

  beforeEach(() => {
    testedDevice = newMockDeviceInfo('testedDevice456');
    testedDevice2 = newMockDeviceInfo('testedDevice123');

    TestBed.configureTestingModule({
      imports: [DevicesModule],
      aotSummaries: DevicesModuleNgSummary,
    });

    devicePickerFixture = TestBed.createComponent(DevicePicker);
    el = devicePickerFixture.debugElement;
    devicePicker = devicePickerFixture.componentInstance;
    devicePicker.selectable = true;
    devicePickerFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(devicePicker).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    expect(getEl(el, 'mat-header-cell')).toBeTruthy();
  });

  it('should show aria-label correctly', () => {
    const checkbox = getEl(el, 'mat-checkbox');
    expect(checkbox).toBeTruthy();
    expect(checkbox.getAttribute('aria-label')).toBe('Check all devices');
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

  it('infosToSerialMap correctly converts device info lists', () => {
    const result = devicePicker.infosToSerialMap([testedDevice2, testedDevice]);
    expect(result[testedDevice2.device_serial]).toBe(testedDevice2);
    expect(result[testedDevice.device_serial]).toBe(testedDevice);
  });

  it('infosToSerialMap handles empty lists', () => {
    const result = devicePicker.infosToSerialMap([]);
    expect(result).toEqual({});
  });

  it('hasSelectedSerial returns true if a serial and product are selected',
     () => {
       devicePicker.serialMap[testedDevice2.device_serial] = testedDevice2;
       devicePicker.serialMap[testedDevice.device_serial] = testedDevice;
       devicePicker.selection.clear();
       devicePicker.selection.select(
           ...[testedDevice2.device_serial, testedDevice.product]);
       expect(devicePicker.hasSelectedSerial()).toEqual(true);
     });

  it('hasSelectedSerial returns false if no serials are selected', () => {
    devicePicker.serialMap[testedDevice2.device_serial] = testedDevice2;
    devicePicker.serialMap[testedDevice.device_serial] = testedDevice;
    devicePicker.selection.clear();
    devicePicker.selection.select(
        ...[testedDevice2.product, testedDevice.product]);
    expect(devicePicker.hasSelectedSerial()).toEqual(false);
  });

  it('displayed correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Device Picker');
  });
});
