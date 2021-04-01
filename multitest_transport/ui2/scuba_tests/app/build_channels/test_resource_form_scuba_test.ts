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
import {of} from 'rxjs';

import {BuildChannelsModule} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module';
import {BuildChannelsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module.ngsummary';
import {TestResourceClassType} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/test_resource_form';
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {TestResourceDef, TestResourceObj, TestResourceType} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {newMockBuildItem} from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TestResourceForm', () => {
  const BUILD_ITEM = newMockBuildItem();
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });

  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj<MttClient>({
      lookupBuildItem: of(BUILD_ITEM),
    });

    setupModule({
      imports: [
        BuildChannelsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
      summaries: [BuildChannelsModuleNgSummary],
    });
  });

  it.async(
      `can render TestResourceForm with different resource type`, async () => {
        const testResourceObjList: TestResourceObj[] = [
          {
            name: 'testname',
            url: 'testurl',
            test_resource_type: TestResourceType.UNKNOWN,
          },
          {
            name: 'testname2',
            url: 'testurl2',
            test_resource_type: TestResourceType.DEVICE_IMAGE,
          },
          {
            name: 'testname3',
            url: 'testurl3',
            test_resource_type: TestResourceType.TEST_PACKAGE,
          }
        ];
        const type = TestResourceClassType.TEST_RESOURCE_OBJ;
        bootstrapTemplate(
            `<test-resource-form
                      [data]="testResourceObjList"
                      [canAdd]="false"
                      [canDelete]="false"
                      [buildChannels]="[]"
                      [testResourceClassType]="type"
                      >
                      </test-resource-form>`,
            {testResourceObjList, type});
        await env.verifyState(
            `test-resource-form_with_different_resource_type`,
            'test-resource-form');
      });

  it.async(`can render TestResourceForm with button`, async () => {
    const testResourceObjList: TestResourceObj[] = [{
      name: 'testname',
      url: 'testurl',
      test_resource_type: TestResourceType.UNKNOWN,
    }];
    const type = TestResourceClassType.TEST_RESOURCE_OBJ;
    bootstrapTemplate(
        `<test-resource-form
                      [data]="testResourceObjList"
                      [canAdd]="true"
                      [canDelete]="true"
                      [buildChannels]="[]"
                      [testResourceClassType]="type"
                      >
                      </test-resource-form>`,
        {testResourceObjList, type});
    await env.verifyState(
        `test-resource-form_with_button`, 'test-resource-form');
  });

  it.async(`can render TestResourceForm with test resource def`, async () => {
    const testResourceObjList: TestResourceDef[] = [{
      name: 'testname',
      default_download_url: 'testdownloadurl',
      test_resource_type: TestResourceType.UNKNOWN,
      decompress: true,
      decompress_dir: 'testdecompressdir'
    }];
    const type = TestResourceClassType.TEST_RESOURCE_DEF;
    bootstrapTemplate(
        `<test-resource-form
                      [data]="testResourceObjList"
                      [canAdd]="true"
                      [canDelete]="true"
                      [buildChannels]="[]"
                      [testResourceClassType]="type"
                      >
                      </test-resource-form>`,
        {testResourceObjList, type});
    await env.verifyState(
        `test-resource-form_with_test_resource_def`, 'test-resource-form');
  });
});
