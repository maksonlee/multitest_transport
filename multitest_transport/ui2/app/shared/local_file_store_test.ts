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
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf, ReplaySubject, Subject, throwError} from 'rxjs';

import {FileNode, FileService, FileType, FileUploadEvent} from '../services/file_service';
import {Notifier} from '../services/notifier';
import {getEl} from '../testing/jasmine_util';

import {LocalFileStore} from './local_file_store';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('LocalFileStore', () => {
  let fixture: ComponentFixture<LocalFileStore>;
  let element: DebugElement;
  let component: LocalFileStore;

  let fs: jasmine.SpyObj<FileService>;
  let notifier: jasmine.SpyObj<Notifier>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    fs = jasmine.createSpyObj([
      'getFileUrl', 'getRelativePathAndHostname', 'listFiles', 'uploadFile',
      'deleteFile'
    ]);
    fs.getRelativePathAndHostname.and.callFake(fileUrl => [fileUrl, '']);
    fs.listFiles.and.returnValue(observableOf([]));
    notifier = jasmine.createSpyObj('notifier', ['confirm', 'showError']);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
        {provide: Notifier, useValue: notifier},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
  });

  /** Helper method to initialize the LocalFileStore component. */
  function initComponent(url = '') {
    fixture = TestBed.createComponent(LocalFileStore);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    component.url = url;
    fixture.detectChanges();
  }

  it('should load local files contents when initialized', () => {
    initComponent();
    expect(component).toBeTruthy();
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store');
    expect(component.selectedFile).toBeUndefined();
    expect(component.currentDirectory).toEqual('local_file_store');
  });

  it('should select file when initialized with url', () => {
    const file = {type: FileType.FILE, path: 'local_file_store/filename'} as
        FileNode;
    fs.listFiles.and.returnValue(observableOf([file]));
    initComponent('local_file_store/filename');
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store');
    expect(component.selectedFile).toEqual(file);
    expect(component.currentDirectory).toEqual('local_file_store');
  });

  it('should load subdirectory when url contains subdirectory', () => {
    initComponent('local_file_store/dir/filename');
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store/dir');
    expect(component.currentDirectory).toEqual('local_file_store/dir');
  });

  it('should change directory when change directory button clicked', () => {
    const dir = {type: FileType.DIRECTORY, path: 'local_file_store/dir'} as
        FileNode;
    fs.listFiles.and.returnValue(observableOf([dir]));
    initComponent();
    expect(component.currentDirectory).toEqual('local_file_store');

    // clicking on change dir button will change directory and reload contents
    getEl(element, 'mat-row button.change-dir').click();
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store/dir');
    expect(component.currentDirectory).toEqual('local_file_store/dir');
  });

  it('should track upload progress when uploading file', fakeAsync(() => {
       initComponent();
       fs.listFiles.calls.reset();
       // use placeholder file and control upload process using subject
       const file = {name: 'filename', size: 100} as File;
       const upload = new Subject<Partial<FileUploadEvent>>();
       fs.uploadFile.and.returnValue(upload);

       // can start upload
       component.uploadFile(file);
       expect(fs.uploadFile)
           .toHaveBeenCalledWith(file, 'local_file_store/filename');
       tick();
       expect(component.isUploading).toBeTruthy();
       expect(component.uploadProgress).toEqual(0);
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Uploading filename', 'polite');

       // can track progress
       upload.next({done: false, progress: 50});
       tick();
       expect(component.isUploading).toBeTruthy();
       expect(component.uploadProgress).toEqual(50);
       expect(fs.listFiles).not.toHaveBeenCalled();

       // can complete upload
       upload.next({done: true, progress: 100});
       upload.complete();
       tick();
       expect(component.isUploading).toBeFalsy();
       expect(fs.listFiles).toHaveBeenCalledWith('local_file_store');
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('filename uploaded', 'assertive');
     }));

  it('should display error if upload fails', fakeAsync(() => {
       initComponent();
       const file = {name: 'filename', size: 100} as File;
       fs.uploadFile.and.returnValue(throwError('Upload error'));
       component.uploadFile(file);
       tick();
       expect(notifier.showError).toHaveBeenCalled();
     }));

  it('should upload file to current directory', () => {
    initComponent();
    component.changeDirectory('local_file_store/dir');
    fs.listFiles.calls.reset();

    // use placeholder file and complete upload immediately
    const file = {name: 'filename', size: 100} as File;
    const upload = new ReplaySubject<Partial<FileUploadEvent>>();
    upload.next({done: true, progress: 100});
    upload.complete();
    fs.uploadFile.and.returnValue(upload);

    // file uploaded to current directory and its contents are reloaded
    component.uploadFile(file);
    expect(fs.uploadFile)
        .toHaveBeenCalledWith(file, 'local_file_store/dir/filename');
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store/dir');
  });

  it('should delete file when delete button clicked', () => {
    // initialize with a file in a nested directory
    const file = {path: 'local_file_store/dir/filename'} as FileNode;
    fs.listFiles.and.returnValue(observableOf([file]));
    initComponent('local_file_store/dir/filename');
    fs.listFiles.calls.reset();
    // confirm deletion
    notifier.confirm.and.returnValue(observableOf(true));
    fs.deleteFile.and.returnValue(observableOf(null));

    // delete button will delete the file and reload the current directory
    getEl(element, 'mat-row button.delete').click();
    expect(notifier.confirm).toHaveBeenCalled();
    expect(fs.deleteFile).toHaveBeenCalledWith('local_file_store/dir/filename');
    expect(fs.listFiles).toHaveBeenCalledWith('local_file_store/dir');
  });
});
