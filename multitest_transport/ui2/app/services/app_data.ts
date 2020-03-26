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

import {InjectionToken} from '@angular/core';

/** Injects the application data loaded from index.html. */
export const APP_DATA = new InjectionToken<string>('APP_DATA');

/** General application data. */
export declare interface AppData {
  /** Current ADB version. */
  readonly adbVersion?: string;
  /** Tracking ID to use if Google Analytics is enabled. */
  readonly analyticsTrackingId?: string;
  /** Base URL for browsing directory contents. */
  readonly fileBrowseUrl?: string;
  /** Base URL for opening files. */
  readonly fileOpenUrl?: string;
  /** Base path served by the file server. */
  readonly fileServerRoot?: string;
  /** True if running in development mode. */
  readonly isDevMode?: boolean;
  /** True if currently running in Google. */
  readonly isGoogle?: boolean;
  /** User login URL create by Google appengine api. */
  readonly loginUrl?: string;
  /** User logout URL create by Google appengine api. */
  readonly logoutUrl?: string;
  /** Current MTT version. */
  readonly mttVersion?: string;
  /** Whether or not the user has completed the setup wizard. */
  readonly setupWizardCompleted?: boolean;
  /** Current login username. */
  readonly userNickname?: string;
}
