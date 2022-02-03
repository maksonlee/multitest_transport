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
import {ActivatedRoute} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceAction} from '../testing/mtt_mocks';

import {DeviceActionEditPage} from './device_action_edit_page';
import {DeviceActionsModule} from './device_actions_module';

describe('DeviceActionEditPage', () => {
  let deviceActionEditPage: DeviceActionEditPage;
  let deviceActionEditPageFixture: ComponentFixture<DeviceActionEditPage>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;
  const mockDeviceAction = newMockDeviceAction();

  beforeEach(() => {
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getBuildChannels', 'getDeviceAction']);
    mttClient.getDeviceAction.and.returnValue(observableOf(mockDeviceAction));
    mttClient.getBuildChannels.and.returnValue(observableOf([]));

    TestBed.configureTestingModule({
      imports: [DeviceActionsModule, RouterTestingModule, NoopAnimationsModule],
      providers: [
        {provide: MttClient, useValue: mttClient},
        {
          provide: ActivatedRoute,
          useValue: {
            params: observableOf({'id': '123'}),
          },
        },
      ],
    });
    deviceActionEditPageFixture = TestBed.createComponent(DeviceActionEditPage);
    el = deviceActionEditPageFixture.debugElement;
    deviceActionEditPageFixture.detectChanges();
    deviceActionEditPage = deviceActionEditPageFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(deviceActionEditPage).toBeTruthy();
  });

  it('calls API correctly', () => {
    expect(mttClient.getDeviceAction).toHaveBeenCalled();
  });

  it('displays texts correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('TradeFed Target Preparers');
    expect(textContent).toContain('Edit Device Action');
    expect(textContent).toContain('Device Action Information');
    expect(textContent).toContain('Description');
    expect(textContent).toContain('Target Device Spec');
    expect(textContent).toContain('TradeFed Options');
  });

  it('handles TradeFed option events', () => {
    expect(deviceActionEditPage.data.tradefed_options).toBeDefined();
    deviceActionEditPage.onAddOption();
    deviceActionEditPage.onAddOption();
    expect(deviceActionEditPage.data.tradefed_options!.length).toBe(2);

    deviceActionEditPage.onOptionValueChange({index: 1, value: 'a\nb'});
    expect(deviceActionEditPage.data.tradefed_options![1].values).toEqual([
      'a', 'b'
    ]);

    deviceActionEditPage.onRemoveOption(0);
    expect(deviceActionEditPage.data.tradefed_options!.length).toBe(1);
    expect(deviceActionEditPage.data.tradefed_options![0].values).toEqual([
      'a', 'b'
    ]);
  });

  describe('back button', () => {
    it('should display correct aria-label and tooltip', () => {
      const backButton = getEl(el, '#back-button');
      expect(backButton).toBeTruthy();
      expect(backButton.getAttribute('aria-label'))
          .toBe('Return to settings page');
      expect(backButton.getAttribute('mattooltip'))
          .toBe('Return to settings page');
    });
  });
});
