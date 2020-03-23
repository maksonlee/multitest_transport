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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {async, ComponentFixture, TestBed} from '@angular/core/testing';
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getTextContent} from '../testing/jasmine_util';
import {newMockNodeConfig, newMockPrivateNodeConfig} from '../testing/test_util';
import {SettingForm} from './setting_form';
import {SettingsModule} from './settings_module';
import {SettingsModuleNgSummary} from './settings_module.ngsummary';

describe('SettingForm', () => {
  const nodeConfig = newMockNodeConfig();
  const privateNodeConfig = newMockPrivateNodeConfig();
  let settingForm: SettingForm;
  let settingFormFixture: ComponentFixture<SettingForm>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getNodeConfig', 'getPrivateNodeConfig']);
    mttClient.getNodeConfig.and.returnValue(observableOf(nodeConfig));
    mttClient.getPrivateNodeConfig.and.returnValue(
        observableOf(privateNodeConfig));

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        SettingsModule,
      ],
      aotSummaries: SettingsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
    settingFormFixture = TestBed.createComponent(SettingForm);
    el = settingFormFixture.debugElement;
    settingForm = settingFormFixture.componentInstance;
    settingFormFixture.detectChanges();
  });

  it('gets initialized correctly', () => {
    expect(settingForm).toBeTruthy();
  });

  it('calls API correctly', () => {
    expect(mttClient.getNodeConfig).toHaveBeenCalled();
  });

  it('displays texts correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Environment Variables');
    expect(textContent)
        .toContain('Test Resource Default Download Urls Variables');
    expect(textContent).toContain('Update');
  });

  it('sets up parameters correctly', async(async () => {
       await settingFormFixture.whenStable();
     }));

  it('displays and announces a loading mask', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    expect(liveAnnouncer.announce)
        .toHaveBeenCalledWith('Settings loaded', 'assertive');
  });
});
