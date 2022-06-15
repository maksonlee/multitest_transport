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

import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {SharedModule} from '../shared';

import {TestRunActionEditPage} from './test_run_action_edit_page';
import {TestRunActionList} from './test_run_action_list';
import {TestRunActionPicker} from './test_run_action_picker';

const COMPONENTS = [
  TestRunActionEditPage,
  TestRunActionList,
  TestRunActionPicker,
];

/** Module for test run action components. */
@NgModule({
  declarations: COMPONENTS,
  imports: [
    RouterModule,
    SharedModule,
  ],
  exports: COMPONENTS,
})
export class TestRunActionsModule {
}
