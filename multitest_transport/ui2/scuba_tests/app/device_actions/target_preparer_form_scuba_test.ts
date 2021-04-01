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
import {TradefedConfigObject} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TargetPreparerForm', () => {
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

  it.async(`can render TargetPreparerForm with empty`, async () => {
    bootstrapTemplate(`<target-preparer-form [targetPreparers]="[]">
        </target-preparer-form>`);
    await env.verifyState(
        `target-preparer-form_with_empty`, 'target-preparer-form');
  });

  it.async(`can render TargetPreparerForm with data`, async () => {
    const targetPreparers = [
      {class_name: 'testname'} as TradefedConfigObject,
      {
        class_name: 'testname1',
        option_values: [{name: 'name1', values: ['value1', 'value2']}]
      } as TradefedConfigObject,
    ];
    bootstrapTemplate(
        `<target-preparer-form [targetPreparers]="targetPreparers">
        </target-preparer-form>`,
        {targetPreparers});
    await env.verifyState(
        `target-preparer-form_with_data`, 'target-preparer-form');
  });
});
