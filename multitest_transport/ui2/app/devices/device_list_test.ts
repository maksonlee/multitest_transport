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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {of as observableOf} from 'rxjs';

import {TfcClient} from '../services/tfc_client';
import {DeviceInfo} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDevice} from '../testing/test_util';

import {DeviceList} from './device_list';
import {DevicesModule} from './devices_module';
import {DevicesModuleNgSummary} from './devices_module.ngsummary';

describe('DeviceList', () => {
  let deviceList: DeviceList;
  let deviceListFixture: ComponentFixture<DeviceList>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;

  let connectedDevice: DeviceInfo;
  let testedDevice: DeviceInfo;

  beforeEach(() => {
    connectedDevice = newMockDevice('connectedDevice123');
    testedDevice = newMockDevice('testedDevice456');
    tfcClient = jasmine.createSpyObj('tfcClient', ['getDeviceInfos']);
    tfcClient.getDeviceInfos.and.returnValue(
        observableOf({device_infos: [connectedDevice]}));

    TestBed.configureTestingModule({
      imports: [DevicesModule],
      aotSummaries: DevicesModuleNgSummary,
      providers: [
        {provide: TfcClient, useValue: tfcClient},
      ],
    });

    deviceListFixture = TestBed.createComponent(DeviceList);
    el = deviceListFixture.debugElement;
    deviceList = deviceListFixture.componentInstance;
    deviceList.selectable = true;
    deviceListFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(deviceList).toBeTruthy();
  });

  it('called tfcApi to load device data', () => {
    expect(tfcClient.getDeviceInfos).toHaveBeenCalled();
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
  });

  it('correctly displays a given empty list', () => {
    deviceList.deviceInfos = [];
    deviceListFixture.detectChanges();
    expect(getTextContent(el)).toContain('No devices found.');
  });

  it('correctly displays a given device list', () => {
    deviceList.deviceInfos = [testedDevice];
    deviceListFixture.detectChanges();
    expect(getTextContent(el)).toContain(testedDevice.device_serial);
  });

  it('infosToSerialMap correctly converts device info lists', () => {
    const result = deviceList.infosToSerialMap([connectedDevice, testedDevice]);
    expect(result[connectedDevice.device_serial]).toBe(connectedDevice);
    expect(result[testedDevice.device_serial]).toBe(testedDevice);
  });

  it('infosToSerialMap handles empty lists', () => {
    const result = deviceList.infosToSerialMap([]);
    expect(result).toEqual({});
  });

  it('hasSelectedSerial returns true if a serial and product are selected',
     () => {
       deviceList.serialMap[connectedDevice.device_serial] = connectedDevice;
       deviceList.serialMap[testedDevice.device_serial] = testedDevice;
       deviceList.selection.clear();
       deviceList.selection.select(
           ...[connectedDevice.device_serial, testedDevice.product]);
       expect(deviceList.hasSelectedSerial()).toEqual(true);
     });

  it('hasSelectedSerial returns false if no serials are selected', () => {
    deviceList.serialMap[connectedDevice.device_serial] = connectedDevice;
    deviceList.serialMap[testedDevice.device_serial] = testedDevice;
    deviceList.selection.clear();
    deviceList.selection.select(
        ...[connectedDevice.product, testedDevice.product]);
    expect(deviceList.hasSelectedSerial()).toEqual(false);
  });

  it('displayed correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Device list');
  });
});
