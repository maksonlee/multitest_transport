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
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {APP_DATA} from '../services';
import {TfcClient} from '../services/tfc_client';
import {newMockAppData} from '../testing/mtt_lab_mocks';

import {TestRunTargetPicker} from './test_run_target_picker';
import {TestRunsModule} from './test_runs_module';
import {TestRunsModuleNgSummary} from './test_runs_module.ngsummary';

describe('TestRunTargetPicker', () => {
  let testRunTargetPicker: TestRunTargetPicker;
  let testRunTargetPickerFixture: ComponentFixture<TestRunTargetPicker>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  const appData = newMockAppData();

  beforeEach(() => {
    tfcClient = jasmine.createSpyObj(
        'tfcClient', ['getDeviceInfos', 'getFilterHintList']);
    tfcClient.getDeviceInfos.and.returnValue(observableOf({device_infos: []}));
    tfcClient.getFilterHintList.and.returnValue(observableOf([]));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, RouterTestingModule, TestRunsModule],
      aotSummaries: TestRunsModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: appData},
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
    expect(testRunTargetPicker.deviceSpecs).toEqual(['device_serial:p1']);

    testRunTargetPicker.onDeviceListSelectionChange(['p1', 'p2']);
    expect(testRunTargetPicker.deviceSpecs).toEqual([
      'device_serial:p1', 'device_serial:p2'
    ]);
  });

  it('can get the device serials', () => {
    testRunTargetPicker.deviceSpecs =
        ['device_serial:host.name.domain:some-device-serial'];
    const serials = testRunTargetPicker.getDeviceSerials();
    expect(serials[0]).toEqual('host.name.domain:some-device-serial');
  });

  it('can handle invalid serials', () => {
    testRunTargetPicker.deviceSpecs =
        ['device_serial:host.name.domain:long-serial-with whitespace '];
    const serials = testRunTargetPicker.getDeviceSerials();
    expect(serials).toEqual([]);
  });

  it('can autocomplete device spec keys', () => {
    let result = testRunTargetPicker.getDeviceSpecsAutocompleteOptions('');
    expect(result.length).toEqual(6);

    result =
        testRunTargetPicker.getDeviceSpecsAutocompleteOptions('Devic').sort(
            (first, second) => first.value.localeCompare(second.value));
    expect(result).toEqual([
      {value: 'device_serial:', displayedValue: 'device_serial'},
      {value: 'device_type:', displayedValue: 'device_type'},
    ]);

    result =
        testRunTargetPicker
            .getDeviceSpecsAutocompleteOptions('product:a;product')
            .sort((first, second) => first.value.localeCompare(second.value));
    expect(result).toEqual([
      {value: 'product:a;product_variant:', displayedValue: 'product_variant'},
      {value: 'product:a;product:', displayedValue: 'product'},
    ]);
  });

  it('can autocomplete device spec values', () => {
    let result = testRunTargetPicker.getDeviceSpecsAutocompleteOptions(':');
    expect(result).toEqual([]);

    result = testRunTargetPicker.getDeviceSpecsAutocompleteOptions('notfound:');
    expect(result).toEqual([]);

    result =
        testRunTargetPicker.getDeviceSpecsAutocompleteOptions('device_type:');
    expect(result).toEqual([
      {value: 'device_type:PHYSICAL', displayedValue: 'PHYSICAL'},
      {value: 'device_type:LOCAL_VIRTUAL', displayedValue: 'LOCAL_VIRTUAL'},
    ]);

    result = testRunTargetPicker.getDeviceSpecsAutocompleteOptions(
        'product:a;sim_state:a');
    expect(result).toEqual([
      {value: 'product:a;sim_state:ABSENT', displayedValue: 'ABSENT'},
      {value: 'product:a;sim_state:READY', displayedValue: 'READY'},
    ]);

    result = testRunTargetPicker.getDeviceSpecsAutocompleteOptions(
        'device_serial:sim_state:a');
    expect(result).toEqual([]);
  });
});
