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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {SortDirection} from '@angular/material/sort';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {Router} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA, AppData} from '../services';
import {HOST_LIST_KEY} from '../services/storage_service';
import {TfcClient} from '../services/tfc_client';
import {HostRecoveryStateRequest, RecoveryState} from '../services/tfc_models';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {getMockLabHostInfo, newMockAppData, newMockLabHostInfosResponse} from '../testing/mtt_lab_mocks';

import {HostListTable} from './host_list_table';
import {HostsModule} from './hosts_module';

describe('HostListTable', () => {
  let hostListTable: HostListTable;
  let hostListTableFixture: ComponentFixture<HostListTable>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;
  let mockAppData: AppData;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', {
      createUrlTree: Promise.resolve(true),
      navigate: Promise.resolve(true),
      navigateByUrl: Promise.resolve(true),
      serializeUrl: Promise.resolve(true),
    });

    mockAppData = newMockAppData();
    tfcClientSpy = jasmine.createSpyObj(
        'tfcClient', {batchSetHostsRecoveryStates: observableOf(undefined)});
    TestBed.configureTestingModule({
      imports: [
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: APP_DATA, useValue: mockAppData},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClientSpy},
      ],
    });

    hostListTableFixture = TestBed.createComponent(HostListTable);
    el = hostListTableFixture.debugElement;
    hostListTable = hostListTableFixture.componentInstance;
    hostListTable.selectable = true;
    hostListTableFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(hostListTable).toBeTruthy();
  });

  it('shows aria-label correctly', () => {
    const checkbox = getEl(el, 'mat-checkbox');
    expect(checkbox).toBeTruthy();
    expect(checkbox.getAttribute('aria-label')).toBe('Select all hosts');
  });

  it('correctly displays a given empty list', () => {
    hostListTable.dataSource = [];
    hostListTableFixture.detectChanges();
    expect(getTextContent(el)).toContain('No hosts found.');
  });

  it('correctly displays a given host list', () => {
    const mockHosts = newMockLabHostInfosResponse().host_infos!;
    hostListTable.dataSource = mockHosts;
    hostListTableFixture.detectChanges();
    expect(getTextContent(el)).toContain(mockHosts[0].hostname);
  });

  it('displays correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Host list');
  });

  it(`resets the order of rowIdFieldAllValues correctly after sorting the 
     hostname`,
     fakeAsync(() => {
       spyOn(hostListTable.tableRowsSelectManager, 'resetPrevClickedRowIndex');
       const mockHosts = newMockLabHostInfosResponse().host_infos!.slice(0, 12);
       const expectedRowIdFieldAllValues = [
         'host1', 'host10', 'host11', 'host12', 'host2', 'host3', 'host4',
         'host5', 'host6', 'host7', 'host8', 'host9'
       ];
       hostListTable.dataSource = mockHosts;
       hostListTable.ngOnChanges(
           {dataSource: new SimpleChange(null, mockHosts, true)});
       hostListTableFixture.detectChanges();
       tick();
       expect(hostListTable.tableRowsSelectManager.resetPrevClickedRowIndex)
           .toHaveBeenCalledTimes(1);

       const sortColumn = 'hostname';
       const sortDirection: SortDirection = 'asc';
       hostListTable.matSort.active = sortColumn;
       hostListTable.matSort.direction = sortDirection;

       hostListTable.tableDataSource.sortData(
           hostListTable.tableDataSource.data, hostListTable.matSort);

       expect(hostListTable.tableRowsSelectManager.rowIdFieldAllValues)
           .toEqual(expectedRowIdFieldAllValues);
       expect(hostListTable.tableRowsSelectManager.resetPrevClickedRowIndex)
           .toHaveBeenCalledTimes(2);
     }));

  it(`calls resetSelection method correctly while the host number has changed`,
     fakeAsync(() => {
       spyOn(hostListTable.tableRowsSelectManager, 'resetSelection');
       spyOn(hostListTable.tableRowsSelectManager.selectionChange, 'emit');
       const mockHosts = newMockLabHostInfosResponse().host_infos!;
       hostListTable.dataSource = mockHosts;
       hostListTable.ngOnChanges(
           {dataSource: new SimpleChange(null, mockHosts, true)});
       hostListTableFixture.detectChanges();
       tick();

       hostListTable.tableRowsSelectManager.selection.select(
           ...mockHosts.map(v => v.hostname));

       const newMockHosts = mockHosts.filter(v => v.lab_name === 'lab-1');
       const expectedNumber = newMockHosts.length;
       hostListTable.dataSource = newMockHosts;
       hostListTable.ngOnChanges(
           {dataSource: new SimpleChange(null, newMockHosts, true)});
       hostListTableFixture.detectChanges();
       tick();

       expect(hostListTable.tableRowsSelectManager.rowIdFieldAllValues.length)
           .toEqual(expectedNumber);
       expect(hostListTable.tableRowsSelectManager.resetSelection)
           .toHaveBeenCalledTimes(2);
     }));

  it('can sort correctly', () => {
    const sortColumn = 'hostname';
    const sortDirection: SortDirection = 'desc';
    const sort = {active: sortColumn, direction: sortDirection};
    hostListTable.changeSort(sort);
    expect(hostListTable.matSort.active).toEqual(sortColumn);
    expect(hostListTable.matSort.direction).toEqual(sortDirection);
  });

  it('returns offline devices alert icon name correctly', () => {
    const host3 = getMockLabHostInfo('host3')!;
    const host28 = getMockLabHostInfo('host28')!;
    const host30 = getMockLabHostInfo('host30')!;
    expect(hostListTable.getOfflineDevicesAlertIcon(host3)).toEqual('disabled');
    expect(hostListTable.getOfflineDevicesAlertIcon(host28)).toEqual('error');
    expect(hostListTable.getOfflineDevicesAlertIcon(host30)).toEqual('warning');
  });

  it('returns host overall alert icon name correctly', () => {
    const host45 = getMockLabHostInfo('host45')!;
    const host6 = getMockLabHostInfo('host6')!;
    const host28 = getMockLabHostInfo('host28')!;
    expect(hostListTable.getHostOverallAlertIcon(host45)).toEqual('disabled');
    expect(hostListTable.getHostOverallAlertIcon(host6)).toEqual('warning');
    expect(hostListTable.getHostOverallAlertIcon(host28)).toEqual('warning');
  });

  it('gets sorting data correctly', () => {
    const host3 = getMockLabHostInfo('host3')!;
    expect(hostListTable.getSortingData(host3, 'last_checkin'))
        .toEqual(Date.parse(host3.timestamp));
    expect(hostListTable.getSortingData(host3, 'lastRecoveryTime'))
        .toEqual(Date.parse(host3.lastRecoveryTime));
    expect(hostListTable.getSortingData(host3, 'hostname'))
        .toEqual(host3.hostname);
    expect(hostListTable.getSortingData(host3, 'host_state'))
        .toEqual(host3.host_state);
    expect(hostListTable.getSortingData(host3, 'assignee'))
        .toEqual(host3.assignee);
    expect(hostListTable.getSortingData(host3, 'host_group'))
        .toEqual(host3.host_group);
    expect(hostListTable.getSortingData(host3, 'hostOverallState'))
        .toEqual(hostListTable.getHostOverallAlertIcon(host3));
    expect(hostListTable.getSortingData(host3, 'recoveryState'))
        .toEqual(host3.recoveryState);
    expect(hostListTable.getSortingData(host3, 'others')).toEqual('');
  });

  it('navigates correctly when calling openHostDetails', () => {
    const mouseEvent = new MouseEvent('click');
    const hostname = 'host1';
    const mockHosts = newMockLabHostInfosResponse().host_infos!;
    hostListTable.dataSource = mockHosts;
    hostListTable.openHostDetails(hostname, mouseEvent);
    expect(routerSpy.createUrlTree).toHaveBeenCalledWith(['/hosts', hostname]);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledTimes(1);
  });

  it('call tfcClient correctly when calling toggleHostFixedState', () => {
    const host = getMockLabHostInfo('host2')!;
    const mouseEvent = new MouseEvent('click');
    const hostRecoveryStateRequests = [{
      hostname: host.hostname,
      recovery_state: RecoveryState.FIXED,
      assignee: mockAppData.userNickname
    } as HostRecoveryStateRequest];
    spyOn(hostListTable.removeHostFromList, 'emit');

    hostListTable.toggleHostFixedState(host, mouseEvent);
    expect(tfcClientSpy.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClientSpy.batchSetHostsRecoveryStates)
        .toHaveBeenCalledWith(hostRecoveryStateRequests);
    expect(hostListTable.removeHostFromList.emit).toHaveBeenCalledWith(host);
  });

  it('should store hostname list in local storage correctly', () => {
    hostListTable.storeHostNamesInLocalStorage();
    const data = window.localStorage.getItem(HOST_LIST_KEY);
    expect(data).toBeDefined();

    const hostnames = JSON.parse(data!) as string[];
    expect(hostnames.length)
        .toEqual(hostListTable.dataSource.map(x => x.hostname).length);
  });
});
