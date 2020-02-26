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

import {BuildChannelsModule} from '../../../app/build_channels/build_channels_module';
import {BuildChannelsModuleNgSummary} from '../../../app/build_channels/build_channels_module.ngsummary';
import {BuildChannelAuthState} from '../../../app/services/mtt_models';
import {KarmaTestEnv} from '../../../app/testing/karma_env';

const SCUBA_GOLDENS_PATH =
    'third_party/py/multitest_transport/ui2/scuba_tests/app/build_channels/scuba_goldens';

describe('BuildChannelItem', () => {
  const env = new KarmaTestEnv({
    scubaGoldensPath: SCUBA_GOLDENS_PATH,
    axe: true,
  });

  beforeEach(() => {
    setupModule({
      imports: [BuildChannelsModule, NoopAnimationsModule, RouterTestingModule],
      summaries: [BuildChannelsModuleNgSummary],
    });
  });

  it.async('renders not authorized build channel item', async () => {
    const unauthorizedChannel = {
      name: 'Unauthorized Build Channel',
      need_auth: true,
      auth_state: BuildChannelAuthState.NOT_AUTHORIZED,
    };

    bootstrapTemplate(
        `<build-channel-item [buildChannel]="buildChannel">
         </build-channel-item>`,
        {buildChannel: unauthorizedChannel});
    await env.verifyState(
        `build-channel-item_not_authorized`, 'build-channel-item');
  });

  it.async('renders authorized build channel item', async () => {
    const authorizedChannel = {
      name: 'Authorized Build Channel',
      need_auth: true,
      auth_state: BuildChannelAuthState.AUTHORIZED,
    };

    bootstrapTemplate(
        `<build-channel-item [buildChannel]="buildChannel">
         </build-channel-item>`,
        {buildChannel: authorizedChannel});
    await env.verifyState(
        `build-channel-item_authorized`, 'build-channel-item');
  });

  it.async('renders build channel item which do not require auth', async () => {
    const buildchannel = {
      name: 'Build Channel without Authorization',
      need_auth: false,
    };

    bootstrapTemplate(
        `<build-channel-item [buildChannel]="buildChannel">
         </build-channel-item>`,
        {buildChannel: buildchannel});
    await env.verifyState(
        `build-channel-item_do_not_require_auth`, 'build-channel-item');
  });
});
