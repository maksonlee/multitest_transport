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
 * A module for build channels page
 */
import {NgModule} from '@angular/core';
import {ReactiveFormsModule} from '@angular/forms';
import {RouterModule} from '@angular/router';

import {ServicesModule} from '../services/services_module';
import {SharedModule} from '../shared/shared_module';

import {BuildChannelEditPage} from './build_channel_edit_page';
import {BuildChannelItem} from './build_channel_item';
import {BuildChannelList} from './build_channel_list';
import {BuildPicker} from './build_picker';
import {TestResourceForm} from './test_resource_form';

const COMPONENTS = [
  BuildChannelEditPage, BuildChannelItem, BuildChannelList, TestResourceForm
];

@NgModule({
  declarations: [BuildPicker, COMPONENTS],
  imports: [ServicesModule, SharedModule, RouterModule, ReactiveFormsModule],
  exports: COMPONENTS,
  })
export class BuildChannelsModule {
}
