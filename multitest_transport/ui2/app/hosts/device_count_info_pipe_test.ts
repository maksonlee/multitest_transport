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

import {LabHostExtraInfo} from '../services/mtt_lab_models';
import {DeviceCountInfoPipe} from './device_count_info_pipe';

describe('DeviceCountInfoPipe', () => {
  let pipe: DeviceCountInfoPipe;
  let hostExtraInfo: LabHostExtraInfo;
  let hostExtraInfo2: LabHostExtraInfo;

  beforeEach(() => {
    hostExtraInfo = {
      allocated_devices: '2',
      available_devices: '3',
      device_count_time_stamp: '',
      offline_devices: '4',
      total_devices: '10',
      host_note_id: 0,
    };
    hostExtraInfo2 = {
      allocated_devices: '',
      available_devices: '0',
      device_count_time_stamp: '',
      offline_devices: '',
      total_devices: '3',
      host_note_id: 0,
    };

    pipe = new DeviceCountInfoPipe('en-US');
  });

  it('returns the correct value', () => {
    expect(pipe.transform(hostExtraInfo, 'total')).toEqual('10');
    expect(pipe.transform(hostExtraInfo, 'online')).toEqual('6 (-4) (60.0%)');
    expect(pipe.transform(hostExtraInfo, 'available')).toEqual('3 (30.0%)');
    expect(pipe.transform(hostExtraInfo, 'allocated')).toEqual('2 (20.0%)');
  });

  it('returns the correct value from invalid data', () => {
    expect(pipe.transform(hostExtraInfo2, 'total')).toEqual('3');
    expect(pipe.transform(hostExtraInfo2, 'online')).toEqual('');
    expect(pipe.transform(hostExtraInfo2, 'available')).toEqual('0 (0.0%)');
    expect(pipe.transform(hostExtraInfo2, 'allocated')).toEqual('');
  });

  it('handles missing data', () => {
    expect(pipe.transform(hostExtraInfo, 'default')).toEqual('');
  });
});
