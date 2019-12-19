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

import {getTextContent} from '../testing/jasmine_util';
import {OverflowList, OverflowListType} from './overflow_list';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('OverflowList', () => {
  let overflowList: OverflowList;
  let overflowListFixture: ComponentFixture<OverflowList>;
  let el: DebugElement;

  const labels = ['label1', 'labtwo', '3 label'];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      declarations: [OverflowList],
      aotSummaries: SharedModuleNgSummary,
    });
    overflowListFixture = TestBed.createComponent(OverflowList);
    el = overflowListFixture.debugElement;
    overflowList = overflowListFixture.componentInstance;
    overflowList.data = labels;
    overflowList.overflowListType = OverflowListType.BUTTON;
    overflowListFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(overflowList).toBeTruthy();
  });

  it('displays a single element', () => {
    overflowList.data = [labels[0]];
    overflowListFixture.detectChanges();

    const textContent = getTextContent(el);
    expect(textContent).toContain(labels[0]);
    expect(textContent).not.toContain('+');
  });

  it('collapses multiple elements', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain(labels[0]);
    expect(textContent).toContain('+2');
    expect(textContent).not.toContain(labels[1]);
    expect(textContent).not.toContain(labels[2]);
  });

  it('handles empty data', () => {
    overflowList.data = [];
    overflowListFixture.detectChanges();

    const textContent = getTextContent(el);
    expect(textContent).toEqual('');
  });
});
