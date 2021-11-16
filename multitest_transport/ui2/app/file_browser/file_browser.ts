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
import {Component, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MatTable} from '@angular/material/mdc-table';
import {ActivatedRoute, Router, UrlSegment} from '@angular/router';
import {ReplaySubject} from 'rxjs';
import {filter, finalize, mergeMap, takeUntil} from 'rxjs/operators';

import {FileNode, FileService, FileType, humanFileSize, PROXY_PATH} from '../services/file_service';
import {Notifier} from '../services/notifier';
import {buildApiErrorMessage} from '../shared/util';

/** A component for file browsing */
@Component({
  selector: 'file-browser',
  styleUrls: ['file_browser.css'],
  templateUrl: './file_browser.ng.html',
})
export class FileBrowser implements OnInit, OnDestroy {
  readonly FileType = FileType;
  readonly humanFileSize = humanFileSize;
  readonly PROXY_PATH = PROXY_PATH;

  isLoading = false;
  // Hold list of files when navigate to or load a directory
  files: FileNode[] = [];
  // Hold information of the current directory path
  currentDirectory: string = '';
  // Contains the directory informamtion
  path: string = '';

  // Table that displays the list of files
  @ViewChild(MatTable, {static: false}) table!: MatTable<{}>;
  columnsToDisplay = ['name', 'timestamp', 'size', 'action'];

  /** Notified when the component is destroyed. */
  private readonly destroy = new ReplaySubject<void>();

  constructor(
      private readonly fs: FileService,
      private readonly route: ActivatedRoute,
      private readonly router: Router,
      private readonly notifier: Notifier,
      private readonly location: Location,
  ) {}

  ngOnInit() {
    this.route.url.pipe(takeUntil(this.destroy))
        .subscribe((url: UrlSegment[]) => {
          if (!url || !url.length) {
            return;
          }
          this.path = url.map(u => u.path).join('/');
        });
    this.changeDirectory(this.path ? this.path : '');
  }

  ngOnDestroy() {
    this.destroy.next();
  }

  /**
   * Update url based on current path.
   * @param path: directory path
   */
  updateUrl(path: string) {
    const urlTree =
        this.router.createUrlTree(['file_browser', ...path.split('/')]);
    this.location.replaceState(urlTree.toString());
  }

  /**
   * Change directory
   * @param directory: path to directory
   */
  changeDirectory(directory: string) {
    this.currentDirectory = directory;
    this.updateUrl(this.currentDirectory);
    this.loadFiles();
  }

  /** Reloads the list of files in the current directory. */
  private loadFiles() {
    this.isLoading = true;
    this.fs.listFiles(this.currentDirectory)
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.isLoading = false;
            }),
            )
        .subscribe(
            files => {
              this.files = files;
            },
            error => {
              this.notifier.showError(
                  `Failed to load files.`, buildApiErrorMessage(error));
            });
  }

  /**
   * Deletes a local file.
   * @param file to delete
   */
  deleteFile(file: FileNode) {
    this.notifier
        .confirm(`Do you really want to delete '${file.name}'?`, 'Delete File')
        .pipe(
            filter(x => x),
            mergeMap(() => this.fs.deleteFile(file.path)),
            )
        .subscribe(
            () => {
              this.loadFiles();
            },
            error => {
              this.notifier.showError(
                  `Failed to delete file '${file.name}'.`,
                  buildApiErrorMessage(error));
            });
  }
}
