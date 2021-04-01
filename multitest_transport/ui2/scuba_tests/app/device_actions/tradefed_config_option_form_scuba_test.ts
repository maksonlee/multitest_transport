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
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {DeviceActionsModule} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module';
import {DeviceActionsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/device_actions/device_actions_module.ngsummary';
import {NameMultiValuePair} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TradefedConfigOptionForm', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
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

  it.async(`can render TradefedConfigOptionForm with empty`, async () => {
    bootstrapTemplate(
        `<tradefed-config-option-form></tradefed-config-option-form>`);
    await env.verifyState(
        `tradefed-config-option-form_with_empty`,
        'tradefed-config-option-form');
  });

  it.async(
      `can render TradefedConfigOptionForm with option values`, async () => {
        const optionValues: NameMultiValuePair[] = [
          {name: 'test1', values: ['test value1', 'test value2']},
          {name: 'test2', values: ['test value3', 'test value4']},
        ];
        bootstrapTemplate(
            `<tradefed-config-option-form [optionValues]="optionValues">
        </tradefed-config-option-form>`,
            {optionValues});
        await env.verifyState(
            `tradefed-config-option-form_with_option_values`,
            'tradefed-config-option-form');
      });
});
