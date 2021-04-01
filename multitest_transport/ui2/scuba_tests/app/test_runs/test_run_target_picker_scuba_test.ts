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
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {TfcClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_client';
import {TestRunsModule} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module';
import {TestRunsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('TestRunTargetPicker', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,  // TODO Color constrast violation
  });
  let tfcClient: jasmine.SpyObj<TfcClient>;
  const device = {
    build_id: 'QP1A.190416.002',
    device_serial: 'test1',
    hostname: 'test.hostname.com',
    product_variant: 'Variant',
    product: 'Product',
    state: 'Available',
  };
  tfcClient = jasmine.createSpyObj('tfcClient', ['getDeviceInfos']);
  tfcClient.getDeviceInfos.and.returnValue(
      observableOf({device_infos: [device]}));

  beforeEach(() => {
    setupModule({
      imports: [
        TestRunsModule,
        NoopAnimationsModule,
      ],
      summaries: [TestRunsModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: {}},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });
  });
  it.async(`can render TestRunTargetPicker`, async () => {
    bootstrapTemplate(`<test-run-target-picker></test-run-target-picker>`);
    await env.verifyState(`test-run-target-picker`, 'test-run-target-picker');
  });

  it.async(`can render TestRunTargetPicker with manual editing`, async () => {
    bootstrapTemplate(`<test-run-target-picker></test-run-target-picker>`);
    getEl('.manualDeviceSpecsCheckbox .mat-checkbox-input').click();
    flush();
    await env.verifyState(
        `test-run-target-picker_with_manual_editing`, 'test-run-target-picker');
  });

  it.async(`can render TestRunTargetPicker with device specs`, async () => {
    const deviceSpecs = ['device_serial:test1'];
    bootstrapTemplate(
        `<test-run-target-picker [deviceSpecs]="deviceSpecs"></test-run-target-picker>`,
        {deviceSpecs});
    getEl('.manualDeviceSpecsCheckbox .mat-checkbox-input').click();
    flush();
    await env.verifyState(
        `test-run-target-picker_with_run_target`, 'test-run-target-picker');
  });
});
