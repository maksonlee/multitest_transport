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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf, throwError} from 'rxjs';

import {MttClient, TestRunHookClient} from '../services/mtt_client';
import {AuthorizationState, TestRunHookConfig} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {TestRunHookList} from './test_run_hook_list';
import {TestRunHooksModule} from './test_run_hooks_module';
import {TestRunHooksModuleNgSummary} from './test_run_hooks_module.ngsummary';

describe('TestRunHookList', () => {
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let notifier: jasmine.SpyObj<Notifier>;
  let hookClient: jasmine.SpyObj<TestRunHookClient>;

  let fixture: ComponentFixture<TestRunHookList>;
  let element: DebugElement;
  let component: TestRunHookList;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    notifier = jasmine.createSpyObj('notifier', ['confirm', 'showError']);
    hookClient =
        jasmine.createSpyObj('hookClient', ['list', 'authorize', 'delete']);
    hookClient.list.and.returnValue(observableOf([]));
    hookClient.authorize.and.returnValue(observableOf(null));
    hookClient.delete.and.returnValue(observableOf(null));

    TestBed.configureTestingModule({
      imports: [TestRunHooksModule, NoopAnimationsModule],
      aotSummaries: TestRunHooksModuleNgSummary,
      providers: [
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: Notifier, useValue: notifier},
        {provide: MttClient, useValue: {testRunHooks: hookClient}},
      ],
    });

    fixture = TestBed.createComponent(TestRunHookList);
    fixture.detectChanges();
    element = fixture.debugElement;
    component = fixture.componentInstance;
  });

  /** Convenience method to reload a new set of hook configs. */
  function reload(configs: Array<Partial<TestRunHookConfig>>) {
    hookClient.list.and.returnValue(observableOf(configs));
    component.load();
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
    expect(hookClient.list).toHaveBeenCalled();
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can announce loading start and end', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    expect(liveAnnouncer.announce)
        .toHaveBeenCalledWith('Test run hooks loaded', 'assertive');
  });

  it('can detect that no hook configs were loaded', () => {
    expect(hasEl(element, 'mat-card')).toBeFalsy();
    expect(hasEl(element, '.empty')).toBeTruthy();
  });

  it('can display a list of hook configs', () => {
    reload([{name: 'Hook #1'}, {name: 'Hook #2'}]);
    const cards = getEls(element, 'mat-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('Hook #1');
    expect(cards[1].textContent).toContain('Hook #2');
    expect(hasEl(element, '.empty')).toBeFalsy();
  });

  it('can handle errors when loading hook configs', () => {
    hookClient.list.and.returnValue(throwError('loading failed'));
    component.load();
    expect(notifier.showError).toHaveBeenCalled();
  });

  it('can display an authorized hook config', () => {
    reload([{authorization_state: AuthorizationState.AUTHORIZED}]);
    const statusButton = getEl(element, 'mat-card status-button');
    expect(statusButton.textContent).toContain('Authorized');
    expect(hasEl(element, 'mat-card #auth-button')).toBeFalsy();
  });

  it('can display an unauthorized hook config', () => {
    reload([{authorization_state: AuthorizationState.UNAUTHORIZED}]);
    const statusButton = getEl(element, 'mat-card status-button');
    expect(statusButton.textContent).toContain('Unauthorized');
    expect(hasEl(element, 'mat-card #auth-button')).toBeTruthy();
  });

  it('can display a hook config without authorization', () => {
    reload([{authorization_state: AuthorizationState.NOT_APPLICABLE}]);
    expect(hasEl(element, 'mat-card status-button')).toBeFalsy();
    expect(hasEl(element, 'mat-card #auth-button')).toBeFalsy();
  });

  it('can authorize a hook config', () => {
    reload([
      {id: 'hook_id', authorization_state: AuthorizationState.UNAUTHORIZED}
    ]);
    getEl(element, 'mat-card #auth-button').click();
    expect(hookClient.authorize).toHaveBeenCalledWith('hook_id');
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can handle errors when authorizing a hook config', () => {
    hookClient.authorize.and.returnValue(throwError('authorize failed'));
    reload([
      {id: 'hook_id', authorization_state: AuthorizationState.UNAUTHORIZED}
    ]);
    getEl(element, 'mat-card #auth-button').click();
    expect(notifier.showError).toHaveBeenCalled();
  });

  it('can delete a hook config', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    reload([{id: 'hook_id'}]);
    getEl(element, 'mat-card #delete-button').click();
    expect(hookClient.delete).toHaveBeenCalledWith('hook_id');
    expect(component.hookConfigs).toEqual([]);  // hook config removed
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can confirm deleting a hook config', () => {
    notifier.confirm.and.returnValue(observableOf(false));  // cancel delete
    reload([{id: 'hook_id'}]);
    getEl(element, 'mat-card #delete-button').click();
    expect(hookClient.delete).not.toHaveBeenCalledWith('hook_id');
  });

  it('can handle errors when deleting a hook config', () => {
    hookClient.delete.and.returnValue(throwError('delete failed'));
    notifier.confirm.and.returnValue(observableOf(true));    // confirm delete
    reload([{id: 'hook_id'}]);
    getEl(element, 'mat-card #delete-button').click();
    expect(notifier.showError).toHaveBeenCalled();
  });
});
