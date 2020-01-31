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

import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import * as util from '../shared/util';
import {newMockPrivateNodeConfig} from '../testing/test_util';

import {SetupWizardDialog} from './setup_wizard_dialog';
import {SetupWizardModule} from './setup_wizard_module';
import {SetupWizardModuleNgSummary} from './setup_wizard_module.ngsummary';


describe('SetupWizardDialog', () => {
  let setupWizardDialog: SetupWizardDialog;
  let setupWizardDialogFixture: ComponentFixture<SetupWizardDialog>;
  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getPrivateNodeConfig', 'updatePrivateNodeConfig']);
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

    setupWizardDialogFixture = TestBed.createComponent(SetupWizardDialog);
    setupWizardDialog = setupWizardDialogFixture.componentInstance;
    setupWizardDialogFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(setupWizardDialog).toBeTruthy();
  });

  it('sets metric collection', () => {
    setupWizardDialog.submitMetrics(true);
    expect(mttClient.updatePrivateNodeConfig)
        .toHaveBeenCalledWith(newMockPrivateNodeConfig(true, false));

    setupWizardDialog.submitMetrics(false);
    expect(mttClient.updatePrivateNodeConfig)
        .toHaveBeenCalledWith(newMockPrivateNodeConfig(false, false));
  });
});
