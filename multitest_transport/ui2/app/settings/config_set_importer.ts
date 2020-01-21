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
import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {forkJoin} from 'rxjs';
import {delay, filter, finalize, first} from 'rxjs/operators';

import {AuthEventState, AuthService} from '../services/auth_service';
import {MttClient} from '../services/mtt_client';
import {BuildChannel, ConfigSetInfo, isBuildChannelAvailable} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {buildApiErrorMessage} from '../shared/util';

/** A component for downloading and importing config files from GCS. */
@Component({
  selector: 'config-set-importer',
  styleUrls: ['config_set_importer.css'],
  templateUrl: './config_set_importer.ng.html',
})
export class ConfigSetImporter implements OnInit {
  gcsBuildChannel?: BuildChannel;
  configs: ConfigSetInfo[] = [];

  @Input() selectedRows = [];
  selection = new SelectionModel<ConfigSetInfo>(
      /*allow multi select*/ true, this.configs);

  @Input()
  displayedColumns: string[] = [
    'select',
    'name',
    'last_update_time',
    'url',
    'status',
  ];

  @Output() selectionChange = new EventEmitter<ConfigSetInfo[]>();

  isLoading = false;
  isBuildChannelAvailable = isBuildChannelAvailable;

  constructor(
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier,
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly authService: AuthService) {}

  ngOnInit() {
    // Refresh data after authentication
    this.authService
        .getAuthProgress()
        // delay is needed for data to be populated in database
        .pipe(filter(x => x.type === AuthEventState.COMPLETE), delay(500))
        .subscribe(
            res => {
              this.load();
            },
            error => {
              this.notifier.showError(
                  'Failed to authenticate build channel.',
                  buildApiErrorMessage(error));
            });

    this.load();
  }

  load() {
    this.isLoading = true;
    this.liveAnnouncer.announce('Loading', 'polite');
    this.mttClient.getBuildChannels()
        .pipe(first())
        .pipe(finalize(() => {
          this.isLoading = false;
          this.liveAnnouncer.announce('Loading complete', 'assertive');
        }))
        .subscribe(result => {
          if (!result.build_channels) {
            return;
          }
          this.gcsBuildChannel = result.build_channels.find(
              bc => bc.id === 'google_cloud_storage');
          this.loadConfigSetInfos();
        });
  }

  /** Get the list of config sets from local and remote storage */
  loadConfigSetInfos() {
    this.mttClient.getConfigSetInfos(!!this.gcsBuildChannel)
        .pipe(first())
        .subscribe(res => {
          this.configs = res.config_set_infos;
        });
  }

  importSelectedConfigSets() {
    this.isLoading = true;
    this.liveAnnouncer.announce('Importing config sets', 'assertive');

    const configObs = [];
    for (const info of this.selection.selected) {
      configObs.push(this.mttClient.importConfigSet(info.url));
    }
    forkJoin(configObs)
        .pipe(first())
        .pipe(delay(100))  // Wait for updates when reloading page
        .pipe(finalize(() => {
          this.isLoading = false;
          this.liveAnnouncer.announce('Loading complete', 'assertive');
        }))
        .subscribe(res => {
          this.notifier.showMessage(`Configuration(s) imported`);
          this.loadConfigSetInfos();
        });
  }

  getStatus(info: ConfigSetInfo) {
    if (!info.imported) {
      return 'Not Imported';
    }
    if (info.update_available) {
      return 'Updatable';
    }
    return 'Imported';
  }

  /**
   * Triggered when import file button is clicked
   * On selecting a file, it will start to upload the file
   * @param file The selected file
   */
  onFileInputChange(file?: File) {
    // TODO: Refactor file import button into shared component
    if (!file) {
      return;
    }

    const reader = new FileReader();
    this.isLoading = true;
    this.liveAnnouncer.announce('Uploading file', 'polite');

    reader.onloadend = () => {
      // import file contents
      const content = reader.result as string;

      if (!content) {
        this.notifier.showError(
            `Failed to import configuration with empty content`);
        return;
      }

      this.mttClient.importNodeConfig(content).subscribe(
          result => {
            this.notifier.showMessage(`Configuration imported`);
            this.isLoading = false;
            this.liveAnnouncer.announce('File uploaded', 'assertive');
          },
          error => {
            this.notifier.showError(
                'Failed to import configuration.', buildApiErrorMessage(error));
            this.isLoading = false;
          });
    };
    // read contents
    reader.readAsText(file);
  }

  /**
   * On selection change, toggle the corresponding row and emit the selected
   * rows
   */
  onSelectionChange(row: ConfigSetInfo) {
    this.selection.toggle(row);
    this.selectionChange.emit(this.selection.selected);
  }

  /**
   * Authorize Build Channel
   * @param buildChannelId A buildchannel id
   */
  authorize(buildChannelId: string) {
    this.authService.startAuthFlow(buildChannelId);
  }
}
