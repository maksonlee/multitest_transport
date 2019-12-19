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
import {AfterViewInit, Component, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MatButton} from '@angular/material/button';
import {Router} from '@angular/router';
import {EMPTY, interval, ReplaySubject, zip} from 'rxjs';
import {finalize, switchMap, takeUntil} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {isFinalTestRunState, TestRun} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {CommandAttempt, InvocationStatus, isFinalCommandState, Request} from '../services/tfc_models';
import {OverflowListType} from '../shared/overflow_list';
import {assertRequiredInput, buildApiErrorMessage, joinPath} from '../shared/util';

/** A component for displaying the details of a test run. */
@Component({
  selector: 'test-run-detail',
  styleUrls: ['test_run_detail.css'],
  templateUrl: './test_run_detail.ng.html',
})
export class TestRunDetail implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('backButton', {static: false}) backButton?: MatButton;
  readonly OverflowListType = OverflowListType;
  @Input() testRunId!: string;

  isLoading = false;
  isFinalTestRunState = isFinalTestRunState;
  deviceInfoColumns = ['device_serial', 'product', 'build_id'];

  private readonly destroyed = new ReplaySubject();
  private readonly autoUpdate =
      interval(60_000).pipe(takeUntil(this.destroyed)).subscribe(() => {
        this.loadTestRun();
      });

  /** Current test run information. */
  testRun?: TestRun;
  /** Underlying TFC request, only present if test run has started. */
  request?: Request;
  /** Test statuses (number of passed/failed). */
  invocationStatus?: InvocationStatus;
  /** Link to view the latest output files */
  outputFilesUrl?: string;
  /** Test run results URL. */
  exportUrl?: string;

  constructor(
      private readonly notifier: Notifier,
      private readonly router: Router,
      private readonly mtt: MttClient,
      private readonly tfc: TfcClient,
      private readonly liveAnnouncer: LiveAnnouncer,
  ) {}

  ngOnInit() {
    assertRequiredInput(this.testRunId, 'testRunId', 'test-run-detail');
    this.loadTestRun();
  }

  ngAfterViewInit() {
    this.backButton!.focus();
  }

  ngOnDestroy() {
    this.destroyed.next();
    this.liveAnnouncer.clear();
  }

  loadTestRun() {
    this.isLoading = true;
    this.liveAnnouncer.announce('Loading', 'polite');
    this.mtt.getTestRun(this.testRunId)
        .pipe(switchMap((testRun: TestRun) => {
          // Update run information.
          this.testRun = testRun;
          this.updateExportUrl();
          if (testRun && isFinalTestRunState(testRun.state)) {
            this.autoUpdate.unsubscribe();  // Stop auto-updating when complete.
          }
          // Fetch TFC data if possible.
          if (testRun && testRun.request_id) {
            return zip(
                this.tfc.getRequest(testRun.request_id),
                this.tfc.getRequestInvocationStatus(testRun.request_id),
            );
          }
          return EMPTY;
        }))
        .pipe(finalize(() => {
          this.isLoading = false;
        }))
        .subscribe(
            ([request, invocationStatus]) => {
              this.request = request;
              this.invocationStatus = invocationStatus;
              this.updateOutputFilesUrl();
              this.liveAnnouncer.announce(
                  'Test run details loaded', 'assertive');
            },
            error => {
              this.notifier.showError(
                  `Failed to load info for test run '${this.testRunId}'.`,
                  buildApiErrorMessage(error));
            },
        );
  }

  updateOutputFilesUrl() {
    if (!this.testRun || !this.request || !this.request.command_attempts ||
        !this.request.command_attempts.length) {
      return;
    }

    const attempts = this.request.command_attempts;
    const lastAttempt = attempts[attempts.length - 1];
    this.outputFilesUrl = this.getFileLink(lastAttempt, this.testRun);
  }

  getFileLink(attempt: CommandAttempt, testRun: TestRun): string {
    const active = !isFinalCommandState(attempt.state);

    let link: string;
    if (active) {
      link = this.mtt.getFileBrowseUrl(joinPath(
          'file:///', this.mtt.getFileServerRoot(), 'tmp', attempt.attempt_id));
    } else {
      link = this.mtt.getFileBrowseUrl(joinPath(
          testRun.output_url!, attempt.command_id, attempt.attempt_id));
    }
    return link;
  }

  updateExportUrl() {
    if (!this.testRun) {
      return;
    }

    const nextResources = this.testRun.next_test_context &&
        this.testRun.next_test_context.test_resources;
    const contextFile = nextResources && nextResources[0].url;
    if (!contextFile) {
      return;
    }

    this.exportUrl = this.mtt.getFileOpenUrl(contextFile);
  }

  cancelTestRun() {
    this.notifier
        .confirm(
            'Do you really want to cancel this test run?', 'Cancel Test Run')
        .subscribe(result => {
          if (!result) {
            return;
          }
          this.mtt.cancelTestRun(this.testRunId).subscribe(result => {
            this.notifier.showMessage(`Test run '${this.testRunId}' canceled`);
            this.loadTestRun();
          });
        });
  }

  rerunTestRun() {
    this.router.navigate(
        [`test_runs/new`], {queryParams: {'prevTestRunId': this.testRunId}});
  }

  back() {
    this.router.navigate([`test_runs`], {queryParamsHandling: 'merge'});
  }
}
