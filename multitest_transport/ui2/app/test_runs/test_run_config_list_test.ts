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

import {HttpClientTestingModule} from '@angular/common/http/testing';
import {DebugElement} from '@angular/core';
import {inject, ComponentFixture, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {APP_DATA} from '../services/app_data';
import {Test, TestRunConfig} from '../services/mtt_models';
import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockTest, newMockTestRunConfig} from '../testing/test_util';

import {TestRunConfigList} from './test_run_config_list';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunConfigList', () => {
  let testRunConfigs: TestRunConfig[];
  let test1: Test;
  let test2: Test;
  let testMap: {[id: string]: Test};

  let testRunConfigList: TestRunConfigList;
  let testRunConfigListFixture: ComponentFixture<TestRunConfigList>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, TestRunsModule, HttpClientTestingModule],
      providers: [
        {provide: APP_DATA, useValue: {}},
      ],
      aotSummaries: TestRunsModuleNgSummary,
    });

    test1 = newMockTest('test1');
    test2 = newMockTest('xTS 2.0');
    testMap = {[test1.id!]: test1, [test2.id!]: test2};
    testRunConfigs =
        [newMockTestRunConfig(test1.id!), newMockTestRunConfig(test2.id!)];

    testRunConfigListFixture = TestBed.createComponent(TestRunConfigList);
    el = testRunConfigListFixture.debugElement;
    testRunConfigList = testRunConfigListFixture.componentInstance;
    testRunConfigList.data = testRunConfigs;
    testRunConfigList.testMap = testMap;
    testRunConfigListFixture.detectChanges();
  });

  it('should get initialized correctly', () => {
    expect(testRunConfigList).toBeTruthy();
  });

  it('should render HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain(test1.name);
    expect(textContent).toContain(test2.name);
  });

  it('should displays correct number of items', () => {
    const items = getEls(el, '.mat-card');
    expect(items).toBeTruthy();
    expect(items.length).toBe(testRunConfigList.data.length);
  });

  it('should trigger removeTestRunConfig on delete button click', () => {
    const removeItemIndex = 0;
    spyOn(testRunConfigList, 'delete');
    getEl(el, '.test-run-config-delete-button').click();
    expect(testRunConfigList.delete).toHaveBeenCalledWith(removeItemIndex);
  });

  it('should open test run config editor on openTestRunConfigEditor called',
     inject([MatDialog], (dialog: MatDialog) => {
       spyOn(dialog, 'open').and.callThrough();
       testRunConfigList.add();
       expect(dialog.open).toHaveBeenCalled();
       expect(dialog.open).toHaveBeenCalledTimes(1);
     }));

  describe('delete button', () => {
    it('should display correct aria-label and tooltip', () => {
      const deleteButton = getEl(el, '.test-run-config-delete-button');
      expect(deleteButton).toBeTruthy();
      expect(deleteButton.getAttribute('aria-label')).toBe('Delete');
      expect(deleteButton.getAttribute('mattooltip')).toBe('Delete');
    });
  });

  describe('add button', () => {
    it('should display correct aria-label and tooltip', () => {
      const addButton = getEl(el, '.add-button');
      expect(addButton).toBeTruthy();
      expect(addButton.getAttribute('aria-label'))
          .toBe('Add test run configuration');
    });
  });
});
