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
import {ComponentFixture, inject, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, convertToParamMap, Router} from '@angular/router';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {FeedbackService} from '../services/feedback_service';
import {HostSearchCriteria, SurveyTrigger} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';
import {HOST_LIST_KEY} from '../services/storage_service';
import {TfcClient} from '../services/tfc_client';
import {FilterHintType} from '../services/tfc_models';
import {DEFAULT_PAGE_SIZE} from '../shared/paginator';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getEl, getEls} from '../testing/jasmine_util';
import {newMockAppData, newMockFilterHintList, newMockLabHostInfo} from '../testing/mtt_lab_mocks';

import {HostList} from './host_list';
import {HostsModule} from './hosts_module';

describe('HostList', () => {
  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let hostList: HostList;
  let hostListFixture: ComponentFixture<HostList>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;
  let notifierSpy: jasmine.SpyObj<Notifier>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  const pageSize = 10000;
  const filterHintList = newMockFilterHintList(FilterHintType.HOST);
  const hostname = 'HOST-5';
  const filterHintType = String(FilterHintType.HOST);
  const activatedRouteSpy = new ActivatedRouteStub({
    lab: 'LAB-1',
    hostnames: ['HOST-1', 'HOST-2'],
    hostGroups: ['HOST_GROUP-1', 'HOST_GROUP-2'],
    testHarness: ['TEST_HARNESS-1', 'TEST_HARNESS-2'],
    testHarnessVersions: ['TEST_HARNESS_VERSION-1', 'TEST_HARNESS_VERSION-2'],
    pools: ['POOL-1', 'POOL-2'],
    hostStates: ['HOST_STATE-1', 'HOST_STATE-2'],
    hostListPageSize: pageSize,
  });

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    routerSpy = jasmine.createSpyObj(
        'Router',
        ['createUrlTree', 'navigate', 'navigateByUrl', 'serializeUrl']);
    routerSpy.createUrlTree.and.returnValue({});

    tfcClient = jasmine.createSpyObj('tfcClient', {
      getFilterHintList: observableOf({}),
      getHostInfos: observableOf({}),
      getLabInfo: observableOf({}),
      removeHost: observableOf({}),
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
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: FeedbackService, useValue: feedbackService},
        {provide: LOCALE_ID, useValue: 'en-US'},
        {provide: Notifier, useValue: notifierSpy},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
      ],
      });
    hostListFixture = TestBed.createComponent(HostList);
    hostListFixture.detectChanges();
    el = hostListFixture.debugElement;
    hostList = hostListFixture.componentInstance;
  });

  it('should gets initialized correctly', () => {
    expect(hostList).toBeTruthy();
  });

  it('should get queryParams correctly', () => {
    expect(hostList.paginator.pageSize).toEqual(pageSize);
  });

  it('should call the tfc client api methods correctly', async () => {
    window.sessionStorage.clear();
    await hostListFixture.whenStable();
    expect(tfcClient.getHostInfos).toHaveBeenCalledTimes(1);
    expect(tfcClient.getFilterHintList).toHaveBeenCalledTimes(8);
  });

  it('can load previous page of host list', () => {
    window.sessionStorage.clear();
    const searchCriteria = hostList.getSearchCriteria();
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    hostList.load(-1);
    expect(tfcClient.getHostInfos)
        .toHaveBeenCalledWith(searchCriteria, pageSize, 'prev', true);
  });

  it('can load next page of host list', () => {
    window.sessionStorage.clear();
    const searchCriteria = hostList.getSearchCriteria();
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    hostList.load(1);
    expect(tfcClient.getHostInfos)
        .toHaveBeenCalledWith(searchCriteria, pageSize, 'next', false);
  });

  it('can handle page size change', () => {
    window.sessionStorage.clear();
    const searchCriteria = hostList.getSearchCriteria();
    hostList.nextPageToken = 'next';
    hostList.paginator.changePageSize(20);
    expect(tfcClient.getHostInfos)
        .toHaveBeenCalledWith(searchCriteria, 20, undefined, false);
  });

  it('can update query parameters', inject([Router], (router: Router) => {
       window.sessionStorage.clear();
       tfcClient.getHostInfos.and.returnValue(observableOf(
           {host_infos: [], prevCursor: 'prev', nextCursor: 'next'}));
       hostList.load();
       expect(hostList.prevPageToken).toEqual('prev');
       expect(hostList.nextPageToken).toEqual('next');
       expect(hostList.paginator.hasPrevious).toBe(true);
       expect(hostList.paginator.hasNext).toBe(true);
       expect(router.createUrlTree).toHaveBeenCalledWith([], {
         queryParams: hostList.getQueryParamsFromOptions(),
         queryParamsHandling: 'merge'
       });
     }));


  it('should remove host correctly', () => {
    const host = 'host01';
    hostList.removeHost(host);
    expect(tfcClient.removeHost).toHaveBeenCalledWith(host);
  });

  it('can reset search steps correctly', () => {
    hostList.filterBarUtility.selectedColumn = 'A';
    hostList.filterBarUtility.isAllSelected = true;
    hostList.resetSearchSteps();
    expect(hostList.filterBarUtility.selectedColumn).toEqual('');
    expect(hostList.filterBarUtility.isAllSelected).toEqual(false);
  });

  it('gets filteredOptions correctly when calling toggleSelection with a root option',
     () => {
       const columnName = hostList.getColumnName(filterHintType);
       const hostOptions =
           hostList.convertToFilterOptions(filterHintList, filterHintType);
       hostList.filterBarUtility.appendFilterOptions(hostOptions);
       const option = hostList.filterBarUtility.getFilterOption(
           hostList.filterBarUtility.rootColumnType, columnName);

       const event = new MouseEvent('click');
       hostList.toggleSelection(event, option);
       expect(hostList.filteredOptions.length).toEqual(hostOptions.length);
     });

  it('gets selectedOption correctly when calling toggleSelection with a leaf option',
     () => {
       const columnName = hostList.getColumnName(filterHintType);
       const hostOptions =
           hostList.convertToFilterOptions(filterHintList, filterHintType);
       hostList.filterBarUtility.appendFilterOptions(hostOptions);
       const option =
           hostList.filterBarUtility.getFilterOption(columnName, hostname);
       const event = new MouseEvent('click');
       hostList.toggleSelection(event, option);
       const selectedOption = hostList.filterBarUtility.allOptions.find(
                                  x => x.value === hostname &&
                                      x.type === columnName && x.selected) ||
           undefined;
       expect(selectedOption).not.toBeUndefined();
     });

  it('gets selectedOption correctly when calling toggleSelectAll', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    hostList.filterBarUtility.displayLeafFilterOptions(columnName);
    const event = new MouseEvent('click');
    hostList.toggleSelectAll(event);
    const count = hostList.filteredOptions.filter(x => x.selected).length;
    expect(hostOptions.length).toEqual(count);
  });

  it('gets SelectedOptionString correctly when calling addExtraInfoCriteria',
     () => {
       const extraInfo = 'key:value';
       const columnName = hostList.getColumnName(filterHintType);
       const hostOptions =
           hostList.convertToFilterOptions(filterHintList, filterHintType);
       hostList.filterBarUtility.appendFilterOptions(hostOptions);
       const option =
           hostList.filterBarUtility.getFilterOption(columnName, hostname);
       const event = new MouseEvent('click');
       hostList.toggleSelection(event, option);
       hostList.addInputOption(extraInfo);
       const result = hostList.filterBarUtility.getSelectedOptionString();
       expect(result).toEqual(
           `Extra Info: (${extraInfo}) Hostname: (${hostname})`);
     });

  it('calls backToRoot correctly', () => {
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const event = new MouseEvent('click');
    hostList.backToRoot(event);
    expect(hostList.filterBarUtility.selectedColumn).toEqual('');
    expect(hostList.filteredOptions.length)
        .toEqual(hostList.filterBarUtility.filterBarColumns.length);
  });

  it('gets getRunTargets correctly', () => {
    const hostInfo = newMockLabHostInfo(hostname);
    const runTargets = hostList.getRunTargets(hostInfo);
    expect(runTargets.length).toEqual(3);
    expect(runTargets[0]).toEqual('target1');
    expect(runTargets[1]).toEqual('target2');
    expect(runTargets[2]).toEqual('target3');
  });

  it('calls resetSelection correctly', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const option =
        hostList.filterBarUtility.getFilterOption(columnName, hostname);
    const event = new MouseEvent('click');
    hostList.toggleSelection(event, option);
    hostList.resetSelection();
    const selected =
        hostList.filterBarUtility.allOptions.filter(x => x.selected).length;
    expect(selected).toEqual(0);
  });

  it('calls dispatchHandler with "Back" correctly', () => {
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    hostList.dispatchHandler(hostList.back, event);
    expect(hostList.filterBarUtility.selectedColumn).toEqual('');
    expect(hostList.filteredOptions.length)
        .toEqual(hostList.filterBarUtility.filterBarColumns.length);
  });

  it('calls dispatchHandler with "All" correctly', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);

    const option = hostList.filterBarUtility.getFilterOption(
        hostList.filterBarUtility.rootColumnType, columnName);
    const mouseEvent = new MouseEvent('click');
    hostList.toggleSelection(mouseEvent, option);

    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    hostList.dispatchHandler(hostList.all, event);
    const count = hostList.filteredOptions.filter(x => x.selected).length;
    expect(hostOptions.length).toEqual(count);
  });

  it('calls dispatchHandler with "Hostname" correctly', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    hostList.dispatchHandler(columnName, event);
    expect(hostList.filterBarUtility.selectedColumn).toEqual(columnName);
    expect(hostList.filteredOptions.length).toEqual(hostOptions.length);
  });

  it('calls dispatchHandler with "key:value" correctly', () => {
    const extraInfo = 'key:value';
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    hostList.filterBarUtility.selectedColumn = hostList.extraInfoDisplay;
    hostList.dispatchHandler(extraInfo, event);
    const result = hostList.filterBarUtility.getSelectedOptionString();
    expect(result).toEqual(`Extra Info: (${extraInfo})`);
  });

  it('calls renderSelectedOptionsAndResetFilterbar correctly', () => {
    hostList.renderSelectedOptionsAndResetFilterbar();
    expect(hostList.filterBarUtility.selectedColumn).toEqual('');
    expect(hostList.filterBarUtility.isAllSelected).toEqual(false);
  });

  it('gets getPools correctly', () => {
    const hostInfo = newMockLabHostInfo(hostname);
    const pools = hostList.getPools(hostInfo);
    expect(pools.length).toEqual(2);
    expect(pools[0]).toEqual('pool1');
    expect(pools[1]).toEqual('pool2');
  });

  it('should call getHostInfos when enter clicked', () => {
    hostList.filterBarUtility.selectedColumn = '';
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    hostList.submit(event);
    expect(tfcClient.getHostInfos).toHaveBeenCalledTimes(1);
  });

  it('saves last filter criteria into localStorage correctly', async () => {
    await hostListFixture.whenStable();

    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const option =
        hostList.filterBarUtility.getFilterOption(columnName, hostname);
    const event = new MouseEvent('click');
    hostList.toggleSelection(event, option);
    hostList.saveSearchCriteriaToLocalStorage();

    const searchCriteria =
        window.localStorage.getItem(hostList.searchCriteriaStorageKey);
    const storedObject = searchCriteria ?
        (JSON.parse(searchCriteria) as HostSearchCriteria) :
        null;
    expect(storedObject).toEqual(hostList.getSearchCriteria());
  });

  it('should hide column on view_columns dropdown menu button clicked', () => {
    getEl(el, '#view-columns-btn').click();

    const removableColumns = hostList.columns.filter((c) => c.removable);
    const column = removableColumns[0];
    getEl(el, '#' + column.fieldName + '-menu-btn').click();
    hostListFixture.detectChanges();
    el = hostListFixture.debugElement;
    expect(getEls(el, 'mat-header-cell').length)
        .toBe(hostList.columns.length - 1);
  });

  it('should detect filter changed correctly', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const option =
        hostList.filterBarUtility.getFilterOption(columnName, hostname);
    const event = new MouseEvent('click');
    hostList.toggleSelection(event, option);
    expect(hostList.filterBarUtility.filterChanged).toEqual(true);
    hostList.load();
    expect(hostList.filterBarUtility.filterChanged).toEqual(false);
  });

  it('loads extrinfo from localstorage correctly', () => {
    const extraInfo = 'key:value';
    hostList.addInputOption(extraInfo);
    hostList.saveSearchCriteriaToLocalStorage();
    expect(hostList.getSearchCriteriaFromLocalStorageByProperty(
               hostList.extraInfoParamName)[0])
        .toEqual(extraInfo);
  });

  it('calls router.navigate when open host details', () => {
    hostList.openHostDetails(hostname);
    expect(routerSpy.createUrlTree).toHaveBeenCalledWith(['/hosts', hostname]);
    expect(routerSpy.navigateByUrl).toHaveBeenCalledTimes(1);
  });

  it('loads display columns from localstorage correctly', () => {
    const event = new MouseEvent('click');
    hostList.toggleDisplayColumn(event, true, 3);
    hostList.loadDisplayColumnFromLocalStorage();
    expect(hostList.columns.filter(x => x.show).length).toEqual(13);
  });

  it('can transform input string to filter options', () => {
    const type = FilterHintType.POOL;
    const poolHints = newMockFilterHintList(type);
    const poolOptions = hostList.convertToFilterOptions(poolHints, type);
    hostList.filterBarUtility.appendFilterOptions(poolOptions);
    hostList.parseInputValue('Pool: (POOL-1 | POOL-3)');
    expect(hostList.filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(2);
  });

  it('can transform extraInfo to filter options', () => {
    const extraInfo = 'key1:value1';
    hostList.parseInputValue(`${hostList.extraInfoDisplay}: (${extraInfo})`);
    expect(hostList.filterBarUtility.allOptions
               .filter(x => x.selected && x.type === hostList.extraInfoDisplay)
               .length)
        .toEqual(1);
    expect(
        hostList.filterBarUtility.allOptions
            .filter(x => x.selected && x.type === hostList.extraInfoDisplay)[0]
            .value)
        .toEqual(extraInfo);
  });

  it('can load filterHint from sessionStorage correctly', () => {
    window.sessionStorage.clear();
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    window.sessionStorage.setItem(
        String(filterHintType), JSON.stringify(hostOptions));
    hostList.getFilterHintObservable(FilterHintType.HOST);

    expect(hostList.filterBarUtility.allOptions.length)
        .toEqual(
            hostOptions.length +
            hostList.filterBarUtility.filterBarColumns.length);
  });


  it('returns the sessionStorage key correctly', () => {
    const searchCriteria = hostList.getSearchCriteria();
    const result = `${JSON.stringify(searchCriteria)}-${
        String(hostList.getPageSize())}-${hostList.paginator.pageIndex}`;
    hostList.setSessionStorageKey();
    expect(hostList.sessionStorageKey).toEqual(result);
  });

  it('can case insensitive keyword search on the root nodes', () => {
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);

    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    hostList.formGroup.setValue({valueControl: 'hostname'});
    hostList.submit(event);
    // should list all hostOptions
    const resultOptions =
        hostList.filterBarUtility.allOptions.filter(x => !x.hidden);
    expect(resultOptions.length).toEqual(hostOptions.length);
    expect(resultOptions.every(x => x.type === 'Hostname')).toEqual(true);
  });

  it('gets the search criteria correctly', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);

    const option =
        hostList.filterBarUtility.getFilterOption(columnName, hostname);
    const event = new MouseEvent('click');
    hostList.toggleSelection(event, option);

    const searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(1);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);
  });

  it('can remove search text manually', () => {
    // edit the pool then press enter
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    const hostname2 = 'HOST-8';
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    const event = new KeyboardEvent('keydown', {key: 'Enter'});

    hostList.formGroup.setValue(
        {valueControl: `Hostname: (${hostname} | ${hostname2})`});
    hostList.submit(event);
    let searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(2);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);
    expect(searchCriteria.hostnames![1]).toEqual(hostname2);

    // step 2: edit search criteria manually
    hostList.formGroup.setValue({valueControl: `Hostname: (${hostname})`});
    hostList.submit(event);
    searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(1);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);
  });

  it('can clear search text manually', () => {
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    hostList.filterBarUtility.searchCriteriaSnapshot = '';
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    hostList.formGroup.setValue({valueControl: `Hostname: (${hostname})`});
    hostList.submit(event);
    let searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(1);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);

    // step 2 clear
    hostList.formGroup.setValue({valueControl: ''});
    hostList.submit(event);
    searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames).not.toBeDefined();
  });

  it('can add multiple search criteria manually', () => {
    const hostGroup = 'HOST_GROUP-8';
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    const hostGroupFilterHintList =
        newMockFilterHintList(FilterHintType.HOST_GROUP);
    const hostGroupOptions = hostList.convertToFilterOptions(
        hostGroupFilterHintList, FilterHintType.HOST_GROUP);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);
    hostList.filterBarUtility.appendFilterOptions(hostGroupOptions);
    hostList.filterBarUtility.searchCriteriaSnapshot = '';
    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    hostList.formGroup.setValue(
        {valueControl: `Hostname: (${hostname}) Host Group: (${hostGroup})`});
    hostList.submit(event);
    const searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(1);
    expect(searchCriteria.hostGroups!.length).toEqual(1);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);
    expect(searchCriteria.hostGroups![0]).toEqual(hostGroup);
  });

  it('can press enter key to refresh search criteria', () => {
    const columnName = hostList.getColumnName(filterHintType);
    const hostOptions =
        hostList.convertToFilterOptions(filterHintList, filterHintType);
    hostList.filterBarUtility.appendFilterOptions(hostOptions);

    const rootOption = hostList.filterBarUtility.getFilterOption(
        hostList.filterBarUtility.rootColumnType, columnName);
    const option =
        hostList.filterBarUtility.getFilterOption(columnName, hostname);

    const event = new KeyboardEvent('keydown', {key: 'Enter'});
    hostList.toggleSelection(event, rootOption);
    hostList.toggleSelection(event, option);
    hostList.submit(event);
    const searchCriteria = hostList.getSearchCriteria();
    expect(searchCriteria.hostnames!.length).toEqual(1);
    expect(searchCriteria.hostnames![0]).toEqual(hostname);
  });

  it('should reflect the column name on search criteria string right after the column is selected',
     () => {
       const columnName = hostList.getColumnName(filterHintType);
       const hostOptions =
           hostList.convertToFilterOptions(filterHintList, filterHintType);
       hostList.filterBarUtility.appendFilterOptions(hostOptions);
       const option = hostList.filterBarUtility.getFilterOption(
           hostList.filterBarUtility.rootColumnType, columnName);
       const event = new MouseEvent('click');
       hostList.toggleSelection(event, option);
       expect(hostList.filterBarUtility.searchCriteriaSnapshot)
           .toEqual(' Hostname:');
     });

  it('should not use page token when search criteria changed', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    tfcClient.getHostInfos.calls.reset();
    window.sessionStorage.clear();
    hostList.load();
    expect(tfcClient.getHostInfos)
        .toHaveBeenCalledWith(
            hostList.getSearchCriteria(), pageSize, undefined, false);
  });

  it('should call HaTS client on host filter correctly', () => {
    hostList.startHostFilterBarHats();
    expect(feedbackService.startSurvey)
        .toHaveBeenCalledWith(SurveyTrigger.HOST_FILTER_BAR);
  });

  it('can load pageSize from queryParams correctly', () => {
    expect(hostList.paginator.pageSize).toEqual(pageSize);
  });

  it('calls the getHostInfos api when the refresh button clicked', () => {
    tfcClient.getHostInfos.calls.reset();
    getEl(el, '.refresh-button').click();
    expect(tfcClient.getHostInfos).toHaveBeenCalledTimes(1);
  });

  it('calls with pageToken when the queryParam has the value', () => {
    tfcClient.getHostInfos.calls.reset();
    window.sessionStorage.clear();
    const pageToken = 'token';
    const queryParams = {
      hostListPageToken: pageToken,
    };
    hostList.updatePaginatorParamsAndLoad(convertToParamMap(queryParams));
    expect(tfcClient.getHostInfos)
        .toHaveBeenCalledWith(
            hostList.getSearchCriteria(), DEFAULT_PAGE_SIZE, pageToken);
  });

  it('returns prevPageToken when getPageToken(-1)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(-1)).toEqual(hostList.prevPageToken);
  });

  it('returns nextPageToken when getPageToken(1)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(1)).toEqual(hostList.nextPageToken);
  });

  it('returns undefined when getPageToken(0)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(0)).toBeUndefined();
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(-1, true)).toEqual(hostList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(1, true)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(1, true)).toEqual(hostList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    hostList.prevPageToken = 'prev';
    hostList.nextPageToken = 'next';
    expect(hostList.getPageToken(0, true)).toEqual(hostList.prevPageToken);
  });

  it('should store hostname list in local storage correctly', () => {
    hostList.storeHostNamesInLocalStorage();
    const data = window.localStorage.getItem(HOST_LIST_KEY);
    expect(data).toBeDefined();

    const hostnames = JSON.parse(data!) as string[];
    expect(hostnames.length)
        .toEqual(hostList.dataSource.map(x => x.hostname).length);
  });

  it('should disable load selected values from localStorage with queryString',
     () => {
       expect(hostList.hasQueryStringParams(convertToParamMap({test: 'value'})))
           .toBeTrue();
       expect(
           hostList.filterBarUtility.allOptions.filter(x => x.selected).length)
           .toEqual(0);
     });

  it('should enable load selected values from localStorage without queryString',
     () => {
       expect(hostList.hasQueryStringParams(convertToParamMap({}))).toBeFalse();
     });
});
