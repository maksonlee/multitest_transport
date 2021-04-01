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

import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {HostsModule} from 'google3/third_party/py/multitest_transport/ui2/app/hosts/hosts_module';
import {HostsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/hosts/hosts_module.ngsummary';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {TfcClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_client';
import {HostState, RecoveryState, TestHarness} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_models';
import {UserService} from 'google3/third_party/py/multitest_transport/ui2/app/services/user_service';
import {DEVICE_COUNT_SUMMARIES, newMockAppData, newMockHostExtraInfo, newMockLabHostInfo} from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_lab_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('HostDetailsSummary', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  describe('Lab admin', () => {
    beforeEach(() => {
      tfcClientSpy = jasmine.createSpyObj('tfcClient', ['getHostInfo']);
      userServiceSpy = jasmine.createSpyObj('userService', {
        isAdmin: false,
        isMyLab: observableOf(true),
        isAdminOrMyLab: observableOf(true),
      });
      setupModule({
        imports: [
          HostsModule,
          NoopAnimationsModule,
          RouterTestingModule,
        ],
        summaries: [HostsModuleNgSummary],
        providers: [
          {provide: APP_DATA, useValue: newMockAppData()},
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: UserService, useValue: userServiceSpy},
        ],
      });
    });

    it.async('can render page with host correctly', async () => {
      const hostname = 'host1';
      const testHarness = TestHarness.TF;
      const hidden = false;
      const labName = 'lab1';
      const hostGroup = 'host group 1';
      const extraInfo = newMockHostExtraInfo(0);
      const assignee = 'user1';
      const pools: string[] = [];
      const mockHostsInfo = newMockLabHostInfo(
          hostname, testHarness, HostState.RUNNING, RecoveryState.UNKNOWN,
          hidden, labName, hostGroup, extraInfo, assignee,
          DEVICE_COUNT_SUMMARIES[0], pools);
      tfcClientSpy.getHostInfo.and.returnValue(observableOf(mockHostsInfo));

      bootstrapTemplate(
          `<host-details-summary [id]="id"></host-details-summary>`,
          {id: hostname});
      await env.verifyState(
          `host-details-summary_unknown_recovery`, 'host-details-summary');
    });

    it.async(
        'can show assigned to chip correctly when host recovery state is ASSIGNED',
        async () => {
          const hostname = 'host2';
          const testHarness = TestHarness.TF;
          const hidden = false;
          const labName = 'lab1';
          const hostGroup = 'host group 1';
          const extraInfo = newMockHostExtraInfo(0);
          const assignee = 'user3';
          const pools: string[] = [];
          const mockHostsInfo = newMockLabHostInfo(
              hostname, testHarness, HostState.RUNNING, RecoveryState.ASSIGNED,
              hidden, labName, hostGroup, extraInfo, assignee,
              DEVICE_COUNT_SUMMARIES[0], pools);
          tfcClientSpy.getHostInfo.and.returnValue(observableOf(mockHostsInfo));

          bootstrapTemplate(
              `<host-details-summary [id]="id"></host-details-summary>`,
              {id: hostname});
          await env.verifyState(
              `host-details-summary_admin_tf_assigned`, 'host-details-summary');
        });
  });
});
