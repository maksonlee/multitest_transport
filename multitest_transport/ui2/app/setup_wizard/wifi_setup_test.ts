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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getTextContent} from '../testing/jasmine_util';
import {newMockNameValuePair} from '../testing/mtt_mocks';

import {SetupWizardModule} from './setup_wizard_module';
import {WifiSetup} from './wifi_setup';


describe('WiFi Setup', () => {
  const WIFI_PSK = 'password';

  let wifiSetup: WifiSetup;
  let wifiSetupFixture: ComponentFixture<WifiSetup>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['getNodeConfig']);
    mttClient.getNodeConfig.and.returnValue(
        observableOf({env_vars: [newMockNameValuePair('WIFI_PSK', WIFI_PSK)]}));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SetupWizardModule],
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });

    wifiSetupFixture = TestBed.createComponent(WifiSetup);
    el = wifiSetupFixture.debugElement;
    wifiSetupFixture.detectChanges();
    wifiSetup = wifiSetupFixture.componentInstance;
  });

  it('initializes a component', () => {
    expect(wifiSetup).toBeTruthy();
    expect(getTextContent(el)).toContain('WiFi information');
  });

  it('loads existing env vars', () => {
    wifiSetup.load();
    expect(wifiSetup.envVarMap['WIFI_SSID']).toEqual('');
    expect(wifiSetup.envVarMap['WIFI_PSK']).toEqual(WIFI_PSK);
  });

  it('converts arrays to dicts', () => {
    expect(wifiSetup.arrayToDict([])).toEqual({});
    expect(wifiSetup.arrayToDict([newMockNameValuePair('a', 'x')])).toEqual({
      'a': 'x',
    });

    // Pair with no value
    expect(wifiSetup.arrayToDict([newMockNameValuePair('a')])).toEqual({
      'a': '',
    });

    // Two pairs with same name
    expect(wifiSetup.arrayToDict([
      newMockNameValuePair('a', 'x'),
      newMockNameValuePair('a', 'z'),
      newMockNameValuePair('b', 'y'),
    ])).toEqual({
      'a': 'z',
      'b': 'y',
    });
  });

  it('converts dicts to arrays', () => {
    expect(wifiSetup.dictToArray({})).toEqual([]);
    expect(wifiSetup.dictToArray({'a': 'x'})).toEqual([newMockNameValuePair(
        'a', 'x')]);
    expect(wifiSetup.dictToArray({'a': '', 'b': 'y'})).toEqual([
      newMockNameValuePair('a', ''), newMockNameValuePair('b', 'y')
    ]);
  });
});
