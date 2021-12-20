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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, UrlSegment} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf, ReplaySubject} from 'rxjs';

import {FileNode, FileService, FileType} from '../services/file_service';
import {Notifier} from '../services/notifier';
import {getEl} from '../testing/jasmine_util';

import {FileBrowser} from './file_browser';
import {FileBrowserModule} from './file_browser_module';
import {FileBrowserModuleNgSummary} from './file_browser_module.ngsummary';

describe('FileBrowser', () => {
  let fixture: ComponentFixture<FileBrowser>;
  let element: DebugElement;
  let component: FileBrowser;

  let fs: jasmine.SpyObj<FileService>;
  let notifier: jasmine.SpyObj<Notifier>;
  let url: ReplaySubject<UrlSegment[]>;

  beforeEach(() => {
    fs = jasmine.createSpyObj(['listFiles', 'deleteFile']);
    fs.listFiles.and.returnValue(observableOf([]));
    notifier = jasmine.createSpyObj('notifier', ['confirm', 'showError']);
    url = new ReplaySubject<UrlSegment[]>();

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, FileBrowserModule, RouterTestingModule],
      aotSummaries: FileBrowserModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
        {provide: Notifier, useValue: notifier},
        {provide: ActivatedRoute, useValue: {url}},
      ],
    });
  });

  /** Helper method to initialize the FileBrowser component. */
  function initComponent(path = '', nodes: Array<Partial<FileNode>> = []) {
    fixture = TestBed.createComponent(FileBrowser);
    component = fixture.componentInstance;
    element = fixture.debugElement;
    fs.listFiles.and.returnValue(observableOf(nodes));
    url.next([new UrlSegment(path, {})]);
    fixture.detectChanges();
  }

  it('can load path correctly', () => {
    initComponent('a/b');
    expect(component).toBeTruthy();
    expect(component.currentDirectory).toEqual('a/b');
    expect(fs.listFiles).toHaveBeenCalledWith('a/b');
  });

  it('should have fs_proxy href on file name link', () => {
    initComponent('dir', [{path: 'dir/filename', type: FileType.FILE}]);
    const link = getEl<HTMLAnchorElement>(element, '.name-cell a');
    expect(link.href.endsWith('fs_proxy/file/dir/filename')).toBeTruthy();
  });

  it('should have file_browser href on directory name link', () => {
    initComponent('dir', [{path: 'dir/nested', type: FileType.DIRECTORY}]);
    const link = getEl<HTMLAnchorElement>(element, '.name-cell a');
    expect(link.href.endsWith('file_browser/dir/nested')).toBeTruthy();
  });

  it('should have download href on file download link', () => {
    initComponent('dir', [{path: 'dir/filename', type: FileType.FILE}]);
    const link = getEl<HTMLAnchorElement>(element, '.action-cell a.download');
    expect(link.href.endsWith('fs_proxy/file/dir/filename?download=true'))
        .toBeTruthy();
  });

  it('should have download href on directory download link', () => {
    initComponent('dir', [{path: 'dir/nested', type: FileType.DIRECTORY}]);
    const link =
        getEl<HTMLAnchorElement>(element, '.action-cell a.download-dir');
    expect(link.href.endsWith('fs_proxy/dir/dir/nested?download=true'))
        .toBeTruthy();
  });

  it('should have file_browser href on directory change link', () => {
    initComponent('dir', [{path: 'dir/nested', type: FileType.DIRECTORY}]);
    const link = getEl<HTMLAnchorElement>(element, '.action-cell a.change-dir');
    expect(link.href.endsWith('file_browser/dir/nested')).toBeTruthy();
  });

  it('should delete file when delete button clicked', () => {
    initComponent('dir', [{path: 'dir/filename', type: FileType.FILE}]);
    // confirm deletion
    notifier.confirm.and.returnValue(observableOf(true));
    fs.deleteFile.and.returnValue(observableOf(null));

    // delete button will delete the file and reload the current directory
    getEl(element, 'mat-row button.delete').click();
    expect(notifier.confirm).toHaveBeenCalled();
    expect(fs.deleteFile).toHaveBeenCalledWith('dir/filename');
  });
});
