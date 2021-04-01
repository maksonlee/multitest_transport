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

import {DOCUMENT, Location} from '@angular/common';
import {DebugElement, ElementRef} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {Title} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router, UrlSerializer} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA, AppData} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {ALL_OPTIONS_VALUE, OfflineHostFilterParams, SurveyTrigger} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {TimeFilterOperator} from '../shared/time_input_filter';
import {UserService} from '../services/user_service';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getTextContent} from '../testing/jasmine_util';
import {newMockAppData, newMockLabAssignedHostInfosByLabResponse, newMockLabInfosResponse, newMockLabOfflineHostInfosByLabResponse} from '../testing/mtt_lab_mocks';

import {HostsModule} from './hosts_module';
import {HostsModuleNgSummary} from './hosts_module.ngsummary';
import {OfflineHostAssignmentsPage} from './offline_host_assignments_page';

describe('OfflineHostAssignmentsPage', () => {
  let offlineHostAssignmentsPage: OfflineHostAssignmentsPage;
  let offlineHostAssignmentsPageFixture:
      ComponentFixture<OfflineHostAssignmentsPage>;
  let el: DebugElement;
  let mockAppData: AppData;
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let urlSerializerSpy: jasmine.SpyObj<UrlSerializer>;
  let locationSpy: jasmine.SpyObj<Location>;
  let userServiceSpy: jasmine.SpyObj<UserService>;
  let lab: string;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', {
      createUrlTree: Promise.resolve(true),
      navigate: Promise.resolve(true),
      navigateByUrl: Promise.resolve(true),
      serializeUrl: Promise.resolve(true),
    });
    locationSpy = jasmine.createSpyObj('locationSpy', ['replaceState']);
    urlSerializerSpy =
        jasmine.createSpyObj('urlSerializerSpy', {serialize: ''});
    mockAppData = newMockAppData(true, 'user1');
  });

  describe('default url', () => {
    beforeEach(() => {
      lab = 'lab-1';
      feedbackService =
          jasmine.createSpyObj('feedbackService', ['startSurvey']);
      const hostInfosResponse = newMockLabOfflineHostInfosByLabResponse(lab);
      const assignedHostInfosResponse =
          newMockLabAssignedHostInfosByLabResponse(lab);
      const labInfosResponse = newMockLabInfosResponse();
      const activatedRouteSpy = new ActivatedRouteStub({});
      tfcClientSpy = jasmine.createSpyObj('tfcClient', {
        batchSetHostsRecoveryStates: observableOf(undefined),
        getOfflineHostInfos: observableOf(hostInfosResponse),
        getMyLabInfos: observableOf(labInfosResponse),
        getAssignedHostsInfos: observableOf(assignedHostInfosResponse),
      });
      userServiceSpy = jasmine.createSpyObj('userService', {
        isAdmin: true,
        isAdminOrMyLab: true,
      });

      TestBed.configureTestingModule({
        declarations: [
          OfflineHostAssignmentsPage,
        ],
        imports: [
          HostsModule,
          NoopAnimationsModule,
        ],
        aotSummaries: HostsModuleNgSummary,
        providers: [
          Title,
          {provide: ActivatedRoute, useValue: activatedRouteSpy},
          {provide: APP_DATA, useValue: mockAppData},
          {provide: DOCUMENT, useValue: document},
          {provide: ElementRef, useValue: {}},
          {provide: FeedbackService, useValue: feedbackService},
          {provide: Location, useValue: locationSpy},
          {provide: Router, useValue: routerSpy},
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: UrlSerializer, useValue: urlSerializerSpy},
          {provide: UserService, useValue: userServiceSpy},
        ],
      });
      offlineHostAssignmentsPageFixture =
          TestBed.createComponent(OfflineHostAssignmentsPage);
      el = offlineHostAssignmentsPageFixture.debugElement;
      offlineHostAssignmentsPage =
          offlineHostAssignmentsPageFixture.componentInstance;
      offlineHostAssignmentsPageFixture.detectChanges();
    });

    it('has a correct page title', () => {
      expect(el.injector.get(Title).getTitle())
          .toEqual('Android Test Station Lab - Offline Host Assignments');
    });

    it('renders header content correctly', () => {
      const textContent = getTextContent(el);
      expect(textContent).toContain('Offline Host Assignments');
    });

    it('initializes correctly', () => {
      expect(offlineHostAssignmentsPage).toBeTruthy();
    });

    it('renders the headers of panels correctly', () => {
      const textContent = getTextContent(el);
      expect(textContent).toContain('Hosts assigned to me');
      expect(textContent).toContain('Hosts assigned to others');
      expect(textContent).toContain('All unassigned offline hosts');
    });

    it('calls getMyLabInfos api when the component loaded', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      expect(tfcClientSpy.getMyLabInfos).toHaveBeenCalledTimes(1);
    });

    it('calls getHostInfos api when the component loaded', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(1);
    });

    it('loads data correctly when specifying a lab', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      const mockSelectedLab = 'lab-3';
      const offlineHostInfosResponse =
          newMockLabOfflineHostInfosByLabResponse(mockSelectedLab);
      const assignedHostInfosResponse =
          newMockLabAssignedHostInfosByLabResponse(mockSelectedLab);

      tfcClientSpy.getOfflineHostInfos.and.returnValue(
          observableOf(offlineHostInfosResponse));
      tfcClientSpy.getAssignedHostsInfos.and.returnValue(
          observableOf(assignedHostInfosResponse));

      offlineHostAssignmentsPage.selectedLab = mockSelectedLab;
      offlineHostAssignmentsPage.refresh();
      await offlineHostAssignmentsPageFixture.whenStable();

      const hosts = offlineHostAssignmentsPage.offlineHosts;
      expect(hosts.length).toEqual(9);
      expect(offlineHostAssignmentsPage.totalDeviceCountSummary).toEqual({
        offlineDevices: 45,
        allDevices: 90,
      });
    });

    it('calls tfcClient methods when calling assignToMe', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(1);
      const hosts = offlineHostAssignmentsPage.unassignedHostListDataSource.map(
          host => host.hostname);
      offlineHostAssignmentsPage.assignToMe(hosts);
      expect(tfcClientSpy.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(2);
    });

    it('calls getOfflineHostInfos api when calling refresh', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      offlineHostAssignmentsPage.refresh();
      await offlineHostAssignmentsPageFixture.whenStable();
      expect(tfcClientSpy.getOfflineHostInfos).toHaveBeenCalledTimes(2);
      expect(tfcClientSpy.getAssignedHostsInfos).toHaveBeenCalledTimes(2);
    });

    it('saves last filter criteria into localStorage correctly', async () => {
      await offlineHostAssignmentsPageFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedHostGroups = ['host group-2'];
      const mockSelectedRunTargets = ['target4'];
      const mockSelectedTestHarness = 'MH';
      const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
      const mockInputTimeHours = 5;

      offlineHostAssignmentsPage.selectedLab = mockSelectedLab;
      await offlineHostAssignmentsPageFixture.whenStable();

      offlineHostAssignmentsPage.selectedHostGroups = mockSelectedHostGroups;
      offlineHostAssignmentsPage.selectedRunTargets = mockSelectedRunTargets;
      offlineHostAssignmentsPage.selectedTestHarness = mockSelectedTestHarness;
      offlineHostAssignmentsPage.lastCheckInOperator = mockSelectedTimeOperator;
      offlineHostAssignmentsPage.lastCheckInHours = mockInputTimeHours;

      offlineHostAssignmentsPage.updateLocalStorage();

      const storedText = window.localStorage.getItem(
          offlineHostAssignmentsPage.FILTER_CRITERIA_STORAGE_KEY);
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
      await offlineHostAssignmentsPageFixture.whenStable();
      const mockSelectedLab = 'lab-2';
      const mockSelectedHostGroups = ['host group-2'];
      const mockSelectedRunTargets = ['target4'];
      const mockSelectedTestHarness = 'MH';
      const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
      const mockInputTimeHours = 5;

      offlineHostAssignmentsPage.selectedLab = mockSelectedLab;
      await offlineHostAssignmentsPageFixture.whenStable();

      offlineHostAssignmentsPage.selectedHostGroups = mockSelectedHostGroups;
      offlineHostAssignmentsPage.selectedRunTargets = mockSelectedRunTargets;
      offlineHostAssignmentsPage.selectedTestHarness = mockSelectedTestHarness;
      offlineHostAssignmentsPage.lastCheckInOperator = mockSelectedTimeOperator;
      offlineHostAssignmentsPage.lastCheckInHours = mockInputTimeHours;

      offlineHostAssignmentsPage.updateLocalStorage();

      const storedData = offlineHostAssignmentsPage.loadFromLocalStorage();

      expect(storedData).toEqual({
        lab: mockSelectedLab,
        hostGroups: mockSelectedHostGroups,
        runTargets: mockSelectedRunTargets,
        testHarness: mockSelectedTestHarness,
        lastCheckInOperator: mockSelectedTimeOperator.urlId,
        lastCheckInHours: mockInputTimeHours,
      });
    });

    it('should contains hosts without device under it when "All" options are selected for run targets',
       async () => {
         await offlineHostAssignmentsPageFixture.whenStable();
         const mockSelectedLab = 'lab-1';
         const mockSelectedHostGroups = [ALL_OPTIONS_VALUE];
         const mockSelectedRunTargets = [ALL_OPTIONS_VALUE];
         const mockSelectedTestHarness = ALL_OPTIONS_VALUE;
         const mockSelectedTimeOperator = TimeFilterOperator.GREATER_THAN;
         const mockInputTimeHours = 5;

         offlineHostAssignmentsPage.selectedLab = mockSelectedLab;
         await offlineHostAssignmentsPageFixture.whenStable();

         offlineHostAssignmentsPage.selectedHostGroups = mockSelectedHostGroups;
         offlineHostAssignmentsPage.selectedRunTargets = mockSelectedRunTargets;
         offlineHostAssignmentsPage.selectedTestHarness =
             mockSelectedTestHarness;
         offlineHostAssignmentsPage.lastCheckInOperator =
             mockSelectedTimeOperator;
         offlineHostAssignmentsPage.lastCheckInHours = mockInputTimeHours;

         const hostWithoutDevice =
             offlineHostAssignmentsPage.assignedHosts.find(
                 (x) => x.device_count_summaries.length === 0);

         offlineHostAssignmentsPage.filterHostListsDataSources();

         expect(offlineHostAssignmentsPage.assignedOthersHostListDataSource.map(
                    (x) => x.hostname))
             .toContain(hostWithoutDevice!.hostname);
       });

    it('calls location.replaceState method when the component is loaded',
       async () => {
         await offlineHostAssignmentsPageFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(1);
       });

    it(`calls location.replaceState method when the run target is changed by the user`,
       async () => {
         await offlineHostAssignmentsPageFixture.whenStable();
         const mockSelectedRunTargets = ['target1'];
         offlineHostAssignmentsPage.selectedRunTargets = mockSelectedRunTargets;
         offlineHostAssignmentsPage.reloadHosts();
         await offlineHostAssignmentsPageFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(2);
       });

    it('calls location.replaceState method when the lab is changed by the user',
       async () => {
         await offlineHostAssignmentsPageFixture.whenStable();
         offlineHostAssignmentsPage.selectedLab = 'lab-2';
         offlineHostAssignmentsPage.refresh();
         await offlineHostAssignmentsPageFixture.whenStable();
         expect(locationSpy.replaceState).toHaveBeenCalledTimes(2);
       });

    it('should call HaTS client on change device sort correctly', () => {
      offlineHostAssignmentsPage.startChangeSortHats();
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.SORT_HOST_DATA);
    });

    it('should call HaTS client on offline host assignment correctly', () => {
      offlineHostAssignmentsPage.startOfflineHostAssignmentHats();
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.OFFLINE_HOST_ASSIGNMENT);
    });

    it('should call searchable filter HaTS client correctly', () => {
      offlineHostAssignmentsPage.startSearchableFilterHats();
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.SEARCHABLE_FILTER);
    });
  });
});
