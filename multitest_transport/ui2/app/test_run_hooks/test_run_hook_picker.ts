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

import {SelectionModel} from '@angular/cdk/collections';
import {CdkDragDrop, moveItemInArray} from '@angular/cdk/drag-drop';
import {Component, Input, OnInit} from '@angular/core';

import {TestRunHookConfig} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {assertRequiredInput} from '../shared/util';

/**
 * Manages a list of hook configurations, allowing users to add, remove, edit,
 * or rearrange them.
 */
@Component({
  selector: 'test-run-hook-picker',
  styleUrls: ['test_run_hook_picker.css'],
  templateUrl: './test_run_hook_picker.ng.html',
  providers: [{provide: FormChangeTracker, useExisting: TestRunHookPicker}]
})
export class TestRunHookPicker extends FormChangeTracker implements OnInit {
  @Input() hookConfigs!: TestRunHookConfig[];
  @Input() selectedHookConfigs!: TestRunHookConfig[];

  selection =
      new SelectionModel<TestRunHookConfig>(true, this.selectedHookConfigs);

  ngOnInit() {
    assertRequiredInput(
        this.hookConfigs, 'hookConfigs', 'test-run-hook-picker');
    assertRequiredInput(
        this.selectedHookConfigs, 'selectedHookConfigs',
        'test-run-hook-picker');
  }

  /** Moves an hook config after drag and drop in the selected list. */
  moveConfig(event: CdkDragDrop<TestRunHookConfig[]>) {
    moveItemInArray(
        this.selectedHookConfigs, event.previousIndex, event.currentIndex);
  }

  /** Removes a hook config from the selected list. */
  removeConfig(hookConfig: TestRunHookConfig) {
    const index = this.selectedHookConfigs.indexOf(hookConfig);
    if (index > -1) {
      this.selectedHookConfigs.splice(index, 1);
    }
  }

  /** Adds all hook configs from the selection menu. */
  addSelectedConfigs() {
    this.selectedHookConfigs.push(...this.selection.selected);
    this.selection.clear();
  }
}
