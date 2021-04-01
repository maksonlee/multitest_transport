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

import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {NotesModule} from 'google3/third_party/py/multitest_transport/ui2/app/notes/notes_module';
import {NotesModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/notes/notes_module.ngsummary';
import {NoteType} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_lab_models';
import {TfcClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_client';
import {UserService} from 'google3/third_party/py/multitest_transport/ui2/app/services/user_service';
import {ActivatedRouteStub} from 'google3/third_party/py/multitest_transport/ui2/app/testing/activated_route_stub';
import {newMockDeviceNoteList, newMockHostNoteList} from 'google3/third_party/py/multitest_transport/ui2/app/testing/mtt_lab_mocks';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('NoteList', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: true,
  });
  let tfcClientSpy: jasmine.SpyObj<TfcClient>;
  let userServiceSpy: jasmine.SpyObj<UserService>;
  let activatedRouteSpy: ActivatedRouteStub;

  describe('Device noteList', () => {
    let deviceSerial: string;
    const noteType: NoteType = NoteType.DEVICE;

    beforeEach(() => {
      deviceSerial = 'serial1';
      const mockDeviceNotes = newMockDeviceNoteList(deviceSerial);
      activatedRouteSpy = new ActivatedRouteStub({});
      tfcClientSpy = jasmine.createSpyObj('tfcClient', {
        getDeviceInfo: observableOf({}),
        getDeviceNotes: observableOf(mockDeviceNotes),
      });
      userServiceSpy = jasmine.createSpyObj('userService', {
        isAdmin: false,
        isMyLab: observableOf(true),
        isAdminOrMyLab: observableOf(true),
      });
      setupModule({
        imports: [
          NotesModule,
          NoopAnimationsModule,
          RouterTestingModule,
        ],
        summaries: [NotesModuleNgSummary],
        providers: [
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: ActivatedRoute, useValue: activatedRouteSpy},
          {provide: UserService, useValue: userServiceSpy},
        ],
      });
    });

    it.async('can render device note list correctly', async () => {
      bootstrapTemplate(
          `<note-list  [id]="id" [noteType]="noteType"></note-list>`,
          {id: deviceSerial, noteType});
      await env.verifyState(`note-list_device_notes`, 'note-list');
    });

    it.async('can render empty device note list', async () => {
      const mockDeviceNotes = {
        notes: [],
        next_cursor: '',
        prev_cursor: '',
      };
      tfcClientSpy.getDeviceNotes.and.returnValue(
          observableOf(mockDeviceNotes));
      bootstrapTemplate(
          `<note-list  [id]="id" [noteType]="noteType"></note-list>`,
          {id: deviceSerial, noteType});
      await env.verifyState(`note-list_device_notes_empty`, 'note-list');
    });
  });

  describe('Host noteList', () => {
    let hostname: string;
    const noteType: NoteType = NoteType.HOST;

    beforeEach(() => {
      hostname = 'hostname';
      const mockHostNotes = newMockHostNoteList(hostname);
      activatedRouteSpy = new ActivatedRouteStub({});
      tfcClientSpy = jasmine.createSpyObj('tfcClient', {
        getHostInfo: observableOf({}),
        getHostNotes: observableOf(mockHostNotes),
      });
      userServiceSpy = jasmine.createSpyObj('userService', {
        isAdmin: false,
        isMyLab: observableOf(true),
        isAdminOrMyLab: observableOf(true),
      });
      setupModule({
        imports: [
          NotesModule,
          NoopAnimationsModule,
          RouterTestingModule,
        ],
        summaries: [NotesModuleNgSummary],
        providers: [
          {provide: TfcClient, useValue: tfcClientSpy},
          {provide: ActivatedRoute, useValue: activatedRouteSpy},
          {provide: UserService, useValue: userServiceSpy},
        ],
      });
    });

    it.async('can render host note list correctly', async () => {
      bootstrapTemplate(
          `<note-list  [id]="id" [noteType]="noteType"></note-list>`,
          {id: hostname, noteType});
      await env.verifyState(`note-list_host_notes`, 'note-list');
    });

    it.async('can render empty host note list', async () => {
      const mockHostNotes = {
        notes: [],
        next_cursor: '',
        prev_cursor: '',
      };
      tfcClientSpy.getHostNotes.and.returnValue(observableOf(mockHostNotes));
      bootstrapTemplate(
          `<note-list  [id]="id" [noteType]="noteType"></note-list>`,
          {id: hostname, noteType});
      await env.verifyState(`note-list_host_notes_empty`, 'note-list');
    });
  });
});
