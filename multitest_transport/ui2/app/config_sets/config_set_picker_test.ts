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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {ConfigSetInfo} from '../services/mtt_models';
import {getTextContent} from '../testing/jasmine_util';
import * as testUtil from '../testing/mtt_mocks';

import {ConfigSetPicker} from './config_set_picker';
import {ConfigSetsModule} from './config_sets_module';
import {ConfigSetsModuleNgSummary} from './config_sets_module.ngsummary';


describe('ConfigSetPicker', () => {
  let configSetPicker: ConfigSetPicker;
  let configSetPickerFixture: ComponentFixture<ConfigSetPicker>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;

  let notImported: ConfigSetInfo;

  beforeEach(() => {
    const gcsBuildChannel = testUtil.newMockBuildChannel(
        'google_cloud_storage', 'Google Cloud Storage');
    notImported = testUtil.newMockNotImportedConfigSetInfo();

    mttClient = jasmine.createSpyObj(
        'mttClient', ['getConfigSetBuildChannels', 'getConfigSetInfos']);
    mttClient.getConfigSetBuildChannels.and.returnValue(
        observableOf({build_channels: [gcsBuildChannel]}));
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [notImported]}));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, ConfigSetsModule],
      aotSummaries: ConfigSetsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    configSetPickerFixture = TestBed.createComponent(ConfigSetPicker);
    el = configSetPickerFixture.debugElement;
    configSetPickerFixture.detectChanges();
    configSetPicker = configSetPickerFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(configSetPicker).toBeTruthy();
    expect(getTextContent(el)).toContain('Import Selected');
  });

  it('lists configs', () => {
    const text = getTextContent(el);
    expect(text).toContain(notImported.name);
  });
});
