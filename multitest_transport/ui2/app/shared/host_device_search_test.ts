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

import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {MatSnackBar} from '@angular/material/snack-bar';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {Router} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf, throwError} from 'rxjs';

import {FeedbackService} from '../services/feedback_service';
import {TfcClient} from '../services/tfc_client';
import {newMockLabDeviceInfo, newMockLabHostInfo} from '../testing/mtt_lab_mocks';

import {HostDeviceSearch} from './host_device_search';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('HostDeviceSearch', () => {
  const serial = 'device1';
  const hostname = 'host01';
  let hostDeviceSearch: HostDeviceSearch;
  let hostDeviceSearchFixture: ComponentFixture<HostDeviceSearch>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let routerSpy: jasmine.SpyObj<Router>;
  const mockDeviceInfo = newMockLabDeviceInfo(serial);
  const hostInfo = newMockLabHostInfo(hostname);
  let feedbackService: jasmine.SpyObj<FeedbackService>;

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    feedbackService.startSurvey.and.returnValue(observableOf({}));
    tfcClient =
        jasmine.createSpyObj('tfcClient', ['getDeviceInfo', 'getHostInfo']);

    routerSpy = jasmine.createSpyObj('Router', ['navigateByUrl']);

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        SharedModule,
        RouterTestingModule,
      ],
      aotSummaries: SharedModuleNgSummary,
      providers: [
        {provide: FeedbackService, useValue: feedbackService},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });

    hostDeviceSearchFixture = TestBed.createComponent(HostDeviceSearch);
    hostDeviceSearch = hostDeviceSearchFixture.componentInstance;
    hostDeviceSearchFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(hostDeviceSearch).toBeTruthy();
  });

  it('should navigate to device page after input a device serial', () => {
    tfcClient.getDeviceInfo.and.returnValue(observableOf(mockDeviceInfo));
    hostDeviceSearch.onEnter(serial);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledTimes(1);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith(`/devices/${serial}`);
    expect(routerSpy.navigateByUrl).not.toContain(`/hosts/${serial}`);
  });

  it('should navigate to host page after input a hostname', () => {
    tfcClient.getDeviceInfo.and.returnValue(throwError({'status': 404}));
    tfcClient.getHostInfo.and.returnValue(observableOf(hostInfo));
    hostDeviceSearch.onEnter(hostname);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledTimes(1);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith(`/hosts/${hostname}`);
    expect(routerSpy.navigateByUrl).not.toContain(`/devices/${hostname}`);
  });

  it('should show error when getDeviceInfo returns without serial', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    tfcClient.getDeviceInfo.and.returnValue(
        observableOf(newMockLabDeviceInfo('')));
    hostDeviceSearch.onEnter(serial);
    expect(dialog.open).toHaveBeenCalled();
  });

  it('should show error when getDeviceInfo returns 404 and getHostInfo returns without hostname',
     () => {
       const dialog = TestBed.inject(MatDialog);
       spyOn(dialog, 'open').and.callThrough();
       tfcClient.getDeviceInfo.and.returnValue(throwError({'status': 404}));
       tfcClient.getHostInfo.and.returnValue(
           observableOf(newMockLabHostInfo('')));
       hostDeviceSearch.onEnter(serial);
       expect(dialog.open).toHaveBeenCalled();
     });

  it('should show error when getDeviceInfo return 500', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    tfcClient.getDeviceInfo.and.returnValue(throwError({'status': 500}));
    hostDeviceSearch.onEnter(hostname);
    expect(dialog.open).toHaveBeenCalled();
  });

  it('should show error when getDeviceInfo return 404 and getHostInfo retuen 500',
     () => {
       const dialog = TestBed.inject(MatDialog);
       spyOn(dialog, 'open').and.callThrough();
       tfcClient.getDeviceInfo.and.returnValue(throwError({'status': 404}));
       tfcClient.getHostInfo.and.returnValue(throwError({'status': 500}));
       hostDeviceSearch.onEnter(hostname);
       expect(dialog.open).toHaveBeenCalled();
     });

  it('should show warning when getDeviceInfo return 404 and getHostInfo retuen 404',
     () => {
       const snackBar = TestBed.inject(MatSnackBar);
       spyOn(snackBar, 'open').and.callThrough();
       tfcClient.getDeviceInfo.and.returnValue(throwError({'status': 404}));
       tfcClient.getHostInfo.and.returnValue(throwError({'status': 404}));
       hostDeviceSearch.onEnter(hostname);
       expect(snackBar.open).toHaveBeenCalled();
     });
});