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

import {HttpClient, HttpParams} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

import {DeviceInfosResponse, InvocationStatus, Request} from './tfc_models';

/** URL for TFC API methods */
export const TFC_API_URL = '/_ah/api/tradefed_cluster/v1';

/** Client for TFC API access */
@Injectable({
  providedIn: 'root',
})
export class TfcClient {

  constructor(private readonly http: HttpClient) {}

  getDeviceInfos(): Observable<DeviceInfosResponse> {
    const params = new HttpParams().set('include_offline_devices', 'false');
    return this.http.get<DeviceInfosResponse>(
        `${TFC_API_URL}/devices`, {params});
  }

  getRequest(requestId: string): Observable<Request> {
    return this.http.get<Request>(`${TFC_API_URL}/requests/${requestId}`);
  }

  getRequestInvocationStatus(requestId: string): Observable<InvocationStatus> {
    return this.http.get<InvocationStatus>(
        `${TFC_API_URL}/requests/${requestId}/invocation_status`);
  }
}
