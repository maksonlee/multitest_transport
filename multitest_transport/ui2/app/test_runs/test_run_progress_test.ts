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
import {of as observableOf} from 'rxjs';

import {FileService} from '../services/file_service';
import {EventLogEntry, TestRun} from '../services/mtt_models';
import {TfcClient} from '../services/tfc_client';
import {Command, CommandAttempt, CommandState, Request} from '../services/tfc_models';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';

import {TestRunProgress} from './test_run_progress';
import {TestRunsModule} from './test_runs_module';

describe('TestRunProgress', () => {
  let fs: jasmine.SpyObj<FileService>;
  let tfcClient: jasmine.SpyObj<TfcClient>;

  let command: Command;
  let attempt: CommandAttempt;

  let fixture: ComponentFixture<TestRunProgress>;
  let element: DebugElement;
  let component: TestRunProgress;

  beforeEach(() => {
    command = {
      request_id: 'request_id',
      id: 'command_id',
      name: 'name',
      command_line: 'command_line',
      state: CommandState.COMPLETED,
    };

    attempt = {
      attempt_id: 'attempt_id',
      command_id: 'command_id',
      request_id: 'request_id',
      create_time: '2000-01-01T00:00:00',
      state: CommandState.COMPLETED,
      hostname: 'hostname',
    };

    fs = jasmine.createSpyObj(['getTestRunFileUrl', 'getFileBrowseUrl']);
    tfcClient = jasmine.createSpyObj(
        'tfcClient',
        ['getCommandStateStats', 'listCommands', 'listCommandAttempts']);

    tfcClient.getCommandStateStats.and.returnValue(observableOf({
      state_stats: [
        {state: CommandState.COMPLETED, count: 3},
        {state: CommandState.ERROR, count: 2},
        {state: CommandState.RUNNING, count: 1},
      ],
      create_time: '2000-01-01T00:00:00',
    }));

    tfcClient.listCommands.and.returnValue(observableOf({commands: [command]}));

    tfcClient.listCommandAttempts.and.returnValue(
        observableOf({command_attempts: [attempt]}));

    TestBed.configureTestingModule({
      imports: [TestRunsModule, NoopAnimationsModule],
      providers: [
        {provide: FileService, useValue: fs},
        {provide: TfcClient, useValue: tfcClient},
      ]
    });

    fixture = TestBed.createComponent(TestRunProgress);
    element = fixture.debugElement;
    component = fixture.componentInstance;

    reload([], [command], [attempt]);
  });

  /** Convenience method to reload a new set of progress entities. */
  function reload(
      logEntries?: Array<Partial<EventLogEntry>>,
      commands?: Array<Partial<Command>>,
      attempts?: Array<Partial<CommandAttempt>>) {
    component.testRun = {log_entries: logEntries} as TestRun;
    component.request = {
      commands,
      command_attempts: attempts
    } as Request;
    component.loadCommandStateStats();
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    reload();
    expect(component).toBeTruthy();
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
        [command], [attempt]);

    // Three entities displayed in ascending order by timestamp
    const entities = getEls(element, '.entity');
    expect(entities.length).toBe(3);
    expect(entities[0].textContent).toContain('Log #1');
    expect(entities[1].textContent).toContain('Test run started');
    expect(entities[2].textContent).toContain('Log #2');
  });

  it('can display the command state stats', () => {
    const stats = getEls(element, '.command-state-stats');
    expect(stats.length).toBe(1);
    expect(stats[0].textContent).toContain('Completed (3)');
    expect(stats[0].textContent).toContain('Error (2)');
    expect(stats[0].textContent).toContain('Running (1)');
  });

  it('can display the commands', () => {
    component.expandStatNode(CommandState.COMPLETED);
    fixture.detectChanges();
    const commandRow = getEl(element, '.command-row');
    expect(commandRow.textContent).toContain('Job command_id: name');
  });

  it('can display the attempts', () => {
    component.expandStatNode(CommandState.COMPLETED);
    component.expandCommandNode(CommandState.COMPLETED, 'command_id');
    fixture.detectChanges();
    const attemptRow = getEl(element, '.attempt-row');
    expect(attemptRow.textContent).toContain('Attempt attempt_id');
  });
});
