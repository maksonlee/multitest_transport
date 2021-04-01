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

import {Injectable} from '@angular/core';
import {forkJoin, Observable, of as observableOf} from 'rxjs';
import {first, map} from 'rxjs/operators';

import {MttClient} from './mtt_client';
import * as mttModels from './mtt_models';


/** Contains maps for the different MTT models */
export interface MttObjectMap {
  buildChannelMap: {[id: string]: mttModels.BuildChannel};
  configSetInfoMap: {[id: string]: mttModels.ConfigSetInfo};
  deviceActionMap: {[id: string]: mttModels.DeviceAction};
  testMap: {[id: string]: mttModels.Test};
  testRunActionMap: {[id: string]: mttModels.TestRunAction};
}

/** Returns a new empty MttObjectMap object */
export function newMttObjectMap(): MttObjectMap {
  return {
    buildChannelMap: {},
    configSetInfoMap: {},
    deviceActionMap: {},
    testMap: {},
    testRunActionMap: {}
  };
}

/**
 * This service gets all common MTT data models (tests, build channels,
 * device actions, and test run actions) and stores them into arrays or maps.
 */
@Injectable({
  providedIn: 'root',
})
export class MttObjectMapService {
  private readonly loadDataObs: Observable<MttObjectMap>;
  private data?: MttObjectMap;

  constructor(
      private readonly mttClient: MttClient,
  ) {
    const buildChannelObs = this.mttClient.getBuildChannels();
    const configSetInfoObs = this.mttClient.getConfigSetInfos();
    const deviceActionObs = this.mttClient.getDeviceActionList();
    const testObs = this.mttClient.getTests();
    const testRunActionObs = this.mttClient.testRunActions.list();
    const dataObs = forkJoin({
      buildChannelList: buildChannelObs,
      configSetInfoList: configSetInfoObs,
      deviceActionList: deviceActionObs,
      testList: testObs,
      testRunActions: testRunActionObs,
    });

    this.loadDataObs = dataObs.pipe(
        first(), map(res => {
          const resData = newMttObjectMap();

          // Build Channels
          const buildChannels = res.buildChannelList.build_channels || [];
          for (const buildChannel of buildChannels) {
            resData.buildChannelMap[buildChannel.id] = buildChannel;
          }

          // Config Set Infos
          const configSetInfos = res.configSetInfoList.config_set_infos || [];
          for (const configSetInfo of configSetInfos) {
            resData.configSetInfoMap[configSetInfo.url] = configSetInfo;
          }

          // Device Actions
          const deviceActions = res.deviceActionList.device_actions || [];
          for (const deviceAction of deviceActions) {
            resData.deviceActionMap[deviceAction.id] = deviceAction;
          }

          // Test Run Actions
          for (const action of res.testRunActions || []) {
            resData.testRunActionMap[action.id] = action;
          }

          // Tests
          for (const test of res.testList.tests || []) {
            if (test.id) {
              resData.testMap[test.id] = test;
            }
          }
          this.data = resData;
          return resData;
        }));
  }

  getMttObjectMap(forceUpdate = false): Observable<MttObjectMap> {
    if (forceUpdate || !this.data) {
      return this.loadDataObs;
    }
    return observableOf(this.data);
  }
}
