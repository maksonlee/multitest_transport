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

import {ChangeDetectionStrategy, Component, Input, OnChanges, OnInit} from '@angular/core';
import * as moment from 'moment';

import {EventLogEntry, EventLogLevel, TestRun} from '../services/mtt_models';
import {Command, CommandAttempt, Request} from '../services/tfc_models';
import {assertRequiredInput, millisToDuration} from '../shared/util';

/** Progress entity which represents a log entry. */
interface LogEntity extends EventLogEntry {
  readonly progressType: 'log';
  readonly timestamp: moment.Moment;
}

/** Progress entity which represents an attempt. */
interface AttemptEntity extends CommandAttempt {
  readonly progressType: 'attempt';
  readonly timestamp: moment.Moment;
}

/** Entities which define a test run's progress. */
type ProgressEntity = LogEntity|AttemptEntity;

/** Displays the test run progress entities (log entries and attempts). */
@Component({
  selector: 'test-run-progress',
  styleUrls: ['test_run_progress.css'],
  templateUrl: './test_run_progress.ng.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TestRunProgress implements OnInit, OnChanges {
  readonly EventLogLevel = EventLogLevel;

  @Input() testRun!: TestRun;
  @Input() request?: Request;

  entities: ProgressEntity[] = [];

  ngOnInit() {
    assertRequiredInput(this.testRun, 'testRun', 'test-run-progress');
  }

  ngOnChanges() {
    // Convert log entries
    const logEntries = this.testRun.log_entries || [];
    const logEntities: LogEntity[] = logEntries.map(e => {
      return {progressType: 'log', timestamp: moment.utc(e.create_time), ...e};
    });
    // Convert attempts
    const commands = this.request && this.request.commands || [];
    const commandMap = commands.reduce((map: Map<string, Command>, obj: Command) => {
      map.set(obj.id, obj);
      return map;
    }, new Map<string, Command>());
    const attempts = this.request && this.request.command_attempts || [];
    const attemptEntities: AttemptEntity[] = attempts.map(e => {
      return {
        progressType: 'attempt',
        timestamp: moment.utc(e.create_time),
        command: commandMap.get(e.command_id),
        ...e,
      };
    });
    // Combine and sort entities
    this.entities = [...logEntities, ...attemptEntities].sort(
        (a, b) => a.timestamp.diff(b.timestamp));
  }

  /** Calculate an attempt's duration. */
  getDuration(attempt: CommandAttempt): string {
    const start = moment.utc(attempt.start_time);
    const end = moment.utc(attempt.end_time);
    return millisToDuration(end.diff(start));
  }
}
