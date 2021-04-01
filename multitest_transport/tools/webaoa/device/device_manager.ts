/**
 * @license
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
import {Observable, Subject} from 'rxjs';

import {AoaDevice} from './device';

/**
 * USB and AOA device manager. Tracks connected devices and requests access to
 * unpaired devices.
 */
@Injectable()
export class DeviceManager implements OnDestroy {
  private readonly usb?: USB = navigator.usb;
  private readonly connectionSubject = new Subject<void>();
  private readonly connectionListener = () => {
    this.connectionSubject.next();
  };

  constructor() {
    if (this.usb) {
      this.usb.addEventListener('connect', this.connectionListener);
      this.usb.addEventListener('disconnect', this.connectionListener);
    }
  }

  ngOnDestroy() {
    if (this.usb) {
      this.usb.removeEventListener('connect', this.connectionListener);
      this.usb.removeEventListener('disconnect', this.connectionListener);
    }
  }

  /** Emits whenever an authorized USB device is connected or disconnected. */
  onConnectionChange(): Observable<void> {
    return this.connectionSubject;
  }

  /** @return list of authorized AOA-compatible devices */
  async getDevices(): Promise<AoaDevice[]> {
    const delegates = await this.usb!.getDevices();
    const devices = await Promise.all(delegates.map(d => {
      return AoaDevice.fromUSBDevice(d).catch(() => Promise.resolve(null));
    }));
    return devices.filter(d => !!d) as AoaDevice[];
  }

  /**
   * Opens browser dialog to request access to an AOA-compatible device.
   * @param serialNumber optional device serial number
   * @return newly paired device
   */
  async requestDevice(serialNumber?: string): Promise<AoaDevice> {
    const filters: USBDeviceFilter[] = serialNumber ? [{serialNumber}] : [];
    const delegate = await this.usb!.requestDevice({filters});
    const device = await AoaDevice.fromUSBDevice(delegate);
    this.connectionSubject.next();
    return device;
  }
}
