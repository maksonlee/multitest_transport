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
import {KarmaTestEnv} from '../testing/karma_env';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

const SCUBA_GOLDENS_PATH =
    'third_party/py/multitest_transport/ui2/app/shared/scuba_goldens';

describe('Status button', () => {
  const env = new KarmaTestEnv({
    scubaGoldensPath: SCUBA_GOLDENS_PATH,
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

  const generalStateList = [
    'Allocated', 'Available', 'Canceled', 'Completed', 'Error', 'Running',
    'Authorized', 'Unauthorized', 'Random'
  ];

  const configSetStateList = ['Imported', 'Not Imported', 'Updatable'];

  const hostStateList = ['Quitting', 'Killing', 'Unknown', 'Gone', 'Running'];

  for (let state of generalStateList) {
    it.async(`can render a state button with state ${state}`, async () => {
      bootstrapTemplate(
          `<status-button [state]="state"></status-button>`, {state});
      state = state.toLowerCase();
      await env.verifyState(`status-button_${state}`, 'status-button');
    });
  }

  for (let state of configSetStateList) {
    it.async(
        `can render a state button in configset context with state ${state}`,
        async () => {
          bootstrapTemplate(
              `<status-button class="config-set" [state]="state">
              </status-button>`,
              {state});
          state = state.toLowerCase();
          await env.verifyState(
              `status-button_config_set_${state}`, 'status-button');
        });
  }

  for (let state of hostStateList) {
    it.async(
        `can render a state button in host context with state ${state}`,
        async () => {
          bootstrapTemplate(
              `<status-button class="host" [state]="state"></status-button>`,
              {state});
          state = state.toLowerCase();
          await env.verifyState(`status-button_host_${state}`, 'status-button');
        });
  }
});
