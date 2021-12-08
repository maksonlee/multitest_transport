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

import {Component, EventEmitter, Input, Output} from '@angular/core';

import {NameMultiValuePair} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {arrayToString} from '../shared/util';

/**
 * An event object emitted when option's value changed
 */
export interface OptionValueChangeEvent {
  value: string;
  index: number;
}

/**
 * Form for Tradefed Config Options
 */
@Component({
  selector: 'tradefed-config-option-form',
  styleUrls: ['tradefed_config_option_form.css'],
  templateUrl: './tradefed_config_option_form.ng.html',
  providers:
      [{provide: FormChangeTracker, useExisting: TradefedConfigOptionForm}]
})
export class TradefedConfigOptionForm extends FormChangeTracker {
  @Input() optionTypeName = 'TradeFed Option';
  @Input() optionValues?: NameMultiValuePair[];
  @Input() canEdit = true;
  @Output() readonly addOption = new EventEmitter();
  @Output() readonly removeOption = new EventEmitter<number>();
  @Output() readonly optionValueChange = new EventEmitter<OptionValueChangeEvent>();
  arrayToString = arrayToString;

  /** Emit event when option's value changes */
  onOptionValueChange(value: string, index: number) {
    const event: OptionValueChangeEvent = {value, index};
    this.optionValueChange.emit(event);
  }
}
