/**
 * @license
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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {getEl, getEls, hasEl} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {Subject} from 'rxjs';

import {AoaDevice} from './device';
import {DeviceList} from './device_list';
import {DeviceManager} from './device_manager';
import {DeviceModule} from './device_module';

/** Creates a fake AOA device for testing. */
function createMockAoaDevice(
    params: Partial<AoaDevice> = {}, accessoryMode = false,
    adbEnabled = false): AoaDevice {
  return jasmine.createSpyObj<AoaDevice>(
      {
        isAccessoryMode: accessoryMode,
        isAdbEnabled: adbEnabled,
      },
      {...params},
  );
}

describe('DeviceList', () => {
  let connectionChange: Subject<void>;
  let deviceManager: jasmine.SpyObj<DeviceManager>;

  let fixture: ComponentFixture<DeviceList>;
  let element: DebugElement;
  let component: DeviceList;

  beforeEach(() => {
    connectionChange = new Subject();
    deviceManager = jasmine.createSpyObj<DeviceManager>(
        ['getDevices', 'onConnectionChange', 'requestDevice']);
    deviceManager.getDevices.and.resolveTo([]);
    deviceManager.onConnectionChange.and.returnValue(connectionChange);

    TestBed.configureTestingModule({
      imports: [DeviceModule],
      providers: [{provide: DeviceManager, useValue: deviceManager}],
    });

    fixture = TestBed.createComponent(DeviceList);
    element = fixture.debugElement;
    component = fixture.componentInstance;
  });

  /** Reload a new list of devices. */
  function reload(devices: AoaDevice[]) {
    deviceManager.getDevices.and.resolveTo(devices);
    connectionChange.next();
    tick();
    fixture.detectChanges();
  }

  it('should display warning if no devices found', fakeAsync(() => {
       reload([]);
       expect(hasEl(element, '.empty')).toBeTrue();
       expect(getEls(element, '.device').length).toEqual(0);
     }));

  it('should display device information', fakeAsync(() => {
       const device = createMockAoaDevice({
         serialNumber: 'serial',
         manufacturerName: 'manufacturer',
         productName: 'product',
       });
       reload([device]);
       expect(hasEl(element, '.empty')).toBeFalse();
       expect(getEls(element, '.device').length).toEqual(1);
       expect(getEl(element, '.device .product').textContent)
           .toEqual('manufacturer product');
       expect(getEl(element, '.device .serial').textContent).toEqual('serial');
     }));

  it('should display default mode if AOA disabled', fakeAsync(() => {
       const device = createMockAoaDevice({}, false, false);
       reload([device]);
       expect(hasEl(element, '.device .default-mode')).toBeTrue();
       expect(hasEl(element, '.device .accessory-mode')).toBeFalse();
     }));

  it('should display accessory mode if AOA enabled', fakeAsync(() => {
       const device = createMockAoaDevice({}, true, false);
       reload([device]);
       expect(hasEl(element, '.device .default-mode')).toBeFalse();
       expect(hasEl(element, '.device .accessory-mode')).toBeTrue();
       expect(getEl(element, '.device .accessory-mode').textContent)
           .not.toContain('ADB');
     }));

  it('should display accessory with ADB if ADB enabled', fakeAsync(() => {
       const device = createMockAoaDevice({}, true, true);
       reload([device]);
       expect(hasEl(element, '.device .default-mode')).toBeFalse();
       expect(hasEl(element, '.device .accessory-mode')).toBeTrue();
       expect(getEl(element, '.device .accessory-mode').textContent)
           .toContain('ADB');
     }));

  it('should emit device when selected', fakeAsync(() => {
       spyOn(component.selectionChange, 'emit');
       const device = createMockAoaDevice();
       reload([device]);
       getEl(element, '.device').click();
       expect(component.selectionChange.emit).toHaveBeenCalledWith(device);
     }));
});
