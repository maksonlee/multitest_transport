/**
 * Copyright 2020 Google LLC
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
import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {ConfigSetInfo} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {buildApiErrorMessage} from '../shared/util';

/** A component for displaying a list of imported config sets. */
@Component({
  selector: 'config-set-list',
  styleUrls: ['config_set_list.css'],
  templateUrl: './config_set_list.ng.html',
})
export class ConfigSetList implements OnInit, OnDestroy {
  isLoading = false;
  infos: ConfigSetInfo[] = [];

  private readonly destroy = new ReplaySubject();

  @Input()
  displayedColumns: string[] = [
    'name',
    'description',
    'status',
  ];

  constructor(
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier,
      private readonly liveAnnouncer: LiveAnnouncer,
  ) {}

  ngOnInit() {
    this.load();
  }

  ngOnDestroy() {
    this.destroy.next();
    this.liveAnnouncer.clear();
  }

  load() {
    this.isLoading = true;
    this.liveAnnouncer.announce('Loading config sets', 'polite');

    this.mttClient.getConfigSetInfos()
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.isLoading = false;
            }),
            )
        .subscribe(
            result => {
              this.infos = result.config_set_infos || [];
              this.liveAnnouncer.announce('Config set loaded', 'assertive');
            },
            error => {
              this.notifier.showError(
                  'Failed to load config sets.', buildApiErrorMessage(error));
            },
        );
  }

  /**
   * Triggered when import file button is clicked
   * On selecting a file, it will start to upload the file
   * @param file The selected file
   */
  onConfigSetFileUpload(file?: File) {
    // TODO: Switch to import local config API
  }

  deleteInfo(info: ConfigSetInfo) {
    // TODO: Add deleteConfigSet API
  }
}
