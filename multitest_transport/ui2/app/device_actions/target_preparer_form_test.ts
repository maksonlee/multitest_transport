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

import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockNameMultiValuePairList, newMockTradefedConfigObjectList} from '../testing/test_util';

import {DeviceActionsModule} from './device_actions_module';
import {DeviceActionsModuleNgSummary} from './device_actions_module.ngsummary';
import {TargetPreparerForm} from './target_preparer_form';
import {OptionValueChangeEvent} from './target_preparer_option_form';

describe('TargetPreparerForm', () => {
  let targetPreparerForm: TargetPreparerForm;
  let targetPreparerFormFixture: ComponentFixture<TargetPreparerForm>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, DeviceActionsModule],
      aotSummaries: DeviceActionsModuleNgSummary,
    });

    targetPreparerFormFixture = TestBed.createComponent(TargetPreparerForm);
    el = targetPreparerFormFixture.debugElement;
    targetPreparerForm = targetPreparerFormFixture.componentInstance;
    targetPreparerForm.targetPreparers = newMockTradefedConfigObjectList();
    targetPreparerFormFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(targetPreparerForm).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Class Name');
    expect(textContent).toContain('Add New Target Preparer Option');
  });

  it('called correct function on press add button', () => {
    const onAddTargetPreparer = jasmine.createSpy('onAddTargetPreparer');
    targetPreparerForm.addTargetPreparer.subscribe(onAddTargetPreparer);
    getEl(el, '#addTargetPreparerButton').click();
    expect(onAddTargetPreparer).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onDeleteTargetPreparer = jasmine.createSpy('onDeleteTargetPreparer');
    targetPreparerForm.deleteTargetPreparer.subscribe(onDeleteTargetPreparer);
    getEl(el, '.delete-button').click();
    expect(onDeleteTargetPreparer).toHaveBeenCalled();
    expect(onDeleteTargetPreparer).toHaveBeenCalledWith(0);
  });

  it('has correct number of entries', () => {
    const buttons = getEls(el, '.delete-button');
    expect(buttons.length).toBe(3);
  });

  describe('onAddOption', () => {
    it('adds a new option with valid index', () => {
      const tp = targetPreparerForm.targetPreparers[0];
      targetPreparerForm.onAddOption(tp);
      expect(tp.option_values!.length).toBe(1);
    });
  });

  describe('onRemoveOption', () => {
    it('removes an option with valid index', () => {
      const tp = targetPreparerForm.targetPreparers[1];
      targetPreparerForm.onAddOption(tp);
      expect(tp.option_values!.length).toBe(1);
      targetPreparerForm.onRemoveOption(tp, 0);
      expect(tp.option_values!.length).toBe(0);
    });
  });

  describe('onOptionValueChange', () => {
    it('returns correct output with valid input', () => {
      const event: OptionValueChangeEvent = {value: 'a\nb', index: 0};
      const tp = targetPreparerForm.targetPreparers[0];
      tp.option_values = newMockNameMultiValuePairList();
      const res = targetPreparerForm.onOptionValueChange(tp, event);
      expect(res![0]).toBe('a');
      expect(res![1]).toBe('b');
    });
  });
});
