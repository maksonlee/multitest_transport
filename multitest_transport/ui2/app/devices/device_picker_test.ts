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
import {of as observableOf} from 'rxjs';

import {DeviceInfoService} from '../services/device_info_service';
import {DeviceInfo} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';

import {DevicePicker} from './device_picker';
import {DevicesModule} from './devices_module';
import {DevicesModuleNgSummary} from './devices_module.ngsummary';

describe('DevicePicker', () => {
  let devicePicker: DevicePicker;
  let devicePickerFixture: ComponentFixture<DevicePicker>;
  let deviceInfoService: jasmine.SpyObj<DeviceInfoService>;
  let el: DebugElement;

  let connectedDevice: DeviceInfo;
  let testedDevice: DeviceInfo;

  beforeEach(() => {
    connectedDevice = newMockDeviceInfo('connectedDevice123');
    testedDevice = newMockDeviceInfo('testedDevice456');
    deviceInfoService =
        jasmine.createSpyObj({getDeviceInfos: observableOf([connectedDevice])});

    TestBed.configureTestingModule({
      imports: [DevicesModule],
      aotSummaries: DevicesModuleNgSummary,
      providers: [
        {provide: DeviceInfoService, useValue: deviceInfoService},
      ],
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

  it('called deviceInfoService to load device data', () => {
    expect(deviceInfoService.getDeviceInfos).toHaveBeenCalled();
  });

  it('should show HTML correctly', () => {
    expect(getEl(el, 'mat-header-cell')).toBeTruthy();
  });

  it('should show aria-label correctly', () => {
    const checkbox = getEl(el, 'mat-checkbox');
    expect(checkbox).toBeTruthy();
    expect(checkbox.getAttribute('aria-label')).toBe('Check all devices');
  });

  it('displayed correct device info', () => {
    expect(getTextContent(el)).toContain(connectedDevice.device_serial);
    expect(getTextContent(el))
        .toContain(connectedDevice.sim_operator as string);
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
  });

  it('infosToSerialMap correctly converts device info lists', () => {
    const result =
        devicePicker.infosToSerialMap([connectedDevice, testedDevice]);
    expect(result[connectedDevice.device_serial]).toBe(connectedDevice);
    expect(result[testedDevice.device_serial]).toBe(testedDevice);
  });

  it('infosToSerialMap handles empty lists', () => {
    const result = devicePicker.infosToSerialMap([]);
    expect(result).toEqual({});
  });

  it('hasSelectedSerial returns true if a serial and product are selected',
     () => {
       devicePicker.serialMap[connectedDevice.device_serial] = connectedDevice;
       devicePicker.serialMap[testedDevice.device_serial] = testedDevice;
       devicePicker.selection.clear();
       devicePicker.selection.select(
           ...[connectedDevice.device_serial, testedDevice.product]);
       expect(devicePicker.hasSelectedSerial()).toEqual(true);
     });

  it('hasSelectedSerial returns false if no serials are selected', () => {
    devicePicker.serialMap[connectedDevice.device_serial] = connectedDevice;
    devicePicker.serialMap[testedDevice.device_serial] = testedDevice;
    devicePicker.selection.clear();
    devicePicker.selection.select(
        ...[connectedDevice.product, testedDevice.product]);
    expect(devicePicker.hasSelectedSerial()).toEqual(false);
  });

  it('displayed correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Device Picker');
  });
});
