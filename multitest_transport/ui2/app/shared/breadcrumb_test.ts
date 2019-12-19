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

import {DebugElement, SimpleChange} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {Breadcrumb} from './breadcrumb';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('Breadcrumb', () => {
  let breadcrumb: Breadcrumb;
  let breadcrumbFixture: ComponentFixture<Breadcrumb>;
  let el: DebugElement;
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });
    breadcrumbFixture = TestBed.createComponent(Breadcrumb);
    el = breadcrumbFixture.debugElement;
    breadcrumb = breadcrumbFixture.componentInstance;
    breadcrumb.path = 'a/b/c';
    breadcrumbFixture.detectChanges();
    breadcrumb.ngOnChanges(
        {path: new SimpleChange(null, breadcrumb.path, true)});
  });

  it('initializes a component', () => {
    expect(breadcrumb).toBeTruthy();
  });

  it('initializes correct path array', () => {
    expect(breadcrumb.pathArray.length).toBe(3);
    expect(breadcrumb.pathArray).toEqual(['a', 'b', 'c']);
  });

  describe('onPathClick', () => {
    it('clear path array if root element is clicked', () => {
      breadcrumb.onPathClick(undefined);
      expect(breadcrumb.pathArray.length).toBe(0);
    });

    it('resets path array to have correct content', () => {
      breadcrumb.onPathClick(1);
      expect(breadcrumb.pathArray.length).toBe(2);
      expect(breadcrumb.pathArray).toEqual(['a', 'b']);
    });
  });
});
