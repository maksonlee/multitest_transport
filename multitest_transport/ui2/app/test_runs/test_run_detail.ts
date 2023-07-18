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
import {MatLegacyDialog} from '@angular/material/legacy-dialog';
import {MatLegacyTabChangeEvent, MatLegacyTabGroup} from '@angular/material/legacy-tabs';
import {ActivatedRoute, Router} from '@angular/router';
import {EMPTY, interval, Observable, ReplaySubject, zip} from 'rxjs';
import {finalize, first, switchMap, takeUntil} from 'rxjs/operators';

import {AnalyticsService} from '../services/analytics_service';
import {FileService} from '../services/file_service';
import {MttClient} from '../services/mtt_client';
import {isFinalTestRunState, isTestRunShardingModeModule, TestRun, TestRunAction, TestRunActionRef, TestRunPhase, TestRunSummary, TestRunSummaryList} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {isFinalCommandState, Request} from '../services/tfc_models';
import {OverflowListType} from '../shared/overflow_list';
import {assertRequiredInput, buildApiErrorMessage} from '../shared/util';
import {TestRunActionPickerDialog, TestRunActionPickerDialogData} from '../test_run_actions/test_run_action_picker_dialog';

/** A component for displaying the details of a test run. */
@Component({
  selector: 'test-run-detail',
  styleUrls: ['test_run_detail.css'],
  templateUrl: './test_run_detail.ng.html',
})
export class TestRunDetail implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('backButton', {static: false}) backButton?: MatButton;
  // TODO Add test for tab change
  @ViewChild('tabGroup', {static: false}) tabGroup?: MatLegacyTabGroup;
  readonly OverflowListType = OverflowListType;
  @Input() testRunId!: string;

  isLoading = false;
  isFinalTestRunState = isFinalTestRunState;
  isTestRunShardingModeModule = isTestRunShardingModeModule;
  deviceInfoColumns = ['device_serial', 'product', 'build_id'];

  private readonly destroyed = new ReplaySubject<void>();
  private readonly autoUpdate =
      interval(60_000).pipe(takeUntil(this.destroyed)).subscribe(() => {
        this.loadTestRun();
      });

  /** Current test run information. */
  testRun?: TestRun;
  /** Underlying TFC request, only present if test run has started. */
  request?: Request;
  /** List of summaries of reruns. */
  reruns: TestRunSummary[] = [];
  /** Link to view the latest output files. */
  outputFilesUrl?: string;
  /** Test run results URL. */
  exportUrl?: string;
  /** Current tab index. */
  currentTabIndex: number = 0;
  /** List of available API test run actions. */
  manualTestRunActions: TestRunAction[] = [];


  readonly matTabOptions =
      ['test_results', 'progress', 'logs', 'test_resources', 'config'];

  constructor(
      private readonly notifier: Notifier,
      private readonly router: Router,
      private readonly route: ActivatedRoute,
      private readonly fs: FileService,
      private readonly mtt: MttClient,
      private readonly tfc: TfcClient,
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly analytics: AnalyticsService,
      private readonly matDialog: MatLegacyDialog,
  ) {}

  ngOnInit() {
    assertRequiredInput(this.testRunId, 'testRunId', 'test-run-detail');
    this.loadTestRun();

    // tslint:disable-next-line:no-unnecessary-type-assertion
    (this.route.fragment as Observable<string>)
        .subscribe((fragment: string) => {
          const idx = this.matTabOptions.indexOf(fragment);
          this.currentTabIndex = idx === -1 ? 0 : idx;
        });
  }

  ngAfterViewInit() {
    this.backButton!.focus();
  }

  ngOnDestroy() {
    this.destroyed.next();
    this.liveAnnouncer.clear();
  }

  switchTab(tabChangeEvent: MatLegacyTabChangeEvent) {
    this.router.navigate([], {
      fragment: this.matTabOptions[tabChangeEvent.index],
      queryParamsHandling: 'merge',
    });
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
            this.loadManualTestRunActions();
          }
          this.loadReruns();

          // Fetch TFC data if possible.
          if (testRun && testRun.request_id) {
            return zip(
                this.tfc.getRequest(testRun.request_id),
            );
          }
          return EMPTY;
        }))
        .pipe(finalize(() => {
          this.isLoading = false;
          if (this.tabGroup) {
            this.tabGroup.selectedIndex = this.currentTabIndex;
          }
        }))
        .subscribe(
            ([request]) => {
              this.request = request;
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

  loadReruns() {
    this.mtt.getReruns(this.testRunId)
        .pipe(first())
        .subscribe((reruns: TestRunSummaryList) => {
          this.reruns = reruns.test_runs || [];
        });
  }

  updateOutputFilesUrl() {
    if (!this.testRun || !this.request || !this.request.command_attempts ||
        !this.request.command_attempts.length) {
      return;
    }

    const attempts = this.request.command_attempts;
    const lastAttempt = attempts[attempts.length - 1];
    const fileUrl = isTestRunShardingModeModule(this.testRun.test_run_config) ?
        this.fs.getTestRunMergedReportDirUrl(this.testRun) :
        this.fs.getTestRunFileUrl(this.testRun, lastAttempt);
    this.outputFilesUrl = this.fs.getFileBrowseUrl(fileUrl);
  }

  updateExportUrl() {
    if (!this.testRun) {
      return;
    }

    if (isTestRunShardingModeModule(this.testRun.test_run_config)) {
      this.updateExportUrlForModuleMode();
      return;
    }

    this.updateExportUrlForRunnerMode();
  }

  updateExportUrlForRunnerMode() {
    if (!this.testRun) {
      return;
    }
    const nextResources = this.testRun.next_test_context &&
        this.testRun.next_test_context.test_resources;
    const contextFile = nextResources && nextResources[0].url;
    if (!contextFile) {
      return;
    }
    this.exportUrl = this.fs.getFileOpenUrl(contextFile);
  }

  updateExportUrlForModuleMode() {
    if (!this.testRun) {
      return;
    }
    const mergedReportDirUrl =
        this.fs.getTestRunMergedReportDirUrl(this.testRun);
    const mergedReportDirRelativePath =
        this.fs.getRelativePathAndHostname(mergedReportDirUrl)[0];

    this.fs.listFiles(mergedReportDirRelativePath).subscribe(files => {
      const mergedReportZipFile = files.find(f => f.path.endsWith('.zip'));
      if (mergedReportZipFile) {
        this.exportUrl = this.fs.getFileOpenUrl(mergedReportZipFile.path);
      } else {
        console.log(
            'Test run %s uses MODULE sharding mode but found no merged ' +
                'report. Fallback to classic behavior.',
            this.testRunId);
        this.updateExportUrlForRunnerMode();
      }
    });
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

  deleteTestRun() {
    this.notifier
        .confirm(
            'Do you really want to delete this test run?', 'Delete Test Run')
        .subscribe(result => {
          if (!result) {
            return;
          }
          this.mtt.deleteTestRuns([this.testRunId]).subscribe(result => {
            this.notifier.showMessage(`Test run '${this.testRunId}' deleted`);
            this.back();
          });
        });
  }

  isLastAttemptFinal() {
    if (!this.request || !this.request.command_attempts ||
        !this.request.command_attempts.length) {
      return false;
    }
    const lastAttempt =
        this.request.command_attempts[this.request.command_attempts.length - 1];
    return isFinalCommandState(lastAttempt.state);
  }

  back() {
    this.router.navigate([`test_runs`], {queryParamsHandling: 'merge'});
  }

  trackClickEvent(action: string) {
    this.analytics.trackEvent('test_run_detail', action);
  }

  loadManualTestRunActions() {
    this.mtt.testRunActions.list().subscribe(actions => {
      this.manualTestRunActions = actions.filter(
          action => action.phases?.includes(TestRunPhase.MANUAL));
    });
  }

  executeTestRunActions() {
    const testRunActionsPickerDialogData: TestRunActionPickerDialogData = {
      actions: this.manualTestRunActions,
      selectedActionRefs:
          this.testRun?.test_run_config?.test_run_action_refs || [],
    };

    const dialogRef = this.matDialog.open(TestRunActionPickerDialog, {
      panelClass: 'test-run-action-picker-dialog',
      data: testRunActionsPickerDialogData,
    });

    dialogRef.componentInstance.confirm.subscribe(
        (refs: TestRunActionRef[]) => {
          this.mtt.testRunActions.executeTestRunActions(this.testRunId, {refs})
              .subscribe(
                  () => {
                    // Switch to progress tab
                    this.router.navigate([], {fragment: 'progress'});
                    this.loadTestRun();
                    this.notifier.showMessage(
                        `Executed test run actions successfully.`);
                  },
                  error => {
                    this.notifier.showError(
                        `Failed to execute test run actions.`,
                        buildApiErrorMessage(error));
                  });
        });
  }
}
