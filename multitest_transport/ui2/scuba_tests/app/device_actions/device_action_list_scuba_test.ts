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
import {DeviceActionsModule} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module';
import {DeviceActionsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module.ngsummary';
import {DeviceActionList} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {MttObjectMap, MttObjectMapService, newMttObjectMap} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_object_map';
import * as mttMocks from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('DeviceActionList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttObjectMapService: jasmine.SpyObj<MttObjectMapService>;
  let mttObjectMap: MttObjectMap;

  beforeEach(() => {
    mttObjectMap = newMttObjectMap();
    mttObjectMapService =
        jasmine.createSpyObj('mttObjectMapService', ['getMttObjectMap']);
    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(mttObjectMap));

    setupModule({
      imports: [
        DeviceActionsModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: MttObjectMapService, useValue: mttObjectMapService},
      ],
      summaries: [DeviceActionsModuleNgSummary],
    });
  });

  it.async(`can render DeviceActionList with empty`, async () => {
    const deviceActionList: DeviceActionList = {device_actions: []};
    bootstrapTemplate(`<device-action-list></device-action-list>`);
    await env.verifyState(
        `device-action-list_with_empty`, 'device-action-list');
  });

  it.async(`can render DeviceActionList with items`, async () => {
    const FACTORY_RESET_ACTION =
        mttMocks.newMockDeviceAction('reset', 'Factory Reset');
    const NAMESPACED_ACTION =
        mttMocks.newMockDeviceAction('ns1::action', 'Namespaced Action');
    const MISSING_NAMESPACE_ACTION =
        mttMocks.newMockDeviceAction('ns2::action', 'Missing Namespace Action');
    const CONFIG_SET_MAP = {
      ns1: mttMocks.newMockConfigSetInfo('ns1', 'Namespace 1'),
    };

    mttObjectMap = newMttObjectMap();
    mttObjectMap.deviceActionMap = {
      'reset': FACTORY_RESET_ACTION,
      'ns1::action': NAMESPACED_ACTION,
      'ns2::action': MISSING_NAMESPACE_ACTION,
    };
    mttObjectMap.configSetInfoMap = CONFIG_SET_MAP;

    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(mttObjectMap));

    bootstrapTemplate(`<device-action-list></device-action-list>`);
    await env.verifyState(
        `device-action-list_with_items`, 'device-action-list');
  });
});
