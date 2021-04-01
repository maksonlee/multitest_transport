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

import {filterHostInfoCount, LabHostInfo} from '../services/mtt_lab_models';

/** Default value for select all options. */
export const ALL_OPTIONS_VALUE = 'All';

/**
 * Filters offline hosts by host group and run target and resets the data
 * source of host list.
 * The offline hosts received from the backend need be filtered further in
 * frontend when the host group or run target filters are selected.
 */
export function filterHostListDataSource(
    hostInfos: LabHostInfo[], hostGroups?: string[], runTargets?: string[],
    testHarness?: string, isOfflineDeviceOnly = true): LabHostInfo[] {
  if (testHarness) {
    hostInfos = filterTestHarness(hostInfos, testHarness);
  }
  if (hostGroups && hostGroups.length) {
    hostInfos = filterHostGroup(hostInfos, hostGroups);
  }
  if (runTargets && runTargets.length) {
    hostInfos = filterRunTarget(hostInfos, runTargets, isOfflineDeviceOnly);
  }
  return hostInfos;
}

/**
 * Filters hostInfos by test harness.
 * @param testHarness: If equal to ALL_OPTIONS_VALUE, escape the filter
 *     condition.
 */
export function filterTestHarness(
    hostInfos: LabHostInfo[], testHarness: string): LabHostInfo[] {
  if (testHarness === ALL_OPTIONS_VALUE) {
    return hostInfos;
  }
  return hostInfos.filter(
      (host: LabHostInfo) => host.testHarness === testHarness);
}

/**
 * Filters hostInfos by host groups.
 * @param hostGroups: If ALL_OPTIONS_VALUE is included, escape the filter
 *     condition.
 */
export function filterHostGroup(
    hostInfos: LabHostInfo[], hostGroups: string[]): LabHostInfo[] {
  if (hostGroups.includes(ALL_OPTIONS_VALUE)) {
    return hostInfos;
  }
  return hostInfos.filter(
      (host) => host.host_group ? hostGroups.includes(host.host_group) : false);
}

/**
 * Filters hostInfos by run targets.
 * @param runTargets: If ALL_OPTIONS_VALUE is included, escape the filter
 *     condition.
 * @param isOfflineOnly: If true, return the hosts that have offline devices.
 *     Otherwise, return the hosts that have devices no matter online or
 *     offline.
 */
export function filterRunTarget(
    hostInfos: LabHostInfo[], runTargets: string[],
    isOfflineOnly = true): LabHostInfo[] {
  if (runTargets.includes(ALL_OPTIONS_VALUE)) {
    return hostInfos;
  }
  const newHosts: LabHostInfo[] = [];
  const tmpData = hostInfos.filter((host: LabHostInfo) => {
    if (!host.device_count_summaries) {
      return false;
    }
    const summaries =
        host.device_count_summaries.filter(runTargetDeviceSummaries => {
          return runTargets.includes(runTargetDeviceSummaries.run_target);
        });

    if (summaries.length === 0) {
      return false;
    }

    let isMatched = false;

    for (const summary of summaries) {
      const deviceCount =
          isOfflineOnly ? Number(summary.offline) : Number(summary.total);
      if (!Number.isNaN(deviceCount)) {
        isMatched = deviceCount > 0;
      } else {
        isMatched = true;
      }
      if (isMatched) break;
    }

    return isMatched;
  });

  for (const host of tmpData) {
    const selectedRunTargets = host.device_count_summaries.filter((x) => {
      return runTargets.includes(x.run_target);
    });
    newHosts.push(filterHostInfoCount(host, selectedRunTargets));
  }
  return newHosts;
}
