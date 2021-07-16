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
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/mdc-dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {AuthorizationMethod, AuthorizationState, BuildChannel} from '../services/mtt_models';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';
import {BuildPicker, BuildPickerData, BuildPickerMode} from './build_picker';

describe('BuildPicker', () => {
  let dialogRef: jasmine.SpyObj<MatDialogRef<BuildPicker>>;
  let dialogData: BuildPickerData;
  let mttClient: jasmine.SpyObj<MttClient>;

  let fixture: ComponentFixture<BuildPicker>;
  let component: BuildPicker;
  let element: DebugElement;

  beforeEach(() => {
    dialogRef = jasmine.createSpyObj<MatDialogRef<BuildPicker>>(['close']);
    mttClient = jasmine.createSpyObj<MttClient>(['listBuildItems']);
    mttClient.listBuildItems.and.returnValue(observableOf({}));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, BuildChannelsModule],
      aotSummaries: BuildChannelsModuleNgSummary,
      providers: [
        {provide: MatDialogRef, useValue: dialogRef},
        {provide: MAT_DIALOG_DATA, useFactory: () => dialogData},
        {provide: MttClient, useValue: mttClient},
      ],
    });
  });

  /** Helper method to initialize the BuildPicker component. */
  function initComponent(
      buildChannels: Array<Partial<BuildChannel>>, resourceUrl?: string) {
    dialogData = {
      buildChannels: buildChannels as BuildChannel[],
      mode: BuildPickerMode.SELECT,
      resourceUrl,
    };
    fixture = TestBed.createComponent(BuildPicker);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  it('should display the two default tabs if no channels provided', () => {
    initComponent([]);
    const tabs = getEls(element, '.mat-tab-label');
    expect(tabs.length).toBe(2);
    expect(tabs[0].textContent).toEqual('By Url');
    expect(tabs[1].textContent).toEqual('Local File');
    // URL tab is selected by default
    expect(getEl(element, '.mat-tab-label-active').textContent)
        .toEqual('By Url');
  });

  it('should set URL value if HTTP URL provided', () => {
    initComponent([], 'https://www.google.com');
    // URL tab is selected and URL value is set
    expect(getEl(element, '.mat-tab-label-active').textContent)
        .toEqual('By Url');
    expect(component.searchBarUrlValue).toEqual('https://www.google.com');
  });

  it('should display an additional tab for each provided channel', () => {
    initComponent([{name: 'Channel #1'}, {name: 'Channel #2'}]);
    const tabs = getEls(element, '.mat-tab-label');
    expect(tabs.length).toBe(4);
    expect(tabs[2].textContent).toEqual('Channel #1');
    expect(tabs[3].textContent).toEqual('Channel #2');
    // URL tab is selected by default
    expect(getEl(element, '.mat-tab-label-active').textContent)
        .toEqual('By Url');
  });

  it('should select channel if it matches the resource URL', () => {
    initComponent(
        [{
          id: 'channel',
          name: 'Channel',
          auth_state: AuthorizationState.AUTHORIZED,
        }],
        'mtt:///channel/path');
    // Build channel tab is selected and path value is initialized
    expect(getEl(element, '.mat-tab-label-active').textContent)
        .toEqual('Channel');
    expect(component.searchBarFilenameValue).toEqual('path');
    // Build items are loaded and authorization buttons are hidden
    expect(mttClient.listBuildItems).toHaveBeenCalled();
    expect(hasEl(element, '.auth-button')).toBeFalse();
    expect(hasEl(element, '.keyfile-button')).toBeFalse();
  });

  it('should display authorize button if supported and unauthorized', () => {
    initComponent(
        [{
          id: 'channel',
          auth_state: AuthorizationState.UNAUTHORIZED,
          auth_methods: [AuthorizationMethod.OAUTH2_AUTHORIZATION_CODE],
        }],
        'mtt:///channel/path');
    expect(mttClient.listBuildItems).not.toHaveBeenCalled();
    expect(hasEl(element, '.auth-button')).toBeTrue();
    expect(hasEl(element, '.keyfile-button')).toBeFalse();
  });

  it('should display keyfile button if supported and unauthorized', () => {
    initComponent(
        [{
          id: 'channel',
          auth_state: AuthorizationState.UNAUTHORIZED,
          auth_methods: [AuthorizationMethod.OAUTH2_SERVICE_ACCOUNT],
        }],
        'mtt:///channel/path');
    expect(mttClient.listBuildItems).not.toHaveBeenCalled();
    expect(hasEl(element, '.auth-button')).toBeFalse();
    expect(hasEl(element, '.keyfile-button')).toBeTrue();
  });

  it('should return an entered URL when select is clicked', () => {
    const url = 'https://www.google.com';
    initComponent([], '');
    component.searchBarUrlValue = url;
    getEl(element, '.select-button').click();
    expect(dialogRef.close).toHaveBeenCalledWith(url);
  });

  it('should return a trimmed URL when select is clicked', () => {
    const url = '  https://www.google.com';
    initComponent([], '');
    component.searchBarUrlValue = url;
    getEl(element, '.select-button').click();
    expect(dialogRef.close).toHaveBeenCalledWith(url.trim());
  });
});
