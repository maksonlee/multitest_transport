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

import {NameValuePair} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {SharedModule} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module';
import {SharedModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('NameValuePairListForm', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  beforeEach(() => {
    setupModule({
      imports: [
        SharedModule,
        NoopAnimationsModule,
      ],
      summaries: [SharedModuleNgSummary],
    });
  });

  it.async(`can render NameValuePairListForm with data`, async () => {
    const data = [{name: 'testName', value: 'testValue'}];
    bootstrapTemplate(
        `<name-value-pair-list-form [data]="data"></name-value-pair-list-form>`,
        {data});
    await env.verifyState(
        `name-value-pair-list-form_with_data`, 'name-value-pair-list-form');
  });

  it.async(`can render NameValuePairListForm without data`, async () => {
    const data = [] as NameValuePair[];
    bootstrapTemplate(
        `<name-value-pair-list-form [data]="data"></name-value-pair-list-form>`,
        {data});
    await env.verifyState(
        `name-value-pair-list-form_without_data`, 'name-value-pair-list-form');
  });
});
