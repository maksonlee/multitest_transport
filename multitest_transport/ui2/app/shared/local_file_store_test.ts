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
import {of as observableOf, Subject} from 'rxjs';

import {FileNode, FileService, FileUploadEvent} from '../services/file_service';
import {Notifier} from '../services/notifier';

import {LocalFileStore} from './local_file_store';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('LocalFileStore', () => {
  let fixture: ComponentFixture<LocalFileStore>;
  let debugEl: DebugElement;
  let localFileStore: LocalFileStore;

  let fs: jasmine.SpyObj<FileService>;
  let notifier: jasmine.SpyObj<Notifier>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    fs = jasmine.createSpyObj([
      'getFileUrl', 'getRelativePath', 'listFiles', 'uploadFile', 'deleteFile'
    ]);
    fs.listFiles.and.returnValue(observableOf([]));
    notifier = jasmine.createSpyObj('notifier', ['confirm']);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
        {provide: Notifier, useValue: notifier},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });

    fixture = TestBed.createComponent(LocalFileStore);
    debugEl = fixture.debugElement;
    localFileStore = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('can initialize the component', () => {
    expect(localFileStore).toBeTruthy();
  });

  it('can upload file', fakeAsync(() => {
       // check whether the files will be reloaded
       spyOn(localFileStore, 'loadFiles');
       // use dummy file and control upload process using subject
       const file = {name: 'filename', size: 100} as File;
       const upload = new Subject<Partial<FileUploadEvent>>();
       fs.uploadFile.and.returnValue(upload);

       // can start upload
       localFileStore.uploadFile(file);
       tick();
       expect(localFileStore.isUploading).toBeTruthy();
       expect(localFileStore.uploadProgress).toEqual(0);
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Uploading filename', 'polite');

       // can track progress
       upload.next({done: false, progress: 50});
       tick();
       expect(localFileStore.isUploading).toBeTruthy();
       expect(localFileStore.uploadProgress).toEqual(50);

       // can complete upload
       upload.next({done: true, progress: 100});
       upload.complete();
       tick();
       expect(localFileStore.isUploading).toBeFalsy();
       expect(localFileStore.loadFiles).toHaveBeenCalledWith();
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('filename uploaded', 'assertive');
     }));

  it('can delete file', () => {
    // check whether the files will be reloaded
    spyOn(localFileStore, 'loadFiles');
    // confirm deletion
    notifier.confirm.and.returnValue(observableOf(true));
    fs.deleteFile.and.returnValue(observableOf(null));

    const file = {path: 'filename'} as FileNode;
    localFileStore.deleteFile(file);
    expect(fs.deleteFile).toHaveBeenCalledWith('filename');
    expect(localFileStore.loadFiles).toHaveBeenCalledWith();
  });
});
