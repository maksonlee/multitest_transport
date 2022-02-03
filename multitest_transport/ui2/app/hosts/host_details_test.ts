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
import {DebugElement, LOCALE_ID} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_DIALOG_DATA} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {SurveyTrigger} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {getEl, getEls} from '../testing/jasmine_util';
import {newMockAppData, newMockDeviceInfosResponse, newMockLabHostInfo} from '../testing/mtt_lab_mocks';

import {HostDetails} from './host_details';
import {HostsModule} from './hosts_module';

describe('HostDetails', () => {
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let hostDetails: HostDetails;
  let hostDetailsFixture: ComponentFixture<HostDetails>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let notifierSpy: jasmine.SpyObj<Notifier>;

  const hostname = 'host1';
  const hostInfo = newMockDeviceInfosResponse(hostname);
  const queryParams = {
    hostnameStorageKey: 'mockStorageKey',
  };

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['navigateByUrl', 'navigate', 'createUrlTree', 'serializeUrl']);
    routerSpy.createUrlTree.and.returnValue({});
    routerSpy.serializeUrl.and.returnValue('/hosts/' + hostname);

    tfcClient = jasmine.createSpyObj('tfcClient', {
      getDeviceInfosFromHost: observableOf(hostInfo),
      getHostHistory: observableOf({}),
      getHostInfo: observableOf(newMockLabHostInfo(hostname)),
      getHostNotes: observableOf({}),
      getHostResource: observableOf(null),
      removeHost: observableOf({}),
    });

    notifierSpy = jasmine.createSpyObj('notifier', {
      confirm: observableOf(true),  // mock confirm click in dialog.
      showMessage: observableOf({}),
      showError: observableOf({}),
    });

    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({id: hostname}),
            queryParams: observableOf(queryParams),
            queryParamMap: observableOf(convertToParamMap(queryParams)),
          },
        },
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: FeedbackService, useValue: feedbackService},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: MAT_DIALOG_DATA, useValue: {}},
        {provide: Notifier, useValue: notifierSpy},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
      ],
      });
    hostDetailsFixture = TestBed.createComponent(HostDetails);
    hostDetailsFixture.detectChanges();
    el = hostDetailsFixture.debugElement;
    hostDetails = hostDetailsFixture.componentInstance;
  });

  it('should gets initialized correctly', () => {
    expect(hostDetails).toBeTruthy();
  });

  it('calls window.history.back when the back button clicked', () => {
    spyOn(window.history, 'back');
    getEl(el, '#back-button').click();
    expect(window.history.back).toHaveBeenCalledTimes(1);
  });

  it('should remove host correctly', () => {
    hostDetails.id = hostname;
    hostDetails.removeHost();
    expect(tfcClient.removeHost).toHaveBeenCalledWith(hostname);
  });

  it('should add hostname to dropdown option when no others', () => {
    hostDetails.hostnames = [];
    hostDetails.id = hostname;
    hostDetails.appendDefaultOption();
    expect(hostDetails.hostnames[0]).toEqual(hostname);
  });

  it('should navigate to the selected host when selection change', () => {
    hostDetails.load(hostname, true);
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/hosts/' + hostname], {
      replaceUrl: true
    });
  });

  it('should call HaTS client on host notes display', () => {
    getEls(el, '.mat-tab-label').find(x => x.textContent === 'Notes')!.click();
    hostDetailsFixture.detectChanges();
    hostDetailsFixture.whenStable().then(() => {
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.HOST_NOTES);
    });
  });

  it('should call HaTS client on host navigation', () => {
    hostDetails.startHostNavigationHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.HOST_NAVIGATION);
  });

  it('should load host correctly when calling refresh method', () => {
    spyOn(hostDetails.hostDetailsSummary, 'loadHost');
    hostDetails.id = hostname;

    hostDetails.refresh();
    expect(tfcClient.getHostInfo).toHaveBeenCalledWith(hostname);
    expect(hostDetails.hostDetailsSummary.loadHost)
        .toHaveBeenCalledWith(hostname);
  });
});
