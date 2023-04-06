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

import {Component, Inject} from '@angular/core';
import {MAT_LEGACY_DIALOG_DATA} from '@angular/material/dialog';

/** Detailed error object */
export interface EndpointDetailedError {
  // Error message
  message?: string;
  // Stacktrace for the error message
  stacktrace?: string;
}

/** Data to be displayed in an error popup dialog box */
export interface ErrorDialogData {
  title: string;
  message: string;
  className?: string;
  icon?: string;
  rejectText?: string;
  confirmText?: string;
  detailedError?: EndpointDetailedError;
}

/** Component that displays an error popup dialog box */
@Component({
  selector: 'error-dialog',
  templateUrl: './error_dialog.ng.html',
  styleUrls: ['./error_dialog.css'],
})
export class ErrorDialog {
  showStacktrace = false;
  constructor(@Inject(MAT_LEGACY_DIALOG_DATA) readonly data: ErrorDialogData) {}
}
