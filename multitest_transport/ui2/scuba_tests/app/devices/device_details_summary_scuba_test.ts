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
import {DevicesModule} from 'google3/third_party/py/multitest_transport/ui2/app/devices/devices_module';
import {DevicesModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/devices/devices_module.ngsummary';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {TfcClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_client';
import {DeviceState, TestHarness} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_models';
import {UserService} from 'google3/third_party/py/multitest_transport/ui2/app/services/user_service';
import {newMockAppData, newMockLabDeviceInfo} from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_lab_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('DeviceDetailsSummary', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  beforeEach(() => {
    tfcClientSpy = jasmine.createSpyObj('tfcClient', ['getDeviceInfo']);
    userServiceSpy = jasmine.createSpyObj('userService', {
      isAdmin: true,
      isMyLab: observableOf(true),
      isAdminOrMyLab: observableOf(true),
    });
    setupModule({
      imports: [
        DevicesModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      summaries: [DevicesModuleNgSummary],
      providers: [
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: TfcClient, useValue: tfcClientSpy},
        {provide: UserService, useValue: userServiceSpy},
      ],
    });
  });

  it.async('can render page with device correctly', async () => {
    const serial = 'device1';
    const mockDeviceInfo = newMockLabDeviceInfo(serial);
    tfcClientSpy.getDeviceInfo.and.returnValue(observableOf(mockDeviceInfo));

    bootstrapTemplate(
        `<device-details-summary [id]="id"></device-details-summary>`,
        {id: serial});
    await env.verifyState(
        `device-details-summary_admin_with_device`, 'device-details-summary');
  });

  it.async(
      'can show remove button correctly when device state is Gone',
      async () => {
        const serial = 'device1';
        const hostname = 'host01';
        const hidden = false;
        const timestamp = new Date().toISOString();
        const testHarness = TestHarness.TF;
        const mockDeviceInfo = newMockLabDeviceInfo(
            serial, 0, DeviceState.GONE, hidden, hostname, timestamp,
            testHarness);
        tfcClientSpy.getDeviceInfo.and.returnValue(
            observableOf(mockDeviceInfo));

        bootstrapTemplate(
            `<device-details-summary [id]="id"></device-details-summary>`,
            {id: serial});
        await env.verifyState(
            `device-details-summary_admin_tf_with_remove_button`,
            'device-details-summary');
      });
});
