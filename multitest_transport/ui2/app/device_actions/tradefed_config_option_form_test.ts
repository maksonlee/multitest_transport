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
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockNameMultiValuePairList} from '../testing/mtt_mocks';

import {DeviceActionsModule} from './device_actions_module';
import {TradefedConfigOptionForm} from './tradefed_config_option_form';

describe('TradefedConfigOptionForm', () => {
  let tradefedConfigOptionForm: TradefedConfigOptionForm;
  let tradefedConfigOptionFormFixture:
      ComponentFixture<TradefedConfigOptionForm>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, DeviceActionsModule],
      });

    tradefedConfigOptionFormFixture =
        TestBed.createComponent(TradefedConfigOptionForm);
    el = tradefedConfigOptionFormFixture.debugElement;
    tradefedConfigOptionForm =
        tradefedConfigOptionFormFixture.componentInstance;
    tradefedConfigOptionForm.optionTypeName = 'Target Preparer Option';
    tradefedConfigOptionForm.optionValues = newMockNameMultiValuePairList();
    tradefedConfigOptionFormFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(tradefedConfigOptionForm).toBeTruthy();

    const textContent = getTextContent(el);
    expect(textContent).toContain('Name');
    expect(textContent).toContain('Add New Target Preparer Option');

    // Inputs should be editable
    const optionNameInput = getEl(el, '.option-name-input');
    expect(optionNameInput.getAttribute('readonly')).toBeNull();
    const optionValueInput = getEl(el, '.option-value-input');
    expect(optionValueInput.getAttribute('readonly')).toBeNull();
  });

  it('should show hide add and delete buttons when not editable', () => {
    tradefedConfigOptionForm.canEdit = false;
    tradefedConfigOptionFormFixture.detectChanges();

    const addButton = tradefedConfigOptionFormFixture.debugElement.query(
        By.css('.add-option-button'));
    expect(addButton).toBeFalsy();
    const deleteButton = tradefedConfigOptionFormFixture.debugElement.query(
        By.css('.shared-delete-buttton'));
    expect(deleteButton).toBeFalsy();

    // Inputs should be editable
    const optionNameInput = getEl(el, '.option-name-input');
    expect(optionNameInput.getAttribute('readonly')).toEqual('true');
    const optionValueInput = getEl(el, '.option-value-input');
    expect(optionValueInput.getAttribute('readonly')).toEqual('true');
  });

  it('called correct function on press add button', () => {
    const onAddOption = jasmine.createSpy('onAddOption');
    tradefedConfigOptionForm.addOption.subscribe(onAddOption);
    getEl(el, '.add-option-button').click();
    expect(onAddOption).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onRemoveOption = jasmine.createSpy('onRemoveOption');
    tradefedConfigOptionForm.removeOption.subscribe(onRemoveOption);
    getEl(el, '.shared-delete-button').click();
    expect(onRemoveOption).toHaveBeenCalled();
    expect(onRemoveOption).toHaveBeenCalledWith(0);
  });

  it('called correct function on changing textarea content', () => {
    const onOptionValueChange = jasmine.createSpy('onOptionValueChange');
    tradefedConfigOptionForm.optionValueChange.subscribe(onOptionValueChange);
    const textarea = el.query(By.css('textarea')).nativeElement;
    textarea.value = '123';
    textarea.dispatchEvent(new Event('input'));
    expect(onOptionValueChange).toHaveBeenCalled();
    expect(onOptionValueChange).toHaveBeenCalledWith({value: '123', index: 0});
  });

  it('has correct number of entries', () => {
    const buttons = getEls(el, '.shared-delete-button');
    expect(buttons.length).toBe(4);
  });

  describe('delete button', () => {
    it('should display correct aria-label and tooltip', () => {
      const deleteButon = getEl(el, '.shared-delete-button');
      expect(deleteButon).toBeTruthy();
      expect(deleteButon.getAttribute('aria-label')).toBe('Delete');
      expect(deleteButon.getAttribute('mattooltip')).toBe('Delete');
    });
  });

  describe('add button', () => {
    it('should display correct aria-label', () => {
      const addButton = getEl(el, '.add-option-button');
      expect(addButton).toBeTruthy();
      expect(addButton.getAttribute('aria-label'))
          .toBe('Add new target preparer option');
    });
  });
});
