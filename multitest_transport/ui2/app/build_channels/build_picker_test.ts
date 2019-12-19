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
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {getTextContent} from '../testing/jasmine_util';

import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';
import {BuildPicker} from './build_picker';

describe('BuildPicker', () => {
  let buildPicker: BuildPicker;
  let buildPickerFixture: ComponentFixture<BuildPicker>;
  let el: DebugElement;
  const dialogData = {
    searchBarUrlValue: 'a/b/c',
    searchBarFilenameValue: 'file.txt',
    buildChannelId: '',
    buildChannels: []
  };
  const dialogRefSpy =
      jasmine.createSpyObj('MatDialogRef', ['close', 'backdropClick']);
  let mttClient: jasmine.SpyObj<MttClient>;

  beforeEach(() => {
    mttClient = jasmine.createSpyObj('mttClient', ['listBuildItems']);
    mttClient.listBuildItems.and.returnValue(
        observableOf({build_items: [], next_page_token: ''}));
    dialogRefSpy.backdropClick.and.returnValue(observableOf({}));
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, BuildChannelsModule],
      aotSummaries: BuildChannelsModuleNgSummary,
      providers: [
        {provide: MatDialogRef, useValue: dialogRefSpy},
        {provide: MAT_DIALOG_DATA, useValue: dialogData},
        {provide: MttClient, useValue: mttClient},
      ],
    });
    buildPickerFixture = TestBed.createComponent(BuildPicker);
    el = buildPickerFixture.debugElement;
    buildPicker = buildPickerFixture.componentInstance;
    buildPickerFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(buildPicker).toBeTruthy();
  });

  it('shows HTML correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain('Select a file');
    expect(textContent).toContain('By Url');
  });
  // TODO: Add more tests as implementing other tabs
});
