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

import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {TestRunHookPicker} from './test_run_hook_picker';
import {TestRunHookConfig} from '../services/mtt_models';
import {TestRunHooksModule} from './test_run_hooks_module';
import {TestRunHooksModuleNgSummary} from './test_run_hooks_module.ngsummary';

describe('TestRunHookPicker', () => {
  let fixture: ComponentFixture<TestRunHookPicker>;
  let element: DebugElement;
  let component: TestRunHookPicker;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, TestRunHooksModule],
      aotSummaries: TestRunHooksModuleNgSummary,
    });

    fixture = TestBed.createComponent(TestRunHookPicker);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    reload([]);
  });

  /** Convenience method to reload a new set of hook configs. */
  function reload(configs: Array<Partial<TestRunHookConfig>>) {
    component.hookConfigs = configs as TestRunHookConfig[];
    component.selectedHookConfigs = configs as TestRunHookConfig[];
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
  });

  it('can display a list of selected hook configs', () => {
    reload([{name: 'Hook #1'}, {name: 'Hook #2'}]);
    const items = getEls(element, '.test-run-hook-item');
    expect(items.length).toBe(2);
  });

  it('can remove a selected hook config', () => {
    reload([{name: 'Hook #1'}]);
    getEl(element, '.clear-button').click();
    expect(component.selectedHookConfigs.length).toBe(0);
  });

  it('can open the hook selection menu', () => {
    // no menu initially
    expect(hasEl(element, '.test-run-hook-menu')).toBeFalsy();
    // pressing the add button will open it
    getEl(element, '.add-button').click();
    expect(hasEl(element, '.test-run-hook-menu')).toBeTruthy();
  });
});
