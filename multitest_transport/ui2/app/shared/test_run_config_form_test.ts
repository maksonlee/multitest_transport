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
import {Subject, throwError} from 'rxjs';

import {FileService, FileUploadEvent} from '../services/file_service';
import {Test, TestRunConfig} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {newMockTest, newMockTestRunConfig} from '../testing/mtt_mocks';

import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';
import {TestRunConfigForm} from './test_run_config_form';

describe('TestRunConfigForm', () => {
  let fs: jasmine.SpyObj<FileService>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;
  let notifier: jasmine.SpyObj<Notifier>;
  let fixture: ComponentFixture<TestRunConfigForm>;
  let debugEl: DebugElement;
  let configForm: TestRunConfigForm;

  let test1: Test;
  let test2: Test;
  let testRunConfig: TestRunConfig;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    fs = jasmine.createSpyObj(['getFileUrl', 'uploadFile']);
    notifier = jasmine.createSpyObj(['showError']);
    test1 = newMockTest('test1');
    test2 = newMockTest('test2', 'name2', 'second command');
    test2.default_test_run_parameters = {
      max_retry_on_test_failures: 2,
      output_idle_timeout_seconds: 2000
    };
    testRunConfig = newMockTestRunConfig(test1.id!, 'modified command');

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      providers: [
        {provide: FileService, useValue: fs},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
        {provide: Notifier, useValue: notifier},
      ],
      aotSummaries: SharedModuleNgSummary,
    });

    fixture = TestBed.createComponent(TestRunConfigForm);
    debugEl = fixture.debugElement;
    configForm = fixture.componentInstance;
    configForm.testMap = {[test1.id!]: test1, [test2.id!]: test2};
    configForm.testId = test1.id!;
    configForm.testRunConfig = testRunConfig;
    spyOn(configForm.rerunContext, 'emit');
    fixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(configForm).toBeTruthy();
  });

  it('can load a previous test run', () => {
    expect(configForm.testRunConfig.command).toEqual('modified command');
    expect(configForm.testRunConfig.max_retry_on_test_failures).toEqual(1);
    expect(configForm.testRunConfig.output_idle_timeout_seconds).toEqual(3600);
  });

  it('can load test defaults when changing tests', () => {
    configForm.loadTest(test2.id!);
    expect(configForm.testRunConfig.command).toEqual(test2.command);
    expect(configForm.testRunConfig.max_retry_on_test_failures).toEqual(2);
    expect(configForm.testRunConfig.output_idle_timeout_seconds).toEqual(2000);
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
      context_filename: undefined,
      context_file_url: undefined,
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
       const upload = new Subject<Partial<FileUploadEvent>>();
       fs.getFileUrl.and.returnValue('file_url');
       fs.uploadFile.and.returnValue(upload);

       // can start upload
       configForm.uploadResultsFile(file);
       tick();
       expect(configForm.isUploading).toBeTruthy();
       expect(configForm.uploadProgress).toEqual(0);

       // can track progress
       upload.next({done: false, progress: 50});
       tick();
       expect(configForm.isUploading).toBeTruthy();
       expect(configForm.uploadProgress).toEqual(50);

       // can complete upload
       upload.next({done: true, progress: 100});
       upload.complete();
       tick();
       expect(configForm.isUploading).toBeFalsy();
       expect(configForm.isRerun).toBeTruthy();
       expect(configForm.rerunContext.emit).toHaveBeenCalledWith({
         context_filename: 'filename',
         context_file_url: 'file_url',
       });
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Uploading filename', 'polite');
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('filename uploaded', 'assertive');
     }));

  it('should display error if results file upload fails', fakeAsync(() => {
    configForm.isRemoteRerun = true;
    const file = {name: 'filename', size: 100} as File;
    fs.uploadFile.and.returnValue(throwError('Upload error'));
    configForm.uploadResultsFile(file);
    tick();
    expect(notifier.showError).toHaveBeenCalled();
  }));
});
