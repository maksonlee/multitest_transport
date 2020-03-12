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
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of, Subject} from 'rxjs';

import {APP_DATA} from '../services/app_data';
import {FileUploadEvent, FileUploadService} from '../services/file_upload_service';
import {Test, TestRunConfig} from '../services/mtt_models';
import {newMockTest, newMockTestRunConfig} from '../testing/test_util';

import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';
import {TestRunConfigForm} from './test_run_config_form';

describe('TestRunConfigForm', () => {
  let uploadService: jasmine.SpyObj<FileUploadService>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let fixture: ComponentFixture<TestRunConfigForm>;
  let debugEl: DebugElement;
  let configForm: TestRunConfigForm;

  let test: Test;
  let testRunConfig: TestRunConfig;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    uploadService = jasmine.createSpyObj(
        'uploadService', ['startUploadProcess', 'uploadFile']);
    test = newMockTest();
    testRunConfig = newMockTestRunConfig(test.id!);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      providers: [
        {provide: APP_DATA, useValue: {}},
        {provide: FileUploadService, useValue: uploadService},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
      aotSummaries: SharedModuleNgSummary,
    });

    fixture = TestBed.createComponent(TestRunConfigForm);
    debugEl = fixture.debugElement;
    configForm = fixture.componentInstance;
    configForm.testMap = {[test.id!]: test};
    configForm.testId = test.id!;
    configForm.testRunConfig = testRunConfig;
    spyOn(configForm.rerunContext, 'emit');
    fixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(configForm).toBeTruthy();
  });

  it('can handle configs without commands', () => {
    const configWithoutCommand = newMockTestRunConfig(test.id!, '', '');
    configForm.testRunConfig = configWithoutCommand;
    configForm.load();
    expect(configForm.testRunConfig.command).toEqual(test.command!);
  });

  it('can disable reruns', () => {
    configForm.enableRerun = false;
    fixture.detectChanges();
    expect(debugEl.query(By.css('.rerun'))).toBeFalsy();

    (configForm.rerunContext.emit as jasmine.Spy).calls.reset();
    configForm.updateRerunContext();
    expect(configForm.rerunContext.emit).not.toHaveBeenCalled();
  });

  it('initially set to local rerun', () => {
    expect(debugEl.query(By.css('.rerun .local'))).toBeTruthy();
    expect(debugEl.query(By.css('.rerun .remote'))).toBeFalsy();
    expect(configForm.isRerun).toBeFalsy();
    expect(configForm.rerunContext.emit).toHaveBeenCalledWith({
      test_run_id: undefined
    });
  });

  it('can set previous run id', () => {
    const input = debugEl.query(By.css('.rerun .local input'));
    input.nativeElement.value = 'test_run_id';
    input.triggerEventHandler('input', {target: input.nativeElement});

    expect(configForm.isRerun).toBeTruthy();
    expect(configForm.rerunContext.emit).toHaveBeenCalledWith({
      test_run_id: 'test_run_id'
    });
  });

  it('can switch to remote rerun', () => {
    configForm.isRemoteRerun = true;
    const select = debugEl.query(By.css('.rerun .type mat-select'));
    select.triggerEventHandler('selectionChange', null);
    fixture.detectChanges();

    expect(debugEl.query(By.css('.rerun .local'))).toBeFalsy();
    expect(debugEl.query(By.css('.rerun .remote'))).toBeTruthy();
    expect(configForm.isRerun).toBeFalsy();
    expect(configForm.rerunContext.emit).toHaveBeenCalledWith({
      context_filename: undefined
    });
  });

  it('can select results file', () => {
    // switch to remote rerun
    configForm.isRemoteRerun = true;
    fixture.detectChanges();

    // select a file and check uploading starts
    spyOn(configForm, 'uploadResultsFile');
    const file = {name: 'filename', size: 100} as File;
    const input = debugEl.query(By.css('.rerun .remote input'));
    input.triggerEventHandler('change', {target: {files: [file]}});
    expect(configForm.uploadResultsFile).toHaveBeenCalledWith(file);
  });

  it('can upload results file', fakeAsync(() => {
       configForm.isRemoteRerun = true;
       const file = {name: 'filename', size: 100} as File;
       const upload = new Subject<FileUploadEvent>();
       uploadService.startUploadProcess.and.returnValue(of('url'));
       uploadService.uploadFile.and.returnValue(upload);

       // can start upload
       configForm.uploadResultsFile(file);
       tick();
       expect(configForm.isUploading).toBeTruthy();
       expect(configForm.uploadProgress).toEqual(0);

       // can track progress
       upload.next({type: 'progress', uploaded: 50});
       tick();
       expect(configForm.isUploading).toBeTruthy();
       expect(configForm.uploadProgress).toEqual(50);

       // can complete upload
       upload.next({type: 'complete', uploaded: 100});
       upload.complete();
       tick();
       expect(configForm.isUploading).toBeFalsy();
       expect(configForm.isRerun).toBeTruthy();
       expect(configForm.rerunContext.emit).toHaveBeenCalledWith({
         context_filename: 'filename'
       });
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Uploading', 'polite');
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Upload completed', 'assertive');
     }));
});
