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

describe('ScheduleTimeForm', () => {
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

  it.async('can render MANUAL schedule', async () => {
    bootstrapTemplate(`<schedule-time-form></schedule-time-form>`);
    await env.verifyState('schedule-time-form_manual', 'schedule-time-form');
  });

  it.async('can render hourly PERIODIC schedule', async () => {
    bootstrapTemplate(`<schedule-time-form [ngModel]="'59 * * * *'"
                          [timezone]="'UTC'"></schedule-time-form>`);
    await env.verifyState('schedule-time-form_hourly', 'schedule-time-form');
  });

  it.async('can render daily PERIODIC schedule', async () => {
    bootstrapTemplate(`<schedule-time-form [ngModel]="'59 23 * * *'"
                          [timezone]="'UTC'"></schedule-time-form>`);
    await env.verifyState('schedule-time-form_daily', 'schedule-time-form');
  });

  it.async('can render weekly PERIODIC schedule', async () => {
    bootstrapTemplate(`<schedule-time-form [ngModel]="'59 23 * * 6'"
                          [timezone]="'UTC'"></schedule-time-form>`);
    await env.verifyState('schedule-time-form_weekly', 'schedule-time-form');
  });

  it.async('can render monthly PERIODIC schedule', async () => {
    bootstrapTemplate(`<schedule-time-form [ngModel]="'59 23 31 * *'"
                          [timezone]="'UTC'"></schedule-time-form>`);
    await env.verifyState('schedule-time-form_monthly', 'schedule-time-form');
  });

  it.async('can render CUSTOM schedule', async () => {
    bootstrapTemplate(`<schedule-time-form [ngModel]="'1/2 3 4 * ?'"
                          [timezone]="'UTC'"></schedule-time-form>`);
    await env.verifyState('schedule-time-form_custom', 'schedule-time-form');
  });
});
