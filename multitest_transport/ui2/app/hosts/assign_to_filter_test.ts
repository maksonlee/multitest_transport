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

import {HostAssignInfo} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';

import {AssignToFilter} from './assign_to_filter';
import {HostsModule} from './hosts_module';

describe('AssignToFilter', () => {
  let assignToFilter: AssignToFilter;
  let assignToFilterFixture: ComponentFixture<AssignToFilter>;
  let el: DebugElement;
  let notifierSpy: jasmine.SpyObj<Notifier>;

  beforeEach(() => {
    notifierSpy = jasmine.createSpyObj('notifier', ['showError']);
    TestBed.configureTestingModule({
      declarations: [
        AssignToFilter,
      ],
      imports: [
        HostsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: Notifier, useValue: notifierSpy},
      ],
    });

    assignToFilterFixture = TestBed.createComponent(AssignToFilter);
    el = assignToFilterFixture.debugElement;
    assignToFilter = assignToFilterFixture.componentInstance;
    assignToFilter.selectedHostnames = [];
    assignToFilter.dataSource = ['user1', 'user2', 'user3'];
    assignToFilterFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(assignToFilter).toBeTruthy();
  });

  it('filters options correctly', async () => {
    await assignToFilterFixture.whenStable();
    assignToFilter.filterOptions('r3');
    expect(assignToFilter.filteredOptions).toEqual(['user3']);
  });

  it('calls enable and disable method when selectedHostnames changed',
     () => {
       spyOn(assignToFilter.valueControl, 'enable');
       spyOn(assignToFilter.valueControl, 'disable');

       assignToFilter.selectedHostnames = ['host1'];
       assignToFilter.ngOnChanges(
           {selectedHostnames: new SimpleChange([], ['host1'], false)});
       expect(assignToFilter.valueControl.enable).toHaveBeenCalledTimes(1);

       assignToFilter.selectedHostnames = [];
       assignToFilter.ngOnChanges(
           {selectedHostnames: new SimpleChange(['host1'], [], false)});
       expect(assignToFilter.valueControl.disable).toHaveBeenCalledTimes(1);
     });

  it('emits submit evnt correctly when assignTo is called with valid assignee',
     () => {
       spyOn(assignToFilter.submit, 'emit');
       const assignee = 'user3';
       assignToFilter.valueControl.setValue(assignee);
       assignToFilter.selectedHostnames = ['host1'];
       const assignInfo: HostAssignInfo = {
         hostnames: assignToFilter.selectedHostnames,
         assignee
       };

       assignToFilter.assignTo();
       expect(assignToFilter.submit.emit).toHaveBeenCalledWith(assignInfo);
     });

  it('calls showError method when assignTo is called with invalid assignee',
     () => {
       const assignee = ' ';
       assignToFilter.valueControl.setValue(assignee);
       assignToFilter.selectedHostnames = ['host1'];

       assignToFilter.assignTo();
       expect(notifierSpy.showError).toHaveBeenCalledTimes(1);
     });
});
