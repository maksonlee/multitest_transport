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
import {ServicesModule} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {SharedModule} from 'google3/third_party/py/multitest_transport/ui2/app/shared';

import {DeviceDetails} from '../devices/device_details';
import {DevicesModule} from '../devices/devices_module';
import {HostsModule} from '../hosts/hosts_module';
import {NotesModule} from '../notes/notes_module';

import {RecoveryDeviceList} from './recovery_device_list';
import {RecoveryHostList} from './recovery_host_list';
import {RecoveryHostStatus} from './recovery_host_status';
import {RecoveryPage} from './recovery_page';
import {RecoverySettingPage} from './recovery_setting_page';

const COMPONENTS = [
  RecoveryDeviceList,
  RecoveryHostList,
  RecoveryHostStatus,
  RecoveryPage,
  RecoverySettingPage,
];

@NgModule({
  declarations: COMPONENTS,
  imports: [
    DevicesModule,
    HostsModule,
    NotesModule,
    RouterModule,
    ServicesModule,
    SharedModule,
  ],
  exports: COMPONENTS,
  entryComponents: [DeviceDetails]
})
export class RecoveryModule {
}
