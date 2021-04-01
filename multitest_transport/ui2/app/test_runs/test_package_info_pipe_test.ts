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

import {TestPackageInfo} from '../services/mtt_models';
import {TestPackageInfoPipe} from './test_package_info_pipe';

describe('TestPackageInfoPipe', () => {
  let pipe: TestPackageInfoPipe;
  let testPackageInfo: TestPackageInfo;

  beforeEach(() => {
    pipe = new TestPackageInfoPipe();
  });

  it('displays package info without a build number', () => {
    testPackageInfo = {name: 'CTS', version: '8.1_r11'};
    expect(pipe.transform(testPackageInfo)).toEqual('CTS 8.1_r11');
  });

  it('displays package info with a build number', () => {
    testPackageInfo = {name: 'CTS', version: '8.1_r11', build_number: '123456'};
    expect(pipe.transform(testPackageInfo)).toEqual('CTS 8.1_r11 (123456)');
  });

  it('handles missing data', () => {
    expect(pipe.transform({})).toEqual('');
  });
});
