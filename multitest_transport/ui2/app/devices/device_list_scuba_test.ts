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

import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {of as observableOf} from 'rxjs';

import {TfcClient} from '../services/tfc_client';
import {KarmaTestEnv} from '../testing/karma_env';

import {DevicesModule} from './devices_module';
import {DevicesModuleNgSummary} from './devices_module.ngsummary';

const SCUBA_GOLDENS_PATH =
    'third_party/py/multitest_transport/ui2/app/devices/scuba_goldens';

describe('DeviceList', () => {
  const env = new KarmaTestEnv({
    scubaGoldensPath: SCUBA_GOLDENS_PATH,
    axe: true,
  });
  let tfcClient: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    tfcClient = jasmine.createSpyObj('tfcClient', ['getDeviceInfos']);
    setupModule({
      imports: [DevicesModule],
      summaries: [DevicesModuleNgSummary],
      providers: [
        {provide: TfcClient, useValue: tfcClient},
      ],
    });
  });

  it.async('can render page with device correctly', async () => {
    const device = {
      battery_level: '85',
      build_id: 'QP1A.190416.002',
      device_serial: '76397612763126391121',
      product_variant: 'Variant',
      product: 'Product',
      state: 'Available',
    };

    tfcClient.getDeviceInfos.and.returnValue(
        observableOf({device_infos: [device]}));
    bootstrapTemplate(`<device-list></device-list>`);
    await env.verifyState(`device-list_with_device`, 'device-list');
  });

  it.async(
      'can render page with devices in different battery level', async () => {
        const devices = [
          {
            device_serial: 'Unknown',
            battery_level: 'unknown',
          },
          {
            device_serial: 'Low battery',
            battery_level: '10',

          },
          {
            device_serial: 'Fully charged',
            battery_level: '100',
          },
        ];

        tfcClient.getDeviceInfos.and.returnValue(
            observableOf({device_infos: devices}));
        bootstrapTemplate(`<device-list></device-list>`);
        await env.verifyState(
            `device-list_devices_with_different_battery_level`, 'device-list');
      });

  it.async('can render page with no device found', async () => {
    tfcClient.getDeviceInfos.and.returnValue(observableOf({device_infos: []}));
    bootstrapTemplate(`<device-list></device-list>`);
    await env.verifyState(`device-list_no_device_found`, 'device-list');
  });
});
