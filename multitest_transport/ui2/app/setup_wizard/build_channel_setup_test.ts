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
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {AuthService} from '../services/auth_service';
import {MttClient} from '../services/mtt_client';
import {BuildChannelAuthState} from '../services/mtt_models';
import {getEl, getTextContent} from '../testing/jasmine_util';

import {BuildChannelSetup} from './build_channel_setup';
import {SetupWizardModule} from './setup_wizard_module';
import {SetupWizardModuleNgSummary} from './setup_wizard_module.ngsummary';

describe('BuildChannelSetup', () => {
  const BUILD_CHANNELS = [
    {
      id: 'google_drive',
      name: 'Google Drive name',
      provider_name: 'Google Drive provider',
      need_auth: true,
      auth_state: BuildChannelAuthState.NOT_AUTHORIZED,
    },
    {
      id: 'google_cloud_storage',
      name: 'Google Cloud Storage name',
      provider_name: 'Google Cloud Storage provider',
      need_auth: true,
      auth_state: BuildChannelAuthState.NOT_AUTHORIZED,
    },
    {
      id: 'local_file_store',
      name: 'Local File Store name',
      provider_name: 'Local File Store provider'
    }
  ];

  let buildChannelSetup: BuildChannelSetup;
  let buildChannelSetupFixture: ComponentFixture<BuildChannelSetup>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let authService: jasmine.SpyObj<AuthService>;
  let el: DebugElement;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getBuildChannels']);
    mttClient.getBuildChannels.and.returnValue(
        observableOf({build_channels: [...BUILD_CHANNELS]}));
    authService = jasmine.createSpyObj(
        'authService', ['getAuthProgress', 'startAuthFlow']);
    authService.getAuthProgress.and.returnValue(
        observableOf({type: 'progress'}));
    authService.startAuthFlow.and.returnValue(true);

    TestBed.configureTestingModule({
      imports: [SetupWizardModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: SetupWizardModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: AuthService, useValue: authService},
      ],
    });
    buildChannelSetupFixture = TestBed.createComponent(BuildChannelSetup);
    el = buildChannelSetupFixture.debugElement;
    buildChannelSetup = buildChannelSetupFixture.componentInstance;
    buildChannelSetupFixture.detectChanges();
  });

  it('gets initialized correctly', () => {
    expect(buildChannelSetup).toBeTruthy();
  });

  it('calls API correctly', () => {
    expect(mttClient.getBuildChannels).toHaveBeenCalled();
  });

  it('displays only Google Drive and Google Cloud Storage', () => {
    const text = getTextContent(el);
    expect(text).toContain('Google Cloud Storage name');
    expect(text).toContain('Google Drive name');
    expect(text).not.toContain('Local File Storage');
  });

  it('triggers the authorization flow', () => {
    getEl(el, '.auth-button').click();
    expect(authService.startAuthFlow).toHaveBeenCalled();
  });
});