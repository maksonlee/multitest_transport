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
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {getEls} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {SharedModule} from './shared_module';
import {TimeFilterOperator, TimeInputFilter} from './time_input_filter';

describe('TimeInputFilter', () => {
  const onFilterChangeSpy = jasmine.createSpy('filterChange');

  let timeInputFilter: TimeInputFilter;
  let timeInputFilterFixture: ComponentFixture<TimeInputFilter>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      declarations: [TimeInputFilter],
      });
    timeInputFilterFixture = TestBed.createComponent(TimeInputFilter);
    el = timeInputFilterFixture.debugElement;
    timeInputFilter = timeInputFilterFixture.componentInstance;
    timeInputFilter.timeFilterChange.subscribe(onFilterChangeSpy);
    timeInputFilterFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(timeInputFilter).toBeTruthy();
  });

  it('displays one input for relevant operators', () => {
    timeInputFilter.operator = TimeFilterOperator.ALL;
    timeInputFilterFixture.detectChanges();
    expect(getEls(el, 'input').length).toEqual(0);

    timeInputFilter.operator = TimeFilterOperator.GREATER_THAN;
    timeInputFilterFixture.detectChanges();
    expect(getEls(el, 'input').length).toEqual(1);
  });

  it('determines the "ALL" option is selected', () => {
    timeInputFilter.operator = TimeFilterOperator.ALL;
    expect(timeInputFilter.isAllOptionSelected()).toBeTrue();

    timeInputFilter.operator = TimeFilterOperator.GREATER_THAN;
    expect(timeInputFilter.isAllOptionSelected()).toBeFalse();
  });

  it('applies filter correctly', () => {
    timeInputFilter.operator = TimeFilterOperator.ALL;
    timeInputFilter.filterChange();
    expect(onFilterChangeSpy).toHaveBeenCalledTimes(1);

    timeInputFilter.operator = TimeFilterOperator.GREATER_THAN;
    timeInputFilter.number = 10;
    timeInputFilter.filterChange();
    expect(onFilterChangeSpy).toHaveBeenCalledTimes(2);

    timeInputFilter.operator = TimeFilterOperator.WITHIN;
    timeInputFilter.number = 0;
    timeInputFilter.filterChange();
    expect(onFilterChangeSpy).toHaveBeenCalledTimes(2);
  });
});
