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
import {Title} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router, UrlSerializer} from '@angular/router';
import {firstValueFrom, of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {TfcClient} from '../services/tfc_client';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {getTextContent} from '../testing/jasmine_util';
import {newMockLabInfosResponse, newMockOfflineHostInfosByLabResponse} from '../testing/mtt_lab_mocks';

import {HostsModule} from './hosts_module';
import {OfflineHostList} from './offline_host_list';
import {OfflineHostListPage} from './offline_host_list_page';

describe('OfflineHostListPage', () => {
  let offlineHostListPage: OfflineHostListPage;
  let offlineHostListPageFixture: ComponentFixture<OfflineHostListPage>;
  let el: DebugElement;
  let routerSpy: jasmine.SpyObj<Router>;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let lab: string;
  let activatedRouteSpy: ActivatedRouteStub;

  beforeEach(() => {
    lab = 'lab-1';
    const hostInfosResponse = newMockOfflineHostInfosByLabResponse(lab);
    const labInfosResponse = newMockLabInfosResponse();
    routerSpy = jasmine.createSpyObj('Router', {
      navigate: firstValueFrom(observableOf(true)),
      createUrlTree: {},
    });
    tfcClientSpy = jasmine.createSpyObj('tfcClient', {
      batchSetHostsRecoveryStates: observableOf(undefined),
      getOfflineHostInfos: observableOf(hostInfosResponse),
      getMyLabInfos: observableOf(labInfosResponse),
    });
    activatedRouteSpy = new ActivatedRouteStub();
    const locationSpy = jasmine.createSpyObj('locationSpy', ['go']);
    const urlSerializerSpy = jasmine.createSpyObj('urlSerializerSpy', {
      serialize: '',
    });

    TestBed.configureTestingModule({
      declarations: [
        OfflineHostList,
        OfflineHostListPage,
      ],
      imports: [
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        Title,
        {
          provide: Router,
          useValue: routerSpy,
        },
        {
          provide: TfcClient,
          useValue: tfcClientSpy,
        },
        {
          provide: ActivatedRoute,
          useValue: activatedRouteSpy,
        },
        {
          provide: Location,
          useValue: locationSpy,
        },
        {
          provide: UrlSerializer,
          useValue: urlSerializerSpy,
        },
        {provide: APP_DATA, useValue: 'app_test_data'},
      ],
    });
    offlineHostListPageFixture = TestBed.createComponent(OfflineHostListPage);
    el = offlineHostListPageFixture.debugElement;
    offlineHostListPage = offlineHostListPageFixture.componentInstance;
    offlineHostListPageFixture.detectChanges();
  });

  it('has a correct page title', () => {
    expect(el.injector.get(Title).getTitle())
        .toEqual('Android Test Station Lab - Offline Hosts & Devices');
  });

  it('renders header content correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Offline Hosts & Devices');
  });

  it('initializes correctly', () => {
    expect(offlineHostListPage).toBeTruthy();
  });
});
