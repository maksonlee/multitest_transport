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
import {ConfigSetsModule} from 'google3/third_party/py/multitest_transport/ui2/app/config_sets/config_sets_module';
import {ConfigSetsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/config_sets/config_sets_module.ngsummary';
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {AuthorizationState, BuildChannel, ConfigSetInfo, ConfigSetStatus} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('ConfigSetPicker', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,  // TODO Fix heading issue on build channel item
  });

  let mttClient: jasmine.SpyObj<MttClient>;
  let buildChannel: BuildChannel;
  let configSets: ConfigSetInfo[];

  beforeEach(() => {
    buildChannel = {
      name: 'Build Channel',
      auth_state: AuthorizationState.AUTHORIZED
    } as BuildChannel;

    configSets = [];

    mttClient = jasmine.createSpyObj<MttClient>({
      getConfigSetBuildChannels: observableOf({build_channels: [buildChannel]}),
      getConfigSetInfos: observableOf({config_set_infos: configSets})
    });

    setupModule({
      imports: [
        ConfigSetsModule,
        NoopAnimationsModule,
      ],
      summaries: [ConfigSetsModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });
  });

  it.async(`can render with nothing to import`, async () => {
    bootstrapTemplate(`<config-set-picker></config-set-picker>`);
    await env.verifyState(
        `config-set-picker_with_nothing_to_import`, 'config-set-picker');
  });

  it.async(`can render with content`, async () => {
    configSets.push(
        ...[{name: 'Not Imported', status: ConfigSetStatus.NOT_IMPORTED},
            {name: 'Imported', status: ConfigSetStatus.IMPORTED},
            {name: 'Updatable', status: ConfigSetStatus.UPDATABLE}] as
        ConfigSetInfo[]);
    bootstrapTemplate(`<config-set-picker></config-set-picker>`);
    await env.verifyState(
        `config-set-picker_with_content`, 'config-set-picker');
  });

  it.async(`can render with unauthorized build channel`, async () => {
    buildChannel.auth_state = AuthorizationState.UNAUTHORIZED;
    bootstrapTemplate(`<config-set-picker></config-set-picker>`);
    await env.verifyState(
        `config-set-picker_with_unauthorized_build_channel`,
        'config-set-picker');
  });
});
