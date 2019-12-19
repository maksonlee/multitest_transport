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
import {RouterTestingModule} from '@angular/router/testing';

import {Mtt, MttModule} from './app';
import {MttModuleNgSummary} from './app.ngsummary';
import {APP_DATA} from './services/app_data';
import {getEl} from './testing/jasmine_util';

describe('Mtt', () => {
  let mtt: Mtt;
  let mttFixture: ComponentFixture<Mtt>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MttModule, RouterTestingModule],
      aotSummaries: MttModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: {}},
      ],
    });

    mttFixture = TestBed.createComponent(Mtt);
    el = mttFixture.debugElement;
    mttFixture.detectChanges();
    mtt = mttFixture.componentInstance;
  });

  it('should gets initialized correctly', () => {
    expect(mtt).toBeTruthy();
  });

  it('should reverse sideNavExpanded on toggleSidenavButton click', () => {
    const sideNavExpanded = mtt.sideNavExpanded;
    getEl(el, '#toggleSidenavButton').click();
    expect(mtt.sideNavExpanded).not.toEqual(sideNavExpanded);
  });
});
