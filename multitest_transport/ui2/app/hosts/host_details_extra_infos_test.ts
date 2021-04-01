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

import {DebugElement, SimpleChange} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';

import {getTextContent} from '../testing/jasmine_util';

import {HostDetailsExtraInfos} from './host_details_extra_infos';
import {HostsModule} from './hosts_module';
import {HostsModuleNgSummary} from './hosts_module.ngsummary';

describe('HostDetailsExtraInfos', () => {
  let hostDetailsExtraInfos: HostDetailsExtraInfos;
  let hostDetailsExtraInfosFixture: ComponentFixture<HostDetailsExtraInfos>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HostsModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      aotSummaries: HostsModuleNgSummary,
      providers: [],
    });

    hostDetailsExtraInfosFixture =
        TestBed.createComponent(HostDetailsExtraInfos);
    hostDetailsExtraInfos = hostDetailsExtraInfosFixture.componentInstance;
    hostDetailsExtraInfos.extraInfos = [];
    hostDetailsExtraInfosFixture.detectChanges();
    el = hostDetailsExtraInfosFixture.debugElement;
  });

  afterEach(() => {
    hostDetailsExtraInfosFixture.destroy();
  });

  it('should get initialized correctly', () => {
    expect(hostDetailsExtraInfos).toBeTruthy();
  });

  it('correctly displays a given empty list', () => {
    hostDetailsExtraInfos.extraInfos = [];
    hostDetailsExtraInfosFixture.detectChanges();
    expect(getTextContent(el)).toContain('No host extra infos found.');
  });

  it('correctly displays a given extra infos', () => {
    const ip = '127.0.0.1';
    hostDetailsExtraInfos.extraInfos = [ip];
    hostDetailsExtraInfosFixture.detectChanges();
    expect(getTextContent(el)).toContain(ip);
  });

  it('set new values correctly when params changed', () => {
    const hostIp = '127.0.0.1';
    const wifi = 'abc-123';
    hostDetailsExtraInfos.extraInfos = [hostIp];
    hostDetailsExtraInfosFixture.detectChanges();
    expect(getTextContent(el)).toContain(hostIp);

    hostDetailsExtraInfos.ngOnChanges(
        {extraInfos: new SimpleChange(null, [hostIp, wifi], false)});
    hostDetailsExtraInfosFixture.detectChanges();
    expect(hostDetailsExtraInfos.extraInfos).toEqual([hostIp, wifi]);
  });
});
