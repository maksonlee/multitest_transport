/**
 * Copyright 2021 Google LLC
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
import {of as observableOf, throwError} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {FileCleanerOperationType, FileCleanerSettings, FileCleanerTargetType} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {getEl, getEls, hasEl} from '../testing/jasmine_util';
import {newMockFileCleanerConfig, newMockFileCleanerCriterion, newMockFileCleanerOperation, newMockFileCleanerPolicy} from '../testing/mtt_mocks';

import {FileCleanerModule} from './file_cleaner_module';
import {FileCleanerSettingList} from './file_cleaner_setting_list';

describe('FileCleanerSettingList', () => {
  const EMPTY_SETTINGS = {policies: [], configs: []};

  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let notifier: jasmine.SpyObj<Notifier>;
  let client: jasmine.SpyObj<MttClient>;

  let fixture: ComponentFixture<FileCleanerSettingList>;
  let element: DebugElement;
  let component: FileCleanerSettingList;

  beforeEach(() => {
    liveAnnouncer = jasmine.createSpyObj(['announce', 'clear']);
    notifier = jasmine.createSpyObj(['confirm', 'showError', 'showMessage']);
    client = jasmine.createSpyObj([
      'getFileCleanerSettings',
      'updateFileCleanerSettings',
      'resetFileCleanerSettings',
    ]);
    client.getFileCleanerSettings.and.returnValue(observableOf(EMPTY_SETTINGS));
    client.updateFileCleanerSettings.and.returnValue(
        observableOf(EMPTY_SETTINGS));
    client.resetFileCleanerSettings.and.returnValue(observableOf(null));

    TestBed.configureTestingModule({
      imports: [FileCleanerModule, NoopAnimationsModule, RouterTestingModule],
      providers: [
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: MttClient, useValue: client},
        {provide: Notifier, useValue: notifier},
      ]
    });

    fixture = TestBed.createComponent(FileCleanerSettingList);
    fixture.detectChanges();
    element = fixture.debugElement;
    component = fixture.componentInstance;
  });

  /** Convenience method to reload new file cleaner settings. */
  function reload(settings: FileCleanerSettings) {
    client.getFileCleanerSettings.and.returnValue(observableOf(settings));
    component.load();
    fixture.detectChanges();
  }

  it('can initialize the component', () => {
    expect(component).toBeTruthy();
  });

  it('can call API correctly', () => {
    expect(client.getFileCleanerSettings).toHaveBeenCalled();
  });

  it('can announce loading start and end', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    expect(liveAnnouncer.announce)
        .toHaveBeenCalledWith('File cleaner settings loaded', 'assertive');
  });

  it('can display empty settings', () => {
    expect(hasEl(element, 'mat-card')).toBeFalsy();
    expect(hasEl(element, '.policy-list-empty')).toBeTruthy();
    expect(hasEl(element, '.config-list-empty')).toBeTruthy();
  });

  it('can display policy list', () => {
    reload({
      policies: [
        newMockFileCleanerPolicy('Policy #1'),
        newMockFileCleanerPolicy(
            'Policy #2', FileCleanerTargetType.DIRECTORY,
            newMockFileCleanerOperation(FileCleanerOperationType.DELETE),
            [newMockFileCleanerCriterion()])
      ],
      configs: [],
    });

    expect(hasEl(element, '.policy-list-empty')).toBeFalsy();
    expect(hasEl(element, '.config-list-empty')).toBeTruthy();
    const cards = getEls(element, 'mat-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('Policy #1');
    expect(cards[0].textContent).toContain('Archive file');
    expect(cards[1].textContent).toContain('Policy #2');
    expect(cards[1].textContent)
        .toContain('Delete directory  based on  last_access_time');
  });

  it('can display config list', () => {
    reload({
      policies: [],
      configs: [
        newMockFileCleanerConfig('Config #1'),
        newMockFileCleanerConfig('Config #2', 'description')
      ],
    });

    expect(hasEl(element, '.policy-list-empty')).toBeTruthy();
    expect(hasEl(element, '.config-list-empty')).toBeFalsy();
    const cards = getEls(element, 'mat-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('Config #1');
    expect(cards[1].textContent).toContain('Config #2');
    expect(cards[1].textContent).toContain('description');
  });

  it('can handle errors when loading settings', () => {
    client.getFileCleanerSettings.and.returnValue(throwError('loading failed'));
    component.load();
    expect(notifier.showError).toHaveBeenCalled();
  });

  it('can delete a policy', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    reload({
      policies: [newMockFileCleanerPolicy('Policy')],
      configs: [newMockFileCleanerConfig('Config', '', [], ['Policy'])],
    });

    getEls(element, 'mat-card .delete-button')[0].click();
    fixture.detectChanges();

    expect(getEls(element, 'mat-card').length).toBe(1);  // 1 card removed
    expect(client.updateFileCleanerSettings).toHaveBeenCalledWith({
      policies: [],
      configs: [newMockFileCleanerConfig('Config', '', [], [])],
    });
    expect(notifier.showMessage)
        .toHaveBeenCalledWith(`File cleaner policy 'Policy' deleted.`);
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can cancel deleting a policy', () => {
    notifier.confirm.and.returnValue(observableOf(false));  // cancel delete
    reload({policies: [newMockFileCleanerPolicy('Policy')], configs: []});

    getEl(element, 'mat-card .delete-button').click();
    fixture.detectChanges();

    expect(hasEl(element, 'mat-card')).toBeTruthy();
    expect(client.updateFileCleanerSettings).not.toHaveBeenCalled();
  });

  it('can handle errors when deleting a policy', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    reload({policies: [newMockFileCleanerPolicy('Policy')], configs: []});
    client.updateFileCleanerSettings.and.returnValue(
        throwError('delete failed'));

    getEl(element, 'mat-card .delete-button').click();
    fixture.detectChanges();

    expect(hasEl(element, 'mat-card')).toBeTruthy();  // reload settings
    expect(client.updateFileCleanerSettings)
        .toHaveBeenCalledWith(EMPTY_SETTINGS);
    expect(notifier.showError).toHaveBeenCalled();
  });

  it('can delete a config', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    reload({policies: [], configs: [newMockFileCleanerConfig('Config')]});

    getEl(element, 'mat-card .delete-button').click();
    fixture.detectChanges();

    expect(getEls(element, 'mat-card').length).toBeFalsy();  // card removed
    expect(client.updateFileCleanerSettings)
        .toHaveBeenCalledWith(EMPTY_SETTINGS);
    expect(notifier.showMessage)
        .toHaveBeenCalledWith(`File cleaner config 'Config' deleted.`);
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can cancel deleting a config', () => {
    notifier.confirm.and.returnValue(observableOf(false));  // cancel delete
    reload({policies: [], configs: [newMockFileCleanerConfig('Config')]});

    getEl(element, 'mat-card .delete-button').click();
    fixture.detectChanges();

    expect(hasEl(element, 'mat-card')).toBeTruthy();
    expect(client.updateFileCleanerSettings).not.toHaveBeenCalled();
  });

  it('can handle errors when deleting a config', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm delete
    reload({policies: [], configs: [newMockFileCleanerConfig('Config')]});
    client.updateFileCleanerSettings.and.returnValue(
        throwError('delete failed'));

    getEl(element, 'mat-card .delete-button').click();
    fixture.detectChanges();

    expect(hasEl(element, 'mat-card')).toBeTruthy();  // reload settings
    expect(client.updateFileCleanerSettings)
        .toHaveBeenCalledWith(EMPTY_SETTINGS);
    expect(notifier.showError).toHaveBeenCalled();
  });

  it('can reset settings', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm reset
    getEl(element, '.reset-button').click();
    fixture.detectChanges();

    expect(client.resetFileCleanerSettings).toHaveBeenCalled();
    expect(notifier.showMessage)
        .toHaveBeenCalledWith('File Cleaner settings reset.');
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can cancel resetting settings', () => {
    notifier.confirm.and.returnValue(observableOf(false));  // cancel reset
    getEl(element, '.reset-button').click();
    fixture.detectChanges();

    expect(client.resetFileCleanerSettings).not.toHaveBeenCalled();
    expect(notifier.showMessage).not.toHaveBeenCalled();
    expect(notifier.showError).not.toHaveBeenCalled();
  });

  it('can handle errors when resetting settings', () => {
    notifier.confirm.and.returnValue(observableOf(true));  // confirm reset
    client.resetFileCleanerSettings.and.returnValue(throwError('reset failed'));
    getEl(element, '.reset-button').click();
    fixture.detectChanges();

    expect(notifier.showMessage).not.toHaveBeenCalled();
    expect(notifier.showError)
        .toHaveBeenCalledWith(
            'Failed to reset File Cleaner settings', jasmine.any(Object));
  });
});
