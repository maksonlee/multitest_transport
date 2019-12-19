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
import {AfterViewInit, Component, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MatButton} from '@angular/material/button';
import {MatChipInputEvent} from '@angular/material/chips';
import {MatStepper} from '@angular/material/stepper';
import {ActivatedRoute, Params, Router} from '@angular/router';
import {forkJoin, of as observableOf, ReplaySubject} from 'rxjs';
import {first, takeUntil} from 'rxjs/operators';

import {TestResourceClassType} from '../build_channels/test_resource_form';
import {TestResourceForm} from '../build_channels/test_resource_form';
import {MttClient} from '../services/mtt_client';
import * as mttModels from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {FormChangeTracker} from '../shared/can_deactivate';
import {ScheduleTimeForm} from '../shared/schedule_time_form';
import {buildApiErrorMessage, resetStepCompletion} from '../shared/util';

enum Step {
  CONFIGURE_TEST_PLAN = 0,
  CONFIGURE_TEST_RUN = 1,
  ADD_DEVICE_ACTIONS = 2,
  SET_TEST_RESOURCES = 3
}
const TOTAL_STEPS = 4;

/**
 * Form for creating or editing a test plan
 */
@Component({
  selector: 'test-plan-edit-page',
  styleUrls: ['test_plan_edit_page.css'],
  templateUrl: './test_plan_edit_page.ng.html',
})
export class TestPlanEditPage extends FormChangeTracker implements
    OnInit, AfterViewInit, OnDestroy {
  @ViewChild('backButton', {static: false}) backButton?: MatButton;
  @ViewChild('scheduleTimeForm', {static: false})
  scheduleTimeForm!: ScheduleTimeForm;

  // Validation variables
  @ViewChild(TestResourceForm, {static: true})
  testResourceForm!: TestResourceForm;
  errorMessage = '';

  // Record each step whether it has finished or not
  stepCompletionStatusMap: {[stepNum: number]: boolean} = {};
  step = Step;
  resetStepCompletion = resetStepCompletion;
  totalSteps = TOTAL_STEPS;

  private readonly destroy = new ReplaySubject<void>();
  buildChannels: mttModels.BuildChannel[] = [];
  data: Partial<mttModels.TestPlan> = mttModels.initTestPlan();
  deviceActions: mttModels.DeviceAction[] = [];
  deviceActionMap: {[key: string]: mttModels.DeviceAction;} = {};
  editMode = false;
  nodeConfigTestResourceUrls: mttModels.NameValuePair[] = [];
  selectedDeviceActions: mttModels.DeviceAction[] = [];
  testMap: {[key: string]: mttModels.Test} = {};
  testResourceClassType = TestResourceClassType;
  testResourceObjs: mttModels.TestResourceObj[] = [];
  testResourceTypeOptions = Object.values(mttModels.TestResourceType);

  /** Keys used to separate labels */
  readonly separatorKeyCodes: number[] = [ENTER, COMMA];

  isLoading = false;

  constructor(
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier,
      private readonly route: ActivatedRoute, private readonly router: Router) {
    super();
  }

  ngOnDestroy() {
    this.destroy.next();
  }

  ngOnInit() {
    this.route.params.pipe(takeUntil(this.destroy))
        .subscribe((params: Params) => {
          this.loadData(params['id']);
        });

    // Initialize step completion status map
    resetStepCompletion(0, this.stepCompletionStatusMap, this.totalSteps);
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
      case Step.CONFIGURE_TEST_PLAN: {
        this.invalidInputs = this.getInvalidInputs();
        return !this.invalidInputs.length;
      }
      case Step.CONFIGURE_TEST_RUN: {
        const res =
            !!this.data.test_run_configs && !!this.data.test_run_configs.length;
        if (!res) {
          this.errorMessage = 'Test run configuration is required';
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


  ngAfterViewInit() {
    this.backButton!.focus();
  }

  loadData(testPlanId: string|undefined) {
    this.editMode = !!testPlanId;
    if (this.editMode) {
      this.isLoading = true;
      this.liveAnnouncer.announce('Loading', 'polite');
    }

    const buildChannelObs = this.mttClient.getBuildChannels();
    const deviceActionObs = this.mttClient.getDeviceActionList();
    const nodeConfigObs = this.mttClient.getNodeConfig();
    const testObs = this.mttClient.getTests();
    const testPlanObs = testPlanId ? this.mttClient.getTestPlan(testPlanId) :
                                     observableOf(null);

    // Get API call results
    forkJoin(
        [buildChannelObs, deviceActionObs, nodeConfigObs, testObs, testPlanObs])
        .pipe(first())
        .subscribe(
            ([
              buildChannelRes, deviceActionRes, nodeConfigRes, testRes,
              testPlanRes
            ]) => {
              // Build Channels
              this.buildChannels = buildChannelRes.build_channels || [];

              // Device Actions
              this.deviceActions = deviceActionRes.device_actions || [];
              this.deviceActionMap = {};
              for (const deviceAction of this.deviceActions) {
                this.deviceActionMap[deviceAction.id] = deviceAction;
              }

              // Node Configs
              this.nodeConfigTestResourceUrls =
                  nodeConfigRes.test_resource_default_download_urls || [];

              // Tests
              this.testMap = {};
              if (testRes.tests) {
                for (const test of testRes.tests) {
                  if (test.id) {
                    this.testMap[test.id] = test;
                  }
                }
              }

              // Test Plan
              this.loadTestPlan(testPlanRes);

              if (this.editMode) {
                this.isLoading = false;
                this.liveAnnouncer.announce('Test plan loaded', 'assertive');
              }
            },
            (error) => {
              this.notifier.showError(
                  'Failed to load test plan.', buildApiErrorMessage(error));
            });
  }

  loadTestPlan(testPlan: mttModels.TestPlan|null) {
    if (!testPlan) {
      return;
    }

    this.data = testPlan;
    this.data.cron_exp = testPlan.cron_exp || '';
    this.data.before_device_action_ids =
        testPlan.before_device_action_ids || [];
    this.data.labels = testPlan.labels || [];
    this.data.test_output_upload_configs =
        testPlan.test_output_upload_configs || [];
    this.data.test_resource_pipes = testPlan.test_resource_pipes || [];

    if (this.scheduleTimeForm) {
      this.scheduleTimeForm.initInputSelector(this.data.cron_exp);
    }

    if (this.data.before_device_action_ids) {
      // Load device actions
      const deviceActionIds = this.data.before_device_action_ids || [];
      for (const deviceActionId of deviceActionIds) {
        this.selectedDeviceActions.push(this.deviceActionMap[deviceActionId]);
      }
    }
    this.updateTestResources();
  }

  /**
   * Under set test resource types, we need to update the required
   * test resources on data changes
   */
  updateTestResources() {
    const updatedObjsMap: {[name: string]: mttModels.TestResourceObj;} = {};

    // Get resource defs from Tests
    for (const config of this.data.test_run_configs!) {
      const testId = config.test_id;
      if (testId && this.testMap[testId] &&
          this.testMap[testId].test_resource_defs) {
        for (const def of this.testMap[testId].test_resource_defs!) {
          updatedObjsMap[def.name] = mttModels.testResourceDefToObj(def);
        }
      }
    }

    // Get resource defs from Device Actions
    for (const deviceAction of this.selectedDeviceActions) {
      if (deviceAction.test_resource_defs) {
        for (const def of deviceAction.test_resource_defs) {
          updatedObjsMap[def.name] = mttModels.testResourceDefToObj(def);
        }
      }
    }

    // Overwrite urls with node config default download values
    for (const nodeUrl of this.nodeConfigTestResourceUrls) {
      if (nodeUrl.name in updatedObjsMap) {
        updatedObjsMap[nodeUrl.name].url = nodeUrl.value;
      }
    }

    // Overwrite urls with previously entered values or existed urls from test
    // plan data.
    if (this.data.test_resource_pipes) {
      for (const testResourcePipe of this.data.test_resource_pipes) {
        if (testResourcePipe.name && testResourcePipe.name in updatedObjsMap) {
          updatedObjsMap[testResourcePipe.name].url = testResourcePipe.url;
        }
      }
    }

    // Save updated values
    this.testResourceObjs = Object.values(updatedObjsMap);
  }

  setCronExpression(cronExpression: string) {
    this.data.cron_exp = cronExpression;
  }

  addLabel(event: MatChipInputEvent) {
    const input = event.input;
    const value = event.value;

    if ((value || '').trim() &&
        this.data.labels!.indexOf(value.trim()) === -1) {
      this.data.labels!.push(value.trim());
    }

    if (input) {
      input.value = '';
    }
  }

  removeLabel(label: string) {
    const index = this.data.labels!.indexOf(label);
    if (index >= 0) {
      this.data.labels!.splice(index, 1);
    }
  }

  back() {
    this.router.navigate(['test_plans']);
  }

  // create or update test plan
  submit() {
    if (!this.validateStep(Step.SET_TEST_RESOURCES)) {
      return;
    }

    const resultTest: mttModels.TestPlan = {
      id: this.data.id,
      name: this.data.name!.trim(),
      labels: this.data.labels,
      cron_exp: this.data.cron_exp!.trim(),
      test_run_configs: this.data.test_run_configs,
      before_device_action_ids:
          this.selectedDeviceActions.map((action) => action.id),
      test_resource_pipes: this.testResourceObjs as
          mttModels.TestResourcePipe[],
    };

    if (this.editMode) {
      this.mttClient.updateTestPlan(resultTest.id!, resultTest)
          .subscribe(
              (result) => {
                super.resetForm();
                this.back();
                this.notifier.showMessage(
                    `Test plan '${resultTest.name}' updated`);
              },
              (error) => {
                this.notifier.showError(
                    'Failed to update test plan.', buildApiErrorMessage(error));
              });
    } else {
      this.mttClient.createTestPlan(resultTest)
          .subscribe(
              (result) => {
                super.resetForm();
                this.back();
                this.notifier.showMessage(
                    `Test plan '${resultTest.name}' created`);
              },
              (error) => {
                this.notifier.showError(
                    'Failed to create test plan.', buildApiErrorMessage(error));
              });
    }
  }
}
