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
import {of} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {TestResourceType} from '../services/mtt_models';
import {getEl, getEls, getTextContent} from '../testing/jasmine_util';
import {newMockBuildItem, newMockTestResourceDef, newMockTestResourceDefs} from '../testing/mtt_mocks';

import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';
import {TestResourceClassType, TestResourceForm} from './test_resource_form';

describe('TestResourceForm', () => {
  const BUILD_ITEM = newMockBuildItem();

  let mttClient: jasmine.SpyObj<MttClient>;

  let testResourceForm: TestResourceForm;
  let testResourceFormFixture: ComponentFixture<TestResourceForm>;
  let el: DebugElement;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj<MttClient>(['lookupBuildItem']);
    mttClient.lookupBuildItem.and.returnValue(of(BUILD_ITEM));
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, BuildChannelsModule],
      aotSummaries: BuildChannelsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
      ],
    });
    testResourceFormFixture = TestBed.createComponent(TestResourceForm);
    el = testResourceFormFixture.debugElement;
    testResourceForm = testResourceFormFixture.componentInstance;
    testResourceForm.data = newMockTestResourceDefs();
    testResourceForm.buildChannels = [];
    testResourceForm.testResourceClassType =
        TestResourceClassType.TEST_RESOURCE_DEF;
    testResourceFormFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(testResourceForm).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Name');
    expect(textContent).toContain('Download Url');
    expect(textContent).toContain('Test Resource Type');
  });

  it('called correct function on press add button', () => {
    const onAddTestResource = jasmine.createSpy('onAddTestResource');
    testResourceForm.addTestResource.subscribe(onAddTestResource);
    getEl(el, '.add-button').click();
    expect(onAddTestResource).toHaveBeenCalled();
  });

  it('called correct function on press delete button', () => {
    const onRemoveTestResource = jasmine.createSpy('onRemoveTestResource');
    testResourceForm.removeTestResource.subscribe(onRemoveTestResource);
    getEl(el, '.shared-delete-button').click();
    expect(onRemoveTestResource).toHaveBeenCalled();
    expect(onRemoveTestResource).toHaveBeenCalledWith(0);
  });

  it('behave correctly with different input length', () => {
    let deleteButtons = getEls(el, '.shared-delete-button');
    expect(deleteButtons.length).toBe(2);
    const data = [
      newMockTestResourceDef('name1', 'url1', TestResourceType.DEVICE_IMAGE),
      newMockTestResourceDef('name2', 'url2', TestResourceType.DEVICE_IMAGE),
      newMockTestResourceDef('name3', 'url3', TestResourceType.DEVICE_IMAGE)
    ];
    testResourceForm.data = data;
    testResourceFormFixture.detectChanges();
    deleteButtons = getEls(el, '.shared-delete-button');
    expect(deleteButtons.length).toBe(3);
  });

  describe('add button', () => {
    it('should display correct aria-label', () => {
      const addButton = getEl(el, '.add-button');
      expect(addButton).toBeTruthy();
      expect(addButton.getAttribute('aria-label')).toBe('Add test resource');
    });
  });

  describe('delete button', () => {
    it('should display correct aria-label and tooltip', () => {
      const deleteButton = getEl(el, '.shared-delete-button');
      expect(deleteButton).toBeTruthy();
      expect(deleteButton.getAttribute('aria-label')).toBe('Delete');
      expect(deleteButton.getAttribute('mattooltip')).toBe('Delete');
    });
  });
});
