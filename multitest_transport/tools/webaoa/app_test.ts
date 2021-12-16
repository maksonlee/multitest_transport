/**
 * @license
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
import {By} from '@angular/platform-browser';
import {getEl, hasEl} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';

import {AppComponent} from './app';
import {AppModule} from './app_module';
import {AppModuleNgSummary} from './app_module.ngsummary';
import {AoaDevice} from './device/device';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let element: DebugElement;
  let component: AppComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AppModule],
      aotSummaries: AppModuleNgSummary,
    });
  });

  /** Checks whether an element is visible. */
  function isVisible(element: HTMLElement): boolean {
    // offsetParent is null if the element or any of its parents are hidden
    return element.offsetParent !== null;
  }

  describe('Insecure context', () => {
    beforeEach(() => {
      spyOnProperty(window, 'isSecureContext').and.returnValue(false);
      fixture = TestBed.createComponent(AppComponent);
      element = fixture.debugElement;
      fixture.detectChanges();
    });

    it('should display insecure context warning', () => {
      expect(hasEl(element, '.insecure-context')).toBeTrue();
      expect(hasEl(element, '.unsupported-browser')).toBeFalse();
      expect(hasEl(element, 'device-list')).toBeFalse();
      expect(hasEl(element, 'workflow-editor')).toBeFalse();
    });
  });

  describe('Secure Context and WebUSB unsupported', () => {
    beforeEach(() => {
      spyOnProperty(window, 'isSecureContext').and.returnValue(true);
      spyOnProperty(window, 'navigator').and.returnValue({});
      fixture = TestBed.createComponent(AppComponent);
      element = fixture.debugElement;
      fixture.detectChanges();
    });

    it('should display unsupported browser warning', () => {
      expect(hasEl(element, '.insecure-context')).toBeFalse();
      expect(hasEl(element, '.unsupported-browser')).toBeTrue();
      expect(hasEl(element, 'device-list')).toBeFalse();
      expect(hasEl(element, 'workflow-editor')).toBeFalse();
    });
  });

  describe('Secure context and WebUSB supported', () => {
    let usb: jasmine.SpyObj<USB>;
    let device: jasmine.SpyObj<AoaDevice>;

    beforeEach(() => {
      spyOnProperty(window, 'isSecureContext').and.returnValue(true);
      usb = jasmine.createSpyObj<USB>([
        'addEventListener', 'getDevices', 'requestDevice', 'removeEventListener'
      ]);
      spyOnProperty(window, 'navigator').and.returnValue({usb});
      device =
          jasmine.createSpyObj<AoaDevice>(['isConnected', 'open', 'close']);
      usb.getDevices.and.resolveTo([device]);

      fixture = TestBed.createComponent(AppComponent);
      element = fixture.debugElement;
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should display device list initially', () => {
      expect(hasEl(element, '.insecure-context')).toBeFalse();
      expect(hasEl(element, '.unsupported-browser')).toBeFalse();
      expect(isVisible(getEl(element, 'device-list'))).toBeTrue();
      expect(isVisible(getEl(element, 'workflow-editor'))).toBeFalse();
    });

    it('should switch to editor when continue button pressed', () => {
      getEl(element, 'button.continue').click();
      fixture.detectChanges();
      expect(isVisible(getEl(element, 'device-list'))).toBeFalse();
      expect(isVisible(getEl(element, 'workflow-editor'))).toBeTrue();
    });

    it('should switch to editor when a device is selected', () => {
      element.query(By.css('device-list'))
          .triggerEventHandler('selectionChange', device);
      fixture.detectChanges();
      expect(isVisible(getEl(element, 'device-list'))).toBeFalse();
      expect(isVisible(getEl(element, 'workflow-editor'))).toBeTrue();
      expect(component.device).toEqual(device);
    });

    it('should return to device list when return button pressed', () => {
      // Initially in workflow editor with a selected device
      component.editing = true;
      component.device = device;
      fixture.detectChanges();

      getEl(element, 'button.return').click();
      fixture.detectChanges();
      expect(isVisible(getEl(element, 'device-list'))).toBeTrue();
      expect(isVisible(getEl(element, 'workflow-editor'))).toBeFalse();
      expect(component.device).toBeUndefined();  // Device is unselected
    });
  });
});
