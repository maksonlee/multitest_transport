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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {APP_DATA, AppData} from '../services';
import {TfcClient} from '../services/tfc_client';
import {HostRecoveryStateRequest, RecoveryState} from '../services/tfc_models';
import {getEl} from '../testing/jasmine_util';
import {newMockAppData} from '../testing/mtt_lab_mocks';

import {HostsMarkAsVerifiedButton} from './hosts_mark_as_verified_button';
import {HostsModule} from './hosts_module';

describe('HostsMarkAsVerifiedButton', () => {
  let hostsMarkAsVerifiedButton: HostsMarkAsVerifiedButton;
  let hostsMarkAsVerifiedButtonFixture:
      ComponentFixture<HostsMarkAsVerifiedButton>;
  let el: DebugElement;
  let appDataSpy: AppData;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    appDataSpy = newMockAppData();
    tfcClientSpy = jasmine.createSpyObj(
        'tfcClient', {batchSetHostsRecoveryStates: observableOf()});

    TestBed.configureTestingModule({
      imports: [
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {
          provide: APP_DATA,
          useValue: appDataSpy,
        },
        {
          provide: TfcClient,
          useValue: tfcClientSpy,
        },
      ],
    });

    hostsMarkAsVerifiedButtonFixture =
        TestBed.createComponent(HostsMarkAsVerifiedButton);
    el = hostsMarkAsVerifiedButtonFixture.debugElement;
    hostsMarkAsVerifiedButton =
        hostsMarkAsVerifiedButtonFixture.componentInstance;
    hostsMarkAsVerifiedButtonFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(hostsMarkAsVerifiedButton).toBeTruthy();
  });

  it('should mark selected hosts as verified recovery state correctly', () => {
    hostsMarkAsVerifiedButton.hostNames = ['host5', 'host6'];
    const hostRecoveryStateRequests = [
      {
        hostname: 'host5',
        recovery_state: RecoveryState.VERIFIED,
      } as HostRecoveryStateRequest,
      {
        hostname: 'host6',
        recovery_state: RecoveryState.VERIFIED,
      } as HostRecoveryStateRequest,
    ];
    hostsMarkAsVerifiedButtonFixture.detectChanges();
    getEl(el, '#mark-as-verified-button').click();
    expect(tfcClientSpy.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClientSpy.batchSetHostsRecoveryStates)
        .toHaveBeenCalledWith(hostRecoveryStateRequests);
  });
});
