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
import {Router} from '@angular/router';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {DevicesModule} from 'google3/third_party/py/multitest_transport/ui2/app/devices/devices_module';
import {DevicesModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/devices/devices_module.ngsummary';
import {APP_DATA} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {LabDeviceInfo} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_lab_models';
import {Notifier} from 'google3/third_party/py/multitest_transport/ui2/app/services/notifier';
import {TfcClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_client';
import {newMockAppData, newMockLabDeviceInfosResponse} from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_lab_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('DeviceListTable', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let notifierSpy: jasmine.SpyObj<Notifier>;
  let routerSpy: jasmine.SpyObj<Router>;
  let mockDeviceList: LabDeviceInfo[];

  beforeEach(() => {
    tfcClientSpy = jasmine.createSpyObj('tfcClient', {
      removeDevice: observableOf(undefined),
      batchSetDevicesRecoveryStates: observableOf(undefined)
    });

    routerSpy = jasmine.createSpyObj('Router', {
      createUrlTree: Promise.resolve(true),
      navigate: Promise.resolve(true),
      navigateByUrl: Promise.resolve(true),
      serializeUrl: Promise.resolve(true),
    });

    notifierSpy = jasmine.createSpyObj('notifier', {
      confirm: observableOf(true),  // mock confirm click in dialog.
      showMessage: observableOf({}),
      showError: observableOf({}),
    });

    window.localStorage.clear();

    setupModule({
      imports: [
        DevicesModule,
        NoopAnimationsModule,
      ],
      summaries: [DevicesModuleNgSummary],
      providers: [
        {provide: APP_DATA, useValue: newMockAppData()},
        {provide: Notifier, useValue: notifierSpy},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClientSpy},
      ],
    });
  });

  it.async('can render empty device list', async () => {
    const deviceInfos: LabDeviceInfo[] = [];

    bootstrapTemplate(
        `<device-list-table
    [dataSource]="deviceInfos"
    [isLoading]="isLoading"
  ></device-list-table>`,
        {deviceInfos, isLoading: false});
    await env.verifyState(`device-list-table_empty`, 'device-list-table');
  });

  it.async('can render device list with item', async () => {
    const hostname = 'host01';
    const hostInfo = newMockLabDeviceInfosResponse(hostname);
    mockDeviceList = hostInfo.deviceInfos!;

    bootstrapTemplate(
        `<device-list-table
    [dataSource]="deviceInfos"
    [isLoading]="isLoading"
  ></device-list-table>`,
        {deviceInfos: mockDeviceList, isLoading: false});
    await env.verifyState(`device-list-table_with_item`, 'device-list-table');
  });
});
