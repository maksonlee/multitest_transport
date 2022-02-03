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
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {TestRunAction} from '../services/mtt_models';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {TestRunActionPicker} from './test_run_action_picker';
import {TestRunActionsModule} from './test_run_actions_module';

describe('TestRunActionPicker', () => {
  let fixture: ComponentFixture<TestRunActionPicker>;
  let element: DebugElement;
  let component: TestRunActionPicker;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, TestRunActionsModule],
      });

    fixture = TestBed.createComponent(TestRunActionPicker);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    reload([]);
  });

  /** Convenience method to reload a new set of actions. */
  function reload(actions: Array<Partial<TestRunAction>>) {
    component.actions = actions as TestRunAction[];
    component.selectedActions = actions as TestRunAction[];
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
  });

  it('can display a list of selected actions', () => {
    reload([{name: 'Action #1'}, {name: 'Action #2'}]);
    const items = getEls(element, '.test-run-action-item');
    expect(items.length).toBe(2);
  });

  it('can display action options', async () => {
    reload([{
      name: 'Action',
      options: [{name: 'K1', value: 'V1'}, {name: 'K2', value: 'V2'}]
    }]);
    await fixture.whenStable();
    const options = getEls(element, '.test-run-action-option');
    expect(options.length).toBe(2);
    expect(options[0].textContent).toContain('K1');
    expect(options[0].getElementsByTagName('input')[0].value).toEqual('V1');
    expect(options[1].textContent).toContain('K2');
    expect(options[1].getElementsByTagName('input')[0].value).toEqual('V2');
  });

  it('can remove a selected action', () => {
    reload([{name: 'Action'}]);
    getEl(element, '.clear-button').click();
    expect(component.selectedActions.length).toBe(0);
  });

  it('can open the action selection menu', () => {
    // no menu initially
    expect(hasEl(element, '.test-run-action-menu')).toBeFalsy();
    // pressing the add button will open it
    getEl(element, '.add-button').click();
    expect(hasEl(element, '.test-run-action-menu')).toBeTruthy();
  });

  it('can add selected actions', async () => {
    const action = {options: [{name: 'key', value: 'value'}]} as TestRunAction;
    expect(component.selectedActions.length).toBe(0);

    // select and add an action
    component.selection.select(action);
    component.addSelected();
    expect(component.selectedActions.length).toBe(1);
    expect(component.selection.isEmpty()).toBeTruthy();

    // add the same action again
    component.selection.select(action);
    component.addSelected();
    expect(component.selectedActions.length).toBe(2);

    // two deep copies were generated
    expect(component.selectedActions[0]).not.toBe(component.selectedActions[1]);
    component.selectedActions[0].options![0].value = 'updated';
    expect(component.selectedActions[1].options![0].value).toEqual('value');
  });
});
