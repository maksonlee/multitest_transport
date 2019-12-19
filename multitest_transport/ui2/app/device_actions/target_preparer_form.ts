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

import {Component, ElementRef, EventEmitter, Input, OnInit, Output, QueryList, ViewChildren} from '@angular/core';

import {TradefedConfigObject} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {assertRequiredInput} from '../shared/util';
import {OptionValueChangeEvent} from './target_preparer_option_form';

/**
 * Form for Target Preparer
 */
@Component({
  selector: 'target-preparer-form',
  styleUrls: ['target_preparer_form.css'],
  templateUrl: './target_preparer_form.ng.html',
  providers: [{provide: FormChangeTracker, useExisting: TargetPreparerForm}]
})
export class TargetPreparerForm extends FormChangeTracker implements OnInit {
  @Input() targetPreparers!: Array<Partial<TradefedConfigObject>>;
  @Output() addTargetPreparer = new EventEmitter();
  @Output() deleteTargetPreparer = new EventEmitter<number>();
  @ViewChildren(FormChangeTracker) trackers!: QueryList<FormChangeTracker>;

  ngOnInit() {
    assertRequiredInput(
        this.targetPreparers, 'targetPreparers', 'target-preparer-form');
  }

  /** Add an option to target preparer */
  onAddOption(targetPreparer: Partial<TradefedConfigObject>) {
    if (!targetPreparer) {
      return;
    }
    if (!targetPreparer.option_values) {
      targetPreparer.option_values = [];
    }
    targetPreparer.option_values.push({name: '', values: []});
  }

  /** Remove the ith option from target preparer */
  onRemoveOption(targetPreparer: Partial<TradefedConfigObject>, i: number) {
    if (!targetPreparer || !targetPreparer.option_values ||
        !targetPreparer.option_values[i]) {
      return;
    }
    targetPreparer.option_values.splice(i, 1);
  }

  /** On option value change, convert the value from string to list */
  onOptionValueChange(
      targetPreparer: Partial<TradefedConfigObject>,
      event: OptionValueChangeEvent) {
    const arr = event.value.split('\n');
    if (!targetPreparer || !targetPreparer.option_values ||
        !targetPreparer.option_values[event.index]) {
      return;
    }
    targetPreparer.option_values[event.index]!.values = arr;
    return arr;
  }

  /**
   * Overwrite the FormChangeTracker getInvalidInputs method
   * to allow childs invalidInputs can be propagated to parent
   * page
   */
  getInvalidInputs(): ElementRef[] {
    this.invalidInputs = super.getInvalidInputs();
    this.trackers.forEach((tracker) => {
      this.invalidInputs.push(...tracker.getInvalidInputs());
    });
    return this.invalidInputs;
  }
}
