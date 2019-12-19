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

import {BuildChannelAuthState} from '../services/mtt_models';
import {getEl, getTextContent} from '../testing/jasmine_util';

import {BuildChannelItem} from './build_channel_item';
import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';

describe('BuildChannelItem', () => {
  const defaultBuildChannel = {
    id: 'google_drive',
    name: 'Google Drive Name',
    provider_name: 'Google Drive',
    need_auth: true,
    auth_state: BuildChannelAuthState.NOT_AUTHORIZED,
  };

  const customBuildChannel = {
    id: '71a29c99-0182-4bf3-aa15-b6aee191e60b',
    name: 'Custom Build Channel',
    provider_name: 'Google Drive',
    need_auth: true,
    auth_state: BuildChannelAuthState.NOT_AUTHORIZED,
  };

  let buildChannelItem: BuildChannelItem;
  let buildChannelItemFixture: ComponentFixture<BuildChannelItem>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BuildChannelsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: BuildChannelsModuleNgSummary,
    });
    buildChannelItemFixture = TestBed.createComponent(BuildChannelItem);
    el = buildChannelItemFixture.debugElement;
    buildChannelItem = buildChannelItemFixture.componentInstance;
    buildChannelItem.buildChannel = defaultBuildChannel;
    buildChannelItemFixture.detectChanges();
  });

  it('gets initialized correctly', () => {
    expect(buildChannelItem).toBeTruthy();
  });

  it('displays build channels correctly', () => {
    const text = getTextContent(el);
    expect(text).toContain(defaultBuildChannel.name);
  });

  it('can delete custom build channels', () => {
    buildChannelItem.buildChannel = customBuildChannel;
    buildChannelItem.ngOnInit();
    buildChannelItemFixture.detectChanges();
    const onDeleteItem = jasmine.createSpy('onDeleteItem');
    buildChannelItem.deleteItem.subscribe(onDeleteItem);
    getEl(el, '.delete-button').click();
    expect(onDeleteItem).toHaveBeenCalled();
    expect(onDeleteItem).toHaveBeenCalledWith(customBuildChannel);
  });

  describe('edit button', () => {
    it('should display correct aria-label and tooltip', () => {
      const editButton = getEl(el, '.edit-button');
      expect(editButton).toBeTruthy();
      expect(editButton.getAttribute('aria-label')).toBe('Edit');
      expect(editButton.getAttribute('mattooltip')).toBe('Edit');
    });
  });

  describe('Authenticate button', () => {
    it('should display correct aria-label', () => {
      const authButton = getEl(el, '.auth-button');
      expect(authButton).toBeTruthy();
      expect(authButton.getAttribute('aria-label')).toBe('Authenticate');
    });
  });
});
