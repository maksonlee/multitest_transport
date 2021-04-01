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
import * as util from '../shared/util';
import {getTextContent} from '../testing/jasmine_util';
import {newMockBuildChannel, newMockNotImportedConfigSetInfo} from '../testing/mtt_mocks';

import {SetupWizardModule} from './setup_wizard_module';
import {SetupWizardModuleNgSummary} from './setup_wizard_module.ngsummary';
import {SetupWizardStepper} from './setup_wizard_stepper';


describe('SetupWizardStepper', () => {
  const DRIVE_BUILD_CHANNEL =
      newMockBuildChannel('google_drive', 'Google Drive');
  const CLOUD_BUILD_CHANNEL =
      newMockBuildChannel('google_cloud_storage', 'Google Cloud Storage');

  let setupWizardStepper: SetupWizardStepper;
  let setupWizardStepperFixture: ComponentFixture<SetupWizardStepper>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', [
      'getBuildChannels', 'getConfigSetBuildChannels', 'getConfigSetInfos',
      'getPrivateNodeConfig', 'updatePrivateNodeConfig'
    ]);
    mttClient.getBuildChannels.and.returnValue(observableOf(
        {build_channels: [CLOUD_BUILD_CHANNEL, DRIVE_BUILD_CHANNEL]}));
    mttClient.getConfigSetBuildChannels.and.returnValue(
        observableOf({build_channels: CLOUD_BUILD_CHANNEL}));
    mttClient.getConfigSetInfos.and.returnValue(
        observableOf({config_set_infos: [newMockNotImportedConfigSetInfo()]}));
    mttClient.getPrivateNodeConfig.and.returnValue(observableOf({}));
    mttClient.updatePrivateNodeConfig.and.returnValue(observableOf({}));

    // Prevent page reloading
    spyOn(util, 'reloadPage');

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SetupWizardModule],
      aotSummaries: SetupWizardModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    setupWizardStepperFixture = TestBed.createComponent(SetupWizardStepper);
    el = setupWizardStepperFixture.debugElement;
    setupWizardStepperFixture.detectChanges();
    setupWizardStepper = setupWizardStepperFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(setupWizardStepper).toBeTruthy();
    expect(getTextContent(el)).toContain('Setup Wizard');
  });

  it('marks as completed', () => {
    setupWizardStepper.submit();
    expect(mttClient.updatePrivateNodeConfig).toHaveBeenCalledWith({
      setup_wizard_completed: true
    });
  });
});
