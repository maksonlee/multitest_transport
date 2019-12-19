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

import {Component, EventEmitter, Inject, OnInit, Output, ViewChild, ViewEncapsulation} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {MatStepper} from '@angular/material/stepper';

import {Test, TestRunConfig} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {TestRunConfigForm} from '../shared/test_run_config_form';
import {resetStepCompletion} from '../shared/util';

/**
 * Data format when passed to TestRunConfigEditor
 * @param editMode determine whether the editor is editing existed config or
 *     creating a new config.
 * @param testRunConfig target config to edit.
 */
export interface TestRunConfigEditorData {
  editMode: boolean;
  testMap: {[id: string]: Test};
  testRunConfig: Partial<TestRunConfig>;
}

enum Step {
  CONFIGURATION = 0,
  SELECT_RUN_TARGETS = 1,
}
const TOTAL_STEPS = 2;

/**
 * This component is used to create or update a test run config.
 */
@Component({
  selector: 'test-run-config-editor',
  styleUrls: ['test_run_config_editor.css'],
  templateUrl: './test_run_config_editor.ng.html',
  encapsulation: ViewEncapsulation.None,
  providers: [{provide: FormChangeTracker, useExisting: TestRunConfigEditor}]
})
export class TestRunConfigEditor extends FormChangeTracker implements OnInit {
  @Output() configSubmitted = new EventEmitter<TestRunConfig>();

  // Record each step whether it has finished or not
  stepCompletionStatusMap: {[stepNum: number]: boolean} = {};
  step = Step;
  resetStepCompletion = resetStepCompletion;
  totalSteps = TOTAL_STEPS;

  // Validation variable
  @ViewChild(TestRunConfigForm, {static: true})
  testRunConfigForm!: TestRunConfigForm;
  errorMessage = '';

  constructor(
      private readonly dialogRef: MatDialogRef<TestRunConfigEditor>,
      @Inject(MAT_DIALOG_DATA) public data: TestRunConfigEditorData) {
    super();
    // When user clicked outside of the dialog, close the dialog
    dialogRef.backdropClick().subscribe(() => {
      this.dialogRef.close();
    });
  }

  ngOnInit() {
    // Initialize step completion status map
    this.resetStepCompletion(0, this.stepCompletionStatusMap, this.totalSteps);
  }

  /**
   * Triggered on click next button in stepper
   * @param stepper MatStepper
   */
  goForward(stepper: MatStepper): void {
    if (this.validateStep(stepper.selectedIndex)) {
      this.stepCompletionStatusMap[stepper.selectedIndex] = true;
      // wait for data to populate stepper
      setTimeout(() => {
        stepper.next();
      }, 100);
    }
  }

  /**
   * Validate each step and populate error messages
   * @param currentStep Indicate which step are we validating
   */
  validateStep(currentStep: Step): boolean {
    this.errorMessage = '';
    this.invalidInputs = [];
    switch (currentStep) {
      case Step.CONFIGURATION: {
        this.invalidInputs = this.testRunConfigForm.getInvalidInputs();
        return !this.invalidInputs.length;
      }
      case Step.SELECT_RUN_TARGETS: {
        const res = !!this.data.testRunConfig.run_target;
        if (!res) {
          this.errorMessage = 'Run target is required';
        }
        return res;
      }
      default: {
        break;
      }
    }
    return true;
  }

  /**
   * On submit test run config, close the dialog.
   */
  submit() {
    if (!this.validateStep(Step.SELECT_RUN_TARGETS)) {
      return;
    }
    this.configSubmitted.emit(this.data.testRunConfig as TestRunConfig);
    this.dialogRef.close();
  }
}
