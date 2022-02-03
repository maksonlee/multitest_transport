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

import {Location} from '@angular/common';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router, UrlSerializer} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA, AppData} from '../services';
import {filterHostInfoCount, OfflineHostFilterParams} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {DeviceCountSummary} from '../services/tfc_models';
import {UserService} from '../services/user_service';
import {TimeFilterOperator} from '../shared/time_input_filter';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getEl} from '../testing/jasmine_util';
import {getMockLabHostInfo, newMockAppData, newMockLabInfosResponse, newMockLabOfflineHostInfosByLabResponse} from '../testing/mtt_lab_mocks';

import {HostsModule} from './hosts_module';
import {OfflineHostList} from './offline_host_list';

describe('OfflineHostList', () => {
  /**
   * Since this project will be open source, we don't use cleanState to test
   * here.
   */
  let offlineHostList: OfflineHostList;
  let offlineHostListFixture: ComponentFixture<OfflineHostList>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let urlSerializerSpy: jasmine.SpyObj<UrlSerializer>;
  let userServiceSpy: jasmine.SpyObj<UserService>;
  let locationSpy: jasmine.SpyObj<Location>;
  let lab: string;
  let mockAppData: AppData;

  beforeEach(() => {
    mockAppData = newMockAppData();
    routerSpy = jasmine.createSpyObj('Router', {
      createUrlTree: Promise.resolve(true),
      navigate: Promise.resolve(true),
      navigateByUrl: Promise.resolve(true),
      serializeUrl: Promise.resolve(true),
    });
    locationSpy = jasmine.createSpyObj('locationSpy', ['replaceState']);
    urlSerializerSpy =
        jasmine.createSpyObj('urlSerializerSpy', {serialize: ''});
  });

  describe('default url', () => {
    beforeEach(() => {
      lab = 'lab-1';
      const hostInfosResponse = newMockLabOfflineHostInfosByLabResponse(lab);
      const labInfosResponse = newMockLabInfosResponse();
      const activatedRouteSpy = new ActivatedRouteStub({});

      tfcClientSpy = jasmine.createSpyObj('tfcClient', {
        batchSetHostsRecoveryStates: observableOf(undefined),
        getOfflineHostInfos: observableOf(hostInfosResponse),
        getMyLabInfos: observableOf(labInfosResponse),
      });

      userServiceSpy = jasmine.createSpyObj('userService', {
        isAdmin: true,
        isMyLab: observableOf(true),
        isAdminOrMyLab: observableOf(true),
      });

      window.localStorage.clear();

      TestBed.configureTestingModule({
        imports: [
          HostsModule,
          NoopAnimationsModule,
        ],
        providers: [
          {provide: Router, useValue: routerSpy},
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: ActivatedRoute, useValue: activatedRouteSpy},
          {provide: Location, useValue: locationSpy},
          {provide: UrlSerializer, useValue: urlSerializerSpy},
          {provide: UserService, useValue: userServiceSpy},
          {provide: APP_DATA, useValue: mockAppData},
        ],
      });

      offlineHostListFixture = TestBed.createComponent(OfflineHostList);
      el = offlineHostListFixture.debugElement;
      offlineHostList = offlineHostListFixture.componentInstance;
      offlineHostListFixture.detectChanges();
    });

    it('initializes correctly', () => {
      expect(offlineHostList).toBeTruthy();
    });

    it('calls getMyLabInfos api when the component loaded', async () => {
      await offlineHostListFixture.whenStable();
      expect(tfcClientSpy.getMyLabInfos).toHaveBeenCalledTimes(1);
    });

    it('calls getHostInfos api when the component loaded', async () => {
      await offlineHostListFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(1);
    });

    it('calls getHostInfos api when the refresh button clicked', async () => {
      await offlineHostListFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(1);
      getEl(el, '#refresh-button').click();
      await offlineHostListFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(2);
    });

    it(`calls batchSetHostsRecoveryStates api correctly when the recover button 
       clicked and hosts are selected`,
       () => {
         offlineHostList.hostList.tableRowsSelectManager.selection.select(
             ...['host1', 'host3', 'host5', 'host6']);
         getEl(el, '#recover-button').click();
         expect(tfcClientSpy.batchSetHostsRecoveryStates)
             .toHaveBeenCalledTimes(1);
       });

    it('tells router to navigate when the recover button clicked', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedHostGroups = ['host group-2'];
      const mockSelectedRunTargets = ['target4'];
      const mockSelectedTestHarness = 'All';
      const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
      const mockInputTimeHours = 5;

      offlineHostList.selectedLab = mockSelectedLab;
      await offlineHostListFixture.whenStable();
      offlineHostList.selectedHostGroups = mockSelectedHostGroups;
      offlineHostList.selectedRunTargets = mockSelectedRunTargets;
      offlineHostList.selectedTestHarness = mockSelectedTestHarness;
      offlineHostList.lastCheckInOperator = mockSelectedTimeOperator;
      offlineHostList.lastCheckInHours = mockInputTimeHours;

      offlineHostList.hostList.tableRowsSelectManager.selection.select(
          'host27');
      getEl(el, '#recover-button').click();

      expect(routerSpy.navigate).toHaveBeenCalledWith(['/recovery'], {
        queryParams: {
          lab: mockSelectedLab,
          hostGroups: mockSelectedHostGroups,
          runTargets: mockSelectedRunTargets,
          testHarness: mockSelectedTestHarness,
          lastCheckInOperator: mockSelectedTimeOperator.urlId,
          lastCheckInHours: mockInputTimeHours,
        }
      });
    });

    it('saves last filter criteria into localStorage correctly', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedHostGroups = ['host group-2'];
      const mockSelectedRunTargets = ['target4'];
      const mockSelectedTestHarness = 'MH';
      const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
      const mockInputTimeHours = 5;

      offlineHostList.selectedLab = mockSelectedLab;
      await offlineHostListFixture.whenStable();

      offlineHostList.selectedHostGroups = mockSelectedHostGroups;
      offlineHostList.selectedRunTargets = mockSelectedRunTargets;
      offlineHostList.selectedTestHarness = mockSelectedTestHarness;
      offlineHostList.lastCheckInOperator = mockSelectedTimeOperator;
      offlineHostList.lastCheckInHours = mockInputTimeHours;

      offlineHostList.updateLocalStorage();

      const storedText = window.localStorage.getItem(
          offlineHostList.FILTER_CRITERIA_STORAGE_KEY);
      const storedObject = storedText ?
          (JSON.parse(storedText) as OfflineHostFilterParams) :
          null;
      expect(storedObject).toEqual({
        lab: mockSelectedLab,
        hostGroups: mockSelectedHostGroups,
        runTargets: mockSelectedRunTargets,
        testHarness: mockSelectedTestHarness,
        lastCheckInOperator: mockSelectedTimeOperator.urlId,
        lastCheckInHours: mockInputTimeHours,
      });
    });

    it('gets filter criteria from local storage correctly', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedHostGroups = ['host group-2'];
      const mockSelectedRunTargets = ['target4'];
      const mockSelectedTestHarness = 'MH';
      const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
      const mockInputTimeHours = 5;

      offlineHostList.selectedLab = mockSelectedLab;
      await offlineHostListFixture.whenStable();

      offlineHostList.selectedHostGroups = mockSelectedHostGroups;
      offlineHostList.selectedRunTargets = mockSelectedRunTargets;
      offlineHostList.selectedTestHarness = mockSelectedTestHarness;
      offlineHostList.lastCheckInOperator = mockSelectedTimeOperator;
      offlineHostList.lastCheckInHours = mockInputTimeHours;

      offlineHostList.updateLocalStorage();

      const storedData = offlineHostList.loadFromLocalStorage();

      expect(storedData).toEqual({
        lab: mockSelectedLab,
        hostGroups: mockSelectedHostGroups,
        runTargets: mockSelectedRunTargets,
        testHarness: mockSelectedTestHarness,
        lastCheckInOperator: mockSelectedTimeOperator.urlId,
        lastCheckInHours: mockInputTimeHours,
      });
    });

    it('gets run target default value correctly', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedRunTargets = ['target4'];
      const hostInfosResponse =
          newMockLabOfflineHostInfosByLabResponse(mockSelectedLab);

      offlineHostList.selectedLab = mockSelectedLab;
      tfcClientSpy.getOfflineHostInfos.and.returnValue(
          observableOf(hostInfosResponse));
      offlineHostList.reloadHostsAndFilters();
      await offlineHostListFixture.whenStable();

      offlineHostList.selectedRunTargets = mockSelectedRunTargets;
      offlineHostList.reloadHosts();

      const value = offlineHostList.getDefaultValues(
          'runTargets', offlineHostList.runTargets);

      expect(value).toEqual(mockSelectedRunTargets);
    });


    it('gets test harness default value correctly', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedTestHarness = 'MOBILEHARNESS';
      const hostInfosResponse =
          newMockLabOfflineHostInfosByLabResponse(mockSelectedLab);

      offlineHostList.selectedLab = mockSelectedLab;
      tfcClientSpy.getOfflineHostInfos.and.returnValue(
          observableOf(hostInfosResponse));
      offlineHostList.reloadHostsAndFilters();
      await offlineHostListFixture.whenStable();

      offlineHostList.selectedTestHarness = mockSelectedTestHarness;
      offlineHostList.reloadHosts();

      const value = offlineHostList.getDefaultValue(
          'testHarness', offlineHostList.testHarnesses);

      expect(value).toEqual(mockSelectedTestHarness);
    });

    it('loads data correctly when specifying a run target', async () => {
      await offlineHostListFixture.whenStable();
      const mockSelectedRunTargets = ['target1'];
      offlineHostList.selectedRunTargets = mockSelectedRunTargets;
      offlineHostList.reloadHosts();
      await offlineHostListFixture.whenStable();
      const hosts = offlineHostList.hostListDataSource.map(h => h.hostname);
      expect(hosts).toContain('host1');
      expect(hosts).not.toContain('host43');
    });

    it('calls createUrlTree method correctly when the component is loaded',
       async () => {
         await offlineHostListFixture.whenStable();
         expect(routerSpy.createUrlTree)
             .toHaveBeenCalledWith(['offline_hosts'], {
               queryParams: {
                 lab,
                 hostGroups: [offlineHostList.allOptionsValue],
                 runTargets: [offlineHostList.allOptionsValue],
                 testHarness: offlineHostList.allOptionsValue,
                 lastCheckInOperator: offlineHostList.allOptionsValue,
                 lastCheckInHours: 0,
               }
             });
       });

    it('calls serialize method when the component is loaded', async () => {
      await offlineHostListFixture.whenStable();
      expect(urlSerializerSpy.serialize).toHaveBeenCalledTimes(1);
    });

    it('calls location.replaceState method when the component is loaded',
       async () => {
         await offlineHostListFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(1);
       });

    it(`calls location.replaceState method when the run target is changed by the user`,
       async () => {
         await offlineHostListFixture.whenStable();
         const mockSelectedRunTargets = ['target1'];
         offlineHostList.selectedRunTargets = mockSelectedRunTargets;
         offlineHostList.reloadHosts();
         await offlineHostListFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(2);
       });

    it('calls location.replaceState method when the lab is changed by the user',
       async () => {
         await offlineHostListFixture.whenStable();
         offlineHostList.selectedLab = 'lab-2';
         offlineHostList.reloadHostsAndFilters();
         await offlineHostListFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(2);
       });
  });

  describe('url with query params', () => {
    const mockHostGroups = ['host group-2'];
    const mockRunTargets = ['target2'];
    const mockTestHarness = 'MOBILEHARNESS';
    const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
    const mockInputTimeHours = 5;

    beforeEach(() => {
      lab = 'lab-2';
      const hostInfosResponse = newMockLabOfflineHostInfosByLabResponse(lab);
      const labInfosResponse = newMockLabInfosResponse();
      const activatedRouteSpy = new ActivatedRouteStub({
        lab,
        hostGroups: mockHostGroups,
        runTargets: mockRunTargets,
        testHarness: mockTestHarness,
        lastCheckInOperator: mockSelectedTimeOperator.urlId,
        lastCheckInHours: mockInputTimeHours,
      });
      tfcClientSpy = jasmine.createSpyObj<TfcClient>('tfcClient', {
        getOfflineHostInfos: observableOf(hostInfosResponse),
        getMyLabInfos: observableOf(labInfosResponse),
      });

      TestBed.configureTestingModule({
        imports: [
          NoopAnimationsModule,
          HostsModule,
        ],
        providers: [
          {provide: Router, useValue: routerSpy},
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: ActivatedRoute, useValue: activatedRouteSpy},
          {provide: Location, useValue: locationSpy},
          {provide: UrlSerializer, useValue: urlSerializerSpy},
          {provide: APP_DATA, useValue: mockAppData},
        ],
      });

      offlineHostListFixture = TestBed.createComponent(OfflineHostList);
      el = offlineHostListFixture.debugElement;
      offlineHostList = offlineHostListFixture.componentInstance;
      offlineHostListFixture.detectChanges();
    });

    it('parse url parameters correctly', async () => {
      await offlineHostListFixture.whenStable();
      expect(offlineHostList.urlParams.lab).toEqual(lab);
      expect(offlineHostList.urlParams.hostGroups).toEqual(mockHostGroups);
      expect(offlineHostList.urlParams.runTargets).toEqual(mockRunTargets);
      expect(offlineHostList.urlParams.testHarness).toEqual(mockTestHarness);
    });

    it('sets filter criteria correctly', async () => {
      await offlineHostListFixture.whenStable();
      expect(offlineHostList.selectedLab).toEqual(lab);
      expect(offlineHostList.selectedHostGroups).toEqual(mockHostGroups);
      expect(offlineHostList.selectedRunTargets).toEqual(mockRunTargets);
      expect(offlineHostList.selectedTestHarness).toEqual(mockTestHarness);
    });

    it('loads data correctly', async () => {
      const hostBefore = getMockLabHostInfo('host44');
      const runTargets = hostBefore!.device_count_summaries.filter(
          (x: DeviceCountSummary) => mockRunTargets.includes(x.run_target));
      const hostAfter = filterHostInfoCount(hostBefore!, runTargets);
      await offlineHostListFixture.whenStable();
      expect(offlineHostList.hostListDataSource).toEqual([hostAfter]);
    });

    it('calls createUrlTree method correctly the component is loaded',
       async () => {
         await offlineHostListFixture.whenStable();
         expect(routerSpy.createUrlTree)
             .toHaveBeenCalledWith(['offline_hosts'], {
               queryParams: {
                 lab,
                 hostGroups: mockHostGroups,
                 runTargets: mockRunTargets,
                 testHarness: mockTestHarness,
                 lastCheckInOperator: mockSelectedTimeOperator.urlId,
                 lastCheckInHours: mockInputTimeHours,
               }
             });
       });

    it('calls serialize method when the component is loaded', async () => {
      await offlineHostListFixture.whenStable();
      expect(urlSerializerSpy.serialize).toHaveBeenCalledTimes(1);
    });

    it('calls location.replaceState method when the component is loaded',
       async () => {
         await offlineHostListFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(1);
       });
  });
});
