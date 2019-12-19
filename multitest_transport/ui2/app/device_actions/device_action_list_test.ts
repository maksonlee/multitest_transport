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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockDeviceAction} from '../testing/test_util';

import {DeviceActionList} from './device_action_list';
import {DeviceActionsModule} from './device_actions_module';
import {DeviceActionsModuleNgSummary} from './device_actions_module.ngsummary';

const FACTORY_RESET_ACTION = newMockDeviceAction('reset', 'Factory Reset');

describe('DeviceActionList', () => {
  let deviceActionList: DeviceActionList;
  let deviceActionListFixture: ComponentFixture<DeviceActionList>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getDeviceActionList', 'deleteDeviceAction']);
    mttClient.getDeviceActionList.and.returnValue(
        observableOf({device_actions: [FACTORY_RESET_ACTION]}));
    mttClient.deleteDeviceAction.and.returnValue(observableOf({}));

    TestBed.configureTestingModule({
      imports: [DeviceActionsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: DeviceActionsModuleNgSummary,
      providers: [
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: MttClient, useValue: mttClient},
      ],
    });
    deviceActionListFixture = TestBed.createComponent(DeviceActionList);
    deviceActionListFixture.detectChanges();
    el = deviceActionListFixture.debugElement;
    deviceActionList = deviceActionListFixture.componentInstance;
  });

  afterEach(() => {
    deviceActionListFixture.destroy();
  });

  it('initializes a component', () => {
    expect(deviceActionList).toBeTruthy();
  });

  it('called mttApi to load device action list', fakeAsync(() => {
       tick(100);
       deviceActionListFixture.whenStable().then(() => {
         expect(mttClient.getDeviceActionList).toHaveBeenCalled();
       });
     }));

  it('displayed correct HTML text content', fakeAsync(() => {
       tick(100);
       deviceActionListFixture.whenStable().then(() => {
         const textContent = getTextContent(el);
         expect(textContent).toContain('Factory Reset');
       });
     }));

  it('displays and announces a loading mask', fakeAsync(() => {
       tick(100);
       expect(deviceActionList.isLoading).toBeTruthy();
       expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
       deviceActionListFixture.whenStable().then(() => {
         expect(deviceActionList.isLoading).toBeFalsy();
         expect(liveAnnouncer.announce)
             .toHaveBeenCalledWith('Device actions loaded', 'assertive');
       });
     }));

  it('deletes a device action correctly', fakeAsync(() => {
       tick(100);
       deviceActionListFixture.whenStable().then(() => {
         expect(getEls(el, 'mat-card').length).toBe(1);
         getEl(el, '.delete-button').click();
         deviceActionListFixture.detectChanges();
         expect(mttClient.deleteDeviceAction)
             .toHaveBeenCalledWith(FACTORY_RESET_ACTION.id);
         expect(getEls(el, 'mat-card').length).toBe(0);
       });
     }));

  describe('update button', () => {
    it('should display correct aria-label and tooltip', fakeAsync(() => {
         tick(100);
         deviceActionListFixture.whenStable().then(() => {
           const updateButton = getEl(el, '.update-button');
           expect(updateButton).toBeTruthy();
           expect(updateButton.getAttribute('aria-label')).toBe('Edit');
           expect(updateButton.getAttribute('mattooltip')).toBe('Edit');
         });
       }));
  });

  describe('delete button', () => {
    it('should display correct aria-label and tooltip', fakeAsync(() => {
         tick(100);
         deviceActionListFixture.whenStable().then(() => {
           const deleteButton = getEl(el, '.delete-button');
           expect(deleteButton).toBeTruthy();
           expect(deleteButton.getAttribute('aria-label')).toBe('Delete');
           expect(deleteButton.getAttribute('mattooltip')).toBe('Delete');
         });
       }));
  });

  describe('more actions button', () => {
    it('should display correct aria-label and tooltip', fakeAsync(() => {
         tick(100);
         deviceActionListFixture.whenStable().then(() => {
           const moreActionsButton = getEl(el, '#menuButton');
           expect(moreActionsButton).toBeTruthy();
           expect(moreActionsButton.getAttribute('aria-label'))
               .toBe('More actions');
           expect(moreActionsButton.getAttribute('mattooltip'))
               .toBe('More actions');
         });
       }));
  });
});
