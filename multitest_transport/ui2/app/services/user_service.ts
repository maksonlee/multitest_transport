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

import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

import {LabInfosResponse} from './mtt_lab_models';
import {TfcClient} from './tfc_client';
import {UserPermission} from './tfc_models';

/** A service to check current user role. */
@Injectable({
  providedIn: 'root',
})
export class UserService {
  private admin = false;
  private myLabs: string[] = [];

  constructor(
      private readonly tfcClient: TfcClient,
  ) {}

  get isAdmin(): boolean {
    return this.admin;
  }

  isMyLab(labName: string): boolean {
    return this.myLabs.indexOf(labName) > -1;
  }

  setAdmin(value: boolean) {
    this.admin = value;
  }

  setMyLabs(labs: string[]) {
    this.myLabs = labs;
  }

  isAdminOrMyLab(labName: string): boolean {
    return (this.isAdmin || this.isMyLab(labName));
  }

  checkPermission(): Observable<UserPermission> {
    return this.tfcClient.checkUserPermission();
  }

  getMyLabInfos(): Observable<LabInfosResponse> {
    return this.tfcClient.getMyLabInfos(this.admin);
  }
}
