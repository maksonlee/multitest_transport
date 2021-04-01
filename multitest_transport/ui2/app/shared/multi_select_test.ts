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

import {DebugElement, SimpleChange} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {MultiSelect} from './multi_select';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('MultiSelect', () => {
  let multiSelect: MultiSelect;
  let multiSelectFixture: ComponentFixture<MultiSelect>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      declarations: [MultiSelect],
      aotSummaries: SharedModuleNgSummary,
    });
    multiSelectFixture = TestBed.createComponent(MultiSelect);
    el = multiSelectFixture.debugElement;
    multiSelect = multiSelectFixture.componentInstance;
    multiSelect.items = ['a', 'b', 'c', 'd'];
    multiSelect.ngOnChanges(
        {items: new SimpleChange(null, multiSelect.items, true)});
    multiSelectFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(multiSelect.multiSelectItems.length)
        .toEqual(multiSelect.items.length);
    expect(multiSelect).toBeTruthy();
  });

  it('selects or deselects all items correctly', () => {
    // Clear selection.
    multiSelect.selection = [];

    // Select all options.
    multiSelect.toggleAllSelection(true);
    expect(multiSelect.selection.length).toEqual(1);

    // Deselect all options.
    multiSelect.toggleAllSelection(false);
    expect(multiSelect.selection.length).toEqual(0);
  });

  it('should filter items correctly', () => {
    multiSelect.filterText = multiSelect.items[0];
    multiSelect.doFilter();
    const filterResults =
        multiSelect.multiSelectItems.filter((x) => x.hidden === false);
    expect(filterResults.length).toEqual(1);
  });

  it('should clear filtered items correctly', () => {
    multiSelect.clearFilter();

    // After filter text is clear should display all select options.
    expect(multiSelect.multiSelectItems.find(x => x.hidden === true))
        .toEqual(undefined);
  });

  it('detects all filtered items are selected correctly', () => {
    // Clear selection.
    multiSelect.selection = [multiSelect.items[0]];

    // Checks all items are selected.
    multiSelect.filterText = multiSelect.items[0];
    multiSelect.doFilter();
    expect(multiSelect.isAllFilteredSelected()).toEqual(true);

    // Checks all items are not selected.
    multiSelect.filterText = multiSelect.items[1];
    multiSelect.doFilter();
    expect(multiSelect.isAllFilteredSelected()).toEqual(false);
  });

  it('selects or deselects all filtered items correctly', () => {
    const selectionChangeSpy = spyOn(multiSelect.selectionChange, 'emit');

    // Clear selection.
    multiSelect.selection = [];
    multiSelect.filterText = multiSelect.items[0];
    multiSelect.doFilter();

    // Select all options.
    multiSelect.toggleFilteredSelection();
    expect(multiSelect.selection).toEqual([multiSelect.items[0]]);

    // Deselect all options.
    multiSelect.toggleFilteredSelection();
    expect(multiSelect.selection.length).toEqual(0);

    expect(selectionChangeSpy).toHaveBeenCalledTimes(2);
  });
});
