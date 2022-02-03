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
import {ComponentFixture, inject, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {DEFAULT_PAGE_SIZE} from 'google3/third_party/py/multitest_transport/ui2/app/shared/paginator';
import {getTextContent} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {of as observableOf, throwError} from 'rxjs';

import {convertToLabDeviceInfoHistoryList} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {newMockAppData, newMockDeviceInfoHistoryList, newMockDeviceNoteList} from '../testing/mtt_lab_mocks';

import {DeviceDetailsHistory} from './device_details_history';
import {DevicesModule} from './devices_module';

describe('DeviceDetailsHistory', () => {
  const serial = 'device1';
  const deviceNoteIds = [101, 102];
  const mockDeviceInfoHistoryList =
      convertToLabDeviceInfoHistoryList(newMockDeviceInfoHistoryList());
  const mockDeviceNoteList = newMockDeviceNoteList(serial, deviceNoteIds);
  let deviceDetailsHistory: DeviceDetailsHistory;
  let deviceDetailsHistoryFixture: ComponentFixture<DeviceDetailsHistory>;
  let deviceInfosSpy: jasmine.Spy;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;

  beforeEach(() => {
    tfcClient = jasmine.createSpyObj(
        'tfcClient',
        ['getDeviceHistory', 'batchGetDeviceNotes', 'getPredefinedMessages']);
    deviceInfosSpy = tfcClient.getDeviceHistory.and.returnValue(
        observableOf(mockDeviceInfoHistoryList));
    tfcClient.batchGetDeviceNotes.and.returnValue(
        observableOf(mockDeviceNoteList));
    tfcClient.getPredefinedMessages.and.returnValue(observableOf({}));
    routerSpy = jasmine.createSpyObj(
        'Router', ['navigateByUrl', 'navigate', 'createUrlTree']);
    routerSpy.createUrlTree.and.returnValue({});

    TestBed.configureTestingModule({
      imports: [
        DevicesModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({id: serial}),
            queryParams: observableOf({}),
          },
        },
      ],
    });

    deviceDetailsHistoryFixture = TestBed.createComponent(DeviceDetailsHistory);
    el = deviceDetailsHistoryFixture.debugElement;
    deviceDetailsHistory = deviceDetailsHistoryFixture.componentInstance;
    deviceDetailsHistory.id = serial;
    deviceDetailsHistory.historyList = mockDeviceInfoHistoryList.histories!;
    deviceDetailsHistoryFixture.detectChanges();
  });

  afterEach(() => {
    deviceDetailsHistoryFixture.destroy();
  });

  it('should get initialized correctly', () => {
    const textContent = getTextContent(el);
    expect(mockDeviceInfoHistoryList).toBeTruthy();
  });

  it('should call the tfc client api method getDeviceHistory and batchGetDeviceNotes correctly',
     async () => {
       await deviceDetailsHistoryFixture.whenStable();
       expect(tfcClient.getDeviceHistory).toHaveBeenCalledTimes(1);
       expect(tfcClient.batchGetDeviceNotes).toHaveBeenCalledTimes(1);
     });

  it('can load previous page of device history', () => {
    deviceDetailsHistory.id = serial;
    deviceDetailsHistory.nextPageToken = 'next';
    deviceDetailsHistory.prevPageToken = 'prev';
    deviceDetailsHistory.load(true);
    expect(tfcClient.getDeviceHistory)
        .toHaveBeenCalledWith(serial, DEFAULT_PAGE_SIZE, 'prev', true);
  });

  it('can load next page of device history', () => {
    deviceDetailsHistory.id = serial;
    deviceDetailsHistory.nextPageToken = 'next';
    deviceDetailsHistory.prevPageToken = 'prev';
    deviceDetailsHistory.load(false);
    expect(tfcClient.getDeviceHistory)
        .toHaveBeenCalledWith(serial, DEFAULT_PAGE_SIZE, 'next', false);
  });

  it('can handle page size change', () => {
    deviceDetailsHistory.id = serial;
    deviceDetailsHistory.nextPageToken = 'next';
    deviceDetailsHistory.paginator.changePageSize(20);
    expect(tfcClient.getDeviceHistory)
        .toHaveBeenCalledWith(serial, 20, undefined, false);
  });

  it('should call getDeviceNoteIds return correctly', () => {
    expect(deviceDetailsHistory.getDeviceNoteIds(
               mockDeviceInfoHistoryList.histories!))
        .toEqual(deviceNoteIds);
  });

  it('should open note dialog on editNote called', () => {
    const noteId = 100;
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    spyOn(deviceDetailsHistory, 'editNote').and.callThrough();
    deviceDetailsHistory.editNote(noteId);
    expect(dialog.open).toHaveBeenCalled();
    expect(deviceDetailsHistory.editNote).toHaveBeenCalledWith(noteId);
  });

  it('should refresh data after dialog save clicked', () => {
    spyOn(deviceDetailsHistory, 'resetPageTokenAndReload');
    let dialogSpy: jasmine.Spy;
    const dialogRefSpy =
        jasmine.createSpyObj({afterClosed: observableOf(true), close: null});
    dialogSpy =
        spyOn(TestBed.inject(MatDialog), 'open').and.returnValue(dialogRefSpy);
    deviceDetailsHistory.editNote(0);
    expect(dialogSpy).toHaveBeenCalled();
    expect(dialogRefSpy.afterClosed).toHaveBeenCalled();
    dialogRefSpy.afterClosed().subscribe(
        (result: boolean) => {
          expect(deviceDetailsHistory.resetPageTokenAndReload)
              .toHaveBeenCalled();
        },
    );
  });

  it('can update pagination parameters', inject([Router], (router: Router) => {
       tfcClient.getDeviceHistory.and.returnValue(observableOf(
           {histories: [], prev_cursor: 'prev', next_cursor: 'next'}));
       deviceDetailsHistory.loadHistory(serial);
       expect(deviceDetailsHistory.prevPageToken).toEqual('prev');
       expect(deviceDetailsHistory.nextPageToken).toEqual('next');
       expect(deviceDetailsHistory.paginator.hasPrevious).toBeTruthy();
       expect(deviceDetailsHistory.paginator.hasNext).toBeTruthy();
       expect(router.createUrlTree).toHaveBeenCalledWith([], {
         queryParams: {
           historyPageToken: 'prev',
           historyPageSize: null,
         },
         queryParamsHandling: 'merge'
       });
     }));

  it('can show error when getDeviceHistory returns 404', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    deviceInfosSpy.calls.reset();
    tfcClient.getDeviceHistory.and.returnValue(throwError({'status': 404}));
    deviceDetailsHistory.loadHistory(serial);
    expect(dialog.open).toHaveBeenCalled();
  });
});
