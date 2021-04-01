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
import {MttClient, TestRunActionClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {AuthorizationState, TestRunAction} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {TestRunActionsModule} from 'google3/third_party/py/multitest_transport/ui2/app/test_run_actions/test_run_actions_module';
import {TestRunActionsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/test_run_actions/test_run_actions_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('TestRunActionList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,  // TODO Duplicate ID violation
  });

  let client: jasmine.SpyObj<TestRunActionClient>;
  let actionList: TestRunAction[];

  beforeEach(() => {
    client = jasmine.createSpyObj(['list']);
    actionList = [];
    client.list.and.returnValue(observableOf(actionList));
    setupModule({
      imports: [
        TestRunActionsModule,
        NoopAnimationsModule,
      ],
      summaries: [TestRunActionsModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: {testRunActions: client}},
      ],
    });
  });

  it.async(`can render with empty`, async () => {
    bootstrapTemplate(`<test-run-action-list></test-run-action-list>`);
    await env.verifyState(
        `test-run-action-list_with_empty`, 'test-run-action-list');
  });

  it.async(`can render with content`, async () => {
    actionList.push(
        ...[{name: 'Action 1'}, {name: 'Action 2'}, {name: 'Action 3'}] as
        TestRunAction[]);
    bootstrapTemplate(`<test-run-action-list></test-run-action-list>`);
    await env.verifyState(
        `test-run-action-list_with_content`, 'test-run-action-list');
  });

  it.async(`can render with authorized action`, async () => {
    actionList.push({
      name: 'Authorized Action',
      authorization_state: AuthorizationState.AUTHORIZED
    } as TestRunAction);
    bootstrapTemplate(`<test-run-action-list></test-run-action-list>`);
    await env.verifyState(
        `test-run-action-list_with_authorized_action`, 'test-run-action-list');
  });

  it.async(`can render with unauthorized action`, async () => {
    actionList.push({
      name: 'Unauthorized Action',
      authorization_state: AuthorizationState.UNAUTHORIZED
    } as TestRunAction);
    bootstrapTemplate(`<test-run-action-list></test-run-action-list>`);
    await env.verifyState(
        `test-run-action-list_with_unauthorized_action`,
        'test-run-action-list');
  });
});
