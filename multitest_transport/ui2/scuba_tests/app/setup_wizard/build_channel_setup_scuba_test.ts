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
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {AuthorizationState} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {SetupWizardModule} from 'google3/third_party/py/multitest_transport/ui2/app/setup_wizard/setup_wizard_module';
import {SetupWizardModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/setup_wizard/setup_wizard_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('BuildChannelSetup', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttClient: jasmine.SpyObj<MttClient>;

  const BUILD_CHANNELS = [
    {
      id: 'google_drive',
      name: 'Google Drive name',
      provider_name: 'Google Drive provider',
      auth_state: AuthorizationState.UNAUTHORIZED,
    },
    {
      id: 'google_cloud',
      name: 'Google Cloud name',
      provider_name: 'Google Cloud',
      auth_state: AuthorizationState.AUTHORIZED,
    }
  ];

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getBuildChannels']);
    mttClient.getBuildChannels.and.returnValue(
        observableOf({build_channels: [...BUILD_CHANNELS]}));

    setupModule({
      imports: [
        SetupWizardModule,
        NoopAnimationsModule,
      ],
      summaries: [SetupWizardModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });
  });

  it.async(`can render with content`, async () => {
    bootstrapTemplate(`<build-channel-setup></build-channel-setup>`);
    await env.verifyState(
        `build-channel-setup_with_content`, 'build-channel-setup');
  });
});
