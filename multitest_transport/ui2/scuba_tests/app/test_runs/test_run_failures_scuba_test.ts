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

import {TestRunState} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {TestRunsModule} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module';
import {TestRunsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TestRunFailures', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  beforeEach(() => {
    setupModule({
      imports: [
        TestRunsModule,
        NoopAnimationsModule,
      ],
      summaries: [TestRunsModuleNgSummary],
    });
  });

  it.async(`can render TestRunFailures with completed state`, async () => {
    const state = TestRunState.COMPLETED;
    bootstrapTemplate(
        `<test-run-failures [state]="state"></test-run-failures>`, {state});
    await env.verifyState(
        `test-run-failures_completed_state`, 'test-run-failures');
  });

  it.async(`can render TestRunFailures with error state`, async () => {
    const state = TestRunState.ERROR;
    const numFailedTests = 1;
    const numTotalTests = 100000;
    bootstrapTemplate(
        `<test-run-failures
          [state]="state"
          [numFailedTests]="numFailedTests"
          [numTotalTests]="numTotalTests"></test-run-failures>`,
        {state, numFailedTests, numTotalTests});
    await env.verifyState(`test-run-failures_error_state`, 'test-run-failures');
  });

  it.async(`can render TestRunFailures with canceled state`, async () => {
    const state = TestRunState.CANCELED;
    bootstrapTemplate(
        `<test-run-failures [state]="state"></test-run-failures>`, {state});
    await env.verifyState(
        `test-run-failures_canceled_state`, 'test-run-failures');
  });
});
