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

import {A11yModule} from '@angular/cdk/a11y';
import {DragDropModule} from '@angular/cdk/drag-drop';
import {CommonModule} from '@angular/common';
import {NgModule} from '@angular/core';
import {FlexLayoutModule} from '@angular/flex-layout';
import {FormsModule} from '@angular/forms';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatChipsModule} from '@angular/material/chips';
import {MatDialogModule} from '@angular/material/dialog';
import {MatDividerModule} from '@angular/material/divider';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatRadioModule} from '@angular/material/radio';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatSortModule} from '@angular/material/sort';
import {MatStepperModule} from '@angular/material/stepper';
import {MatTableModule} from '@angular/material/table';
import {MatTabsModule} from '@angular/material/tabs';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatTreeModule} from '@angular/material/tree';

import {Breadcrumb} from './breadcrumb';
import {FormErrorInfo} from './form_error_info';
import {FromNowPipe} from './from_now_pipe';
import {InfiniteScroll} from './infinite_scroll';
import {ListForm} from './list_form';
import {LocalFileStore} from './local_file_store';
import {MapListFieldPipe} from './map_list_field_pipe';
import {NameValuePairListForm} from './name_value_pair_list_form';
import {OverflowList} from './overflow_list';
import {Paginator} from './paginator';
import {ScheduleTimeForm} from './schedule_time_form';
import {StatusButton} from './status_button';
import {TestRunConfigForm} from './test_run_config_form';
import {TreeTable} from './tree_table';
import {UtcPipe} from './utc_pipe';

const MATERIAL_MODULES = [
  A11yModule,
  DragDropModule,
  FlexLayoutModule,
  FormsModule,
  MatAutocompleteModule,
  MatButtonModule,
  MatCardModule,
  MatChipsModule,
  MatCheckboxModule,
  MatDialogModule,
  MatDividerModule,
  MatFormFieldModule,
  MatGridListModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatMenuModule,
  MatPaginatorModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatRadioModule,
  MatSelectModule,
  MatSidenavModule,
  MatSnackBarModule,
  MatSortModule,
  MatStepperModule,
  MatTableModule,
  MatTabsModule,
  MatToolbarModule,
  MatTooltipModule,
  MatTreeModule,
];

const COMPONENTS = [
  Breadcrumb,
  FormErrorInfo,
  ListForm,
  LocalFileStore,
  NameValuePairListForm,
  OverflowList,
  Paginator,
  ScheduleTimeForm,
  StatusButton,
  TestRunConfigForm,
  TreeTable,
];

/** Abbreviated title of the project, used for page titles */
export const APPLICATION_NAME = 'Android Test Station';

/** Abbreviated title of the lab sub project, used for page titles */
export const LAB_APPLICATION_NAME = `${APPLICATION_NAME} Lab`;

@NgModule({
  declarations: [
    COMPONENTS,
    FromNowPipe,
    InfiniteScroll,
    MapListFieldPipe,
    UtcPipe,
  ],
  imports: [
    CommonModule,
    MATERIAL_MODULES,
  ],
  exports: [
    CommonModule,
    COMPONENTS,
    FromNowPipe,
    InfiniteScroll,
    MapListFieldPipe,
    MATERIAL_MODULES,
    UtcPipe,
  ],
})
export class SharedModule {
}
