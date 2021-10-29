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

import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import * as moment from 'moment';
import {finalize} from 'rxjs/operators';

import {EventLogEntry, EventLogLevel, TestRun} from '../services/mtt_models';
import {TfcClient} from '../services/tfc_client';
import {Command, CommandAttempt, CommandStateStats, Request} from '../services/tfc_models';
import {assertRequiredInput, millisToDuration} from '../shared/util';

/** Progress entity which represents a log entry. */
interface LogEntity extends EventLogEntry {
  readonly progressType: 'log';
  readonly timestamp: moment.Moment;
}

/** Progress entity which represents command state stats. */
interface CommandStateStatsEntity extends CommandStateStats {
  readonly progressType: 'command-state-stats';
  readonly timestamp: moment.Moment;
}

/** Progress entity which represents an attempt. */
interface AttemptEntity extends CommandAttempt {
  readonly progressType: 'attempt';
  readonly timestamp: moment.Moment;
}

/** Entities which define a test run's progress. */
type ProgressEntity = LogEntity|AttemptEntity|CommandStateStatsEntity;

/** Tree node for storing state stats data. */
interface CommandStateStatNode {
  state: string;
  count: string;
  expanded: boolean;
}

/** Displays the test run progress entities (log entries and attempts). */
@Component({
  selector: 'test-run-progress',
  styleUrls: ['test_run_progress.css'],
  templateUrl: './test_run_progress.ng.html',
})
export class TestRunProgress implements OnInit, OnChanges {
  readonly EventLogLevel = EventLogLevel;

  @Input() testRun!: TestRun;
  @Input() request?: Request;

  // TODO: Remove after switching to modular execution UI
  showModUI = false;

  entities: ProgressEntity[] = [];
  stateStats: CommandStateStats = {state_stats: []};
  statNodes: CommandStateStatNode[] = [];

  displayColumns = [
    'expand',
    'jobs',
    'progress',
    'module_results',
    'test_results',
    'start_time',
    'output_files',
  ];

  constructor(
      private readonly tfcClient: TfcClient,
  ) {}

  ngOnInit() {
    assertRequiredInput(this.testRun, 'testRun', 'test-run-progress');
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['testRun'] || changes['request']) {
      this.load();
    }
  }

  load() {
    if (!this.request) {
      this.updateEntities();
      return;
    }

    this.tfcClient.getCommandStateStats(this.request.id)
        .pipe(finalize(() => {
          this.updateEntities();
        }))
        .subscribe(
            (res) => {
              this.stateStats = res;

              for (const stat of this.stateStats.state_stats) {
                if (stat.value !== '0') {
                  this.statNodes.push({
                    state: stat.key,
                    count: stat.value,
                    expanded: false,
                  });
                }
              }
            },
            error => {
              console.log('Failed to load command state stats: %s', error);
            });
  }

  updateEntities() {
    // Convert log entries
    const logEntries = this.testRun.log_entries || [];
    const logEntities: LogEntity[] = logEntries.map(e => {
      return {progressType: 'log', timestamp: moment.utc(e.create_time), ...e};
    });

    // Convert command states
    const stateStatsEntity: CommandStateStatsEntity = {
      progressType: 'command-state-stats',
      timestamp: moment.utc(this.stateStats.create_time) || moment.now(),
      ...this.stateStats,
    };

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
    this.entities = [...logEntities, ...attemptEntities, stateStatsEntity].sort(
        (a, b) => a.timestamp.diff(b.timestamp));
  }

  expandStatNode(index: number) {
    if (this.statNodes[index].expanded) {
      this.statNodes[index].expanded = false;
      return;
    }
    this.statNodes[index].expanded = true;
    // TODO: Load commands
  }

  /** Calculate an attempt's duration. */
  getDuration(attempt: CommandAttempt): string {
    const start = moment.utc(attempt.start_time);
    const end = moment.utc(attempt.end_time);
    return millisToDuration(end.diff(start));
  }
}
