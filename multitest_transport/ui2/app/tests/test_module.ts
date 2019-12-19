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
 * A module for all test components.
 */

import {NgModule} from '@angular/core';
import {ReactiveFormsModule} from '@angular/forms';
import {RouterModule} from '@angular/router';

import {BuildChannelsModule} from '../build_channels/build_channels_module';
import {SharedModule} from '../shared/shared_module';

import {TestEditPage} from './test_edit_page';
import {TestList} from './test_list';
import {TestListPage} from './test_list_page';

@NgModule({
  declarations: [TestEditPage, TestList, TestListPage],
  imports:
      [BuildChannelsModule, SharedModule, RouterModule, ReactiveFormsModule],
  exports: [TestEditPage, TestList, TestListPage],
})
export class TestModule {
}
