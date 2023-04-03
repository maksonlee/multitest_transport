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
import {MatLegacyAutocompleteModule} from '@angular/material/autocomplete';
import {MatLegacyButtonModule} from '@angular/material/button';
import {MatLegacyCardModule} from '@angular/material/card';
import {MatLegacyChipsModule} from '@angular/material/chips';
import {MatLegacyDialogModule} from '@angular/material/dialog';
import {MatDividerModule} from '@angular/material/divider';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatLegacyFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatLegacyInputModule} from '@angular/material/input';
import {MatLegacyListModule} from '@angular/material/list';
import {MatCheckboxModule} from '@angular/material/mdc-checkbox';
import {MatProgressBarModule} from '@angular/material/mdc-progress-bar';
import {MatProgressSpinnerModule} from '@angular/material/mdc-progress-spinner';
import {MatRadioModule} from '@angular/material/mdc-radio';
import {MatSnackBarModule} from '@angular/material/mdc-snack-bar';
import {MatTableModule} from '@angular/material/mdc-table';
import {MatTooltipModule} from '@angular/material/mdc-tooltip';
import {MatLegacyMenuModule} from '@angular/material/menu';
import {MatLegacyPaginatorModule} from '@angular/material/paginator';
import {MatLegacySelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSortModule} from '@angular/material/sort';
import {MatStepperModule} from '@angular/material/stepper';
import {MatLegacyTabsModule} from '@angular/material/tabs';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatTreeModule} from '@angular/material/tree';

import {ErrorDialog} from '../services/error_dialog';

import {Breadcrumb} from './breadcrumb';
import {FileSizePipe} from './file_size_pipe';
import {ForbiddenValuesValidator} from './forbidden_values_validator';
import {FormErrorInfo} from './form_error_info';
import {FromNowPipe} from './from_now_pipe';
import {HostDeviceSearch} from './host_device_search';
import {InfiniteScroll} from './infinite_scroll';
import {LinkifyPipe} from './linkify_pipe';
import {ListForm} from './list_form';
import {LocalFileStore} from './local_file_store';
import {MapListFieldPipe} from './map_list_field_pipe';
import {MultiSelect} from './multi_select';
import {NameMultiValuePairListForm} from './name_multi_value_pair_list_form';
import {NameValuePairListForm} from './name_value_pair_list_form';
import {OverflowList} from './overflow_list';
import {Paginator} from './paginator';
import {PermissionCheckPipe} from './permission_check_pipe';
import {ScheduleTimeForm} from './schedule_time_form';
import {StatusButton} from './status_button';
import {TableRowSelect, TableRowSelectCheckbox, TableRowsSelectCheckbox, TableRowsSelectManager} from './table_rows_select';
import {TestRunConfigForm} from './test_run_config_form';
import {TimeInputFilter} from './time_input_filter';
import {TradefedConfigObjectForm} from './tradefed_config_object_form';
import {TreeTable} from './tree_table';
import {UtcPipe} from './utc_pipe';
import {ValuesPipe} from './values_pipe';
import {ViewColumnsButton} from './view_columns_button';

const MATERIAL_MODULES = [
  A11yModule,         DragDropModule,        FlexLayoutModule,
  FormsModule,        MatLegacyAutocompleteModule, MatLegacyButtonModule,
  MatLegacyCardModule,      MatLegacyChipsModule,        MatCheckboxModule,
  MatLegacyDialogModule,    MatDividerModule,      MatExpansionModule,
  MatLegacyFormFieldModule, MatGridListModule,     MatIconModule,
  MatLegacyInputModule,     MatLegacyListModule,         MatLegacyMenuModule,
  MatLegacyPaginatorModule, MatProgressBarModule,  MatProgressSpinnerModule,
  MatRadioModule,     MatLegacySelectModule,       MatSidenavModule,
  MatSnackBarModule,  MatSortModule,         MatStepperModule,
  MatTableModule,     MatLegacyTabsModule,         MatToolbarModule,
  MatTooltipModule,   MatTreeModule,
];

const COMPONENTS = [
  Breadcrumb,
  FormErrorInfo,
  ListForm,
  LocalFileStore,
  MultiSelect,
  NameMultiValuePairListForm,
  NameValuePairListForm,
  OverflowList,
  Paginator,
  HostDeviceSearch,
  ScheduleTimeForm,
  StatusButton,
  TestRunConfigForm,
  TimeInputFilter,
  TradefedConfigObjectForm,
  TreeTable,
  ViewColumnsButton,
];

const DIRECTIVES = [
  ForbiddenValuesValidator,
  InfiniteScroll,
  TableRowSelect,
  TableRowSelectCheckbox,
  TableRowsSelectCheckbox,
  TableRowsSelectManager,
];

const PIPES = [
  FileSizePipe,
  FromNowPipe,
  LinkifyPipe,
  MapListFieldPipe,
  PermissionCheckPipe,
  UtcPipe,
  ValuesPipe,
];

/** Abbreviated title of the project, used for page titles. */
export const APPLICATION_NAME = 'Android Test Station';

/** Abbreviated title of the lab sub project, used for page titles. */
export const LAB_APPLICATION_NAME = `${APPLICATION_NAME} Lab`;

@NgModule({
  declarations: [
    COMPONENTS,
    DIRECTIVES,
    PIPES,
  ],
  imports: [
    CommonModule,
    MATERIAL_MODULES,
  ],
  exports: [
    CommonModule,
    COMPONENTS,
    DIRECTIVES,
    MATERIAL_MODULES,
    PIPES,
  ],
  entryComponents: [ErrorDialog],
})
export class SharedModule {
}
