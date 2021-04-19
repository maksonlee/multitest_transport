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

import {DebugElement, SimpleChange} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router} from '@angular/router';
import {getTextContent} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {TfcClient} from '../services/tfc_client';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {newMockAppData, newMockDeviceInfosResponse, newMockDeviceNote, newMockDeviceNoteList, newMockLabDeviceInfosResponse} from '../testing/mtt_lab_mocks';

import {RecoveryDeviceList} from './recovery_device_list';
import {RecoveryModule} from './recovery_module';
import {RecoveryModuleNgSummary} from './recovery_module.ngsummary';

describe('RecoveryDeviceList', () => {
  const hostName = 'host1';
  const deviceSerial = 'device1';
  const labDeviceInfosResponse = newMockLabDeviceInfosResponse(hostName);
  const deviceInfosResponse = newMockDeviceInfosResponse(hostName);

  let el: DebugElement;
  let recoveryDeviceList: RecoveryDeviceList;
  let recoveryDeviceListFixture: ComponentFixture<RecoveryDeviceList>;
  let tfcClient: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    const activatedRouteSpy = new ActivatedRouteStub({});
    tfcClient = jasmine.createSpyObj('tfcClient', [
      'getDeviceInfosFromHost', 'removeDevice', 'getDeviceNotes',
      'batchGetDevicesLatestNotes'
    ]);
    tfcClient.getDeviceInfosFromHost.and.returnValue(
        observableOf(labDeviceInfosResponse));
    tfcClient.removeDevice.and.returnValue(observableOf({}));
    tfcClient.getDeviceNotes.and.returnValue(observableOf({}));
    tfcClient.batchGetDevicesLatestNotes.and.returnValue(
        observableOf(newMockDeviceNoteList(
            labDeviceInfosResponse.deviceInfos![0].device_serial)));

    TestBed.configureTestingModule({
      imports: [
        RecoveryModule,
        NoopAnimationsModule,
      ],
      aotSummaries: RecoveryModuleNgSummary,
      providers: [
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: FeedbackService},
        {provide: TfcClient, useValue: tfcClient},
        {provide: Router},
        {
          provide: APP_DATA,
          useValue: newMockAppData(),
        },
      ],
    });

    recoveryDeviceListFixture = TestBed.createComponent(RecoveryDeviceList);
    recoveryDeviceListFixture.detectChanges();
    el = recoveryDeviceListFixture.debugElement;
    recoveryDeviceList = recoveryDeviceListFixture.componentInstance;
    recoveryDeviceList.deviceInfos = labDeviceInfosResponse.deviceInfos!;
  });

  afterEach(() => {
    recoveryDeviceListFixture.destroy();
  });

  it('should get initialized correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Devices');
    expect(recoveryDeviceList).toBeTruthy();
  });

  it('should calls the tfc client api method getDeviceInfosFromHost',
     async () => {
       recoveryDeviceList.hostName = hostName;
       recoveryDeviceList.ngOnChanges({
         hostName: new SimpleChange(null, recoveryDeviceList.hostName, true)
       });
       recoveryDeviceListFixture.detectChanges();
       expect(tfcClient.getDeviceInfosFromHost).toHaveBeenCalledTimes(1);
       // If getDeviceInfosFromHost returns device infos should also get latest
       // device notes.
       expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
     });

  it('opens note editor dialog in create mode for single device correctly',
     () => {
       const dialog = TestBed.inject(MatDialog);
       spyOn(dialog, 'open').and.callThrough();
       const mockClickEvent = new MouseEvent('click');

       // Trigger open editor dialog.
       recoveryDeviceList.openDeviceNoteCreateEditor(
           mockClickEvent, labDeviceInfosResponse.deviceInfos);
       expect(dialog.open).toHaveBeenCalledTimes(1);
     });

  it('opens note editor dialog in create mode for multiple device correctly',
     () => {
       const dialog = TestBed.inject(MatDialog);
       spyOn(dialog, 'open').and.callThrough();
       const mockClickEvent = new MouseEvent('click');

       // Selects all device.
       const selectedDeviceSerials =
           labDeviceInfosResponse.deviceInfos!.map(info => info.device_serial);
       for (const serial of selectedDeviceSerials) {
         recoveryDeviceList.tableRowsSelectManager.selection.select(serial);
       }

       // Trigger open editor dialog.
       recoveryDeviceList.openDeviceNoteCreateEditor(mockClickEvent);
       expect(dialog.open).toHaveBeenCalledTimes(1);
     });

  it('opens note editor dialog in edit mode correctly', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    const mockClickEvent = new MouseEvent('click');

    const deviceInfo = labDeviceInfosResponse.deviceInfos![0];
    const latestNote = newMockDeviceNote(123);
    deviceInfo.latestNote = latestNote;

    // Trigger open editor dialog.
    recoveryDeviceList.openDeviceNoteUpdateEditor(mockClickEvent, deviceInfo);
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });

  it('opens device details dialog correctly', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    const mockClickEvent = new MouseEvent('click');

    // Trigger open device details dialog.
    recoveryDeviceList.openDeviceDetailsDialog(mockClickEvent, deviceSerial);
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });

  it('should remove device correctly', () => {
    recoveryDeviceList.hostName = hostName;
    const mockClickEvent = new MouseEvent('click');

    recoveryDeviceList.removeDevice(mockClickEvent, deviceSerial);

    expect(tfcClient.removeDevice).toHaveBeenCalledWith(deviceSerial, hostName);
    expect(tfcClient.removeDevice).toHaveBeenCalledTimes(1);
  });

  it(`calls resetSelection method correctly while the device number has
    changed`,
     async () => {
       await recoveryDeviceListFixture.whenStable();
       recoveryDeviceList.hostName = hostName;
       const mockClickEvent = new MouseEvent('click');
       spyOn(recoveryDeviceList.tableRowsSelectManager, 'resetSelection');

       const expectedNumber = recoveryDeviceList.deviceInfos.length - 1;

       recoveryDeviceList.removeDevice(mockClickEvent, deviceSerial);
       await recoveryDeviceListFixture.whenStable();

       expect(
           recoveryDeviceList.tableRowsSelectManager.rowIdFieldAllValues.length)
           .toEqual(expectedNumber);
       expect(recoveryDeviceList.tableRowsSelectManager.resetSelection)
           .toHaveBeenCalledTimes(1);
     });

  it('should get latest notes for devices correctly', () => {
    recoveryDeviceList.getLatestNotes([labDeviceInfosResponse.deviceInfos![0]]);
    expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
    expect(labDeviceInfosResponse.deviceInfos![0].latestNote).toBeTruthy();
  });
});