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
import {DebugElement, LOCALE_ID, SimpleChange} from '@angular/core';
import {ComponentFixture, inject, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {DEVICE_SERIAL, DeviceSearchCriteria, HOSTNAME, LabDeviceInfosResponse, SurveyTrigger} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';
import {DEVICE_LIST_KEY} from '../services/storage_service';
import {TfcClient} from '../services/tfc_client';
import {DeviceRecoveryStateRequest, FilterHintType, NoteList, RecoveryState} from '../services/tfc_models';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockAppData, newMockDeviceNote, newMockFilterHintList, newMockLabDeviceInfo, newMockLabDeviceInfosResponse} from '../testing/mtt_lab_mocks';

import {DeviceList} from './device_list';
import {DevicesModule} from './devices_module';

describe('DeviceList', () => {
  let deviceList: DeviceList;
  let deviceListFixture: ComponentFixture<DeviceList>;
  let el: DebugElement;
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let notifierSpy: jasmine.SpyObj<Notifier>;

  const pageSize = 10000;
  const activatedRouteSpy =
      new ActivatedRouteStub({deviceListPageSize: pageSize});
  const filterHintList = newMockFilterHintList(FilterHintType.POOL);
  const pool = 'POOL-3';
  const filterHintType = String(FilterHintType.POOL);
  const appData = newMockAppData();

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['createUrlTree', 'navigate', 'navigateByUrl', 'serializeUrl']);
    routerSpy.createUrlTree.and.returnValue({});

    tfcClient = jasmine.createSpyObj('tfcClient', {
      queryDeviceInfos: observableOf({}),
      removeDevice: observableOf({}),
      getFilterHintList: observableOf({}),
      batchGetDevicesLatestNotes: observableOf({}),
      batchSetDevicesRecoveryStates: observableOf(undefined),
    });

    notifierSpy = jasmine.createSpyObj('notifier', {
      confirm: observableOf(true),  // mock confirm click in dialog.
      showMessage: observableOf({}),
      showError: observableOf({}),
    });

    window.localStorage.clear();
    window.sessionStorage.clear();

    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        DevicesModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: APP_DATA, useValue: appData},
        {provide: FeedbackService, useValue: feedbackService},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: Notifier, useValue: notifierSpy},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
      ],
      });
    deviceListFixture = TestBed.createComponent(DeviceList);
    deviceListFixture.detectChanges();
    el = deviceListFixture.debugElement;
    deviceList = deviceListFixture.componentInstance;
  });

  it('should gets initialized correctly', () => {
    expect(deviceList).toBeTruthy();
  });

  it('should call the tfc client api methods correctly', async () => {
    window.sessionStorage.clear();
    await deviceListFixture.whenStable();
    expect(tfcClient.queryDeviceInfos).toHaveBeenCalledTimes(1);
    expect(tfcClient.getFilterHintList).toHaveBeenCalledTimes(7);
    expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
  });

  it('can load previous page of device list', () => {
    window.sessionStorage.clear();
    const searchCriteria = deviceList.getSearchCriteria();
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    deviceList.load(-1);
    expect(tfcClient.queryDeviceInfos)
        .toHaveBeenCalledWith(searchCriteria, pageSize, 'prev', true);
  });

  it('can load next page of device list', () => {
    window.sessionStorage.clear();
    const searchCriteria = deviceList.getSearchCriteria();
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    deviceList.load(1);
    expect(tfcClient.queryDeviceInfos)
        .toHaveBeenCalledWith(searchCriteria, pageSize, 'next', false);
  });

  it('can handle page size change', () => {
    window.sessionStorage.clear();
    const searchCriteria = deviceList.getSearchCriteria();
    deviceList.nextPageToken = 'next';
    deviceList.paginator.changePageSize(20);
    expect(tfcClient.queryDeviceInfos)
        .toHaveBeenCalledWith(searchCriteria, 20, undefined, false);
  });

  it('can update pagination parameters', inject([Router], (router: Router) => {
       window.sessionStorage.clear();
       tfcClient.queryDeviceInfos.and.returnValue(observableOf(
           {deviceInfos: [], prevCursor: 'prev', nextCursor: 'next'}));
       deviceList.load();
       expect(deviceList.prevPageToken).toEqual('prev');
       expect(deviceList.nextPageToken).toEqual('next');
       expect(deviceList.paginator.hasPrevious).toBe(true);
       expect(deviceList.paginator.hasNext).toBe(true);
       expect(router.createUrlTree).toHaveBeenCalledWith([], {
         queryParams: deviceList.getQueryParamsFromOptions(),
         queryParamsHandling: 'merge'
       });
     }));

  it('should remove device correctly', () => {
    const device = 'device01';
    const hostname = 'host01';
    deviceList.removeDevice(device, hostname);
    expect(tfcClient.removeDevice).toHaveBeenCalledWith(device, hostname);
  });

  it('can reset search steps correctly', () => {
    deviceList.filterBarUtility.selectedColumn = 'A';
    deviceList.filterBarUtility.isAllSelected = true;
    deviceList.resetSearchSteps();
    expect(deviceList.filterBarUtility.selectedColumn).toEqual('');
    expect(deviceList.filterBarUtility.isAllSelected).toEqual(false);
  });

  it('gets filteredOptions correctly when calling toggleSelection with a root option',
     () => {
       const columnName = deviceList.getColumnName(filterHintType);
       const poolOptions =
           deviceList.convertToFilterOptions(filterHintList, filterHintType);
       deviceList.filterBarUtility.appendFilterOptions(poolOptions);
       const option = deviceList.getFilterOption(
           deviceList.filterBarUtility.rootColumnType, columnName);

       const event = new MouseEvent('click');
       deviceList.toggleSelection(event, option);
       expect(deviceList.filteredOptions.length).toEqual(poolOptions.length);
     });

  it('gets selectedOption correctly when calling toggleSelection with a leaf option',
     () => {
       const columnName = deviceList.getColumnName(filterHintType);
       const poolOptions =
           deviceList.convertToFilterOptions(filterHintList, filterHintType);
       deviceList.filterBarUtility.appendFilterOptions(poolOptions);
       const option = deviceList.getFilterOption(columnName, pool);
       const event = new MouseEvent('click');
       deviceList.toggleSelection(event, option);
       const selectedOption =
           deviceList.filterBarUtility.allOptions.find(
               x => x.value === pool && x.type === columnName && x.selected) ||
           undefined;
       expect(selectedOption).not.toBeUndefined();
     });

  it('gets selectedOption correctly when calling toggleSelectAll', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.filterBarUtility.displayLeafFilterOptions(columnName);
    const event = new MouseEvent('click');
    deviceList.toggleSelectAll(event);
    const count = deviceList.filteredOptions.filter(x => x.selected).length;
    expect(poolOptions.length).toEqual(count);
  });

  it('gets SelectedOptionString correctly when calling addExtraInfoCriteria',
     () => {
       const extraInfo = 'key:value';
       const columnName = deviceList.getColumnName(filterHintType);
       const poolOptions =
           deviceList.convertToFilterOptions(filterHintList, filterHintType);
       deviceList.filterBarUtility.appendFilterOptions(poolOptions);
       const option = deviceList.getFilterOption(columnName, pool);
       const event = new MouseEvent('click');
       deviceList.toggleSelection(event, option);
       deviceList.addInputOption(extraInfo, deviceList.extraInfoDisplay);
       const result = deviceList.filterBarUtility.getSelectedOptionString();
       expect(result).toEqual(`Extra Info: (${extraInfo}) Pool: (${pool})`);
     });

  it('gets SelectedOptionString correctly when calling addDeviceSerial', () => {
    const deviceSerial = 'device01';
    deviceList.addInputOption(deviceSerial, deviceList.deviceSerialDisplay);
    const result = deviceList.filterBarUtility.getSelectedOptionString();
    expect(result).toEqual(
        `${deviceList.deviceSerialDisplay}: (${deviceSerial})`);
  });

  it('calls backToRoot correctly', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const event = new MouseEvent('click');
    deviceList.backToRoot(event);
    expect(deviceList.filterBarUtility.selectedColumn).toEqual('');
    expect(deviceList.filteredOptions.length)
        .toEqual(deviceList.filterBarUtility.filterBarColumns.length);
  });

  it('calls resetSelection correctly', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const option = deviceList.getFilterOption(columnName, pool);
    const event = new MouseEvent('click');
    deviceList.toggleSelection(event, option);
    deviceList.resetSelection();
    const selected =
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length;
    expect(selected).toEqual(0);
  });

  it('calls dispatchHandler with "Back" correctly', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    deviceList.dispatchHandler(deviceList.back, event);
    expect(deviceList.filterBarUtility.selectedColumn).toEqual('');
    expect(deviceList.filteredOptions.length)
        .toEqual(deviceList.filterBarUtility.filterBarColumns.length);
  });

  it('calls dispatchHandler with "All" correctly', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);

    const option = deviceList.getFilterOption(
        deviceList.filterBarUtility.rootColumnType, columnName);
    const mouseEvent = new MouseEvent('click');
    deviceList.toggleSelection(mouseEvent, option);

    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    deviceList.dispatchHandler(deviceList.allOptionsValue, event);
    const count = deviceList.filteredOptions.filter(x => x.selected).length;
    expect(poolOptions.length).toEqual(count);
  });

  it('calls dispatchHandler with "Hostname" correctly', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    deviceList.dispatchHandler(columnName, event);
    expect(deviceList.filterBarUtility.selectedColumn).toEqual(columnName);
    expect(deviceList.filteredOptions.length).toEqual(poolOptions.length);
  });

  it('calls dispatchHandler with "key:value" correctly', () => {
    const extraInfo = 'key:value';
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    deviceList.filterBarUtility.selectedColumn = deviceList.extraInfoDisplay;
    deviceList.dispatchHandler(extraInfo, event);
    const result = deviceList.filterBarUtility.getSelectedOptionString();
    expect(result).toEqual(`Extra Info: (${extraInfo})`);
  });

  it('calls renderSelectedOptionsAndResetFilterbar correctly', () => {
    deviceList.renderSelectedOptionsAndResetFilterbar();
    expect(deviceList.filterBarUtility.selectedColumn).toEqual('');
    expect(deviceList.filterBarUtility.isAllSelected).toEqual(false);
  });

  it('gets SelectedOptionString correctly when no option selected', () => {
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.submit(event);
    expect(deviceList.filterBarUtility.getSelectedOptionString()).toEqual('');
  });

  it('gets SelectedOptionString correctly when the option selected', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const option = deviceList.getFilterOption(columnName, pool);
    const mouseEvent = new MouseEvent('click');
    deviceList.toggleSelection(mouseEvent, option);

    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.submit(event);
    expect(deviceList.filterBarUtility.getSelectedOptionString())
        .toEqual(`Pool: (${pool})`);
  });

  it('saves last filter criteria into localStorage correctly', async () => {
    await deviceListFixture.whenStable();

    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const option = deviceList.getFilterOption(columnName, pool);
    const event = new MouseEvent('click');
    deviceList.toggleSelection(event, option);
    deviceList.saveSearchCriteriaToLocalStorage();

    const searchCriteria =
        window.localStorage.getItem(deviceList.searchCriteriaStorageKey);
    const storedObject = searchCriteria ?
        (JSON.parse(searchCriteria) as DeviceSearchCriteria) :
        null;
    expect(storedObject).toEqual(deviceList.getSearchCriteria());
  });

  it('should hide column on view_columns dropdown when menu button clicked',
     () => {
       getEl(el, '#view-columns-btn').click();

       const removableColumns = deviceList.columns.filter((c) => c.removable);
       const column = removableColumns[0];
       getEl(el, '#' + column.fieldName + '-menu-btn').click();
       deviceListFixture.detectChanges();
       el = deviceListFixture.debugElement;
       expect(getEls(el, 'mat-header-cell').length)
           .toEqual(deviceList.columns.length - 1);
     });

  it('calls router.navigate when open device details', () => {
    const device = 'device1';
    deviceList.openDeviceDetails(device);
    expect(routerSpy.createUrlTree).toHaveBeenCalledWith(['/devices', device]);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledTimes(1);
  });

  it('loads display columns from localstorage correctly', () => {
    const event = new MouseEvent('click');
    deviceList.toggleDisplayColumn(event, true, 3);
    deviceList.loadDisplayColumnFromLocalStorage();
    expect(deviceList.columns.filter(x => x.show).length)
        .toEqual(deviceList.columns.length - 1);
  });

  it('can transform input string to filter options', () => {
    const type = FilterHintType.POOL;
    const poolHints = newMockFilterHintList(type);
    const poolOptions = deviceList.convertToFilterOptions(poolHints, type);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.parseInputValue('Pool: (POOL-1 | POOL-3)');
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(2);
  });

  it('can transform adding input string to filter options', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.parseInputValue('Pool: (POOL-1 | POOL-3)');
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(2);
    deviceList.parseInputValue('Pool: (POOL-1 | POOL-3 | POOL-4)');
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(3);
  });

  it('can transform removing input string to filter options', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.parseInputValue('Pool: (POOL-1 | POOL-3)');
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(2);
    deviceList.parseInputValue('Pool: (POOL-3)');
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(1);
  });

  it('can transform extraInfo to filter options', () => {
    const extraInfo = 'key1:value1';
    deviceList.parseInputValue(
        `${deviceList.extraInfoDisplay}: (${extraInfo})`);
    expect(
        deviceList.filterBarUtility.allOptions
            .filter(x => x.selected && x.type === deviceList.extraInfoDisplay)
            .length)
        .toEqual(1);
    expect(deviceList.filterBarUtility.allOptions
               .filter(
                   x => x.selected && x.type === deviceList.extraInfoDisplay)[0]
               .value)
        .toEqual(extraInfo);
  });

  it('can transform extraInfo to filter options when remove a column', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const extraInfo = 'key1:value1';
    deviceList.parseInputValue(`Pool: (POOL-1 | POOL-3) ${
        deviceList.extraInfoDisplay}: (${extraInfo})`);
    expect(
        deviceList.filterBarUtility.allOptions
            .filter(x => x.selected && x.type === deviceList.extraInfoDisplay)
            .length)
        .toEqual(1);
    expect(deviceList.filterBarUtility.allOptions
               .filter(
                   x => x.selected && x.type === deviceList.extraInfoDisplay)[0]
               .value)
        .toEqual(extraInfo);
    deviceList.parseInputValue(`Pool: (POOL-1 | POOL-3)`);
    expect(
        deviceList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(2);
    expect(
        deviceList.filterBarUtility.allOptions
            .filter(x => x.selected && x.type === deviceList.extraInfoDisplay)
            .length)
        .toEqual(0);
  });

  it('can load filterHint from localStorage correctly', () => {
    window.localStorage.clear();
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    window.localStorage.setItem(
        String(filterHintType), JSON.stringify(poolOptions));
    deviceList.getFilterHintObservable(FilterHintType.POOL);

    expect(deviceList.filterBarUtility.allOptions.length)
        .toEqual(
            poolOptions.length +
            deviceList.filterBarUtility.filterBarColumns.length);
  });

  it('can sync filter options from api correctly', () => {
    const returns = {
      filter_hints: [{value: 'lab-1'}, {value: 'lab-2'}, {value: 'lab-3'}]
    };
    const filterHintType = FilterHintType.LAB;
    const columnName = deviceList.getColumnName(filterHintType);
    tfcClient.getFilterHintList.calls.reset();
    tfcClient.getFilterHintList.and.returnValue(observableOf(returns));
    deviceList.getFilterHintObservable(filterHintType).subscribe();
    const options = deviceList.convertToFilterOptions(returns, filterHintType);
    expect(deviceList.filterBarUtility.allOptions.filter(
               x => x.type === columnName))
        .toEqual(options);
  });

  it('returns the sessionStorage key correctly', () => {
    const searchCriteria = deviceList.getSearchCriteria();
    const result = `${JSON.stringify(searchCriteria)}-${
        String(deviceList.getPageSize())}-${
        String(deviceList.paginator.pageIndex)}`;
    deviceList.setSessionStorageKey();
    expect(deviceList.sessionStorageKey).toEqual(result);
  });

  it('can case insensitive keyword search on the root nodes', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.formGroup.setValue({valueControl: 'pool'});
    deviceList.submit(event);
    // should list all poolOptions
    const resultOptions =
        deviceList.filterBarUtility.allOptions.filter(x => !x.hidden);
    expect(resultOptions.length).toEqual(poolOptions.length);
    expect(resultOptions.every(x => x.type === 'Pool')).toEqual(true);
  });

  it('gets the search criteria correctly', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);

    const option = deviceList.getFilterOption(columnName, pool);
    const event = new MouseEvent('click');
    deviceList.toggleSelection(event, option);

    const searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(1);
    expect(searchCriteria.pools![0]).toEqual(pool);
  });

  it('can remove search text manually', () => {
    // edit the pool then press enter
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    const pool2 = 'POOL-5';
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const event = new KeyboardEvent('keydown', {key: 'Enter'});

    deviceList.formGroup.setValue({valueControl: `Pool: (${pool} | ${pool2})`});
    deviceList.submit(event);
    let searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(2);
    expect(searchCriteria.pools![0]).toEqual(pool);
    expect(searchCriteria.pools![1]).toEqual(pool2);

    // step 2: edit search criteria manually
    deviceList.formGroup.setValue({valueControl: `Pool: (${pool})`});
    deviceList.submit(event);
    searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(1);
    expect(searchCriteria.pools![0]).toEqual(pool);
  });

  it('can clear search text manually', () => {
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.filterBarUtility.searchCriteriaSnapshot = '';
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.formGroup.setValue({valueControl: `Pool: (${pool})`});
    deviceList.submit(event);
    let searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(1);
    expect(searchCriteria.pools![0]).toEqual(pool);

    // step 2 clear
    deviceList.formGroup.setValue({valueControl: ''});
    deviceList.submit(event);
    searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools).not.toBeDefined();
  });

  it('can add multiple search criteria manually', () => {
    const hostGroup = 'HOST_GROUP-8';
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    const hostGroupFilterHintList =
        newMockFilterHintList(FilterHintType.HOST_GROUP);
    const hostGroupOptions = deviceList.convertToFilterOptions(
        hostGroupFilterHintList, FilterHintType.HOST_GROUP);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    deviceList.filterBarUtility.appendFilterOptions(hostGroupOptions);

    deviceList.filterBarUtility.searchCriteriaSnapshot = '';
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.formGroup.setValue(
        {valueControl: `Pool: (${pool}) Host Group: (${hostGroup})`});
    deviceList.submit(event);

    const searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(1);
    expect(searchCriteria.hostGroups!.length).toEqual(1);
    expect(searchCriteria.pools![0]).toEqual(pool);
    expect(searchCriteria.hostGroups![0]).toEqual(hostGroup);
  });

  it('can press enter key to refrsh search criteria', () => {
    const columnName = deviceList.getColumnName(filterHintType);
    const poolOptions =
        deviceList.convertToFilterOptions(filterHintList, filterHintType);
    deviceList.filterBarUtility.appendFilterOptions(poolOptions);
    const rootOption = deviceList.getFilterOption(
        deviceList.filterBarUtility.selectedColumn, 'Pool');
    const option = deviceList.getFilterOption(columnName, pool);

    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    deviceList.toggleSelection(event, rootOption);
    deviceList.toggleSelection(event, option);
    deviceList.submit(event);
    const searchCriteria = deviceList.getSearchCriteria();
    expect(searchCriteria.pools!.length).toEqual(1);
    expect(searchCriteria.pools![0]).toEqual(pool);
  });

  it('should reflect the column name on search criteria string right after the column is selected',
     () => {
       const columnName = deviceList.getColumnName(filterHintType);
       const poolOptions =
           deviceList.convertToFilterOptions(filterHintList, filterHintType);
       deviceList.filterBarUtility.appendFilterOptions(poolOptions);

       const option = deviceList.getFilterOption(
           deviceList.filterBarUtility.rootColumnType, columnName);
       const event = new MouseEvent('click');
       deviceList.toggleSelection(event, option);
       expect(deviceList.filterBarUtility.searchCriteriaSnapshot)
           .toEqual(' Pool:');
     });

  it('should not use page token when search criteria changed', () => {
    tfcClient.queryDeviceInfos.calls.reset();
    window.sessionStorage.clear();
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    deviceList.load();
    expect(tfcClient.queryDeviceInfos)
        .toHaveBeenCalledWith(
            deviceList.getSearchCriteria(), pageSize, undefined, false);
  });

  it('should update notes to sessionStorage', () => {
    window.sessionStorage.clear();
    const deviceSerial = 'device1';
    const labDeviceInfosResponse = newMockLabDeviceInfosResponse();
    const note = newMockDeviceNote(1, deviceSerial);
    const noteList = {
      notes: [note],
      prev_cursor: '',
      next_cursor: '',
    };
    deviceList.dataSource = labDeviceInfosResponse.deviceInfos || [];
    deviceList.setSessionStorageKey();
    deviceList.setDeviceNotes(noteList);
    const value =
        window.sessionStorage.getItem(deviceList.sessionStorageKey) || '';
    const result = JSON.parse(value) as LabDeviceInfosResponse;
    const deviceInfos = result.deviceInfos || [];
    expect(deviceInfos.find(x => x.device_serial === 'device1')?.note)
        .toEqual(note);
  });

  it('should get latest notes for devices correctly', () => {
    (tfcClient.batchGetDevicesLatestNotes as jasmine.Spy).calls.reset();
    const deviceSerial = 'device1';
    const note = newMockDeviceNote(
        0, deviceSerial, 'message1', 'reason1', 'action1',
        new Date().toISOString(), 'user1');
    tfcClient.batchGetDevicesLatestNotes.and.returnValue(observableOf({
      notes: [note],
      prev_cursor: '',
      next_cursor: '',
    } as NoteList));
    const deviceInfosResponse = newMockLabDeviceInfosResponse();

    deviceList.dataSource = deviceInfosResponse.deviceInfos || [];
    deviceList.loadDeviceNotes([deviceSerial]);
    expect(tfcClient.batchGetDevicesLatestNotes).toHaveBeenCalledTimes(1);
    expect(deviceList.dataSource[0].note).toEqual(note);
  });

  it('should call survey on batch add devices notes', () => {
    deviceList.startBatchAddDevicesNotesHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.BATCH_ADD_DEVICES_NOTES);
  });

  it('should call survey on view devices columns correctly', () => {
    deviceList.startViewDevicesColumnsHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.VIEW_DEVICES_COLUMNS);
  });

  it('should call survey on device filter correctly', () => {
    deviceList.startDeviceFilterBarHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.DEVICE_FILTER_BAR);
  });

  it('can load pageSize from queryParams correctly', () => {
    expect(deviceList.paginator.pageSize).toEqual(pageSize);
  });

  it('call tfcClient correctly when calling toggleDeviceFixedState', () => {
    const deviceInfosResponse = newMockLabDeviceInfosResponse();
    const mockDeviceList = deviceInfosResponse.deviceInfos || [];
    const device = mockDeviceList[0];
    const mouseEvent = new MouseEvent('click');
    const deviceRecoveryStateRequests = [{
      hostname: device.hostname,
      device_serial: device.device_serial,
      recovery_state: RecoveryState.FIXED,
    } as DeviceRecoveryStateRequest];
    deviceList.toggleDeviceFixedState(device, mouseEvent);

    expect(tfcClient.batchSetDevicesRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClient.batchSetDevicesRecoveryStates)
        .toHaveBeenCalledWith(deviceRecoveryStateRequests);
  });

  it('should call the queryDeviceInfos api when the refresh button clicked',
     () => {
       tfcClient.queryDeviceInfos.calls.reset();
       getEl(el, '.refresh-button').click();
       expect(tfcClient.queryDeviceInfos).toHaveBeenCalledTimes(1);
     });

  it('calls getLogUrl and returns correctly', () => {
    const url = `http://server01/hostname:${HOSTNAME}%20s%2F${DEVICE_SERIAL}`;
    deviceList.logUrl = url;
    const device = 'device01';
    const deviceInfo = newMockLabDeviceInfo(device);
    const logUrl = deviceList.getLogUrl(deviceInfo);
    expect(logUrl).toEqual(
        url.replace(HOSTNAME, deviceInfo.hostname || '')
            .replace(DEVICE_SERIAL, deviceInfo.device_serial));
  });

  it('calls with pageToken when the queryParam has the value', () => {
    tfcClient.queryDeviceInfos.calls.reset();
    window.sessionStorage.clear();
    const pageToken = 'token';
    const queryParams = {
      deviceListPageToken: pageToken,
      deviceListPageSize: pageSize,
    };
    deviceList.urlParams = convertToParamMap(queryParams);
    deviceList.updatePaginatorParamsAndLoad();
    expect(tfcClient.queryDeviceInfos)
        .toHaveBeenCalledWith(
            deviceList.getSearchCriteria(), pageSize, pageToken);
  });

  it('should disable load selected values from localStorage with queryString',
     () => {
       expect(deviceList.hasQueryStringParams()).toBeTrue();
       expect(deviceList.filterBarUtility.allOptions.filter(x => x.selected)
                  .length)
           .toEqual(0);
     });

  it('should enable load selected values from localStorage without queryString',
     () => {
       deviceList.urlParams = convertToParamMap({});
       expect(deviceList.hasQueryStringParams()).toBeFalse();
     });
});

