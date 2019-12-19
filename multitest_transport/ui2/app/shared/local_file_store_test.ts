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
import {SelectionModel} from '@angular/cdk/collections';
import {DebugElement} from '@angular/core';
import {ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf, Subject} from 'rxjs';
import {tap} from 'rxjs/operators';

import {APP_DATA} from '../services/app_data';
import {FileUploadEvent, FileUploadService} from '../services/file_upload_service';
import {MttClient} from '../services/mtt_client';
import {BuildItem} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {getEl, getTextContent} from '../testing/jasmine_util';
import {newMockBuildChannel, newMockBuildItemList} from '../testing/test_util';

import {LocalFileStore} from './local_file_store';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('LocalFileStore', () => {
  let fixture: ComponentFixture<LocalFileStore>;
  let debugEl: DebugElement;
  let localFileStore: LocalFileStore;

  let mttClient: jasmine.SpyObj<MttClient>;
  let fileUploadService: jasmine.SpyObj<FileUploadService>;
  let notifier: jasmine.SpyObj<Notifier>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj(
        'mttClient', ['listBuildItems', 'deleteBuildItem']);
    mttClient.listBuildItems.and.returnValue(observableOf({build_items: []}));
    fileUploadService = jasmine.createSpyObj(
        'fileUploadService', ['startUploadProcess', 'uploadFile']);
    notifier = jasmine.createSpyObj('notifier', ['confirm']);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
      providers: [
        {provide: APP_DATA, useValue: {}},
        {provide: FileUploadService, useValue: fileUploadService},
        {provide: MttClient, useValue: mttClient},
        {provide: Notifier, useValue: notifier},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });

    fixture = TestBed.createComponent(LocalFileStore);
    debugEl = fixture.debugElement;
    localFileStore = fixture.componentInstance;
    localFileStore.buildChannel = newMockBuildChannel();
    fixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(localFileStore).toBeTruthy();
  });

  it('should show HTML correctly', () => {
    const textContent = getTextContent(debugEl);
    expect(textContent).toContain('Selected File');
    expect(textContent).toContain('Uploaded Files');
    expect(textContent).toContain('No File Found');
  });

  it('can upload file', fakeAsync(() => {
       // check whether the files will be reloaded
       spyOn(localFileStore, 'loadBuildItems');
       // use dummy file and control upload process using subject
       const file = {name: 'filename', size: 100} as File;
       const upload = new Subject<FileUploadEvent>();
       fileUploadService.startUploadProcess.and.returnValue(
           observableOf('url'));
       fileUploadService.uploadFile.and.returnValue(upload);

       // can start upload
       localFileStore.uploadFile(file);
       tick();
       expect(localFileStore.isUploading).toBeTruthy();
       expect(localFileStore.uploadProgress).toEqual(0);
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Uploading filename', 'polite');


       // can track progress
       upload.next({type: 'progress', uploaded: 50});
       tick();
       expect(localFileStore.isUploading).toBeTruthy();
       expect(localFileStore.uploadProgress).toEqual(50);

       // can complete upload
       upload.next({type: 'complete', uploaded: 100});
       upload.complete();
       tick();
       expect(localFileStore.isUploading).toBeFalsy();
       expect(localFileStore.loadBuildItems).toHaveBeenCalledWith(true);
       expect(liveAnnouncer.announce)
           .toHaveBeenCalledWith('Completed uploading filename', 'assertive');
     }));

  it('can delete file', () => {
    // check whether the files will be reloaded
    spyOn(localFileStore, 'loadBuildItems');
    // confirm deletion and track whether actually deleted
    notifier.confirm.and.returnValue(observableOf(true));
    let deleted = false;
    mttClient.deleteBuildItem.and.returnValue(
        observableOf(true).pipe(tap(() => {
          deleted = true;
        })));

    const item = {path: 'filename'} as BuildItem;
    localFileStore.deleteFile(item);
    expect(mttClient.deleteBuildItem)
        .toHaveBeenCalledWith(localFileStore.buildChannel.id, 'filename');
    expect(localFileStore.loadBuildItems).toHaveBeenCalledWith(true);
    expect(deleted).toBeTruthy();
  });

  it('displayed correct aria label for table', () => {
    localFileStore.buildItems = newMockBuildItemList().build_items;
    localFileStore.selection = new SelectionModel<BuildItem>(false, []);
    fixture.detectChanges();
    const matTable = getEl(debugEl, 'mat-table');
    expect(matTable).toBeTruthy();
    expect(matTable.getAttribute('aria-label')).toBe('Local file store');
  });
});
