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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {CredentialsInfo} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import * as util from '../shared/util';
import {getEl, getTextContent, hasEl} from '../testing/jasmine_util';
import {newMockCredentialsInfo, newMockPrivateNodeConfig} from '../testing/mtt_mocks';

import {AuthModule} from './auth_module';
import {AuthModuleNgSummary} from './auth_module.ngsummary';
import {LoginButton} from './login_button';

describe('LoginButton', () => {
  let mttApiClient: jasmine.SpyObj<MttClient>;
  let notifier: jasmine.SpyObj<Notifier>;

  let component: LoginButton;
  let fixture: ComponentFixture<LoginButton>;
  let element: DebugElement;

  const privateNodeConfig = newMockPrivateNodeConfig();

  beforeEach(() => {
    notifier = jasmine.createSpyObj(['showError', 'showMessage']);
    mttApiClient = jasmine.createSpyObj([
      'getPrivateNodeConfig',
      'removeDefaultServiceAccount',
      'setDefaultServiceAccount',
    ]);

    mttApiClient.getPrivateNodeConfig.and.returnValue(
        observableOf(privateNodeConfig));
    spyOn(util, 'reloadPage');

    TestBed.configureTestingModule({
      imports: [AuthModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: AuthModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttApiClient},
        {provide: Notifier, useValue: notifier},
      ],
    });

    fixture = TestBed.createComponent(LoginButton);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  /** Reloads the component with the provided data */
  function reload(data: Partial<CredentialsInfo>) {
    component.defaultCredentials = data as CredentialsInfo;
    fixture.detectChanges();
  }

  it('can display without the default service account set', fakeAsync(() => {
       const text = getTextContent(element);
       expect(text).toContain('Set Default Service Account');
       getEl(element, '.login-button').click();
       tick(100);
       fixture.detectChanges();
       expect(hasEl(element, '.set-default-button')).toBeTruthy();
     }));

  it('displays the email when the default service account is set',
     fakeAsync(() => {
       reload(newMockCredentialsInfo());
       const text = getTextContent(element);
       expect(text).toContain('credentials_email');
       getEl(element, '.login-button').click();
       tick(100);
       fixture.detectChanges();
       expect(hasEl(element, '.remove-default-button')).toBeTruthy();
     }));

  it('can set the default service account', fakeAsync(() => {
       mttApiClient.setDefaultServiceAccount.and.returnValue(
           observableOf(null));
       getEl(element, '.login-button').click();
       tick(100);
       fixture.detectChanges();

       const file = new File([], 'file');
       const fileInput = getEl<HTMLInputElement>(element, 'input[type=file]');
       spyOnProperty(fileInput, 'files').and.returnValue([file]);
       fileInput.dispatchEvent(new Event('change'));  // Select a key file
       tick(600);  // Wait for pipe and refresh delays
       expect(mttApiClient.setDefaultServiceAccount).toHaveBeenCalledWith(file);
       expect(notifier.showError).not.toHaveBeenCalled();
     }));

  it('can remove the default service account', fakeAsync(() => {
       reload(newMockCredentialsInfo());
       mttApiClient.removeDefaultServiceAccount.and.returnValue(
           observableOf(null));
       getEl(element, '.login-button').click();
       tick(100);
       getEl(element, '.remove-default-button').click();
       tick(600);  // Wait for pipe and refresh delays
       expect(mttApiClient.removeDefaultServiceAccount).toHaveBeenCalled();
       expect(notifier.showError).not.toHaveBeenCalled();
     }));
});
