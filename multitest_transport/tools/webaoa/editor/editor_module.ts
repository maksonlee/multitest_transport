/**
 * @license
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

import {ClipboardModule} from '@angular/cdk/clipboard';
import {DragDropModule} from '@angular/cdk/drag-drop';
import {CommonModule} from '@angular/common';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatDialogModule} from '@angular/material/dialog';
import {MatIconModule} from '@angular/material/icon';
import {MatLegacyCardModule} from '@angular/material/legacy-card';
import {MatLegacyFormFieldModule} from '@angular/material/legacy-form-field';
import {MatLegacyInputModule} from '@angular/material/legacy-input';
import {MatLegacyListModule} from '@angular/material/legacy-list';
import {MatLegacySelectModule} from '@angular/material/legacy-select';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatTooltipModule} from '@angular/material/tooltip';

import {AoaActionEditor} from './action_editor';
import {TouchScreen} from './touch_screen';
import {ExecutionWakeLock} from './wake_lock';
import {WorkflowEditor} from './workflow_editor';

/** Workflow and action editing module. */
@NgModule({
  declarations: [
    AoaActionEditor,
    TouchScreen,
    WorkflowEditor,
  ],
  exports: [
    TouchScreen,
    WorkflowEditor,
  ],
  imports: [
    CommonModule,
    ClipboardModule,
    DragDropModule,
    FormsModule,
    MatButtonModule,
    MatLegacyCardModule,
    MatDialogModule,
    MatLegacyFormFieldModule,
    MatIconModule,
    MatLegacyInputModule,
    MatLegacyListModule,
    MatProgressBarModule,
    MatLegacySelectModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  providers: [
    ExecutionWakeLock,
  ],
})
export class EditorModule {
}
