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
import {BehaviorSubject, Observable} from 'rxjs';

import {AuthDialog} from './auth_dialog';
import {MttClient} from './mtt_client';

/**
 * Auth event constant
 */
export enum AuthEventState {
  IN_PROGRESS = 'in_progress',
  COMPLETE = 'complete',
}

/** Time in ms for authentication's data to get stored in database */
export const AUTH_DELAY = 500;

const REDIRECT_URI = window.location.origin + '/auth_return';
const REMOTE_REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob';
/**
 * Authentication Client
 * A service to trigger OAuth2 flow for a build channel
 */
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  constructor(
      private readonly dialog: MatDialog,
      private readonly mttClient: MttClient) {}
  private readonly authProgressSubject =
      new BehaviorSubject<AuthEvent>({type: AuthEventState.IN_PROGRESS});

  getAuthProgress(): Observable<AuthEvent> {
    return this.authProgressSubject.asObservable();
  }

  /**
   * Open a authentication dialog to get authentication code
   */
  openRemoteAuthDialog(): Observable<string> {
    const dialogRef =
        this.dialog.open(AuthDialog, {width: '400px', disableClose: true});
    return dialogRef.afterClosed();
  }

  /**
   * Trigger authflow
   * @param buildChannelId A build channel id
   */
  startAuthFlow(buildChannelId: string) {
    this.mttClient.getAuthUrl(buildChannelId, REDIRECT_URI)
        .subscribe(
            result => {
              if (result.is_manual) {
                this.remoteAuthFlow(result.url, buildChannelId);
              } else {
                this.localhostAuthFlow(result.url, buildChannelId);
              }
            },
            error => {
              // TODO: Better error handling
              console.error(error);
            });
  }

  /**
   * Trigger remote authentication flow where user is guided to copy and paste
   * authentication code
   * @param oauthUrl authorized url
   * @param buildChannelId A build channel id
   */
  remoteAuthFlow(oauthUrl: string, buildChannelId: string) {
    const authWindow = window.open(
        oauthUrl, 'authWindow',
        'width=550,height=420,resizable,scrollbars,status');

    this.openRemoteAuthDialog().subscribe(result => {
      this.mttClient.authCallback(result, buildChannelId, REMOTE_REDIRECT_URI)
          .subscribe(
              res => {
                this.authProgressSubject.next({
                  type: AuthEventState.COMPLETE,
                });
              },
              error => {
                // TODO: Better error handling
                console.error(error);
              });
      if (authWindow) {
        authWindow.close();
      }
    });
  }

  /**
   * Trigger local authentication flow where user will guided to allow
   * MTT access Google Service via popup window
   * @param oauthUrl An url returned by getAuthUrl
   * @param buildChannelId The buildchannel that we are authenticating
   */
  localhostAuthFlow(oauthUrl: string, buildChannelId: string) {
    let authWindowHost: string = '';
    const authWindow = window.open(
        oauthUrl, 'authWindow',
        'width=550,height=420,resizable,scrollbars,status');
    if (!authWindow) {
      return;
    }
    // Check authorization status every .5 seconds by checking whether we have
    // closed the authorization window or not
    const pollTimer = window.setInterval(() => {
      if (authWindow && authWindow.closed) {
        window.clearInterval(pollTimer);
      }
      try {
        authWindowHost = authWindow.location.host;
      } catch (e) {
        // still in google oauth page
      }
      if (authWindowHost && authWindowHost === window.location.host) {
        window.clearInterval(pollTimer);
        if (authWindow) {
          const code =
              new URLSearchParams(authWindow.location.search).get('code') || '';
          this.mttClient.authCallback(code, buildChannelId, REDIRECT_URI)
              .subscribe(
                  res => {
                    this.authProgressSubject.next({
                      type: AuthEventState.COMPLETE,
                    });
                  },
                  error => {
                    // TODO: Better error handling
                    console.error(error);
                  });
          authWindow.close();
        }
      }
      this.authProgressSubject.next({
        type: AuthEventState.IN_PROGRESS,
      });
    }, 500);
  }
}

/**
 * Authorization event
 */
export type AuthEvent = AuthEventComplete|AuthEventProgress;

/**
 * A sub event of AuthEvent, indicating that authorization have been completed
 */
export interface AuthEventComplete {
  type: AuthEventState.COMPLETE;
}

/**
 * A sub event of AuthEvent, indicaating that authorization is in progress
 */
export interface AuthEventProgress {
  type: AuthEventState.IN_PROGRESS;
}
