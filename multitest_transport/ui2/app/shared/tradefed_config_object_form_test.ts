/**
 * Copyright 2022 Google LLC
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
import {newMockNameMultiValuePairList, newMockTradefedConfigObjectList} from '../testing/mtt_mocks';

import {OptionValueChangeEvent} from './name_multi_value_pair_list_form';
import {SharedModule} from './shared_module';
import {TradefedConfigObjectForm} from './tradefed_config_object_form';

describe('TradefedConfigObjectForm', () => {
  let configObjectForm: TradefedConfigObjectForm;
  let configObjectFormFixture: ComponentFixture<TradefedConfigObjectForm>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
    });

    configObjectFormFixture = TestBed.createComponent(TradefedConfigObjectForm);
    el = configObjectFormFixture.debugElement;
    configObjectForm = configObjectFormFixture.componentInstance;
    configObjectForm.configObjects = newMockTradefedConfigObjectList();
    configObjectForm.configObjectName = 'Target Preparer';
    configObjectFormFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(configObjectForm).toBeTruthy();

    const textContent = getTextContent(el);
    expect(textContent).toContain('Class Name');
    expect(textContent).toContain('Add New Target Preparer Option');

    // Inputs should be editable
    const classNameInput = getEl(el, '.class-name-input');
    expect(classNameInput.getAttribute('readonly')).toBeNull();
  });

  it('should hide add and remove buttons when not editable', () => {
    configObjectForm.canEdit = false;
    configObjectFormFixture.detectChanges();
    const textContent = getTextContent(el);
    expect(textContent).not.toContain('Add Target Preparer');
    expect(textContent).not.toContain('Remove');

    const classNameInput = getEl(el, '.class-name-input');
    expect(classNameInput.getAttribute('readonly')).toEqual('true');
  });

  it('called correct function on press add button', () => {
    const onAddConfigObject = jasmine.createSpy('onAddConfigObject');
    configObjectForm.addConfigObject.subscribe(onAddConfigObject);
    getEl(el, '#addConfigObjectButton').click();
    expect(onAddConfigObject).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onDeleteConfigObject = jasmine.createSpy('onDeleteConfigObject');
    configObjectForm.deleteConfigObject.subscribe(onDeleteConfigObject);
    getEl(el, '.delete-button').click();
    expect(onDeleteConfigObject).toHaveBeenCalled();
    expect(onDeleteConfigObject).toHaveBeenCalledWith(0);
  });

  it('has correct number of entries', () => {
    const buttons = getEls(el, '.delete-button');
    expect(buttons.length).toBe(3);
  });

  describe('onAddOption', () => {
    it('adds a new option with valid index', () => {
      const tp = configObjectForm.configObjects[0];
      configObjectForm.onAddOption(tp);
      expect(tp.option_values!.length).toBe(1);
    });
  });

  describe('onRemoveOption', () => {
    it('removes an option with valid index', () => {
      const tp = configObjectForm.configObjects[1];
      configObjectForm.onAddOption(tp);
      expect(tp.option_values!.length).toBe(1);
      configObjectForm.onRemoveOption(tp, 0);
      expect(tp.option_values!.length).toBe(0);
    });
  });

  describe('onOptionValueChange', () => {
    it('returns correct output with valid input', () => {
      const event: OptionValueChangeEvent = {value: 'a\nb', index: 0};
      const tp = configObjectForm.configObjects[0];
      tp.option_values = newMockNameMultiValuePairList();
      const res = configObjectForm.onOptionValueChange(tp, event);
      expect(res![0]).toBe('a');
      expect(res![1]).toBe('b');
    });
  });
});
