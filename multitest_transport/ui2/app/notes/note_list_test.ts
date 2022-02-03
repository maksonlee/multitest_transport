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

import {DebugElement} from '@angular/core';
import {ComponentFixture, inject, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {Router} from '@angular/router';
import {ActivatedRoute} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {DEFAULT_PAGE_SIZE} from 'google3/third_party/py/multitest_transport/ui2/app/shared/paginator';
import {getEl} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {of as observableOf} from 'rxjs';

import {NoteType} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {NoteType as TfcNoteType} from '../services/tfc_models';
import {UserService} from '../services/user_service';
import {ActivatedRouteStub} from '../testing/activated_route_stub';
import {newMockDeviceNoteList, newMockHostNoteList} from '../testing/mtt_lab_mocks';

import {NoteList} from './note_list';
import {NoteDialogParams, NoteDialogState} from './notes_dialog';
import {NotesModule} from './notes_module';

describe('Device noteList', () => {
  const id = 'serial01';
  const mockDeviceNotes = newMockDeviceNoteList(id);
  const params: NoteDialogParams = {
    dialogState: NoteDialogState.LIST,
    ids: [id],
    labName: 'labName1',
    noteType: NoteType.DEVICE,
  };

  let hostInfosSpy: jasmine.Spy;
  let noteList: NoteList;
  let noteListFixture: ComponentFixture<NoteList>;
  let routerSpy: jasmine.SpyObj<Router>;
  let userServiceSpy: jasmine.SpyObj<UserService>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;

  beforeEach(() => {
    const activatedRouteSpy = new ActivatedRouteStub({});
    tfcClient =
        jasmine.createSpyObj('tfcClient', ['getDeviceNotes', 'getDeviceInfo']);
    hostInfosSpy =
        tfcClient.getDeviceNotes.and.returnValue(observableOf(mockDeviceNotes));
    routerSpy = jasmine.createSpyObj(
        'Router', ['navigateByUrl', 'navigate', 'createUrlTree']);
    routerSpy.createUrlTree.and.returnValue({});
    tfcClient.getDeviceInfo.and.returnValue(observableOf({}));

    userServiceSpy = jasmine.createSpyObj('userService', {
      isAdmin: true,
      isMyLab: observableOf(true),
      isAdminOrMyLab: observableOf(true),
    });

    TestBed.configureTestingModule({
      imports: [
        NotesModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: TfcClient, useValue: tfcClient},
        {provide: Router, useValue: routerSpy},
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: UserService, useValue: userServiceSpy},
      ],
    });

    noteListFixture = TestBed.createComponent(NoteList);
    noteList = noteListFixture.componentInstance;
    el = noteListFixture.debugElement;
    noteList.id = id;
    noteList.noteType = NoteType.DEVICE;
    noteList.noteList = mockDeviceNotes.notes!;
    noteListFixture.detectChanges();
  });

  afterEach(() => {
    noteListFixture.destroy();
  });

  it('should get initialized correctly', () => {
    expect(noteList).toBeTruthy();
  });

  it('should call the tfc client api method getDeviceNotes and getDeviceInfo correctly',
     async () => {
       await noteListFixture.whenStable();
       expect(tfcClient.getDeviceNotes).toHaveBeenCalledTimes(1);
       expect(tfcClient.getDeviceInfo).toHaveBeenCalledTimes(1);
     });

  it('can load previous page of device note', () => {
    noteList.id = id;
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    noteList.loadNoteList(-1);
    expect(tfcClient.getDeviceNotes)
        .toHaveBeenCalledWith(id, [], DEFAULT_PAGE_SIZE, 'prev', true);
  });

  it('can load next page of device note', () => {
    noteList.id = id;
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    noteList.loadNoteList(1);
    expect(tfcClient.getDeviceNotes)
        .toHaveBeenCalledWith(id, [], DEFAULT_PAGE_SIZE, 'next', false);
  });

  it('can handle page size change', () => {
    noteList.id = id;
    noteList.nextPageToken = 'next';
    noteList.paginator.changePageSize(20);
    expect(tfcClient.getDeviceNotes)
        .toHaveBeenCalledWith(id, [], 20, undefined, false);
  });

  it('should trigger addNote on add note button click', () => {
    spyOn(noteList, 'editNote');
    getEl(el, '.note-list-add-note-button').click();
    expect(noteList.editNote).toHaveBeenCalledTimes(1);
  });


  describe('add notes button', () => {
    it('should display correct aria-label and tooltip', () => {
      const addNoteButton = getEl(el, '.note-list-add-note-button');
      expect(addNoteButton).toBeTruthy();
      expect(addNoteButton.getAttribute('aria-label')).toBe('Add notes');
      expect(addNoteButton.getAttribute('mattooltip')).toBe('Add notes');
    });
  });

  it('can update pagination parameters', inject([Router], (router: Router) => {
       tfcClient.getDeviceNotes.and.returnValue(observableOf(
           {device_notes: [], prev_cursor: 'prev', next_cursor: 'next'}));
       noteList.loadDeviceNoteList();
       expect(noteList.prevPageToken).toEqual('prev');
       expect(noteList.nextPageToken).toEqual('next');
       expect(noteList.paginator.hasPrevious).toBe(true);
       expect(noteList.paginator.hasNext).toBe(true);
       expect(router.createUrlTree).toHaveBeenCalledWith([], {
         queryParams: {
           notePageToken: 'prev',
           notePageSize: null,
         },
         queryParamsHandling: 'merge',
       });
     }));

  it('should open note dialog on addNote called', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    noteList.openEditor();
    expect(dialog.open).toHaveBeenCalled();
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });

  it('should be hide include device notes checkbox', () => {
    expect(document.querySelector('.include-device-notes')).toBeNull();
  });
});

