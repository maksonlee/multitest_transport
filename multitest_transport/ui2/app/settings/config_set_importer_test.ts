/**
 * Copyright 2019 Google LLC
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
import * as testUtil from '../testing/test_util';

import {ConfigSetImporter} from './config_set_importer';
import {SettingsModule} from './settings_module';
import {SettingsModuleNgSummary} from './settings_module.ngsummary';


/** Create a mock ConfigSetInfo that has been imported */
function newMockImportedConfigSetInfo() {
  return testUtil.newMockConfigSetInfo(
      'mtt:///imported/config/set/info', 'Imported Config Set', 'importedhash',
      true, false);
}


/** Create a mock ConfigSetInfo that has not been imported */
function newMockNotImportedConfigSetInfo() {
  return testUtil.newMockConfigSetInfo(
      'mtt:///not/imported/config/set/info', 'Not Imported Config Set',
      'notimportedhash', false, false);
}


/** Create a mock ConfigSetInfo that can be updated */
function newMockUpdatableConfigSetInfo() {
  return testUtil.newMockConfigSetInfo(
      'mtt:///updatable/config/set/info', 'Updatable Config Set', 'updatable',
      true, true);
}


describe('ConfigSetImporter', () => {
  let configSetImporter: ConfigSetImporter;
  let configSetImporterFixture: ComponentFixture<ConfigSetImporter>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;

  let imported: ConfigSetInfo;
  let notImported: ConfigSetInfo;
  let updatable: ConfigSetInfo;

  beforeEach(() => {
    const gcsBuildChannel = testUtil.newMockBuildChannel(
        'google_cloud_storage', 'Google Cloud Storage');
    imported = newMockImportedConfigSetInfo();
    notImported = newMockNotImportedConfigSetInfo();
    updatable = newMockUpdatableConfigSetInfo();

    mttClient = jasmine.createSpyObj(
        'mttClient', ['getBuildChannels', 'getConfigSetInfos']);
    mttClient.getBuildChannels.and.returnValue(
        observableOf({build_channels: [gcsBuildChannel]}));
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [imported, notImported, updatable]}));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SettingsModule],
      aotSummaries: SettingsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    configSetImporterFixture = TestBed.createComponent(ConfigSetImporter);
    el = configSetImporterFixture.debugElement;
    configSetImporterFixture.detectChanges();
    configSetImporter = configSetImporterFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(configSetImporter).toBeTruthy();
    expect(getTextContent(el)).toContain('Import Selected');
  });

  it('lists configs', () => {
    const text = getTextContent(el);
    expect(text).toContain(imported.name);
    expect(text).toContain(notImported.name);
    expect(text).toContain(updatable.name);
  });
});
