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

import {Component, EventEmitter, Input, Output} from '@angular/core';
import {FormChangeTracker} from '../shared/can_deactivate';

/**
 * A component for selecting run targets.
 */
@Component({
  selector: 'test-run-target-picker',
  styleUrls: ['test_run_target_picker.css'],
  templateUrl: './test_run_target_picker.ng.html',
  providers: [{provide: FormChangeTracker, useExisting: TestRunTargetPicker}]

})
export class TestRunTargetPicker extends FormChangeTracker {
  @Input() runTarget = '';
  @Input() shardCount = 0;
  @Input() autoUpdate = false;

  @Output() runTargetChange = new EventEmitter<string>();
  @Output() shardCountChange = new EventEmitter<number>();

  manualRunTarget = false;

  /**
   * When devices are selected in device list section, update shard count and
   * run target info.
   */
  onDeviceListSelectionChange(deviceSerials: string[]) {
    if (!this.manualRunTarget) {
      this.shardCount = deviceSerials.length;
      this.runTarget = deviceSerials.join(';');

      this.runTargetChange.emit(this.runTarget);
      this.shardCountChange.emit(this.shardCount);
    }
  }
}