describe('Host noteList', () => {
  const id = 'hostname';
  const mockHostNotes = newMockHostNoteList(id);
  const params: NoteDialogParams = {
    dialogState: NoteDialogState.LIST,
    ids: [id],
    labName: 'labName1',
    noteType: NoteType.HOST,
  };

  let noteList: NoteList;
  let noteListFixture: ComponentFixture<NoteList>;
  let notifierSpy: jasmine.SpyObj<Notifier>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let routerSpy: jasmine.SpyObj<Router>;
  let el: DebugElement;

  beforeEach(() => {
    const activatedRouteSpy = new ActivatedRouteStub({});

    tfcClient = jasmine.createSpyObj('tfcClient', {
      'batchDeleteDeviceNotes': observableOf({}),
      'batchDeleteHostNotes': observableOf({}),
      'getHostNotes': observableOf(mockHostNotes),
      'getHostInfo': observableOf({}),
    });

    routerSpy = jasmine.createSpyObj(
        'Router', ['navigateByUrl', 'navigate', 'createUrlTree']);
    routerSpy.createUrlTree.and.returnValue({});

    notifierSpy = jasmine.createSpyObj('notifier', {
      confirm: observableOf(true),  // mock confirm click in dialog.
      showMessage: observableOf({}),
      showError: observableOf({}),
    });

    TestBed.configureTestingModule({
      imports: [
        NotesModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        {provide: ActivatedRoute, useValue: activatedRouteSpy},
        {provide: Notifier, useValue: notifierSpy},
        {provide: Router, useValue: routerSpy},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });

    noteListFixture = TestBed.createComponent(NoteList);
    noteList = noteListFixture.componentInstance;
    el = noteListFixture.debugElement;
    noteList.id = id;
    noteList.noteType = NoteType.HOST;
    noteList.noteList = mockHostNotes.notes!;
    noteListFixture.detectChanges();
  });

  afterEach(() => {
    noteListFixture.destroy();
  });

  it('should call the tfc client api method getHostNotes and getHostInfo correctly',
     async () => {
       await noteListFixture.whenStable();
       expect(tfcClient.getHostNotes).toHaveBeenCalledTimes(1);
       expect(tfcClient.getHostInfo).toHaveBeenCalledTimes(1);
     });

  it('can update pagination parameters', inject([Router], (router: Router) => {
       tfcClient.getHostNotes.and.returnValue(observableOf(
           {host_notes: [], prev_cursor: 'prev', next_cursor: 'next'}));
       noteList.loadHostNoteList();
       expect(noteList.prevPageToken).toEqual('prev');
       expect(noteList.nextPageToken).toEqual('next');
       expect(noteList.paginator.hasPrevious).toBe(true);
       expect(noteList.paginator.hasNext).toBe(true);
       expect(router.createUrlTree).toHaveBeenCalledWith([], {
         queryParams: {
           notePageToken: 'prev',
           notePageSize: null,
         },
         queryParamsHandling: 'merge',
       });
     }));

  it('should open note dialog on addNote called', () => {
    const dialog = TestBed.inject(MatDialog);
    spyOn(dialog, 'open').and.callThrough();
    noteList.openEditor();
    expect(dialog.open).toHaveBeenCalled();
    expect(dialog.open).toHaveBeenCalledTimes(1);
  });

  it('should call getHostNotes when checkbox clicked', () => {
    getEl(el, '.include-device-notes').click();
    expect(tfcClient.getHostNotes).toHaveBeenCalledTimes(1);
  });

  it('call openEditor correctly when calling editNote', () => {
    spyOn(noteList, 'openEditor');
    const noteType = TfcNoteType.HOST_NOTE;
    const hostname = 'host1';
    const deviceSerial = 'device1';
    const noteId = 5;
    const expectType = NoteType.HOST;
    const expectId = hostname;

    noteList.editNote(noteId, hostname, deviceSerial, noteType);

    expect(noteList.openEditor)
        .toHaveBeenCalledWith(noteId, expectId, expectType);
  });

  it('should remove host notes correctly', () => {
    spyOn(noteList, 'removeHostNotes').and.callThrough();
    const hostname = 'host1';
    const notesId = 1;
    const noteType = TfcNoteType.HOST_NOTE;
    noteList.removeNote(notesId, noteType, hostname);
    expect(noteList.removeHostNotes).toHaveBeenCalledWith(hostname, notesId);
  });

  it('should call tfcCleint batchDeleteHostNotes on removeHostNotes called',
     () => {
       const hostname = 'host1';
       const notesId = 1;
       noteList.removeHostNotes(hostname, notesId);
       expect(tfcClient.batchDeleteHostNotes).toHaveBeenCalled();
     });

  it('should remove device notes correctly', () => {
    spyOn(noteList, 'removeDeviceNotes');
    const hostname = 'host1';
    const notesId = 1;
    const noteType = TfcNoteType.DEVICE_NOTE;
    const deviceSerial = 'device1';

    noteList.removeNote(notesId, noteType, hostname, deviceSerial);
    expect(noteList.removeDeviceNotes)
        .toHaveBeenCalledWith(deviceSerial, notesId);
  });

  it('should call tfcCleint batchDeleteDeviceNotes on removeDeviceNotes called',
     () => {
       const notesId = 1;
       const deviceSerial = 'device1';
       noteList.removeDeviceNotes(deviceSerial, notesId);
       expect(tfcClient.batchDeleteDeviceNotes).toHaveBeenCalled();
     });

  it('returns prevPageToken when getPageToken(-1)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(-1)).toEqual(noteList.prevPageToken);
  });

  it('returns nextPageToken when getPageToken(1)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(1)).toEqual(noteList.nextPageToken);
  });

  it('returns undefined when getPageToken(0)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(0)).toBeUndefined();
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(-1, true)).toEqual(noteList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(1, true)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(1, true)).toEqual(noteList.prevPageToken);
  });

  it('returns prevPageToken when getPageToken(-1, true)', () => {
    noteList.prevPageToken = 'prev';
    noteList.nextPageToken = 'next';
    expect(noteList.getPageToken(0, true)).toEqual(noteList.prevPageToken);
  });

  it('calls the getHostNotes api when the refresh button clicked', () => {
    tfcClient.getHostNotes.calls.reset();
    getEl(el, '.refresh-button').click();
    expect(tfcClient.getHostNotes)
        .toHaveBeenCalledWith(
            id, [], noteList.paginator.pageSize, '', false, true);
  });
});
