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
import {SelectionModel} from '@angular/cdk/collections';
import {Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges} from '@angular/core';
import {merge, ReplaySubject, Subject, timer} from 'rxjs';
import {filter, first, flatMap, map, repeat, takeUntil, tap} from 'rxjs/operators';

import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {DeviceInfo} from '../services/tfc_models';
import {buildApiErrorMessage} from '../shared/util';

const AUTO_UPDATE_INTERVAL_MILLIS = 5000;

/**
 * A component for displaying a list of devices.
 *
 * If given deviceInfos as input, that list will be displayed. Otherwise, it
 * will retrieve and display the list of devices connected to the host.
 */
@Component({
  selector: 'device-list',
  styleUrls: ['device_list.css'],
  templateUrl: './device_list.ng.html',
})
export class DeviceList implements OnChanges, OnDestroy, OnInit {
  // When true, shows a column of checkboxes
  @Input() selectable = false;
  // When true, disables each checkbox (but still visible)
  @Input() selectDisabled = false;
  @Input() selectedSerials = [];
  @Input()
  displayedDeviceInfoColumns: string[] = [
    'device_serial', 'product', 'product_variant', 'build_id', 'battery_level',
    'state'
  ];
  @Input() deviceInfos?: DeviceInfo[];
  @Input() autoUpdate = false;
  @Output() selectionChange = new EventEmitter<string[]>();

  private readonly updateTrigger = new Subject();
  private readonly destroy = new ReplaySubject(1);

  serialMap: {[serial: string]: DeviceInfo} = {};

  isLoading = false;

  selection = new SelectionModel<string>(
      /*allow multi select*/ true, this.selectedSerials);

  // TODO: Add a process to detect weather new device is added
  constructor(
      private readonly notifier: Notifier, private readonly tfc: TfcClient,
      private readonly liveAnnouncer: LiveAnnouncer) {}

  ngOnInit() {
    if (this.selectable) {
      this.displayedDeviceInfoColumns.unshift('select');
    }

    if (!this.deviceInfos) {
      // Load devices from API.
      this.isLoading = true;
      this.liveAnnouncer.announce('Loading', 'polite');

      const updateTimer = timer(AUTO_UPDATE_INTERVAL_MILLIS)
                              .pipe(filter(() => this.autoUpdate));
      merge(this.updateTrigger, updateTimer)
          .pipe(
              first(), flatMap(() => this.tfc.getDeviceInfos()), tap(() => {
                // This page is constantly loading. Thus, only announce the
                // loading complete status for one time
                if (this.isLoading) {
                  this.liveAnnouncer.announce('Loading complete', 'assertive');
                }
                this.isLoading = false;
              }),
              map(res => res.device_infos), repeat(), takeUntil(this.destroy))
          .subscribe(
              infos => {
                this.deviceInfos = infos || [];

                // Unselect unavailable devices.
                this.serialMap = this.infosToSerialMap(this.deviceInfos);

                this.selection.selected.forEach(serial => {
                  if (!this.serialMap[serial]) {
                    this.selection.deselect(serial);
                  }
                });
                this.selectionChange.emit(this.selection.selected);
              },
              error => {
                this.notifier.showError(
                    'Failed to load devices.', buildApiErrorMessage(error));
              });
      this.updateTrigger.next();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['autoUpdate'] && this.autoUpdate) {
      this.updateTrigger.next();
    }
    if (changes['selectedSerials']) {
      this.selection.clear();
      this.selection.select(...this.selectedSerials);
    }
  }

  ngOnDestroy() {
    this.destroy.next();
    this.destroy.complete();
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
