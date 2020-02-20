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
import {Component, EventEmitter, Inject, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {APP_DATA, AppData} from '../services/app_data';
import {FileUploadService} from '../services/file_upload_service';
import {RerunContext, Test, TestRunConfig} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {assertRequiredInput, noAwait} from './util';

/**
 * A form that display test run config info.
 *
 * After clicking new test run, this is the first component that stepper is
 * going to render.
 */
@Component({
  selector: 'test-run-config-form',
  styleUrls: ['test_run_config_form.css'],
  templateUrl: './test_run_config_form.ng.html',
  providers: [{provide: FormChangeTracker, useExisting: TestRunConfigForm}]
})
export class TestRunConfigForm extends FormChangeTracker implements OnInit,
                                                                    OnDestroy {
  @Input() testMap!: {[id: string]: Test};
  @Input() testId!: string;
  @Input() testRunConfig!: Partial<TestRunConfig>;
  /** True to allow users to select previous test runs to resume. */
  @Input() enableRerun = true;
  /** Local previous test run ID. */
  @Input() prevTestRunId?: string;
  /** Emits the selected test for two-way binding with parent */
  @Output() testIdChange = new EventEmitter();
  /** Emits the latest rerun parameters. */
  @Output() rerunContext = new EventEmitter<RerunContext>();

  /** Notified when the component is destroyed. */
  private readonly destroy = new ReplaySubject();

  /** True if the current run will resume another run. */
  isRerun = false;
  /** True if resuming a remote test run (from another instance). */
  isRemoteRerun = false;
  /** Test results filename of the previous remote run. */
  testResultsFilename?: string;
  /** True if currently uploading a results file for a remote rerun. */
  isUploading = false;
  /** File upload completion percentage (0 to 100). */
  uploadProgress = 0;

  constructor(
      @Inject(APP_DATA) private readonly appData: AppData,
      private readonly uploadService: FileUploadService,
      private readonly liveAnnouncer: LiveAnnouncer) {
    super();
  }

  ngOnInit() {
    assertRequiredInput(this.testMap, 'testMap', 'test-run-config-form');
    assertRequiredInput(
        this.testRunConfig, 'testRunConfig', 'test-run-config-form');
    this.updateRerunContext();
  }

  ngOnDestroy() {
    this.destroy.next();
    this.liveAnnouncer.clear();
  }

  /**
   * Upload a results file for a remote rerun.
   * @param file file to upload
   */
  async uploadResultsFile(file?: File) {
    if (!file) {
      return;
    }
    // Determine the upload URL.
    const url = (this.appData.tempUploadUrl || '') + file.name;
    const location =
        // TODO: toPromise can return Promise<T|undefined>
        // tslint:disable-next-line:no-unnecessary-type-assertion
        (await this.uploadService.startUploadProcess(url).toPromise())!;
    // Perform upload and update progress.
    this.isUploading = true;
    noAwait(this.liveAnnouncer.announce('Uploading', 'polite'));
    this.uploadService.uploadFile(file, location)
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.isUploading = false;
              this.uploadProgress = 0;
            }),
            )
        .subscribe(result => {
          this.uploadProgress = result.uploaded / file.size * 100;
          if (result.type === 'complete') {
            this.testResultsFilename = file.name;
            this.updateRerunContext();
            this.liveAnnouncer.announce('Upload completed', 'assertive');
          }
        });
  }

  /** Updates the rerun context based on the current parameters. */
  updateRerunContext() {
    if (!this.enableRerun) {
      this.isRerun = false;
      return;
    }
    if (this.isRemoteRerun) {
      this.isRerun = !!this.testResultsFilename;
      this.rerunContext.emit({context_filename: this.testResultsFilename});
    } else {
      this.isRerun = !!this.prevTestRunId;
      this.rerunContext.emit({test_run_id: this.prevTestRunId});
    }
  }
}
