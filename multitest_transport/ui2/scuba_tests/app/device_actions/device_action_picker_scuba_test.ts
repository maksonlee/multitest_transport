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
import {beforeEach, bootstrapTemplate, describe, flush, getEl, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {DeviceActionsModule} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module';
import {DeviceActionsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module.ngsummary';
import {DeviceAction} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('DeviceActionPicker', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,  // TODO Color contrast violation
  });

  beforeEach(() => {
    setupModule({
      imports: [
        DeviceActionsModule,
        NoopAnimationsModule,
      ],
      summaries: [DeviceActionsModuleNgSummary],
    });
  });

  it.async(`can render DeviceActionPicker with empty`, async () => {
    bootstrapTemplate(`<device-action-picker
                      [deviceActions]="[]"
                      [selectedDeviceActions]="[]">
                      </device-action-picker>`);
    await env.verifyState(
        `device-action-picker_with_empty`, 'device-action-picker');
  });

  it.async(`can render DeviceActionPicker with items`, async () => {
    const deviceActions: DeviceAction[] = [
      {id: 'testid1', name: 'testname1'},
      {id: 'testid2', name: 'testname2'},
    ];
    const selectedDeviceActions: DeviceAction[] = [
      {id: 'testid1', name: 'testname1'},
    ];
    bootstrapTemplate(
        `<device-action-picker
                      [deviceActions]="deviceActions"
                      [selectedDeviceActions]="selectedDeviceActions">
                      </device-action-picker>`,
        {deviceActions, selectedDeviceActions});
    await env.verifyState(
        `device-action-picker_with_items`, 'device-action-picker');
  });

  it.async(`can render DeviceActionPicker with menu`, async () => {
    const deviceActions: DeviceAction[] = [
      {id: 'testid1', name: 'testname1'},
      {id: 'testid2', name: 'testname2'},
    ];
    const selectedDeviceActions: DeviceAction[] = [
      {id: 'testid1', name: 'testname1'},
    ];
    // Set height to 500px due to screen cut off for menu pop up
    bootstrapTemplate(
        `<device-action-picker
                      style="height: 500px"
                      [deviceActions]="deviceActions"
                      [selectedDeviceActions]="selectedDeviceActions">
                      </device-action-picker>`,
        {deviceActions, selectedDeviceActions});

    getEl('.add-button').click();
    flush();
    await env.verifyState(
        `device-action-picker_with_menu`, 'device-action-picker');
  });
});
