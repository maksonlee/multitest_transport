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

import {of as observableOf} from 'rxjs';

import {TfcClient} from './tfc_client';
import {UserPermission} from './tfc_models';
import {UserService} from './user_service';

describe('UserService', () => {
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let userService: UserService;
  const myLabs = ['lab1', 'lab2'];
  const userPermission: UserPermission = {isAdmin: true};

  beforeEach(() => {
    tfcClient = jasmine.createSpyObj('tfcClient', {
      checkUserPermission: observableOf(userPermission),
      getMyLabInfos: observableOf(myLabs),
    });
    userService = new UserService(tfcClient);
  });

  it('should be instantiated', () => {
    expect(userService).toBeTruthy();
  });

  it('should call checkPermission correctly', () => {
    userService.checkPermission();
    expect(tfcClient.checkUserPermission).toHaveBeenCalledTimes(1);
  });

  it('should call getMyLabInfos correctly', () => {
    userService.getMyLabInfos();
    expect(tfcClient.getMyLabInfos).toHaveBeenCalledTimes(1);
  });

  it('should call isAdminOrMyLab correctly', () => {
    userService.setMyLabs(myLabs);
    userService.setAdmin(true);
    expect(userService.isAdminOrMyLab(myLabs[0])).toBeTrue();

    userService.setAdmin(false);
    expect(userService.isAdminOrMyLab(myLabs[0])).toBeTrue();

    userService.setAdmin(true);
    expect(userService.isAdminOrMyLab('notMyLab')).toBeTrue();
  });
});
