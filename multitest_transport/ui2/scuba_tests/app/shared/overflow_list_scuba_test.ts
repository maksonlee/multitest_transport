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
import {OverflowListType} from 'google3/third_party/py/multitest_transport/ui2/app/shared/overflow_list';
import {SharedModule} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module';
import {SharedModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/shared/shared_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('OverflowList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,
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

  it.async(`can render with button`, async () => {
    const data = ['test1', 'test2', 'test3'];
    const overflowListType = OverflowListType.BUTTON;

    bootstrapTemplate(
        `<overflow-list [data]='data' [overflowListType]='overflowListType'>
        </overflow-list>`,
        {data, overflowListType});
    await env.verifyState(`overflow-list_with_button`, 'overflow-list');
  });

  it.async(`can render with chip`, async () => {
    const data = ['test1', 'test2', 'test3'];
    const overflowListType = OverflowListType.CHIP;

    bootstrapTemplate(
        `<overflow-list [data]='data' [overflowListType]='overflowListType'>
        </overflow-list>`,
        {data, overflowListType});
    await env.verifyState(`overflow-list_with_chip`, 'overflow-list');
  });

  it.async(`can render with one item`, async () => {
    const data = ['test1'];
    const overflowListType = OverflowListType.CHIP;

    bootstrapTemplate(
        `<overflow-list [data]='data' [overflowListType]='overflowListType'>
        </overflow-list>`,
        {data, overflowListType});
    await env.verifyState(`overflow-list_with_one_item`, 'overflow-list');
  });
});
