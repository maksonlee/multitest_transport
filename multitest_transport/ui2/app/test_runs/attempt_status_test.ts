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

import {TestRun} from '../services/mtt_models';
import {CommandAttempt} from '../services/tfc_models';
import {getTextContent} from '../testing/jasmine_util';
import {newMockCommandAttempt, newMockTestRun} from '../testing/mtt_mocks';
import {AttemptStatus} from './attempt_status';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('AttemptStatus', () => {
  let attemptStatus: AttemptStatus;
  let attemptStatusFixture: ComponentFixture<TestRunResults>;
  let el: DebugElement;

  let testRun: TestRun;
  let mockAttempt: CommandAttempt;

  beforeEach(() => {
    testRun = newMockTestRun();
    mockAttempt = newMockCommandAttempt();
    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule],
      aotSummaries: TestRunsModuleNgSummary,
    });
    attemptStatusFixture = TestBed.createComponent(AttemptStatus);
    attemptStatus = attemptStatusFixture.componentInstance;
    el = attemptStatusFixture.debugElement;
    attemptStatus.testRun = testRun;
    attemptStatus.attempt = mockAttempt;
    attemptStatusFixture.detectChanges();
  });

  it('can init properly', () => {
    expect(attemptStatus).toBeTruthy();
  });

  it('can render queued attempt correctly', () => {
    const attempt = newMockCommandAttempt();
    attempt.state = CommandState.QUEUED;
    attemptStatus.attempt = attempt;
    attemptStatusFixture.detectChanges();
    getTextContent(el).contains('Test is queued.');
  });

  it('can render running attempt correctly', () => {
    const attempt = newMockCommandAttempt();
    attempt.state = CommandState.RUNNING;
    attemptStatus.attempt = attempt;
    attemptStatusFixture.detectChanges();
    getTextContent(el).contains('Test is running.');
  });

  it('can render completed attempt correctly', () => {
    const attempt = newMockCommandAttempt();
    attempt.state = CommandState.COMPLETED;
    attempt.failed_test_count = '0';
    attempt.passed_test_count = '123';
    attempt.total_test_count = '1234';
    attemptStatus.attempt = attempt;
    attemptStatusFixture.detectChanges();
    getTextContent(el).contains('Test completed: 123 tests passed.');
  });

  it('can render completed attempt with failed test cases correctly', () => {
    const attempt = newMockCommandAttempt();
    attempt.state = CommandState.COMPLETED;
    attempt.failed_test_count = '12';
    attempt.passed_test_count = '123';
    attempt.total_test_count = '1234';
    attemptStatus.attempt = attempt;
    attemptStatusFixture.detectChanges();
    getTextContent(el).contains('Test completed: 12/135 tests passed.');
  });

  it('can render error attempt correctly', () => {
    const attempt = newMockCommandAttempt();
    attempt.state = CommandState.ERROR;
    attemptStatus.attempt = attempt;
    attemptStatus.error = 'error';
    attemptStatusFixture.detectChanges();
    getTextContent(el).contains('Test failed to start: error');
  });
});
