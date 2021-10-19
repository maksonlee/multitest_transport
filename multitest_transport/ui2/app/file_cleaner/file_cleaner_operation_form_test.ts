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

import {FileCleanerOperationType} from '../services/mtt_models';
import {getTextContent} from '../testing/jasmine_util';
import {newMockFileCleanerOperation} from '../testing/mtt_mocks';

import {FileCleanerModule} from './file_cleaner_module';
import {FileCleanerOperationForm} from './file_cleaner_operation_form';

describe('FileCleanerOperationForm', () => {
  let fixture: ComponentFixture<FileCleanerOperationForm>;
  let element: DebugElement;
  let component: FileCleanerOperationForm;

  beforeEach(() => {
    TestBed.configureTestingModule(
        {imports: [FileCleanerModule, NoopAnimationsModule]});

    fixture = TestBed.createComponent(FileCleanerOperationForm);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    component.operation =
        newMockFileCleanerOperation(FileCleanerOperationType.ARCHIVE, []);
    fixture.detectChanges();
  });

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
  });

  it('can display texts correctly', () => {
    const textContent = getTextContent(element);
    expect(textContent).toContain('Operation Type');
    expect(textContent).toContain('Parameters');
  });

  it('can handle param event', () => {
    expect(component.operation.params).toBeDefined();
    component.onAddParam();
    component.onAddParam();
    expect(component.operation.params!.length).toBe(1);
    expect(component.operation.params![0].name).toBe('remove_file');
    expect(component.operation.params![0].value).toBe('True');

    component.onRemoveParam(0);
    expect(component.operation.params!.length).toBe(0);
  });
});
