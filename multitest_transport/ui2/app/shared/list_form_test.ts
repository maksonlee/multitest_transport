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
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getEl, getTextContent} from '../testing/jasmine_util';

import {ListForm} from './list_form';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('ListForm', () => {
  let listForm: ListForm;
  let listFormFixture: ComponentFixture<ListForm>;
  let el: DebugElement;
  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });
    listFormFixture = TestBed.createComponent(ListForm);
    el = listFormFixture.debugElement;
    listForm = listFormFixture.componentInstance;
    listForm.data = ['aa', 'bb', 'cc'];
    listForm.label = 'row';
    listFormFixture.detectChanges();
    await listFormFixture.whenStable();
  });

  it('initializes a component', () => {
    expect(listForm).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Add');
    expect(textContent).toContain('delete');
  });

  it('called correct function on press add button', () => {
    const onAddItem = jasmine.createSpy('onAddItem');
    listForm.addItem.subscribe(onAddItem);
    getEl(el, '.add-button').click();
    expect(onAddItem).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onRemoveItem = jasmine.createSpy('onRemoveItem');
    listForm.removeItem.subscribe(onRemoveItem);
    getEl(el, '.shared-delete-button').click();
    expect(onRemoveItem).toHaveBeenCalled();
    expect(onRemoveItem).toHaveBeenCalledWith(0);
  });

  it('displayed correct data content', () => {
    const inputEls = el.queryAll(By.css('input'));
    expect(inputEls.length).toBe(3);
    for (let i = 0; i < inputEls.length; i++) {
      const actual = inputEls[i].nativeElement.value;
      const expected = listForm.data[i];
      expect(actual).toEqual(expected);
    }
  });

  describe('add button', () => {
    it('displayed correct label and content', () => {
      const addButton = getEl(el, '.add-button');
      expect(addButton).toBeTruthy();
      expect(addButton.innerText).toBe('+ Add');
      expect(addButton.getAttribute('aria-label')).toBe('Add');
    });
  });

  describe('delete button', () => {
    it('displayed correct label and tooltip', () => {
      const deleteButton = getEl(el, '.shared-delete-button');
      expect(deleteButton).toBeTruthy();
      expect(deleteButton.getAttribute('aria-label')).toBe('Delete');
      expect(deleteButton.getAttribute('matTooltip')).toBe('Delete');
    });
  });
});
