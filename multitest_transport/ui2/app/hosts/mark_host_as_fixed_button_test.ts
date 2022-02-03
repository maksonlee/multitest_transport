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
import {getMockLabHostInfo, newMockAppData} from '../testing/mtt_lab_mocks';

import {HostsModule} from './hosts_module';
import {MarkHostAsFixedButton} from './mark_host_as_fixed_button';

describe('MarkHostAsFixedButton', () => {
  let markHostAsFixedButton: MarkHostAsFixedButton;
  let markHostAsFixedButtonFixture: ComponentFixture<MarkHostAsFixedButton>;
  let el: DebugElement;
  let appDataSpy: AppData;
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    appDataSpy = newMockAppData();
    tfcClientSpy = jasmine.createSpyObj(
        'tfcClient', {batchSetHostsRecoveryStates: observableOf(undefined)});

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

    markHostAsFixedButtonFixture =
        TestBed.createComponent(MarkHostAsFixedButton);
    el = markHostAsFixedButtonFixture.debugElement;
    markHostAsFixedButton = markHostAsFixedButtonFixture.componentInstance;
    markHostAsFixedButtonFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(markHostAsFixedButton).toBeTruthy();
  });

  it('should mark host as fixed correctly', () => {
    const hostname = 'host2';
    markHostAsFixedButton.host = getMockLabHostInfo(hostname)!;
    const mouseEvent = new MouseEvent('click');
    const hostRecoveryStateRequests = [
      {
        hostname,
        recovery_state: RecoveryState.FIXED,
        assignee: appDataSpy.userNickname
      } as HostRecoveryStateRequest,
    ];
    markHostAsFixedButton.toggleHostFixedState(mouseEvent);
    expect(tfcClientSpy.batchSetHostsRecoveryStates).toHaveBeenCalledTimes(1);
    expect(tfcClientSpy.batchSetHostsRecoveryStates)
        .toHaveBeenCalledWith(hostRecoveryStateRequests);
  });
});
