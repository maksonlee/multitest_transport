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

import {UserService} from '../services/user_service';

import {PermissionCheckPipe} from './permission_check_pipe';

describe('PermissionCheckPipe', () => {
  let pipe: PermissionCheckPipe;
  let userServiceSpy: jasmine.SpyObj<UserService>;
  const labs = ['lab1', 'lab2'];

  beforeEach(() => {
    userServiceSpy = jasmine.createSpyObj('UserService', {
      isAdminOrMyLab: true,
      isAdmin: false,
      myLabs: labs,
    });

    pipe = new PermissionCheckPipe(userServiceSpy);
  });

  it('should call isAdminOrMyLab from userService', () => {
    const isAdminOrMyLab = pipe.transform(labs[0]);
    expect(userServiceSpy.isAdminOrMyLab).toHaveBeenCalledTimes(1);
    expect(isAdminOrMyLab).toBeTrue();
  });

  it('handle no input string data', () => {
    expect(pipe.transform()).toBe(userServiceSpy.isAdmin);
  });
});
