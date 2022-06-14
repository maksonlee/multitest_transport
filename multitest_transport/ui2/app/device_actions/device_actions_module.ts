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

/**
 * A module for devices actions page
 */
import {NgModule} from '@angular/core';
import {ReactiveFormsModule} from '@angular/forms';
import {Title} from '@angular/platform-browser';
import {RouterModule} from '@angular/router';

import {BuildChannelsModule} from '../build_channels/build_channels_module';
import {SharedModule} from '../shared/shared_module';

import {DeviceActionEditPage} from './device_action_edit_page';
import {DeviceActionList} from './device_action_list';
import {DeviceActionPicker} from './device_action_picker';

const COMPONENTS = [
  DeviceActionEditPage,
  DeviceActionList,
  DeviceActionPicker,
];

@NgModule({
  declarations: COMPONENTS,
  providers: [Title],
  imports: [
    BuildChannelsModule,
    SharedModule,
    RouterModule,
    ReactiveFormsModule,
  ],
  exports: COMPONENTS,
})
export class DeviceActionsModule {
}
