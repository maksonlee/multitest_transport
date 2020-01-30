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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getTextContent} from '../testing/jasmine_util';

import {ConfigRestoreStep} from './config_restore_step';
import {SetupWizardModule} from './setup_wizard_module';
import {SetupWizardModuleNgSummary} from './setup_wizard_module.ngsummary';


describe('ConfigRestoreStep', () => {
  let configBackupSetup: ConfigRestoreStep;
  let configBackupSetupFixture: ComponentFixture<ConfigRestoreStep>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj('mttClient', ['importNodeConfig']);
    mttClient.importNodeConfig.and.returnValue(observableOf([]));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SetupWizardModule],
      aotSummaries: SetupWizardModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });

    configBackupSetupFixture = TestBed.createComponent(ConfigRestoreStep);
    el = configBackupSetupFixture.debugElement;
    configBackupSetupFixture.detectChanges();
    configBackupSetup = configBackupSetupFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(configBackupSetup).toBeTruthy();
    expect(getTextContent(el)).toContain('Upload File');
  });
});
