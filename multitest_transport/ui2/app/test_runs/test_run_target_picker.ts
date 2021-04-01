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
  @Input() deviceSpecs: string[] = [];
  @Input() shardCount = 0;
  @Input() autoUpdate = false;

  @Output() deviceSpecsChange = new EventEmitter<string[]>();
  @Output() shardCountChange = new EventEmitter<number>();

  manualDeviceSpecs = false;

  getDeviceSerials(): string[] {
    const deviceSerials = [];
    for (const spec of this.deviceSpecs || []) {
      const match = /^device_serial:(\S*)+$/.exec(spec);
      if (match) {
        deviceSerials.push(match[1]);
      }
    }
    return deviceSerials;
  }

  getDeviceSpecsString(): string {
    return (this.deviceSpecs || []).join(';');
  }

  onDeviceSpecsStringChange(deviceSpecsString: string) {
    this.deviceSpecs = (deviceSpecsString || '').split(';');
    this.deviceSpecsChange.emit(this.deviceSpecs);
  }

  /**
   * When devices are selected in device list section, update shard count and
   * run target info.
   */
  onDeviceListSelectionChange(deviceSerials: string[]) {
    if (!this.manualDeviceSpecs) {
      this.deviceSpecs =
          deviceSerials.map(serial => `device_serial:${serial}`);
      this.deviceSpecsChange.emit(this.deviceSpecs);
      this.shardCount = deviceSerials.length;
      this.shardCountChange.emit(this.shardCount);
    }
  }
}
