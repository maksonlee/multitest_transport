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
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {ConfigSetInfo} from '../services/mtt_models';
import {getTextContent} from '../testing/jasmine_util';
import * as testUtil from '../testing/test_util';

import {ConfigSetList} from './config_set_list';
import {ConfigSetsModule} from './config_sets_module';
import {ConfigSetsModuleNgSummary} from './config_sets_module.ngsummary';


describe('ConfigSetList', () => {
  let configSetList: ConfigSetList;
  let configSetListFixture: ComponentFixture<ConfigSetList>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;

  let imported: ConfigSetInfo;
  let notImported: ConfigSetInfo;

  beforeEach(() => {
    imported = testUtil.newMockImportedConfigSetInfo();
    notImported = testUtil.newMockNotImportedConfigSetInfo();

    mttClient = jasmine.createSpyObj(
        'mttClient', ['getBuildChannels', 'getConfigSetInfos']);
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [imported]}));

    TestBed.configureTestingModule({
      imports: [ConfigSetsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: ConfigSetsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    configSetListFixture = TestBed.createComponent(ConfigSetList);
    el = configSetListFixture.debugElement;
    configSetListFixture.detectChanges();
    configSetList = configSetListFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(configSetList).toBeTruthy();
    expect(getTextContent(el)).toContain('Import');
    expect(getTextContent(el)).toContain('Upload');
  });

  it('lists configs', () => {
    const text = getTextContent(el);
    expect(text).toContain(imported.name);
    expect(text).not.toContain(notImported.name);
  });
});
