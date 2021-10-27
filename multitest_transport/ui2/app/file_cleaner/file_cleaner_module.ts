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

/** Module for file cleaner components. */
import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {SharedModule} from '../shared/shared_module';

import {FileCleanerConfigEditPage} from './file_cleaner_config_edit_page';
import {FileCleanerCriterionForm} from './file_cleaner_criterion_form';
import {FileCleanerOperationForm} from './file_cleaner_operation_form';
import {FileCleanerPolicyEditPage} from './file_cleaner_policy_edit_page';
import {FileCleanerSettingList} from './file_cleaner_setting_list';

const COMPONENTS = [
  FileCleanerConfigEditPage,
  FileCleanerCriterionForm,
  FileCleanerOperationForm,
  FileCleanerPolicyEditPage,
  FileCleanerSettingList,
];

@NgModule({
  declarations: COMPONENTS,
  imports: [
    RouterModule,
    SharedModule,
  ],
  exports: COMPONENTS,
})
export class FileCleanerModule {
}
