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
import {NodeConfig, PrivateNodeConfig} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {SettingsModule} from 'google3/third_party/py/multitest_transport/ui2/app/settings/settings_module';
import {SettingsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/settings/settings_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('SettingForm', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttClient: jasmine.SpyObj<MttClient>;
  let nodeConfig: NodeConfig;
  let privateNodeConfig: PrivateNodeConfig;

  beforeEach(() => {
    nodeConfig = {};
    privateNodeConfig = {};

    mttClient = jasmine.createSpyObj(
        'mttClient', ['getNodeConfig', 'getPrivateNodeConfig']);
    mttClient.getNodeConfig.and.returnValue(observableOf(nodeConfig));
    mttClient.getPrivateNodeConfig.and.returnValue(
        observableOf(privateNodeConfig));

    setupModule({
      imports: [
        SettingsModule,
        NoopAnimationsModule,
      ],
      summaries: [SettingsModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });
  });

  it.async(`can render with empty`, async () => {
    bootstrapTemplate(`<setting-form></setting-form>`);
    await env.verifyState(`setting-form_empty`, 'setting-form');
  });

  it.async(`can render with metric enabled`, async () => {
    privateNodeConfig.metrics_enabled = true;
    bootstrapTemplate(`<setting-form></setting-form>`);
    await env.verifyState(`setting-form_with_metric_enabled`, 'setting-form');
  });

  it.async(`can render with content`, async () => {
    nodeConfig.env_vars = [{name: 'test name', value: 'test value'}];
    nodeConfig.test_resource_default_download_urls =
        [{name: 'test name', value: 'test value'}];
    bootstrapTemplate(`<setting-form></setting-form>`);
    await env.verifyState(`setting-form_with_content`, 'setting-form');
  });
});
