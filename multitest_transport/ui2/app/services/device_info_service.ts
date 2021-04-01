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

import {Injectable, OnDestroy} from '@angular/core';
import {defer, Observable, ReplaySubject, timer} from 'rxjs';
import {delayWhen, map, publishReplay, refCount, repeatWhen, takeUntil, tap} from 'rxjs/operators';

import {TfcClient} from './tfc_client';
import {DeviceInfo} from './tfc_models';

/** Visible for testing */
export const AUTO_UPDATE_INTERVAL_MILLIS = 5000;

/**
 * This service polls TFC getDeviceInfos and multicasts to the subscribers. It
 * stops polling when there is no subscriber. The service caches the latest
 * response from TFC for a short time. It emits the cached data to the new
 * subscribers immediately and then emits the updates periodically.
 */
@Injectable({
  providedIn: 'root',
})
export class DeviceInfoService implements OnDestroy {
  private readonly source: Observable<DeviceInfo[]>;
  private latestDeviceInfos?: DeviceInfo[];

  private readonly destroy = new ReplaySubject<void>(1);

  constructor(private readonly tfc: TfcClient) {
    this.source =
        defer(() => this.tfc.getDeviceInfos())
            .pipe(
                map(res => res.device_infos || []),
                tap((infos) => {
                  this.latestDeviceInfos = infos;
                }),
                repeatWhen((notifications) => {
                  return notifications.pipe(
                      // delay(AUTO_UPDATE_INTERVAL_MILLIS) doesn't work with
                      // tick() in the unit test.
                      delayWhen(() => timer(AUTO_UPDATE_INTERVAL_MILLIS)));
                }),
                takeUntil(this.destroy),
                publishReplay(1, AUTO_UPDATE_INTERVAL_MILLIS * 2),
                refCount());
  }

  ngOnDestroy() {
    this.destroy.next();
    this.destroy.complete();
  }

  getDeviceInfos(): Observable<DeviceInfo[]> {
    return this.source;
  }

  get isInitialized(): boolean {
    return typeof this.latestDeviceInfos !== 'undefined';
  }

  matchesDeviceSpec(info: DeviceInfo, spec: string): boolean {
    const regex = /([^\s:]+):(\S+)/g;
    let matches;
    while ((matches = regex.exec(spec))) {
      const key = matches[1];
      const value = matches[2];
      if (!(key in info) || info[key as keyof DeviceInfo] !== value) {
        return false;
      }
    }
    return true;
  }

  /**
   * Converts device specs to a set of device types by using the latest
   * device info snapshot.
   */
  deviceSpecsToDeviceTypes(deviceSpecs: string[]): Set<string> {
    if (!this.latestDeviceInfos) {
      return new Set();
    }
    const deviceTypes = new Set<string>();
    for (const info of this.latestDeviceInfos) {
      for (const spec of deviceSpecs) {
        if (this.matchesDeviceSpec(info, spec) && info.device_type) {
          deviceTypes.add(info.device_type);
        }
      }
    }
    return deviceTypes;
  }
}
