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
import {RouterTestingModule} from '@angular/router/testing';
import * as moment from 'moment';

import {MttClient} from '../services/mtt_client';
import {Test, TestRun} from '../services/mtt_models';
import {Command, CommandAttempt, Request} from '../services/tfc_models';
import {getEl} from '../testing/jasmine_util';
import {addTime, newMockCommand, newMockCommandAttempt, newMockRequest, newMockTest, newMockTestRun} from '../testing/test_util';

import {TestJobTree} from './test_job_tree';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestJobTree', () => {
  let testJobTree: TestJobTree;
  let testJobTreeFixture: ComponentFixture<TestJobTree>;
  let el: DebugElement;
  let mttClient: jasmine.SpyObj<MttClient>;

  let request: Request;
  let command: Command;
  let attempt: CommandAttempt;
  let attemptWithResults: CommandAttempt;
  let test: Test;
  let testRun: TestRun;

  beforeEach(() => {
    attempt = newMockCommandAttempt();
    attemptWithResults = newMockCommandAttempt(13, 42);
    command = newMockCommand();
    request = newMockRequest([command], [attemptWithResults, attempt]);
    test = newMockTest();
    testRun = newMockTestRun(test);

    mttClient = jasmine.createSpyObj(
        'mttClient', ['getFileBrowseUrl', 'getFileServerRoot']);
    mttClient.getFileBrowseUrl.and.returnValue('file/browse/url');
    mttClient.getFileServerRoot.and.returnValue('file/server/root');

    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    testJobTreeFixture = TestBed.createComponent(TestJobTree);
    testJobTree = testJobTreeFixture.componentInstance;
    testJobTree.request = request;
    testJobTree.testRun = testRun;
    testJobTreeFixture.detectChanges();
    el = testJobTreeFixture.debugElement;
  });

  it('gets initialized', () => {
    expect(TestJobTree).toBeTruthy();
  });

  it('displays the correct request values', () => {
    const text = getEl(el, 'mat-tree').textContent;
    expect(text).toContain(command.id);
    expect(text).toContain(attempt.attempt_id);

    expect(text).toContain(attemptWithResults.attempt_id);
    expect(text).toContain(13);
    expect(text).toContain(42 + 13);
  });

  it('correctly generates a tree of requests, commands, and attempts', () => {
    // Request node
    const requestNode = testJobTree.createRequestNode(request);
    expect(requestNode.content[0]).toContain(request.id);
    expect(requestNode.children.length).toEqual(1);

    // Command Node
    const commandNode = requestNode.children[0];
    expect(commandNode.content[0]).toContain(command.id);
    expect(commandNode.children.length).toEqual(2);

    // Check result test counts
    expect(commandNode.content[2]).toContain(String(42 + 13));
    expect(commandNode.content[2]).toContain('13');

    // Attempt node
    const attemptNode = commandNode.children[0];
    expect(attemptNode.content[0]).toContain(attemptWithResults.attempt_id);
    expect(attemptNode.children.length).toEqual(1);

    // Check result test counts
    expect(attemptNode.content[2]).toContain(String(42 + 13));
    expect(attemptNode.content[2]).toContain('13');

    // Check start date and run time
    expect(attemptNode.content[3])
        .toContain(moment(attemptWithResults.start_time!).format('L, LTS'));
    expect(attemptNode.content[4]).toContain('00:05:00');
  });

  it('correctly calculates run time', () => {
    const DATE = new Date().toISOString();
    let DATE2: string;
    let result: string;

    // 5 minutes
    DATE2 = addTime(DATE, 0, 5, 0);
    result = testJobTree.getRunTime(DATE, DATE2);
    expect(result).toContain('00:05:00');

    // 1 hour, 13 minutes, 6 seconds
    DATE2 = addTime(DATE, 1, 13, 36);
    result = testJobTree.getRunTime(DATE, DATE2);
    expect(result).toContain('01:13:36');

    // 123 hours, 0 minutes, 10 seconds
    DATE2 = addTime(DATE, 123, 0, 10);
    result = testJobTree.getRunTime(DATE, DATE2);
    expect(result).toContain('123:00:10');
  });
});
