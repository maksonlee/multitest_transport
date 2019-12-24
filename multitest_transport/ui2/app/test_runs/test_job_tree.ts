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

import {ChangeDetectionStrategy, Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import * as moment from 'moment';

import {MttClient} from '../services/mtt_client';
import {TestRun} from '../services/mtt_models';
import {Command, CommandAttempt, isFinalCommandState, Request} from '../services/tfc_models';
import {TreeNode} from '../shared/tree_table';
import {assertRequiredInput, joinPath, millisToDuration} from '../shared/util';

/** A component for displaying a tree of test jobs. */
@Component({
  selector: 'test-job-tree',
  template: `<tree-table [data]="treeNodes"
                         [columns]="treeTableColumns"></tree-table>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TestJobTree implements OnInit, OnChanges {
  @Input() testRun!: TestRun;
  @Input() request?: Request;

  treeNodes: TreeNode[] = [];
  treeTableColumns = [
    {
      title: 'Job ID',
      flexWidth: '45',
    },
    {
      title: 'Status',
      flexWidth: '10',
    },
    {
      title: 'Test Failures',
      flexWidth: '15',
    },
    {
      title: 'Start Time',
      flexWidth: '20',
    },
    {
      title: 'Run Time',
      flexWidth: '10',
    }
  ];

  constructor(private readonly mtt: MttClient) {}

  ngOnInit() {
    assertRequiredInput(this.testRun, 'testRun', 'test-job-tree');
    this.update();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.update();
  }

  private update() {
    this.treeNodes = this.testRun && this.request ?
        this.createRequestNode(this.request).children :
        [];
  }

  createRequestNode(request: Request): TreeNode {
    const commandNodes: TreeNode[] = [];
    if (request.commands) {
      request.commands.forEach((command) => {
        commandNodes.push(
            this.createCommandNode(command, request.command_attempts || []));
      });
    }

    return {
      content: [`Request ${request.id}`],
      children: commandNodes,
      level: 0,
    };
  }

  createCommandNode(command: Command, attempts: CommandAttempt[]): TreeNode {
    const attemptNodes: TreeNode[] = [];
    for (const attempt of attempts) {
      if (attempt.command_id === command.id) {
        attemptNodes.push(this.createAttemptNode(attempt));
      }
    }

    // Get latest results
    let failedTestCount = 0;
    let passedTestCount = 0;
    for (const attempt of attempts) {
      if (attempt.passed_test_count && attempt.failed_test_count) {
        failedTestCount = Number(attempt.failed_test_count);
        passedTestCount = Number(attempt.passed_test_count);
      }
    }

    // Set the last attempt to be expanded by default
    if (attemptNodes.length > 0) {
      attemptNodes[attemptNodes.length - 1].expanded = true;
    }

    // Get start time and run time info
    const startTime = command.start_time ?
        moment.utc(command.start_time).local().format('L, LTS') : '';
    const runTime = this.getRunTime(command.start_time, command.end_time);

    return {
      content: [
        `Job ${command.id}`, `${command.state}`,
        `${failedTestCount}/${failedTestCount + passedTestCount}`,
        `${startTime}`, `${runTime}`
      ],
      children: attemptNodes,
      level: 0,
      expanded: true,
    };
  }

  createAttemptNode(attempt: CommandAttempt): TreeNode {
    const failed = attempt.failed_test_count || 0;
    const passed = attempt.passed_test_count || 0;
    const results = `${failed}/${Number(passed) + Number(failed)}`;
    const startTime = attempt.start_time ?
        moment.utc(attempt.start_time).local().format('L, LTS') : '';
    const runTime = this.getRunTime(attempt.start_time, attempt.end_time);

    // TODO: Add stylings
    return {
      content: [attempt.attempt_id, attempt.state, results, startTime, runTime],
      children: [this.createSummaryNode(attempt)],
      level: 1,
    };
  }

  createSummaryNode(attempt: CommandAttempt): TreeNode {
    // TODO: Add material components and styling
    const fileLink = this.getFileLink(attempt);
    let content = `<a href='${fileLink}' target='_blank'>View Output Files</a>`;

    if (attempt.summary) {
      content += '<br><br>Summary: ' + attempt.summary;
    }
    if (attempt.error) {
      content += '<br><br>Error: ' + attempt.error;
    }

    return {content: [content], children: [], level: 2};
  }

  getFileLink(attempt: CommandAttempt): string {
    const active = !isFinalCommandState(attempt.state);

    let link: string;
    if (active) {
      link = this.mtt.getFileBrowseUrl(joinPath(
          'file:///', this.mtt.getFileServerRoot(), 'tmp', attempt.attempt_id));
    } else {
      link = this.mtt.getFileBrowseUrl(joinPath(
          this.testRun.output_url!, attempt.command_id, attempt.attempt_id));
    }
    return link;
  }

  getRunTime(startDate?: string, endDate?: string): string {
    const currentTime = moment();
    const start = startDate ? moment.utc(startDate) : currentTime;
    const end = endDate ? moment.utc(endDate) : currentTime;
    return millisToDuration(end.diff(start));
  }
}
