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

import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {TfcClient} from '../services/tfc_client';

import {TestRunTargetPicker} from './test_run_target_picker';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunTargetPicker', () => {
  let testRunTargetPicker: TestRunTargetPicker;
  let testRunTargetPickerFixture: ComponentFixture<TestRunTargetPicker>;
  let tfcClient: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    tfcClient = jasmine.createSpyObj('tfcClient', ['getDeviceInfos']);
    tfcClient.getDeviceInfos.and.returnValue(observableOf({device_infos: []}));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, TestRunsModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: TfcClient, useValue: tfcClient},
      ],
    });
    testRunTargetPickerFixture = TestBed.createComponent(TestRunTargetPicker);
    testRunTargetPickerFixture.detectChanges();
    testRunTargetPicker = testRunTargetPickerFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(testRunTargetPicker).toBeTruthy();
  });

  it('updates the data correctly', () => {
    testRunTargetPicker.onDeviceListSelectionChange([]);
    expect(testRunTargetPicker.shardCount).toBe(0);

    testRunTargetPicker.onDeviceListSelectionChange(['p1']);
    expect(testRunTargetPicker.shardCount).toBe(1);
    expect(testRunTargetPicker.runTarget).toBe('p1');

    testRunTargetPicker.onDeviceListSelectionChange(['p1', 'p2']);
    expect(testRunTargetPicker.runTarget).toBe('p1;p2');
  });
});
