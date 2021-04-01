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
import {RouterTestingModule} from '@angular/router/testing';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {ConfigSetsModule} from 'google3/third_party/py/multitest_transport/ui2/app/config_sets/config_sets_module';
import {ConfigSetsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/config_sets/config_sets_module.ngsummary';
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {ConfigSetInfo} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import * as testUtil from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('ConfigSetList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getBuildChannels', 'getConfigSetInfos']);

    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: []}));

    setupModule({
      imports: [ConfigSetsModule, NoopAnimationsModule, RouterTestingModule],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
      summaries: [ConfigSetsModuleNgSummary],
    });
  });

  it.async(`can render with no config set`, async () => {
    bootstrapTemplate(`<config-set-list></config-set-list>`);
    await env.verifyState(
        `config-set-list_with_no_config_set`, 'config-set-list');
  });

  it.async(`can render with imported config set`, async () => {
    const imported = testUtil.newMockImportedConfigSetInfo() as ConfigSetInfo;
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [imported]}));
    bootstrapTemplate(`<config-set-list></config-set-list>`);
    await env.verifyState(
        `config-set-list_with_imported_config_set`, 'config-set-list');
  });

  it.async(`can render with not imported config set`, async () => {
    const notImported =
        testUtil.newMockNotImportedConfigSetInfo() as ConfigSetInfo;
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [notImported]}));
    bootstrapTemplate(`<config-set-list></config-set-list>`);
    await env.verifyState(
        `config-set-list_with_not_imported_config_set`, 'config-set-list');
  });
});
