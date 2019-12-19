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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getEl, getEls, getTextContent} from '../testing/jasmine_util';

import {TestList} from './test_list';
import {TestModule} from './test_module';
import {TestModuleNgSummary} from './test_module.ngsummary';

describe('TestList', () => {
  const TESTS = [{id: 'id', name: 'name'}, {id: 'id2', name: 'name2'}];

  let testList: TestList;
  let testListFixture: ComponentFixture<TestList>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj('mttClient', ['getTests', 'deleteTest']);
    mttClient.getTests.and.returnValue(observableOf({tests: [...TESTS]}));
    mttClient.deleteTest.and.returnValue(observableOf({}));

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        TestModule,
        RouterTestingModule,
      ],
      aotSummaries: TestModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
    testListFixture = TestBed.createComponent(TestList);
    testListFixture.detectChanges();
    el = testListFixture.debugElement;
    testList = testListFixture.componentInstance;
  });

  afterEach(() => {
    testListFixture.destroy();
  });

  it('gets initialized correctly', () => {
    expect(testList).toBeTruthy();
  });

  it('calls API correctly', fakeAsync(() => {
       tick(200);
       testListFixture.whenStable().then(() => {
         expect(mttClient.getTests).toHaveBeenCalled();
       });
     }));

  it('displays tests correctly', fakeAsync(() => {
       tick(200);
       testListFixture.whenStable().then(() => {
         const textContent = getTextContent(el);
         for (const test of TESTS) {
           expect(textContent).toContain(test.name);
         }
       });
     }));

  it('deletes a test correctly', fakeAsync(() => {
       tick(200);
       testListFixture.whenStable().then(() => {
         // Delete the first test.
         getEl(el, '#menuButton').click();
         getEl(el, '#deleteButton').click();
         expect(mttClient.deleteTest).toHaveBeenCalledWith(TESTS[0].id);
         expect(getEls(el, 'mat-row').length).toBe(1);
       });
     }));

  it('renders page header correctly', () => {
    const header = getEl(el, 'h1');
    expect(header).toBeTruthy();
    expect(header.innerText).toBe('Test Suites');
  });

  it('displayed correct aria label for table', () => {
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Test suites');
  });

  it('displays and announces a loading mask', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
  });
});
