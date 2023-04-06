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
import {MAT_LEGACY_DIALOG_DATA} from '@angular/material/dialog';
import {Title} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {TfcClient} from '../services/tfc_client';
import {newMockAppData, newMockLabHostInfo} from '../testing/mtt_lab_mocks';

import {HostDetails, HostDetailsDialogParams} from './host_details';
import {HostDetailsPage} from './host_details_page';
import {HostsModule} from './hosts_module';

describe('HostDetailsPage', () => {
  const hostname = 'AndroidEngProdApiClusterClientFuncTest';
  let hostDetailsPage: HostDetailsPage;
  let hostDetailsPageFixture: ComponentFixture<HostDetailsPage>;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  let dialogData: HostDetailsDialogParams;
  const mockHostInfo = newMockLabHostInfo(hostname);
  const queryParams = {
    hostnames: ['HOST-1', 'HOST-2'],
  };

  beforeEach(() => {
    dialogData = {id: 'host1', newWindow: false};
    routerSpy = jasmine.createSpyObj(
        'Router', ['navigateByUrl', 'navigate', 'createUrlTree']);
    tfcClient = jasmine.createSpyObj('tfcClient', [
      'getHostInfo', 'getDeviceInfosFromHost', 'getHostHistory', 'getHostNotes',
      'getHostResource',
    ]);
    tfcClient.getHostInfo.and.returnValue(observableOf(mockHostInfo));
    tfcClient.getDeviceInfosFromHost.and.returnValue(observableOf({}));
    tfcClient.getHostHistory.and.returnValue(observableOf({}));
    tfcClient.getHostNotes.and.returnValue(observableOf({}));
    tfcClient.getHostResource.and.returnValue(observableOf(null));
    routerSpy.createUrlTree.and.returnValue({});

    TestBed.configureTestingModule({
      declarations: [
        HostDetails,
        HostDetailsPage,
      ],
      imports: [
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        Title,
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({id: hostname}),
            queryParams: observableOf(queryParams),
            queryParamMap: observableOf(convertToParamMap(queryParams)),
          },
        },
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: FeedbackService},
        {provide: TfcClient, useValue: tfcClient},
        {provide: Router, useValue: routerSpy},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: MAT_LEGACY_DIALOG_DATA, useValue: dialogData},
      ],
    });
    hostDetailsPageFixture = TestBed.createComponent(HostDetailsPage);
    el = hostDetailsPageFixture.debugElement;
    hostDetailsPage = hostDetailsPageFixture.componentInstance;
    hostDetailsPageFixture.detectChanges();
  });

  it('initializes correctly and has a correct page title', () => {
    expect(hostDetailsPage).toBeTruthy();
    expect(el.injector.get(Title).getTitle())
        .toEqual('Android Test Station Lab - Host Details');
  });
});
