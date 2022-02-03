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

import {DebugElement, LOCALE_ID} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_DIALOG_DATA} from '@angular/material/dialog';
import {Title} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {of as observableOf} from 'rxjs';

import {TfcClient} from '../services/tfc_client';
import {newMockAppData, newMockLabDeviceInfo} from '../testing/mtt_lab_mocks';

import {DeviceDetails, DeviceDetailsDialogParams} from './device_details';
import {DeviceDetailsPage} from './device_details_page';
import {DevicesModule} from './devices_module';

describe('DeviceDetailsPage', () => {
  const serial = 'serial';
  let deviceDetailsPage: DeviceDetailsPage;
  let deviceDetailsPageFixture: ComponentFixture<DeviceDetailsPage>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  let dialogData: DeviceDetailsDialogParams;
  const mockDeviceInfo = newMockLabDeviceInfo(serial);
  const queryParams = {
    deviceSerials: ['device1', 'device2'],
  };

  beforeEach(() => {
    dialogData = {id: serial, newWindow: false};
    tfcClient = jasmine.createSpyObj('tfcClient', [
      'getDeviceInfo', 'batchGetDeviceNotes', 'getDeviceHistory',
      'getPredefinedMessages', 'getDeviceNotes'
    ]);
    tfcClient.getDeviceInfo.and.returnValue(observableOf(mockDeviceInfo));
    tfcClient.batchGetDeviceNotes.and.returnValue(observableOf({}));
    tfcClient.getDeviceHistory.and.returnValue(observableOf({}));
    tfcClient.getPredefinedMessages.and.returnValue(observableOf({}));
    tfcClient.getDeviceNotes.and.returnValue(observableOf({}));

    TestBed.configureTestingModule({
      declarations: [
        DeviceDetails,
        DeviceDetailsPage,
      ],
      imports: [
        DevicesModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        Title,
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({id: serial}),
            queryParams: observableOf(queryParams),
            queryParamMap: observableOf(convertToParamMap(queryParams)),
          },
        },
        {provide: TfcClient, useValue: tfcClient},
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: MAT_DIALOG_DATA, useValue: dialogData},
      ],
    });
    deviceDetailsPageFixture = TestBed.createComponent(DeviceDetailsPage);
    el = deviceDetailsPageFixture.debugElement;
    deviceDetailsPage = deviceDetailsPageFixture.componentInstance;
    deviceDetailsPageFixture.detectChanges();
  });

  it('initializes correctly and has a correct page title', () => {
    expect(deviceDetailsPage).toBeTruthy();
    expect(el.injector.get(Title).getTitle())
        .toEqual('Android Test Station Lab - Device Details');
  });
});
