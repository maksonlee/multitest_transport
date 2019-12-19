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
import {of as observableOf} from 'rxjs';

import {newMockCommand, newMockCommandAttempt, newMockDevice, newMockInvocationStatus, newMockRequest} from '../testing/test_util';
import {TFC_API_URL, TfcClient} from './tfc_client';
import {DeviceInfosResponse} from './tfc_models';

describe('TfcClient', () => {
  let httpClientSpy: jasmine.SpyObj<HttpClient>;
  let tfcClient: TfcClient;

  describe('getDeviceInfos', () => {
    const DEVICES: DeviceInfosResponse = {device_infos: [newMockDevice()]};

    beforeEach(() => {
      httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);
      tfcClient = new TfcClient(httpClientSpy);
      httpClientSpy.get.and.returnValue(observableOf(DEVICES));
    });

    it('calls API and parses response correctly', () => {
      const observable = tfcClient.getDeviceInfos();
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${TFC_API_URL}/devices`, jasmine.anything());
      expect(httpClientSpy.get).toHaveBeenCalledWith(jasmine.anything(), {
        params: new HttpParams().set('include_offline_devices', 'false')
      });
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
      expect(httpClientSpy.get).not.toHaveBeenCalledWith(jasmine.anything(), {
        params: new HttpParams().set('wrong argument', 'false')
      });

      observable.subscribe((response) => {
        expect(response).toEqual(DEVICES);
      });
    });
  });

  describe('getRequestInvocationStatus', () => {
    const invocationStatus = newMockInvocationStatus();

    beforeEach(() => {
      httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);
      tfcClient = new TfcClient(httpClientSpy);
      httpClientSpy.get.and.returnValue(observableOf(invocationStatus));
    });

    it('calls API and parses response correctly', () => {
      const observable = tfcClient.getRequestInvocationStatus('requestid');
      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(
              `${TFC_API_URL}/requests/requestid/invocation_status`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);

      observable.subscribe((response) => {
        expect(response).toEqual(invocationStatus);
      });
    });
  });

  describe('getRequest', () => {
    const attempt = newMockCommandAttempt();
    const command = newMockCommand();
    const request = newMockRequest([command], [attempt]);

    beforeEach(() => {
      httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);
      tfcClient = new TfcClient(httpClientSpy);
      httpClientSpy.get.and.returnValue(observableOf(request));
    });

    it('calls API and parses response correctly', () => {
      const observable = tfcClient.getRequest(request.id);
      observable.subscribe((response) => {
        expect(response).toEqual(request);
      });

      expect(httpClientSpy.get)
          .toHaveBeenCalledWith(`${TFC_API_URL}/requests/${request.id}`);
      expect(httpClientSpy.get).toHaveBeenCalledTimes(1);
    });
  });
});
