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
import {ActivatedRoute} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {ALL_OPTIONS_VALUE} from '../hosts/offline_host_filter';
import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {TfcClient} from '../services/tfc_client';
import {HostRecoveryStateRequest, HostState, RecoveryState, TestHarness} from '../services/tfc_models';
import {UserService} from '../services/user_service';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockAppData, newMockLabHostInfo, newMockLabHostInfosResponse} from '../testing/mtt_lab_mocks';

import {RecoveryHostList} from './recovery_host_list';
import {RecoveryModule} from './recovery_module';

describe('RecoveryHostList', () => {
  const hostInfosResponse = newMockLabHostInfosResponse();

  let el: DebugElement;
  let recoveryHostList: RecoveryHostList;
  let recoveryHostListFixture: ComponentFixture<RecoveryHostList>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  const labName = 'lab1';

  beforeEach(() => {
    const activatedRouteSpy = new ActivatedRouteStub({});
    tfcClient = jasmine.createSpyObj('tfcClient', [
      'batchSetHostsRecoveryStates', 'getMyRecoveryHostInfos', 'getHostNotes'
    ]);
    tfcClient.getMyRecoveryHostInfos.and.returnValue(
        observableOf(hostInfosResponse));
    tfcClient.batchSetHostsRecoveryStates.and.returnValue(observableOf());
    tfcClient.getHostNotes.and.returnValue(observableOf({}));

    userServiceSpy = jasmine.createSpyObj('userService', {
      isAdmin: true,
      isMyLab: observableOf(true),
      isAdminOrMyLab: observableOf(true),
    });

    TestBed.configureTestingModule({
      imports: [
        RecoveryModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: FeedbackService},
        {provide: TfcClient, useValue: tfcClient},
        {provide: UserService, useValue: userServiceSpy},
      ],
    });

    recoveryHostListFixture = TestBed.createComponent(RecoveryHostList);
    el = recoveryHostListFixture.debugElement;
    recoveryHostList = recoveryHostListFixture.componentInstance;
    recoveryHostList.hostInfos = hostInfosResponse.host_infos!;
    recoveryHostListFixture.detectChanges();
  });

  afterEach(() => {
    recoveryHostListFixture.destroy();
  });

  it('should get initialized correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Hosts');
    expect(recoveryHostList).toBeTruthy();
  });

  it('should display lab name correctly', () => {
    recoveryHostList.selectedLab = labName;
    recoveryHostListFixture.detectChanges();
    const textContent = getTextContent(el);
    expect(textContent).toContain(`Lab: ${recoveryHostList.selectedLab}`);
  });

  it('infosToHostNameMap should converts host info lists correctly', () => {
    const host1 =
        newMockLabHostInfo('host1', TestHarness.TF, HostState.RUNNING);
    const result = recoveryHostList.infosToHostNameMap([host1]);
    expect(result[host1.hostname]).toBe(host1);
  });

  it('infosToHostNameMap should handles empty lists', () => {
    const result = recoveryHostList.infosToHostNameMap([]);
    expect(result).toEqual({});
  });

  it('should call the tfc client api method getMyRecoveryHostInfos correctly',
     async () => {
       await recoveryHostListFixture.whenStable();
       expect(tfcClient.getMyRecoveryHostInfos).toHaveBeenCalledTimes(1);
     });

  it('should refresh host list correctly on refresh button clicked', () => {
    // Reset called count.
    getEl(el, '#refresh-button').click();
    expect(tfcClient.getMyRecoveryHostInfos).toHaveBeenCalledTimes(1);
  });

  it('focus host should unselect all host and display collapse columns', () => {
    const hostName = recoveryHostList.hostInfos[0].hostname;
    spyOn(recoveryHostList.focusedHostNameChange, 'emit');
    recoveryHostList.focusHost(hostName);
    expect(recoveryHostList.selection.selected.length).toEqual(0);
    recoveryHostList.ngOnChanges({
      focusedHostName:
          new SimpleChange(null, recoveryHostList.focusedHostName, true)
    });
    expect(recoveryHostList.displayColumns)
        .toEqual(recoveryHostList.collapseDisplayColumns);
    expect(recoveryHostList.focusedHostNameChange.emit).toHaveBeenCalled();
    expect(recoveryHostList.focusedHostNameChange.emit)
        .toHaveBeenCalledWith(hostName);
  });

  it('onSelectionChange should remove/add hostName in selection', () => {
    const hostName = recoveryHostList.hostInfos[0].hostname;
    spyOn(recoveryHostList.selectionChange, 'emit');
    spyOn(recoveryHostList.focusedHostNameChange, 'emit');

    // Select host.
    recoveryHostList.onSelectionChange(hostName);
    expect(recoveryHostList.selection.selected).toContain(hostName);
    expect(recoveryHostList.focusedHostName).toEqual('');
    expect(recoveryHostList.focusedHostNameChange.emit)
        .toHaveBeenCalledTimes(1);
    expect(recoveryHostList.selectionChange.emit).toHaveBeenCalledTimes(1);

    // Unselect host.
    recoveryHostList.onSelectionChange(hostName);
    expect(recoveryHostList.selection.selected).not.toContain(hostName);
    expect(recoveryHostList.selectionChange.emit).toHaveBeenCalledTimes(2);
  });

  it('should select all and unselect all correctly', () => {
    spyOn(recoveryHostList.selectionChange, 'emit');

    // Select all hosts.
    recoveryHostList.toggleSelection();
    expect(recoveryHostList.isAllSelected()).toBe(true);
    expect(recoveryHostList.selectionChange.emit)
        .toHaveBeenCalledWith(
            recoveryHostList.hostInfos.map(hostInfo => hostInfo.hostname));

    // Unselect all hosts.
    recoveryHostList.toggleSelection();
    expect(recoveryHostList.isAllSelected()).toBe(false);
    expect(recoveryHostList.selectionChange.emit).toHaveBeenCalledWith([]);
  });

  it('function hasSelectedHostName should return the correct value', () => {
    recoveryHostList.hostNameMap =
        recoveryHostList.infosToHostNameMap(recoveryHostList.hostInfos);
    const hostName = recoveryHostList.hostInfos[0].hostname;

    // Select host.
    recoveryHostList.onSelectionChange(hostName);
    expect(recoveryHostList.hasSelectedHostName()).toBe(true);

    // Unselect host.
    recoveryHostList.onSelectionChange(hostName);
    expect(recoveryHostList.hasSelectedHostName()).toBe(false);
  });

  it('should mark selected hosts as done recovery state correctly', () => {
    recoveryHostList.toggleSelection();
    recoveryHostListFixture.detectChanges();
    getEl(el, '#mark-selection-recovered-button').click();
    expect(tfcClient.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClient.batchSetHostsRecoveryStates)
        .toHaveBeenCalledWith(recoveryHostList.hostInfos.map(hostInfo => {
          return {
            hostname: hostInfo.hostname,
            recovery_state: RecoveryState.VERIFIED,
          } as HostRecoveryStateRequest;
        }));
  });

  it('should mark focused host as done recovery state correctly', () => {
    const focusedHostName = recoveryHostList.hostInfos[0].hostname;
    recoveryHostList.focusedHostName = focusedHostName;
    const hostRecoveryStateRequests = [{
      hostname: focusedHostName,
      recovery_state: RecoveryState.VERIFIED,
    } as HostRecoveryStateRequest];
    recoveryHostList.selection.clear();
    recoveryHostListFixture.detectChanges();
    getEl(el, '#mark-selection-recovered-button').click();
    expect(tfcClient.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClient.batchSetHostsRecoveryStates)
        .toHaveBeenCalledWith(hostRecoveryStateRequests);
  });

  it('should display correct text in host group chip', () => {
    // If exists an 'All' in the selected host group, should display 'All'.
    recoveryHostList.selectedHostGroups = [ALL_OPTIONS_VALUE];
    expect(recoveryHostList.multiSelectedDisplay(
               recoveryHostList.selectedHostGroups))
        .toBe(ALL_OPTIONS_VALUE);

    // No selected host group should display 'All'.
    recoveryHostList.selectedHostGroups = [];
    expect(recoveryHostList.multiSelectedDisplay(
               recoveryHostList.selectedHostGroups))
        .toBe(ALL_OPTIONS_VALUE);

    // Only one host group selected should display the group name.
    recoveryHostList.selectedHostGroups = ['group1'];
    expect(recoveryHostList.multiSelectedDisplay(
               recoveryHostList.selectedHostGroups))
        .toBe(recoveryHostList.selectedHostGroups[0]);

    // Multiple host groups are selected should display selected number 'n
    // selected'.
    recoveryHostList.selectedHostGroups = ['group1', 'group2'];
    expect(recoveryHostList.multiSelectedDisplay(
               recoveryHostList.selectedHostGroups))
        .toMatch('^[0-9]* selected$');
    expect(recoveryHostList.multiSelectedDisplay(
               recoveryHostList.selectedHostGroups))
        .toBe(`${recoveryHostList.selectedHostGroups.length} selected`);
  });

  it('opens note editor dialog in create mode correctly', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    const mockClickEvent = new MouseEvent('click');

    // Trigger open editor dialog.
    recoveryHostList.openHostNoteCreateEditor(mockClickEvent, ['host01']);
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });

  it('opens note editor dialog in edit mode correctly', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    const mockClickEvent = new MouseEvent('click');

    // Trigger open editor dialog.
    recoveryHostList.openHostNoteUpdateEditor(mockClickEvent, 'host01');
    expect(dialog.open).toHaveBeenCalledTimes(1);
    expect(tfcClient.getHostNotes).toHaveBeenCalledTimes(1);
  });

  it('opens host details dialog correctly', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    const mockClickEvent = new MouseEvent('click');

    // Trigger open host details dialog.
    recoveryHostList.openHostDetails(mockClickEvent, 'host01');
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });
});
