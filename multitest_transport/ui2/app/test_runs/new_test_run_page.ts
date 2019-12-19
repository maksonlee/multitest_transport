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
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {AfterViewInit, Component, OnInit, ViewChild} from '@angular/core';
import {MatButton} from '@angular/material/button';
import {MatChipInputEvent} from '@angular/material/chips';
import {MatStepper} from '@angular/material/stepper';
import {ActivatedRoute, Params, Router} from '@angular/router';
import {forkJoin, of as observableOf} from 'rxjs';
import {first} from 'rxjs/operators';

import {TestResourceForm} from '../build_channels/test_resource_form';
import {MttClient} from '../services/mtt_client';
import * as mttModels from '../services/mtt_models';
import {RerunContext, testResourceDefToObj} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {FormChangeTracker} from '../shared/can_deactivate';
import {TestRunConfigForm} from '../shared/test_run_config_form';
import {buildApiErrorMessage, resetStepCompletion} from '../shared/util';

enum Step {
  CONFIGURE_TEST_RUN = 0,
  SELECT_DEVICES = 1,
  ADD_DEVICE_ACTIONS = 2,
  SET_TEST_RESOURCES = 3
}
const TOTAL_STEPS = 4;

/**
 * Form for running a new test
 */
@Component({
  selector: 'new-test-run-page',
  styleUrls: ['new_test_run_page.css'],
  templateUrl: './new_test_run_page.ng.html',
})
export class NewTestRunPage extends FormChangeTracker implements OnInit,
                                                                 AfterViewInit {
  @ViewChild('backButton', {static: false}) backButton?: MatButton;
  // Validation variable
  @ViewChild(TestRunConfigForm, {static: true})
  testRunConfigForm!: TestRunConfigForm;
  @ViewChild(TestResourceForm, {static: true})
  testResourceForm!: TestResourceForm;
  errorMessage = '';

  // Record each step whether it has finished or not
  stepCompletionStatusMap: {[stepNum: number]: boolean} = {};
  step = Step;
  resetStepCompletion = resetStepCompletion;
  totalSteps = TOTAL_STEPS;

  prevTestRunId?: string;
  rerunContext?: RerunContext;

  testMap: {[key: string]: mttModels.Test} = {};
  testRunConfig = mttModels.initTestRunConfig();

  deviceActions: mttModels.DeviceAction[] = [];
  deviceActionMap: {[key: string]: mttModels.DeviceAction;} = {};
  selectedDeviceActions: mttModels.DeviceAction[] = [];

  labels: string[] = [];
  testResourceObjs: mttModels.TestResourceObj[] = [];
  nodeConfigTestResourceUrls: mttModels.NameValuePair[] = [];
  buildChannels: mttModels.BuildChannel[] = [];

  isLoading = false;

  /** Keys used to separate labels */
  readonly separatorKeyCodes: number[] = [ENTER, COMMA];

  back() {
    this.router.navigate(['tests']);
  }

  constructor(
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly router: Router, private readonly route: ActivatedRoute,
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier) {
    super();
  }

  ngOnInit() {
    // init data
    this.route.queryParams.pipe(first()).subscribe((params: Params) => {
      // TODO: Reset test run and stepper on id change
      this.prevTestRunId = params['prevTestRunId'];
      this.loadData(params['testId'], params['prevTestRunId']);
    });

    // Initialize step completion status map
    resetStepCompletion(0, this.stepCompletionStatusMap, this.totalSteps);
  }

  ngAfterViewInit() {
    this.backButton!.focus();
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
      case Step.CONFIGURE_TEST_RUN: {
        this.invalidInputs = this.testRunConfigForm.getInvalidInputs();
        return !this.invalidInputs.length;
      }
      case Step.SELECT_DEVICES: {
        const res = !!this.testRunConfig.run_target;
        if (!res) {
          this.errorMessage = 'Run target is required';
        }
        return res;
      }
      case Step.SET_TEST_RESOURCES: {
        this.invalidInputs = this.testResourceForm.getInvalidInputs();
        return !this.invalidInputs.length;
      }
      default: {
        break;
      }
    }
    return true;
  }

  /**
   * Load MTT models data
   * @param testId ID of the selected test to run
   * @param prevTestRunId ID of a previous test run to rerun
   */
  loadData(testId?: string, prevTestRunId?: string) {
    // Make API calls
    const testObs = this.mttClient.getTests();
    const deviceActionObs = this.mttClient.getDeviceActionList();
    const nodeConfigObs = this.mttClient.getNodeConfig();
    const buildChannelObs = this.mttClient.getBuildChannels();
    const prevTestRunObs = prevTestRunId ?
        this.mttClient.getTestRun(prevTestRunId) :
        observableOf(null);

    this.isLoading = true;
    this.liveAnnouncer.announce('Loading', 'polite');

    if (typeof testId !== 'undefined') {
      this.testRunConfig.test_id = testId;
    }

    // Get API call results
    forkJoin([
      testObs, deviceActionObs, nodeConfigObs, buildChannelObs, prevTestRunObs
    ])
        .pipe(first())
        .subscribe(
            ([
              testRes, deviceActionRes, nodeConfigRes, buildChannelRes,
              prevTestRunRes
            ]) => {
              // Tests
              this.testMap = {};
              if (testRes.tests) {
                for (const test of testRes.tests) {
                  if (test.id) {
                    this.testMap[test.id] = test;
                  }
                }
              }

              // Device Actions
              this.deviceActions = deviceActionRes.device_actions || [];
              this.deviceActionMap = {};
              for (const deviceAction of this.deviceActions) {
                this.deviceActionMap[deviceAction.id] = deviceAction;
              }

              // Node Configs
              this.nodeConfigTestResourceUrls =
                  nodeConfigRes.test_resource_default_download_urls || [];

              // Build Channels
              this.buildChannels = buildChannelRes.build_channels || [];

              // Previous test run
              this.loadPrevTestRun(prevTestRunRes);

              this.updateTestResources();

              this.isLoading = false;
              this.liveAnnouncer.announce('Test run loaded', 'assertive');
            },
            error => {
              this.notifier.showError(
                  'Failed to load test run.', buildApiErrorMessage(error));
            });
  }

  /** Load config values from a previous test run */
  loadPrevTestRun(prevTestRun: mttModels.TestRun|null) {
    if (!prevTestRun) {
      return;
    }

    if (prevTestRun.test) {
      this.testRunConfig.test_id = prevTestRun.test.id;
    }

    if (prevTestRun.test_run_config) {
      /**
       * TODO: If the run target is something other than serials,
       * the run target will be cleared.
       */
      this.testRunConfig = prevTestRun.test_run_config;

      // Load device actions
      const deviceActionIds = this.testRunConfig.before_device_action_ids || [];
      for (const deviceActionId of deviceActionIds) {
        this.selectedDeviceActions.push(this.deviceActionMap[deviceActionId]);
      }
    }

    if (prevTestRun.test_resources) {
      this.testResourceObjs = prevTestRun.test_resources;
    }

    this.labels = prevTestRun.labels || [];
  }

  /**
   * Under set test resource types, we need to update the required
   * test resources on data changes
   */
  updateTestResources() {
    const updatedObjsMap: {[name: string]: mttModels.TestResourceObj;} = {};

    // Get resource defs from Test
    if (typeof this.testRunConfig.test_id !== 'undefined') {
      const test = this.testMap[this.testRunConfig.test_id];
      if (test && test.test_resource_defs) {
        for (const def of test.test_resource_defs) {
          updatedObjsMap[def.name] = testResourceDefToObj(def);
        }
      }
    }

    // Get resource defs from Device Actions
    for (const deviceAction of this.selectedDeviceActions) {
      if (deviceAction.test_resource_defs) {
        for (const def of deviceAction.test_resource_defs) {
          updatedObjsMap[def.name] = testResourceDefToObj(def);
        }
      }
    }

    // Overwrite urls with node config default download values
    for (const nodeUrl of this.nodeConfigTestResourceUrls) {
      if (nodeUrl.name in updatedObjsMap) {
        updatedObjsMap[nodeUrl.name].url = nodeUrl.value;
      }
    }

    // Overwrite urls with previously entered values
    for (const oldObj of this.testResourceObjs) {
      if (oldObj.name && oldObj.name in updatedObjsMap) {
        updatedObjsMap[oldObj.name] = oldObj;
      }
    }

    // Save updated values
    this.testResourceObjs = Object.values(updatedObjsMap);
  }

  addLabel(event: MatChipInputEvent) {
    const input = event.input;
    const value = event.value;

    if ((value || '').trim() && this.labels.indexOf(value.trim()) === -1) {
      this.labels.push(value.trim());
    }

    if (input) {
      input.value = '';
    }
  }

  removeLabel(label: string) {
    const index = this.labels.indexOf(label);
    if (index >= 0) {
      this.labels.splice(index, 1);
    }
  }

  startTestRun() {
    // TODO: Add input verification and error message
    if (!this.validateStep(Step.SET_TEST_RESOURCES)) {
      return;
    }
    // prepare test run config
    this.testRunConfig.before_device_action_ids =
        this.selectedDeviceActions.map(action => action.id);

    const newTestRunRequest: mttModels.NewTestRunRequest = {
      // TODO: Implement output upload config after sync with
      // design
      labels: this.labels,
      test_output_upload_configs: [],
      test_resource_pipes: this.testResourceObjs as
          mttModels.TestResourcePipe[],
      test_run_config: {...this.testRunConfig} as mttModels.TestRunConfig,
      rerun_context: this.rerunContext || {}
    };

    this.mttClient.createNewTestRunRequest(newTestRunRequest)
        .pipe(first())
        .subscribe(
            result => {
              super.resetForm();
              this.router.navigate([`test_runs/${result.id}`]);
              this.notifier.showMessage(`Test run '${result.id}' started`);
            },
            error => {
              this.notifier.showError(
                  'Failed to schedule a new test run.',
                  buildApiErrorMessage(error));
            });
  }
}
