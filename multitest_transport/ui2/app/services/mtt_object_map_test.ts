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

import {of as observableOf} from 'rxjs';

import * as mttMocks from '../testing/mtt_mocks';

import {MttClient, TestRunActionClient} from './mtt_client';
import {MttObjectMapService, newMttObjectMap} from './mtt_object_map';

describe('MttObjectMapService', () => {
  let mttClient: jasmine.SpyObj<MttClient>;
  let service: MttObjectMapService;
  const buildChannel = mttMocks.newMockBuildChannel('build_channel_id');
  const deviceAction = mttMocks.newMockDeviceAction('device_action_id');
  const test = mttMocks.newMockTest('test_id');
  const configSetInfo = mttMocks.newMockConfigSetInfo('config_set_url');

  beforeEach(() => {
    mttClient = {
      ...jasmine.createSpyObj({
        getBuildChannels: observableOf({build_channels: [buildChannel]}),
        getConfigSetInfos: observableOf({config_set_infos: [configSetInfo]}),
        getDeviceActionList: observableOf({device_actions: [deviceAction]}),
        getTests: observableOf({tests: [test]}),
      }),
      testRunActions:
          jasmine.createSpyObj<TestRunActionClient>({list: observableOf([])}),
    } as jasmine.SpyObj<MttClient>;
    service = new MttObjectMapService(mttClient);
  });


  it('gets the data from MttClient', () => {
    let map = newMttObjectMap();
    service.getMttObjectMap().subscribe((res) => {
      map = res;
    });
    expect(map.buildChannelMap).toEqual({build_channel_id: buildChannel});
    expect(map.configSetInfoMap).toEqual({config_set_url: configSetInfo});
    expect(map.deviceActionMap).toEqual({device_action_id: deviceAction});
    expect(map.testMap).toEqual({test_id: test});
  });
});
