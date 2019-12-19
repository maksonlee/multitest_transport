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

import {Component, OnInit} from '@angular/core';
import {delay, filter, first} from 'rxjs/operators';

import {AuthEventState, AuthService} from '../services/auth_service';
import {MttClient} from '../services/mtt_client';
import {BuildChannel} from '../services/mtt_models';

/**
 * This component allows users to authenticate their Google Drive or Google
 * Cloud Storage build channels
 */
@Component({
  selector: 'build-channel-setup',
  styleUrls: ['build_channel_setup.css'],
  templateUrl: './build_channel_setup.ng.html',
})
export class BuildChannelSetup implements OnInit {
  GOOGLE_CLOUD_STORAGE_ID = 'google_cloud_storage';
  GOOGLE_DRIVE_ID = 'google_drive';

  cloudBuildChannel!: BuildChannel;
  driveBuildChannel!: BuildChannel;

  constructor(
      private readonly mtt: MttClient,
      private readonly authService: AuthService) {}

  ngOnInit() {
    this.authService
        .getAuthProgress()
        // delay is needed for data to be populated in database
        .pipe(filter(x => x.type === AuthEventState.COMPLETE), delay(500))
        .subscribe(
            res => {
              this.load();
            },
            error => {
                // TODO: Better error handling
            });

    this.load();
  }

  load() {
    this.mtt.getBuildChannels().pipe(first()).subscribe(buildChannelList => {
      const buildChannelMap: {[key: string]: BuildChannel} = {};
      for (const buildChannel of buildChannelList.build_channels!) {
        buildChannelMap[buildChannel.id] = buildChannel;
      }

      this.cloudBuildChannel = buildChannelMap[this.GOOGLE_CLOUD_STORAGE_ID];
      this.driveBuildChannel = buildChannelMap[this.GOOGLE_DRIVE_ID];
    });
  }

  /**
   * Authorize Build Channel
   * @param buildChannelId A buildchannel id
   */
  authorize(buildChannelId: string) {
    this.authService.startAuthFlow(buildChannelId);
  }
}
