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

import {DebugElement, ElementRef} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getTextContent} from '../testing/jasmine_util';
import {FormErrorInfo} from './form_error_info';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('FormErrorInfo', () => {
  let formErrorInfo: FormErrorInfo;
  let formErrorInfoFixture: ComponentFixture<FormErrorInfo>;
  let el: DebugElement;
  let elementRef: ElementRef;
  beforeEach(() => {
    const element = document.createElement('div');
    document.body.appendChild(element);
    elementRef = new ElementRef(element);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });
    formErrorInfoFixture = TestBed.createComponent(FormErrorInfo);
    el = formErrorInfoFixture.debugElement;
    formErrorInfo = formErrorInfoFixture.componentInstance;
    formErrorInfo.invalidInputs = [elementRef];
    formErrorInfoFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(formErrorInfo).toBeTruthy();
  });

  it('displays texts correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Your changes could not be saved');
    expect(textContent).toContain('1 issue');
    expect(textContent).toContain('See first issue ');
  });
});
