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

import {Injectable} from '@angular/core';
import {MatDialog} from '@angular/material/dialog';
import {EMPTY, interval, Observable} from 'rxjs';
import {filter, finalize, first, map, switchMap} from 'rxjs/operators';

import {AuthDialog} from './auth_dialog';
import {MttClient} from './mtt_client';
import {AuthorizationInfo} from './mtt_models';

const REDIRECT_URI = window.location.origin + '/auth_return';
const AUTH_WINDOW_NAME = 'authWindow';
const AUTH_WINDOW_FEATURES = 'width=550,height=420,resizable,scrollbars,status';

/** Manage OAuth2 authorizations for build channels. */
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  constructor(
      private readonly dialog: MatDialog,
      private readonly mttClient: MttClient) {}

  /**
   * Authorizes a build channel.
   * @param buildChannelId build channel identifier
   */
  authorizeBuildChannel(buildChannelId: string): Observable<void> {
    return this.mttClient
        .getBuildChannelAuthorizationInfo(buildChannelId, REDIRECT_URI)
        .pipe(switchMap(authInfo => this.getAuthorizationCode(authInfo)))
        .pipe(switchMap(code => {
          if (!code) {
            return EMPTY;
          }
          return this.mttClient.authorizeBuildChannel(
              code, buildChannelId, REDIRECT_URI);
        }));
  }

  // Opens a new authorization window or replaces an existing one.
  private static openAuthorizationWindow(authUrl: string): Window|null {
    return window.open(authUrl, AUTH_WINDOW_NAME, AUTH_WINDOW_FEATURES);
  }

  // Ensures the authorization window is closed.
  private static closeAuthorizationWindow(authWindow: Window|null) {
    if (authWindow) {
      authWindow.close();
    }
  }

  // Checks if the authorization window has returned to the redirect URI.
  private static hasAuthorizationReturned(authWindow: Window): boolean {
    try {
      return authWindow.location.host === window.location.host;
    } catch {
      return false;  // Cross-origin access blocked (not returned).
    }
  }

  // Fetches an authorization code using automatic or manual copy-paste flows.
  private getAuthorizationCode(authInfo: AuthorizationInfo) {
    if (authInfo.is_manual) {
      return this.getManualAuthorizationCode(authInfo.url);
    }
    return this.getRedirectAuthorizationCode(authInfo.url);
  }

  // Asks the user to manually copy-paste an authorization code.
  private getManualAuthorizationCode(authUrl: string): Observable<string|null> {
    const authWindow = AuthService.openAuthorizationWindow(authUrl);
    // Waits for the user to provide the authorization code.
    return this.dialog.open(AuthDialog, {width: '400px', disableClose: true})
        .afterClosed()
        .pipe(finalize(() => {
          AuthService.closeAuthorizationWindow(authWindow);
        }));
  }

  // Fetches an authorization code automatically by monitoring the authorization
  // window's query parameters after redirection.
  private getRedirectAuthorizationCode(authUrl: string):
      Observable<string|null> {
    const authWindow = AuthService.openAuthorizationWindow(authUrl);
    // Periodically check if the authorization window has returned to the
    // redirect URI with an authorization code.
    return interval(500)
        .pipe(filter(() => {
          if (!authWindow || authWindow.closed) {
            return true;  // Authorization window unexpectedly closed, abort.
          }
          return AuthService.hasAuthorizationReturned(authWindow);
        }))
        .pipe(first())
        .pipe(finalize(() => {
          AuthService.closeAuthorizationWindow(authWindow);
        }))
        .pipe(map(() => {
          return authWindow &&
              new URLSearchParams(authWindow.location.search).get('code');
        }));
  }
}
