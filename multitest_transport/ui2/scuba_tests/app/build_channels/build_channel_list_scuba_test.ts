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
import {BuildChannelsModule} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module';
import {BuildChannelsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module.ngsummary';
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {BuildChannel, BuildChannelList, DEFAULT_BUILD_CHANNEL_IDS} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('BuildChannelList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getBuildChannels']);

    setupModule({
      imports: [
        BuildChannelsModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
      summaries: [BuildChannelsModuleNgSummary],
    });
  });

  it.async(`can render empty BuildChannelList`, async () => {
    const buildChannelList: BuildChannelList = {build_channels: []};
    mttClient.getBuildChannels.and.returnValue(observableOf(buildChannelList));
    bootstrapTemplate(`<build-channel-list></build-channel-list>`);
    await env.verifyState(
        `build-channel-list_with_empty`, 'build-channel-list');
  });

  it.async(`can render BuildChannelList with item`, async () => {
    const buildChannelList: BuildChannelList = {
      build_channels: [
        {id: DEFAULT_BUILD_CHANNEL_IDS[0], name: 'Default'} as BuildChannel,
        {id: 'custom', name: 'Custom'} as BuildChannel,
      ]
    };

    mttClient.getBuildChannels.and.returnValue(observableOf(buildChannelList));
    bootstrapTemplate(`<build-channel-list></build-channel-list>`);
    await env.verifyState(`build-channel-list_with_item`, 'build-channel-list');
  });
});