describe('DeviceList in ATS instance', () => {
  let deviceList: DeviceList;
  let deviceListFixture: ComponentFixture<DeviceList>;
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;
  const pageSize = 10000;
  const activatedRouteSpy =
      new ActivatedRouteStub({deviceListPageSize: pageSize});

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['createUrlTree', 'navigate', 'navigateByUrl', 'serializeUrl']);
    routerSpy.createUrlTree.and.returnValue({});
    tfcClient = jasmine.createSpyObj('tfcClient', {
      queryDeviceInfos: observableOf({}),
      removeDevice: observableOf({}),
      getFilterHintList: observableOf({}),
      batchGetDevicesLatestNotes: observableOf({}),
      batchSetDevicesRecoveryStates: observableOf(undefined),
    });
    window.localStorage.clear();
    window.sessionStorage.clear();

    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        DevicesModule,
        NoopAnimationsModule,
      ],
      providers: [
        {
          provide: APP_DATA,
          useValue: {isAtsLabInstance: false},
        },
        {provide: FeedbackService, useValue: feedbackService},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
        {
          provide: ActivatedRoute,
          useValue: activatedRouteSpy,
        },
      ],
      });
    deviceListFixture = TestBed.createComponent(DeviceList);
    deviceListFixture.detectChanges();
    deviceList = deviceListFixture.componentInstance;
    el = deviceListFixture.debugElement;
  });

  it('displays the 9 columns correctly', () => {
    expect(deviceList.columns.length).toEqual(9);
  });

  it('should call the queryDeviceInfos api with includeOfflineDevices=false',
     () => {
       const searchCriteria = deviceList.getSearchCriteria();
       searchCriteria.includeOfflineDevices = false;
       expect(tfcClient.queryDeviceInfos)
           .toHaveBeenCalledWith(searchCriteria, pageSize, '');
     });


  it('returns prevPageToken when getPageToken(-1)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(-1)).toEqual(deviceList.prevPageToken);
  });

  it('returns nextPageToken when getPageToken(1)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(1)).toEqual(deviceList.nextPageToken);
  });

  it('returns undefined when getPageToken(0)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(0)).toBeUndefined();
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(-1, true)).toEqual(deviceList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(1, true)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(1, true)).toEqual(deviceList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    deviceList.prevPageToken = 'prev';
    deviceList.nextPageToken = 'next';
    expect(deviceList.getPageToken(0, true)).toEqual(deviceList.prevPageToken);
  });

  it('should store device serial list in local storage correctly', () => {
    deviceList.storeDeviceSerialsInLocalStorage();
    const data = window.localStorage.getItem(DEVICE_LIST_KEY);
    expect(data).toBeDefined();

    const deviceSerials = JSON.parse(data!) as string[];
    expect(deviceSerials.length)
        .toEqual(deviceList.dataSource.map(x => x.device_serial).length);
  });

  it('should be able to show the notes button', () => {
    expect(getTextContent(el)).not.toContain('Add notes');
    deviceList.notesEnabled = true;
    deviceListFixture.detectChanges();
    el = deviceListFixture.debugElement;
    expect(getTextContent(el)).toContain('Add notes');
  });

  it('validates input devices if validation is enabled', () => {
    deviceList.validationEnabled = true;
    // Two devices are initially selected, but only device-2 is valid.
    deviceList.initialSelection = ['device-1', 'device-2'];
    tfcClient.queryDeviceInfos.and.returnValue(
        observableOf({deviceInfos: [{device_serial: 'device-2'}]}));
    deviceList.ngOnChanges({'initialSelection': {} as SimpleChange});
    deviceListFixture.detectChanges();
    // Device validity was checked and device-1 was automatically unselected.
    const query: DeviceSearchCriteria = {
      deviceSerial: ['device-1', 'device-2'],
      includeOfflineDevices: false,  // ATS doesn't include offline devices.
    };
    expect(tfcClient.queryDeviceInfos).toHaveBeenCalledWith(query, 2);
    expect(deviceList.selectedSerials).toEqual(['device-2']);
  });
});
