/**
 * Copyright 2021 Google LLC
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

import {FileCleanerCriterionType} from '../services/mtt_models';
import {getTextContent} from '../testing/jasmine_util';
import {newMockFileCleanerCriterion} from '../testing/mtt_mocks';

import {FileCleanerCriterionForm} from './file_cleaner_criterion_form';
import {FileCleanerModule} from './file_cleaner_module';

describe('FileCleanerCriterionForm', () => {
  let fixture: ComponentFixture<FileCleanerCriterionForm>;
  let element: DebugElement;
  let component: FileCleanerCriterionForm;

  beforeEach(() => {
    TestBed.configureTestingModule(
        {imports: [FileCleanerModule, NoopAnimationsModule]});

    fixture = TestBed.createComponent(FileCleanerCriterionForm);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    component.criteria = [newMockFileCleanerCriterion(
        FileCleanerCriterionType.LAST_ACCESS_TIME, [])];
    fixture.detectChanges();
  });

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
  });

  it('can display texts correctly', () => {
    const textContent = getTextContent(element);
    expect(textContent).toContain('Criterion');
    expect(textContent).toContain('Criterion Type');
    expect(textContent).toContain('Parameters');
    expect(textContent).toContain('+ Add Criterion');
  });

  it('can handle param event', () => {
    const criterion = component.criteria[0];
    expect(criterion.params).toBeDefined();
    component.onAddParam(criterion);
    component.onAddParam(criterion);
    expect(criterion.params!.length).toBe(1);
    expect(criterion.params![0].name).toBe('ttl');
    expect(criterion.params![0].value).toBe('7 days');

    component.onRemoveParam(criterion, 0);
    expect(criterion.params!.length).toBe(0);
  });
});
