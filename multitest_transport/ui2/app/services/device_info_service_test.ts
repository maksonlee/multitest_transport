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

import {fakeAsync, tick} from '@angular/core/testing';
import {Subject} from 'rxjs';
import {first} from 'rxjs/operators';

import {newMockDeviceInfo} from '../testing/mtt_lab_mocks';
import {AUTO_UPDATE_INTERVAL_MILLIS, DeviceInfoService} from './device_info_service';
import {TfcClient} from './tfc_client';
import {DeviceInfosResponse, DeviceState, DeviceType} from './tfc_models';

describe('DeviceInfoService', () => {
  let tfc: jasmine.SpyObj<TfcClient>;
  let tfcSubject: Subject<DeviceInfosResponse>;
  const response = {device_infos: []};
  let service: DeviceInfoService;

  beforeEach(() => {
    tfc = jasmine.createSpyObj<TfcClient>(['getDeviceInfos']);
    tfc.getDeviceInfos.and.callFake(() => {
      tfcSubject = new Subject<DeviceInfosResponse>();
      return tfcSubject;
    });
    service = new DeviceInfoService(tfc);
  });

  it('calls TFC once after multiple clients subscribe', (done) => {
    let cnt = 0;
    const next = () => {
      cnt++;
      if (cnt === 2) {
        done();
      }
    };
    service.getDeviceInfos().pipe(first()).subscribe(next);
    service.getDeviceInfos().pipe(first()).subscribe(next);
    expect(tfc.getDeviceInfos).toHaveBeenCalledTimes(1);
    tfcSubject.next(response);
    tfcSubject.complete();
  });

  it('stops calling TFC after all clients ubsubscribe', fakeAsync(() => {
       let cnt = 0;
       service.getDeviceInfos().pipe(first()).subscribe(() => {
         cnt++;
       });
       expect(tfc.getDeviceInfos).toHaveBeenCalledTimes(1);
       tfcSubject.next(response);
       tfcSubject.complete();
       expect(cnt).toBe(1);
       tick(AUTO_UPDATE_INTERVAL_MILLIS * 2);
       expect(tfc.getDeviceInfos).toHaveBeenCalledTimes(1);
     }));

  it('calls TFC once at each time interval and notifies multiple clients',
     fakeAsync(() => {
       let cnt1 = 0;
       let cnt2 = 0;
       const subscription1 = service.getDeviceInfos().subscribe(() => {
         cnt1++;
       });
       const subscription2 = service.getDeviceInfos().subscribe(() => {
         cnt2++;
       });
       for (let i = 1; i < 5; i++) {
         expect(tfc.getDeviceInfos).toHaveBeenCalledTimes(i);
         tfcSubject.next(response);
         tfcSubject.complete();
         expect(cnt1).toBe(i);
         expect(cnt2).toBe(i);
         tick(AUTO_UPDATE_INTERVAL_MILLIS);
       }
       subscription1.unsubscribe();
       subscription2.unsubscribe();
     }));

  describe('deviceSpecsToDeviceTypes', () => {
    const deviceInfos = [
      newMockDeviceInfo(
          'serial1', '0', DeviceState.AVAILABLE, false, 'host01', 'runTarget1',
          DeviceType.REMOTE),
      newMockDeviceInfo(
          'serial2', '0', DeviceState.AVAILABLE, false, 'host01', 'runTarget2'),
      newMockDeviceInfo('serial3'),
    ];

    beforeEach(() => {
      service.getDeviceInfos().pipe(first()).subscribe(() => {});
      tfcSubject.next({device_infos: deviceInfos});
    });

    it('maps matching device specs to correct device types', () => {
      expect(service.isInitialized).toBeTrue();
      const deviceTypes = service.deviceSpecsToDeviceTypes(
          ['device_serial:serial1', 'device_serial:serial2']);
      expect(deviceTypes).toEqual(new Set(['REMOTE', 'PHYSICAL']));
    });

    it('maps missing device specs to an empty set', () => {
      expect(service.isInitialized).toBeTrue();
      const deviceTypes =
          service.deviceSpecsToDeviceTypes(['device_serial:serial4']);
      expect(deviceTypes).toEqual(new Set());
    });
  });
});
