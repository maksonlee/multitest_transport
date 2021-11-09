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
import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';

import {DeviceInfo} from '../services/tfc_models';

/** A component for displaying a given list of devices. */
@Component({
  selector: 'device-picker',
  styleUrls: ['device_picker.css'],
  templateUrl: './device_picker.ng.html',
})
export class DevicePicker implements OnChanges, OnInit {
  // TODO: Remove the selection and rename this class.
  // When true, shows a column of checkboxes
  @Input() selectable = false;
  // When true, disables each checkbox (but still visible)
  @Input() selectDisabled = false;
  @Input() selectedSerials = [];
  @Input()
  displayedDeviceInfoColumns: string[] = [
    'device_serial', 'hostname', 'product', 'product_variant', 'build_id',
    'battery_level', 'sim_status', 'state'
  ];
  @Input() deviceInfos: DeviceInfo[] = [];
  @Output() selectionChange = new EventEmitter<string[]>();

  serialMap: {[serial: string]: DeviceInfo} = {};

  selection = new SelectionModel<string>(
      /*allow multi select*/ true, this.selectedSerials);

  ngOnInit() {
    if (this.selectable) {
      this.displayedDeviceInfoColumns.unshift('select');
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['deviceInfos']) {
      this.serialMap = this.infosToSerialMap(this.deviceInfos);
    }
    if (changes['selectedSerials'] || changes['deviceInfos']) {
      this.selection.clear();
      this.selection.select(...this.selectedSerials);
    }
  }

  /** Converts an array of DeviceInfos to a map indexed by serials */
  infosToSerialMap(infos: DeviceInfo[]): {[serial: string]: DeviceInfo} {
    const serialMap: {[serial: string]: DeviceInfo} = {};
    return infos.reduce((map, info) => {
      map[info.device_serial] = info;
      return map;
    }, serialMap);
  }

  /**
   * Returns true if a device serial has been selected, false otherwise.
   */
  hasSelectedSerial(): boolean {
    for (const target of this.selection.selected) {
      if (this.serialMap[target]) {
        return true;
      }
    }
    return false;
  }

  /**
   * Whether the number of selected elements matches the total number of rows.
   */
  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.deviceInfos && this.deviceInfos.length;
    return numSelected === numRows;
  }

  /**
   * Selects all rows if they are not all selected; otherwise clear selection.
   */
  toggleSelection() {
    this.isAllSelected() ? this.selection.clear() :
                           this.deviceInfos && this.deviceInfos.forEach(row => {
                             this.selection.select(row.device_serial);
                           });
    this.selectionChange.emit(this.selection.selected);
  }

  /**
   * When people with disability clicked on the checkbox, they don't
   * no what they are checking. This method with genereate the aria-label
   * for checkbox in the table.
   */
  getDeviceAriaMessage(row: DeviceInfo): string {
    return `Device with serial ${row.device_serial}`;
  }

  /**
   * On selection change, toggle the corresponding row and emit the selected
   * devices
   */
  onSelectionChange(row: DeviceInfo) {
    this.selection.toggle(row.device_serial);
    this.selectionChange.emit(this.selection.selected);
  }
}
