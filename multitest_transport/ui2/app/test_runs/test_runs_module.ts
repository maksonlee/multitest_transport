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
 * A module for all test run components and pages
 */

import {NgModule} from '@angular/core';
import {Title} from '@angular/platform-browser';

import {BuildChannelsModule} from '../build_channels/build_channels_module';
import {DeviceActionsModule} from '../device_actions/device_actions_module';
import {DevicesModule} from '../devices/devices_module';
import {ServicesModule} from '../services/services_module';
import {SharedModule} from '../shared/shared_module';
import {TestRunActionsModule} from '../test_run_actions/test_run_actions_module';

import {AttemptStatus} from './attempt_status';
import {NewTestRunPage} from './new_test_run_page';
import {TestModuleResultList} from './test_module_result_list';
import {TestPackageInfoPipe} from './test_package_info_pipe';
import {TestResourceList} from './test_resource_list';
import {TestRunConfigEditor} from './test_run_config_editor';
import {TestRunConfigList} from './test_run_config_list';
import {TestRunConfigSummary} from './test_run_config_summary';
import {TestRunConsole} from './test_run_console';
import {TestRunDetail} from './test_run_detail';
import {TestRunDetailPage} from './test_run_detail_page';
import {TestRunFailures} from './test_run_failures';
import {TestRunList} from './test_run_list';
import {TestRunListPage} from './test_run_list_page';
import {TestRunProgress} from './test_run_progress';
import {TestRunResults} from './test_run_results';
import {TestRunTargetPicker} from './test_run_target_picker';
import {TestRunTreeTable} from './test_run_tree_table';

const COMPONENTS = [
  AttemptStatus,       NewTestRunPage,
  TestPackageInfoPipe, TestResourceList,  TestModuleResultList,
  TestRunConfigEditor, TestRunConfigList, TestRunConfigSummary,
  TestRunConsole,      TestRunDetail,     TestRunDetailPage,
  TestRunFailures,     TestRunList,       TestRunListPage,
  TestRunProgress,     TestRunResults,    TestRunTargetPicker,
  TestRunTreeTable,
];

@NgModule({
  declarations: COMPONENTS,
  providers: [Title],
  imports: [
    BuildChannelsModule, DeviceActionsModule, DevicesModule,
    TestRunActionsModule, ServicesModule, SharedModule
  ],
  exports: COMPONENTS,
  entryComponents: [TestRunConfigEditor],
})
export class TestRunsModule {
}
