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

import {Location} from '@angular/common';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute, Router, UrlSegment} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {FileNode, FileService, FileType} from '../services/file_service';
import {Notifier} from '../services/notifier';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
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
  let router: jasmine.SpyObj<Router>;
  let location: jasmine.SpyObj<Location>;
  const urlSegments = [new UrlSegment('a', {}), new UrlSegment('b', {})];
  const activatedRouteSpy = new ActivatedRouteStub(undefined, urlSegments);

  beforeEach(() => {
    fs = jasmine.createSpyObj(['getRelativePath', 'listFiles', 'deleteFile']);
    fs.getRelativePath.and.callFake(fileUrl => fileUrl);
    fs.listFiles.and.returnValue(observableOf([]));
    notifier = jasmine.createSpyObj('notifier', ['confirm', 'showError']);
    router = jasmine.createSpyObj(['createUrlTree']);
    router.createUrlTree.and.returnValue('');
    location = jasmine.createSpyObj('location', ['replaceState']);
    location.replaceState.and.returnValue((''));

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, FileBrowserModule, RouterTestingModule],
      aotSummaries: FileBrowserModuleNgSummary,
      providers: [
        {provide: FileService, useValue: fs},
        {provide: Notifier, useValue: notifier},
        {provide: Router, useValue: router},
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: Location, useValue: location},
      ],
    });
  });

  /** Helper method to initialize the FileBrowser component. */
  function initComponent(path = '') {
    fixture = TestBed.createComponent(FileBrowser);
    component = fixture.componentInstance;
    element = fixture.debugElement;
    component.path = path;
    fixture.detectChanges();
  }

  it('can load path correctly', () => {
    initComponent();
    expect(component).toBeTruthy();
    expect(component.path).toEqual('a/b');
    expect(router.createUrlTree).toHaveBeenCalledWith([
      'file_browser', 'a', 'b'
    ]);
  });

  it('should display correct href on anchor tag for navigation', () => {
    const path = 'local_file_store/dir';
    const directory = {path, type: FileType.DIRECTORY} as FileNode;
    fs.listFiles.and.returnValue(observableOf([directory]));
    initComponent(path);
    const link = getEl<HTMLAnchorElement>(element, 'mat-row a');
    expect(link.href.endsWith('file_browser/local_file_store/dir'))
        .toBeTruthy();
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
  });
});
