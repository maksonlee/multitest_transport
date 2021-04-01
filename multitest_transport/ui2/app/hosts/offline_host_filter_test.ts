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

import 'jasmine';

import {convertToLabHostInfosResponse, LabHostInfo, LabHostInfosResponse} from '../services/mtt_lab_models';
import {HostInfosResponse} from '../services/tfc_models';
import {newMockHostInfosResponse} from '../testing/mtt_lab_mocks';

import {ALL_OPTIONS_VALUE, filterHostListDataSource} from './offline_host_filter';

describe('Offline host filter', () => {
  let hostInfos: LabHostInfo[];
  let hostGroups: string[];
  let runTargets: string[];
  let labHostInfosResponse: LabHostInfosResponse;
  let hostInfosResponse: HostInfosResponse;

  beforeEach(() => {
    hostInfosResponse = newMockHostInfosResponse();
    labHostInfosResponse = convertToLabHostInfosResponse(hostInfosResponse);
    hostInfos = labHostInfosResponse.host_infos || [];
    hostGroups = [...new Set(hostInfos.map((x) => x.host_group))];
    runTargets = [...new Set(hostInfos.flatMap((x) => x.device_count_summaries)
                                 .map((x) => x.run_target))];
  });

  describe('filterHostListDataSource', () => {
    it('should not filter hostInfos if there are no hostGroups, runTarget and testHarness',
       () => {
         const filteredHostInfos = filterHostListDataSource(hostInfos);
         expect(filteredHostInfos).toEqual(hostInfos);
       });

    it('should filter testHarness correctly', () => {
      const filterTestharness = 'MOBILEHARNESS';
      const filteredHostInfos =
          filterHostListDataSource(hostInfos, [], [], filterTestharness);

      const filteredTestHarness =
          [...new Set(filteredHostInfos.map((x) => x.testHarness))];
      expect(filteredTestHarness.length).toEqual(1);
      expect(filteredTestHarness[0]).toEqual(filterTestharness);
    });

    it('should not filter testHarness when testHarness equal to "All" option',
       () => {
         const filterTestharness = ALL_OPTIONS_VALUE;
         const filteredHostInfos =
             filterHostListDataSource(hostInfos, [], [], filterTestharness);

         // Make sure nothing change if testHarness is equal to "All" option.
         expect(hostInfos).toEqual(filteredHostInfos);
       });

    it('should filter hostGroups correctly', () => {
      const filterHostGroups = [hostGroups[0]];
      const filteredHostInfos =
          filterHostListDataSource(hostInfos, filterHostGroups);
      const filteredHostGroups =
          [...new Set(filteredHostInfos.map((x) => x.host_group).concat())];

      // Make sure only contains host group that is in filter criteria.
      expect(filteredHostGroups).toEqual(filterHostGroups);
    });

    it('should not filter hostInfos when hostGroup contains "All" option',
       () => {
         const filterHostGroups = [ALL_OPTIONS_VALUE];
         const filteredHostInfos =
             filterHostListDataSource(hostInfos, filterHostGroups);

         // Make sure nothing change if "All" option is contain in filter
         // criteria.
         expect(hostInfos).toEqual(filteredHostInfos);
       });

    it('should filter runTarget correctly', () => {
      const temRunTargets = runTargets.slice(0, 1);
      const filteredHostInfos =
          filterHostListDataSource(hostInfos, [], temRunTargets);
      const filteredRunTarget =
          [...new Set(filteredHostInfos.flatMap(x => x.device_count_summaries)
                          .map(x => x.run_target))];

      expect(filteredRunTarget).toEqual(temRunTargets);
    });

    it('should not filter hostInfos with runTarget equal to "All"', () => {
      const filterRunTarget = [ALL_OPTIONS_VALUE];
      const filteredHostInfos =
          filterHostListDataSource(hostInfos, [], filterRunTarget);

      expect(filteredHostInfos).toEqual(hostInfos);
    });
  });
});
