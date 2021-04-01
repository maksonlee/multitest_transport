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
import {TestRunAction} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {TestRunActionsModule} from 'google3/third_party/py/multitest_transport/ui2/app/test_run_actions/test_run_actions_module';
import {TestRunActionsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/test_run_actions/test_run_actions_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TestRunActionPicker', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,  // TODO Color contrast violation
  });

  beforeEach(() => {
    setupModule({
      imports: [
        TestRunActionsModule,
        NoopAnimationsModule,
      ],
      summaries: [TestRunActionsModuleNgSummary],
    });
  });

  it.async(`can render`, async () => {
    const actions = [] as TestRunAction[];
    const selectedActions = [] as TestRunAction[];
    bootstrapTemplate(
        `<test-run-action-picker [actions]="actions"
        [selectedActions]="selectedActions">
        </test-run-action-picker>`,
        {actions, selectedActions});

    await env.verifyState(`test-run-action-picker`, 'test-run-action-picker');
  });

  it.async(`can render with selected actions`, async () => {
    const actions = [] as TestRunAction[];
    const selectedActions = [{id: 'id', name: 'test'}] as TestRunAction[];
    bootstrapTemplate(
        `<test-run-action-picker [actions]="actions"
        [selectedActions]="selectedActions">
        </test-run-action-picker>`,
        {actions, selectedActions});
    await env.verifyState(
        `test-run-action-picker_with_selected_actions`,
        'test-run-action-picker');
  });

  it.async(`can render with open menu`, async () => {
    const actions = [{id: 'id', name: 'test'}, {id: 'id2', name: 'test2'}] as
        TestRunAction[];
    const selectedActions = [{id: 'id', name: 'test'}] as TestRunAction[];
    bootstrapTemplate(
        `<test-run-action-picker [actions]="actions"
        [selectedActions]="selectedActions">
        </test-run-action-picker>`,
        {actions, selectedActions});
    getEl('.add-button').click();
    flush();
    await env.verifyState(`test-run-action-picker_with_open_menu`, 'body');
  });
});
