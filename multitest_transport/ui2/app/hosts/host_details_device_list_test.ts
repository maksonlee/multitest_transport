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
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute} from '@angular/router';
import {Router} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {SurveyTrigger} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {getTextContent} from '../testing/jasmine_util';
import {newMockAppData, newMockDeviceNoteList, newMockLabDeviceInfosResponse} from '../testing/mtt_lab_mocks';

import {HostDetailsDeviceList} from './host_details_device_list';
import {HostsModule} from './hosts_module';

describe('HostDetailsDeviceList', () => {
  let hostDetailsDeviceList: HostDetailsDeviceList;
  let hostDetailsDeviceListFixture: ComponentFixture<HostDetailsDeviceList>;
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;

  const hostname = 'host01';
  const labHostInfo = newMockLabDeviceInfosResponse(hostname);

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['createUrlTree', 'navigateByUrl', 'navigate', 'serializeUrl']);

    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    tfcClient = jasmine.createSpyObj('tfcClient', [
      'getDeviceInfosFromHost', 'removeDevice', 'batchGetDevicesLatestNotes'
    ]);
    tfcClient.getDeviceInfosFromHost.and.returnValue(observableOf(labHostInfo));
    tfcClient.removeDevice.and.returnValue(observableOf({}));
    tfcClient.batchGetDevicesLatestNotes.and.returnValue(observableOf(
        newMockDeviceNoteList(labHostInfo.deviceInfos![0].device_serial)));

    TestBed.configureTestingModule({
      imports: [
        HostsModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {
          provide: APP_DATA,
          useValue: newMockAppData(),
        },
        {
          provide: ActivatedRoute,
          useValue: {params: observableOf({id: hostname})},
        },
        {provide: FeedbackService, useValue: feedbackService},
        {provide: TfcClient, useValue: tfcClient},
        {
          provide: Router,
          useValue: routerSpy,
        },
      ],
    });

    hostDetailsDeviceListFixture =
        TestBed.createComponent(HostDetailsDeviceList);
    hostDetailsDeviceList = hostDetailsDeviceListFixture.componentInstance;
    hostDetailsDeviceList.id = hostname;
    hostDetailsDeviceListFixture.detectChanges();
    el = hostDetailsDeviceListFixture.debugElement;
  });

  afterEach(() => {
    hostDetailsDeviceListFixture.destroy();
  });

  it('should get initialized correctly', () => {
    expect(hostDetailsDeviceList).toBeTruthy();
  });

  it('should call the tfc client api method getDeviceInfosFromHost and batchGetDevicesLatestNotes correctly',
     async () => {
       await hostDetailsDeviceListFixture.whenStable();
       expect(tfcClient.getDeviceInfosFromHost).toHaveBeenCalledTimes(1);
       expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
     });

  it('correctly displays a given empty list', () => {
    hostDetailsDeviceList.deviceInfos = [];
    hostDetailsDeviceListFixture.detectChanges();
    expect(getTextContent(el)).toContain('No devices found.');
  });

  it('correctly displays a given device list', () => {
    const mockDeviceList = labHostInfo.deviceInfos!;
    hostDetailsDeviceList.deviceInfos = mockDeviceList;
    hostDetailsDeviceListFixture.detectChanges();
    expect(getTextContent(el)).toContain(mockDeviceList[0].device_serial);
  });


  it('should get latest notes for devices correctly', () => {
    (tfcClient.batchGetDevicesLatestNotes as jasmine.Spy).calls.reset();
    hostDetailsDeviceList.loadDeviceNotes(['device1']);
    expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
    expect(labHostInfo.deviceInfos![0].note).toBeTruthy();
  });

  it('should load device notes when calling reloadDevices', () => {
    spyOn(hostDetailsDeviceList, 'loadDeviceNotes');

    const deviceNumber = hostDetailsDeviceList.deviceInfos.length;

    hostDetailsDeviceList.reloadDevices(['device1']);
    expect(hostDetailsDeviceList.loadDeviceNotes).toHaveBeenCalledWith([
      'device1'
    ]);
  });

  it('should call HaTS client on change device sort correctly', () => {
    hostDetailsDeviceList.startChangeSortHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.SORT_DEVICE_DATA);
  });

  it('should call HaTS client on view devices columns correctly', () => {
    hostDetailsDeviceList.startViewDevicesColumnsHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.VIEW_DEVICES_COLUMNS);
  });

  it('should call HaTS client on batch add devices notes', () => {
    hostDetailsDeviceList.startBatchAddDevicesNotesHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.BATCH_ADD_DEVICES_NOTES);
  });
});
