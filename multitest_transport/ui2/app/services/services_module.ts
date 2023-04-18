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
 * A module for components in services
 */
import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {MatIconModule} from '@angular/material/icon';
import {MatLegacyButtonModule} from '@angular/material/legacy-button';
import {MatLegacyDialogModule} from '@angular/material/legacy-dialog';
import {MatLegacyFormFieldModule} from '@angular/material/legacy-form-field';
import {MatLegacyInputModule} from '@angular/material/legacy-input';

import {AuthDialog} from './auth_dialog';
import {ErrorDialog} from './error_dialog';
import {NotifierDialog} from './notifier_dialog';

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    MatLegacyButtonModule,
    MatLegacyDialogModule,
    MatIconModule,
    MatLegacyFormFieldModule,
    FormsModule,
    MatLegacyInputModule,
  ],
  declarations: [
    AuthDialog,
    ErrorDialog,
    NotifierDialog,
  ],
  entryComponents: [
    ErrorDialog,
    NotifierDialog,
    AuthDialog,
  ]
})
export class ServicesModule {
}
