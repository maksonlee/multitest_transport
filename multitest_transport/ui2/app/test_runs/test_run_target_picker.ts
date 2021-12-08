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

import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

import {DeviceType} from '../services/tfc_models';
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
export class TestRunTargetPicker extends FormChangeTracker implements OnInit {
  @Input() deviceSpecs: string[] = [];
  @Input() shardCount = 0;
  @Input() autoUpdate = false;
  @Input() allowPartialDeviceMatch = false;

  @Output() readonly deviceSpecsChange = new EventEmitter<string[]>();
  @Output() readonly shardCountChange = new EventEmitter<number>();
  @Output() readonly allowPartialDeviceMatchChange =
      new EventEmitter<boolean>();

  manualDeviceSpecs = false;
  deviceSpecsAutocompleteOptions:
      Array<{value: string, displayedValue: string}> = [];

  // TODO: Query TFC for possible values.
  private readonly DEVICE_SPEC_SUGGESTION: {[key: string]: string[]} = {
    device_serial: [],
    // List only the types supported by ATS.
    device_type: [DeviceType.PHYSICAL, DeviceType.LOCAL_VIRTUAL],
    hostname: [],
    product: [],
    product_variant: [],
    sim_state: ['ABSENT', 'READY'],
  };

  ngOnInit() {
    this.deviceSpecsAutocompleteOptions =
        this.getDeviceSpecsAutocompleteOptions(this.getDeviceSpecsString());
  }

  getDeviceSerials(): string[] {
    const deviceSerials: string[] = [];
    for (const spec of this.deviceSpecs || []) {
      const match = /^device_serial:(\S+)$/.exec(spec);
      if (match) {
        deviceSerials.push(match[1]);
      }
    }
    return deviceSerials;
  }

  /**
   * This function converts a device specs string to autocomplete options. The
   * string consists of device specs separated by ';'. A device spec consists of
   * key-value pairs separated by ' '. A key and a value are separated by ':'.
   * This function first determines whether the suffix of the string is a
   * partial key or a partial value, and then filters the options by the suffix.
   * When the user selects any option, it is appended to the input field.
   */
  getDeviceSpecsAutocompleteOptions(specs: string):
      Array<{value: string, displayedValue: string}> {
    const keyBegin =
        Math.max(0, specs.lastIndexOf(' ') + 1, specs.lastIndexOf(';') + 1);
    const colon = specs.indexOf(':', keyBegin);
    if (colon < 0) {
      // The suffix is a key.
      const prefix = specs.slice(0, keyBegin);
      const partialKey = specs.slice(keyBegin);
      return Object.keys(this.DEVICE_SPEC_SUGGESTION)
          .filter(key => key.toLowerCase().includes(partialKey.toLowerCase()))
          .map(key => ({value: prefix + key + ':', displayedValue: key}));
    } else {
      // The suffix is a value.
      const key = specs.slice(keyBegin, colon);
      if (this.DEVICE_SPEC_SUGGESTION[key]) {
        const prefix = specs.slice(0, colon + 1);
        const partialValue = specs.slice(colon + 1);
        return this.DEVICE_SPEC_SUGGESTION[key]
            .filter(
                value =>
                    value.toLowerCase().includes(partialValue.toLowerCase()))
            .map(value => ({value: prefix + value, displayedValue: value}));
      }
    }
    return [];
  }

  getDeviceSpecsString(): string {
    return (this.deviceSpecs || []).join(';');
  }

  onDeviceSpecsStringChange(deviceSpecsString: string) {
    this.deviceSpecs = (deviceSpecsString || '').split(';');
    this.deviceSpecsChange.emit(this.deviceSpecs);
  }

  onDeviceSpecsModelChange(deviceSpecsString: string) {
    this.deviceSpecsAutocompleteOptions =
        this.getDeviceSpecsAutocompleteOptions(deviceSpecsString);
  }

  /**
   * When devices are selected in device list section, update shard count and
   * run target info.
   */
  onDeviceListSelectionChange(deviceSerials: string[]) {
    if (!this.manualDeviceSpecs) {
      this.deviceSpecs = deviceSerials.map(serial => `device_serial:${serial}`);
      this.deviceSpecsAutocompleteOptions =
          this.getDeviceSpecsAutocompleteOptions(this.getDeviceSpecsString());
      this.deviceSpecsChange.emit(this.deviceSpecs);
      this.shardCount = deviceSerials.length;
      this.shardCountChange.emit(this.shardCount);
    }
  }
}
