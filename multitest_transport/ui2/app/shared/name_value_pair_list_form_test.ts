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
import {ComponentFixture, fakeAsync, TestBed} from '@angular/core/testing';
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockNameValuePairList} from '../testing/mtt_mocks';
import {NameValuePairListForm} from './name_value_pair_list_form';
import {SharedModule} from './shared_module';

describe('NameValuePairListForm', () => {
  let nameValuePairListForm: NameValuePairListForm;
  let nameValuePairListFormFixture: ComponentFixture<NameValuePairListForm>;
  let el: DebugElement;
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      });
    nameValuePairListFormFixture =
        TestBed.createComponent(NameValuePairListForm);
    el = nameValuePairListFormFixture.debugElement;
    nameValuePairListForm = nameValuePairListFormFixture.componentInstance;
    nameValuePairListForm.data = newMockNameValuePairList();
    nameValuePairListFormFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(nameValuePairListForm).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Name');
    expect(textContent).toContain('Value');
  });

  it('called correct function on press add button', () => {
    const onAddNameValuePair = jasmine.createSpy('onAddNameValuePair');
    nameValuePairListForm.addNameValuePair.subscribe(onAddNameValuePair);
    getEl(el, '.add-button').click();
    expect(onAddNameValuePair).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onRemoveNameValuePair = jasmine.createSpy('onRemoveNameValuePair');
    nameValuePairListForm.removeNameValuePair.subscribe(onRemoveNameValuePair);
    getEl(el, '.shared-delete-button').click();
    expect(onRemoveNameValuePair).toHaveBeenCalled();
    expect(onRemoveNameValuePair).toHaveBeenCalledWith(0);
  });

  it('displayed correct number of data', () => {
    const deleteButtons = getEls(el, '.shared-delete-button');
    expect(deleteButtons.length).toBe(3);
  });

  it('displayed correct data content', fakeAsync(() => {
       nameValuePairListFormFixture.whenStable().then(() => {
         const inputEls = el.queryAll(By.css('input'));
         expect(inputEls.length).toBe(6);
         expect(inputEls[0].nativeElement.value).toBe('pair1');
         expect(inputEls[2].nativeElement.value).toBe('pair2');
         expect(inputEls[4].nativeElement.value).toBe('pair3');
       });
     }));

  describe('add button', () => {
    it('should display correct aria-label', () => {
      const addButton = getEl(el, '.add-button');
      expect(addButton).toBeTruthy();
      expect(addButton.getAttribute('aria-label')).toBe('Add');
    });
  });

  describe('delete button', () => {
    it('should display correct aria-label and tooltip', () => {
      const deleteButton = getEl(el, '.shared-delete-button');
      expect(deleteButton).toBeTruthy();
      expect(deleteButton.getAttribute('aria-label')).toBe('Delete');
      expect(deleteButton.getAttribute('mattooltip')).toBe('Delete');
    });
  });
});
