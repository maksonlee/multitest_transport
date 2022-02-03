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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {ConfigSetClient, MttClient} from '../services/mtt_client';
import * as mttModels from '../services/mtt_models';
import {MttObjectMap, MttObjectMapService, newMttObjectMap} from '../services/mtt_object_map';
import {Notifier} from '../services/notifier';
import {getEl, getTextContent} from '../testing/jasmine_util';
import * as mttMocks from '../testing/mtt_mocks';

import {TestList} from './test_list';
import {TestModule} from './test_module';

describe('TestList', () => {
  const TEST_MAP = {
    id1: {id: 'id1', name: 'name1'},
    id2: {id: 'id2', name: 'name2'},
  };

  let testList: TestList;
  let testListFixture: ComponentFixture<TestList>;
  let configSetClient: jasmine.SpyObj<ConfigSetClient>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let mttObjectMapService: jasmine.SpyObj<MttObjectMapService>;
  let mttObjectMap: MttObjectMap;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let notifier: jasmine.SpyObj<Notifier>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    notifier = jasmine.createSpyObj(['confirm', 'showError']);

    configSetClient =
        jasmine.createSpyObj('configSetClient', ['getLatestVersion']);
    configSetClient.getLatestVersion.and.returnValue(observableOf());

    mttClient = {
      ...jasmine.createSpyObj('mttClient', ['deleteTest', 'deleteConfigSet']),
      configSets: configSetClient,
    };
    mttClient.deleteTest.and.returnValue(observableOf(null));
    mttClient.deleteConfigSet.and.returnValue(observableOf(null));

    mttObjectMapService =
        jasmine.createSpyObj('mttObjectMapService', ['getMttObjectMap']);
    mttObjectMap = newMttObjectMap();
    mttObjectMap.testMap = TEST_MAP;
    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(mttObjectMap));

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        TestModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: MttObjectMapService, useValue: mttObjectMapService},
        {provide: Notifier, useValue: notifier},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
    testListFixture = TestBed.createComponent(TestList);
    testListFixture.detectChanges();
    el = testListFixture.debugElement;
    testList = testListFixture.componentInstance;
  });

  afterEach(() => {
    testListFixture.destroy();
  });

  function reload(mttObjectMap: MttObjectMap) {
    mttObjectMapService.getMttObjectMap.and.returnValue(
        observableOf(mttObjectMap));
    testList.load();
    testListFixture.detectChanges();
  }

  it('gets initialized correctly', () => {
    expect(testList).toBeTruthy();

    const header = getEl(el, 'h1');
    expect(header).toBeTruthy();
    expect(header.innerText).toBe('Test Suites');

    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    const matTable = getEl(el, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Test suites');
  });

  it('displays tests correctly', () => {
    expect(mttObjectMapService.getMttObjectMap).toHaveBeenCalled();
    const textContent = getTextContent(el);
    for (const test of Object.values(TEST_MAP)) {
      expect(textContent).toContain(test.name);
    }
  });

  it('can display namespaced tests',
     () => {
       const NAMESPACED_TEST_MAP = {
         id1: {id: 'ns1::id1', name: 'Valid namespace'},
         id2: {id: 'id2', name: 'No namespace'},
         id3: {id: 'ns2::id3', name: 'Unmatched namepsace'},
       };
       const configSet1 = mttMocks.newMockConfigSetInfo('ns1', 'Namespace 1');
       configSet1.status = mttModels.ConfigSetStatus.UPDATABLE;
       const CONFIG_SET_MAP = {ns1: configSet1};

       mttObjectMap = newMttObjectMap();
       mttObjectMap.testMap = NAMESPACED_TEST_MAP;
       mttObjectMap.configSetInfoMap = CONFIG_SET_MAP;
       reload(mttObjectMap);

       const textContent = getTextContent(el);
       for (const test of Object.values(NAMESPACED_TEST_MAP)) {
         expect(textContent).toContain(test.name);
       }
       expect(textContent).toContain('Default/Custom Test Suites');
       expect(textContent).toContain('Namespace 1');
       expect(textContent).toContain('Unknown Config Set (ns2)');
       expect(textContent).toContain('Updatable');
     });

  it('deletes a test correctly', () => {
    // Delete the first test.
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    getEl(el, '#menuButton').click();
    getEl(el, '#deleteButton').click();
    expect(mttClient.deleteTest).toHaveBeenCalledWith('id1');
  });

  it('can delete config sets', () => {
    const NAMESPACED_TEST_MAP = {
      id1: {id: 'ns1::id1', name: 'Valid namespace'},
      id2: {id: 'id2', name: 'No namespace'},
    };
    const CONFIG_SET_MAP = {
      ns1: mttMocks.newMockConfigSetInfo('ns1', 'Namespace 1'),
    };

    mttObjectMap = newMttObjectMap();
    mttObjectMap.testMap = NAMESPACED_TEST_MAP;
    mttObjectMap.configSetInfoMap = CONFIG_SET_MAP;
    reload(mttObjectMap);
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete

    getEl(el, '#configSetMenuButton').click();
    getEl(el, '#configSetDeleteButton').click();
    expect(mttClient.deleteConfigSet).toHaveBeenCalledWith('ns1');
  });
});
