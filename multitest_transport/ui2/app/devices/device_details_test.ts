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

import {HttpClientTestingModule} from '@angular/common/http/testing';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_LEGACY_DIALOG_DATA} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {SurveyTrigger} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_lab_models';
import {getEl, getEls, getTextContent} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {of as observableOf} from 'rxjs';

import {FeedbackService} from '../services/feedback_service';
import {newMockAppData} from '../testing/mtt_lab_mocks';

import {DeviceDetails} from './device_details';
import {DevicesModule} from './devices_module';

describe('DeviceDetails', () => {
  let deviceDetails: DeviceDetails;
  let deviceDetailsFixture: ComponentFixture<DeviceDetails>;
  let el: DebugElement;
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let routerSpy: jasmine.SpyObj<Router>;
  const deviceSerial = 'device1';
  const queryParams = {
    deviceSerials: [deviceSerial, 'device2'],
  };
  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['navigateByUrl', 'navigate', 'createUrlTree', 'serializeUrl']);
    routerSpy.createUrlTree.and.returnValue({});
    routerSpy.serializeUrl.and.returnValue('/devices/' + deviceSerial);

    TestBed.configureTestingModule({
      imports: [
        DevicesModule,
        HttpClientTestingModule,
        NoopAnimationsModule,
      ],
      providers: [
        {
          provide: APP_DATA,
          useValue: newMockAppData(),
        },
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({id: deviceSerial}),
            queryParams: observableOf({}),
            queryParamMap: observableOf(convertToParamMap(queryParams)),
          },
        },
        {provide: FeedbackService, useValue: feedbackService},
        {
          provide: Router,
          useValue: routerSpy,
        },
        {provide: MAT_LEGACY_DIALOG_DATA, useValue: {}},
      ],
      });
    deviceDetailsFixture = TestBed.createComponent(DeviceDetails);
    deviceDetailsFixture.detectChanges();
    el = deviceDetailsFixture.debugElement;
    deviceDetails = deviceDetailsFixture.componentInstance;
  });

  it('should gets initialized correctly', () => {
    const textContent = getTextContent(el);
    expect(deviceDetails).toBeTruthy();
  });

  it('calls window.history.back when the back button clicked', () => {
    spyOn(window.history, 'back');
    getEl(el, '#back-button').click();
    expect(window.history.back).toHaveBeenCalledTimes(1);
  });

  it('should add device serial to dropdown option when no others', () => {
    deviceDetails.deviceSerials = [];
    deviceDetails.id = deviceSerial;
    deviceDetails.appendDefaultOption();
    expect(deviceDetails.deviceSerials[0]).toEqual(deviceSerial);
  });

  it('should navigate to the selected device when selection change', () => {
    const device = 'device2';
    routerSpy.serializeUrl.and.returnValue('/devices/' + device);
    deviceDetails.load(device, true);
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/devices/' + device], {
      replaceUrl: true
    });
  });

  it('should call HaTS client on device history display', () => {
    getEls(el, '.mat-tab-label')
        .find(x => x.textContent === 'History')!.click();
    deviceDetailsFixture.detectChanges();
    deviceDetailsFixture.whenStable().then(() => {
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.DEVICE_HISTORY);
    });
  });

  it('should call HaTS client on device navigation', () => {
    deviceDetails.startDeviceNavigationHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.DEVICE_NAVIGATION);
  });
});
