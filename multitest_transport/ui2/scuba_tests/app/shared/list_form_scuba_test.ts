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

import {SharedModule} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module';
import {SharedModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('ListForm', () => {
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

  it.async(`can render ListForm with data`, async () => {
    const data = ['testData1', 'testData2'];
    const label = 'Test label';
    bootstrapTemplate(
        `<list-form [data]="data" [label]="label"></list-form>`, {data, label});
    await env.verifyState(`list-form_with_data`, 'list-form');
  });

  it.async(`can render ListForm without data`, async () => {
    const data = [] as string[];
    const label = 'Test label';
    bootstrapTemplate(
        `<list-form [data]="data" [label]="label"></list-form>`, {data, label});
    await env.verifyState(`list-form_without_data`, 'list-form');
  });
});
