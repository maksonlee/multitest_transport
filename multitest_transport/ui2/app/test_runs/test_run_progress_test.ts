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

import {FileService} from '../services/file_service';
import {EventLogEntry, TestRun} from '../services/mtt_models';
import {CommandAttempt, CommandState, Request} from '../services/tfc_models';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {TestRunProgress} from './test_run_progress';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunProgress', () => {
  let fs: jasmine.SpyObj<FileService>;

  let fixture: ComponentFixture<TestRunProgress>;
  let element: DebugElement;
  let component: TestRunProgress;

  beforeEach(() => {
    fs = jasmine.createSpyObj(['getTestRunFileUrl', 'getFileBrowseUrl']);

    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
      ]
    });

    fixture = TestBed.createComponent(TestRunProgress);
    element = fixture.debugElement;
    component = fixture.componentInstance;
  });

  /** Convenience method to reload a new set of progress entities. */
  function reload(
      logEntries?: Array<Partial<EventLogEntry>>,
      attempts?: Array<Partial<CommandAttempt>>) {
    component.testRun = {log_entries: logEntries} as TestRun;
    component.request = {command_attempts: attempts} as Request;
    component.ngOnChanges();
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    reload();
    expect(component).toBeTruthy();
    expect(hasEl(element, '.entity')).toBeFalsy();
  });

  it('can display a log entry', () => {
    reload([{
      create_time: '2000-01-01T00:00:00',
      message: 'Log message',
    }]);

    // One log entity is displayed
    expect(hasEl(element, '.attempt')).toBeFalsy();
    const logEntries = getEls(element, '.log');
    expect(logEntries.length).toBe(1);
    expect(logEntries[0].textContent).toContain('Log message');
  });

  it('can display an attempt', () => {
    fs.getFileBrowseUrl.and.returnValue('http://browse_url/');
    reload([], [{
             attempt_id: 'attempt_id',
             create_time: '2000-01-01T00:00:00',
             state: CommandState.COMPLETED,
           }]);

    // One attempt entity is displayed
    expect(hasEl(element, '.log')).toBeFalsy();
    const attempts = getEls(element, '.attempt');
    expect(attempts.length).toBe(1);
    expect(attempts[0].textContent).toContain('(attempt attempt_id)');

    // Output file URL generated
    const link = getEl<HTMLAnchorElement>(element, '.attempt a');
    expect(link.href).toEqual('http://browse_url/');
  });

  it('can display multiple progress entities', () => {
    reload(
        [
          {
            create_time: '2000-01-01T00:00:00',
            message: 'Log #1',
          },
          {
            create_time: '2000-01-03T00:00:00',
            message: 'Log #2',
          }
        ],
        [{
          attempt_id: 'Attempt #1',
          create_time: '2000-01-02T00:00:00',
          state: CommandState.COMPLETED,
        }]);

    // Three entities displayed in ascending order by timestamp
    const entities = getEls(element, '.entity');
    expect(entities.length).toBe(3);
    expect(entities[0].textContent).toContain('Log #1');
    expect(entities[1].textContent).toContain('Attempt #1');
    expect(entities[2].textContent).toContain('Log #2');
  });
});
