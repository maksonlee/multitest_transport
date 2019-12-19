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
import {Component, EventEmitter, Inject, Input, OnDestroy, OnInit, Output, ViewChild} from '@angular/core';
import {MatTable} from '@angular/material/table';
import {ReplaySubject, Subscription} from 'rxjs';
import {filter, finalize, mergeMap, takeUntil} from 'rxjs/operators';

import {APP_DATA, AppData} from '../services/app_data';
import {FileUploadService} from '../services/file_upload_service';
import {MttClient} from '../services/mtt_client';
import {BuildChannel, BuildItem} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {assertRequiredInput, buildApiErrorMessage, noAwait} from './util';

/**
 * Form for local file store.
 */
@Component({
  selector: 'local_file_store',
  styleUrls: ['local_file_store.css'],
  templateUrl: './local_file_store.ng.html',
})
export class LocalFileStore implements OnInit, OnDestroy {
  @Input() buildChannel!: BuildChannel;
  @Input() selectedFile!: string;
  @Input() selection!: SelectionModel<BuildItem>;
  @Output() fileSelected = new EventEmitter<BuildItem>();

  @ViewChild(MatTable, {static: false}) table!: MatTable<{}>;
  columnsToDisplay = ['name', 'timestamp', 'size', 'action'];

  /** Notified when the component is destroyed. */
  private readonly destroy = new ReplaySubject();

  isLoading = false;
  buildItems: BuildItem[] = [];
  nextPageToken?: string;
  buildItemsSubscription?: Subscription;

  /** True if currently uploading a file to local storage. */
  isUploading = false;
  /** File upload completion percentage (0 to 100). */
  uploadProgress = 0;

  constructor(
      @Inject(APP_DATA) private readonly appData: AppData,
      private readonly fileUploadService: FileUploadService,
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier) {}

  ngOnInit() {
    assertRequiredInput(this.buildChannel, 'buildChannel', 'local_file_store');
    this.loadBuildItems();
  }

  ngOnDestroy() {
    this.destroy.next();
  }

  loadBuildItems(reset?: boolean) {
    if (this.buildItemsSubscription) {
      this.buildItemsSubscription.unsubscribe();
      this.buildItemsSubscription = undefined;
    }
    if (reset) {
      this.buildItems = [];
      this.nextPageToken = undefined;
    }
    this.isLoading = true;
    this.buildItemsSubscription =
        this.mttClient
            .listBuildItems(this.buildChannel.id, '', this.nextPageToken)
            .pipe(finalize(() => {
              this.isLoading = false;
            }))
            .subscribe(res => {
              this.buildItems = this.buildItems.concat(res.build_items || []);
              this.nextPageToken = res.next_page_token;
              if (this.table) {
                this.table.renderRows();
              }
            });
  }

  /**
   * Trigger when a row clicked inside the table
   * @param row A buildItem
   */
  onRowClick(row: BuildItem) {
    this.selectedFile = row.path;
    this.fileSelected.emit(row);
  }

  /**
   * Uploads a file to the local file store, and reload content.
   * @param file file to upload
   */
  async uploadFile(file?: File) {
    if (!file) {
      return;
    }
    // Determine the upload URL.
    const url = (this.appData.fileUploadUrl || '') + file.name;
    const location =
        await this.fileUploadService.startUploadProcess(url).toPromise();
    // Perform upload and update progress.
    this.isUploading = true;
    noAwait(this.liveAnnouncer.announce('Uploading ' + file.name, 'polite'));
    this.fileUploadService.uploadFile(file, location)
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.isUploading = false;
              this.uploadProgress = 0;
            }),
        )
        .subscribe(result => {
          this.uploadProgress = result.uploaded / file.size * 100;
          if (result.type === 'complete') {
            this.liveAnnouncer.announce('Completed uploading ' + file.name,
                                        'assertive');
            if (this.selectedFile) {
              this.liveAnnouncer.announce(
                  this.selectedFile + ' is currently selected', 'polite');
            }
            this.loadBuildItems(true);
          }
        });
  }

  /**
   * Deletes a local file.
   * @param item build item corresponding to the file
   */
  deleteFile(item: BuildItem) {
    this.notifier
        .confirm('Do you really want to delete this file?', 'Delete File')
        .pipe(
            filter(x => x),
            mergeMap(
                () => this.mttClient.deleteBuildItem(
                    this.buildChannel.id, item.path)))
        .subscribe(
            res => {
              this.loadBuildItems(true);
            },
            error => {
              this.notifier.showError(
                  `Failed to delete file '${item.name}'.`,
                  buildApiErrorMessage(error));
            });
  }
}
