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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf, throwError} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {AuthorizationState, BuildChannel} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {getEl, hasEl} from '../testing/jasmine_util';

import {BuildChannelItem} from './build_channel_item';
import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';

describe('BuildChannelItem', () => {
  let mtt: jasmine.SpyObj<MttClient>;
  let notifier: jasmine.SpyObj<Notifier>;

  let component: BuildChannelItem;
  let fixture: ComponentFixture<BuildChannelItem>;
  let element: DebugElement;

  beforeEach(() => {
    notifier = jasmine.createSpyObj(['showError']);
    mtt = jasmine.createSpyObj(['authorizeBuildChannel']);

    TestBed.configureTestingModule({
      imports: [BuildChannelsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: BuildChannelsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mtt},
        {provide: Notifier, useValue: notifier},
      ],
    });

    fixture = TestBed.createComponent(BuildChannelItem);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    spyOn(component.authChange, 'emit');
    spyOn(component.deleteItem, 'emit');
  });

  /** Convenience method to reload a new build channel. */
  function reload(data: Partial<BuildChannel>, editable = true) {
    component.buildChannel = data as BuildChannel;
    component.edit = editable;
    fixture.detectChanges();
  }

  it('can display an authorized build channel', () => {
    reload({auth_state: AuthorizationState.AUTHORIZED});
    expect(hasEl(element, '.auth-button')).toBeFalsy();
  });

  it('can display an unauthorized build channel', () => {
    reload({auth_state: AuthorizationState.UNAUTHORIZED});
    expect(hasEl(element, '.auth-button')).toBeTruthy();
  });

  it('can display a build channel without authorization', () => {
    reload({auth_state: AuthorizationState.NOT_APPLICABLE});
    expect(hasEl(element, '.auth-button')).toBeFalsy();
  });

  it('can enable editing', () => {
    reload({}, true);
    expect(hasEl(element, '.edit-button')).toBeTruthy();
    expect(hasEl(element, '.delete-button')).toBeTruthy();
  });

  it('can disable editing', () => {
    reload({}, false);
    expect(hasEl(element, '.edit-button')).toBeFalsy();
    expect(hasEl(element, '.delete-button')).toBeFalsy();
  });

  it('can display a default build channel', () => {
    reload({id: 'google_cloud_storage'});  // default GCS build channel
    // can't delete default build channel
    expect(hasEl(element, '.edit-button')).toBeTruthy();
    expect(hasEl(element, '.delete-button')).toBeFalsy();
  });

  it('can delete a build channel', () => {
    reload({id: 'bc_id'});
    getEl(element, '.delete-button').click();
    // notifies parent to delete item
    expect(component.deleteItem.emit)
        .toHaveBeenCalledWith(jasmine.objectContaining({id: 'bc_id'}));
  });

  it('can authorize a build channel', fakeAsync(() => {
       mtt.authorizeBuildChannel.and.returnValue(observableOf(null));
       reload({id: 'bc_id', auth_state: AuthorizationState.UNAUTHORIZED});
       getEl(element, '.auth-button').click();
       tick(500);
       // authorizes build channel and notifies parent
       expect(mtt.authorizeBuildChannel).toHaveBeenCalledWith('bc_id');
       expect(notifier.showError).not.toHaveBeenCalled();
       expect(component.authChange.emit)
           .toHaveBeenCalledWith(jasmine.objectContaining({id: 'bc_id'}));
     }));

  it('can handle errors when authorizing', () => {
    mtt.authorizeBuildChannel.and.returnValue(throwError('authorize failed'));
    reload({id: 'bc_id', auth_state: AuthorizationState.UNAUTHORIZED});
    getEl(element, '.auth-button').click();
    // displays error and doesn't notify parent
    expect(notifier.showError).toHaveBeenCalled();
    expect(component.authChange.emit).not.toHaveBeenCalled();
  });
});
