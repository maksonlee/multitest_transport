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

import {TotalOfflineDevicesAlertIconPipe} from './total_offline_devices_alert_icon_pipe';

describe('TotalOfflineDevicesAlertIconPipe', () => {
  let pipe: TotalOfflineDevicesAlertIconPipe;

  beforeEach(() => {
    pipe = new TotalOfflineDevicesAlertIconPipe();
  });

  it('returns the correct icon name', () => {
    expect(pipe.transform(0, 0, 0.4)).toEqual('disabled');
    expect(pipe.transform(0, 100, 0.4)).toEqual('disabled');
    expect(pipe.transform(1, 100, 0.4)).toEqual('error');
    expect(pipe.transform(40, 100, 0.4)).toEqual('error');
    expect(pipe.transform(41, 100, 0.4)).toEqual('warning');
    expect(pipe.transform(100, 100, 0.4)).toEqual('warning');

    expect(pipe.transform(0, 0, 4)).toEqual('disabled');
    expect(pipe.transform(0, 100, 4)).toEqual('disabled');
    expect(pipe.transform(1, 100, 4)).toEqual('error');
    expect(pipe.transform(40, 100, 4)).toEqual('error');
    expect(pipe.transform(41, 100, 4)).toEqual('error');
    expect(pipe.transform(100, 100, 4)).toEqual('error');

    expect(pipe.transform(0, 0, -0.4)).toEqual('disabled');
    expect(pipe.transform(0, 100, -0.4)).toEqual('disabled');
    expect(pipe.transform(1, 100, -0.4)).toEqual('warning');
    expect(pipe.transform(40, 100, -0.4)).toEqual('warning');
    expect(pipe.transform(41, 100, -0.4)).toEqual('warning');
    expect(pipe.transform(100, 100, -0.4)).toEqual('warning');
  });
});
