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
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf} from 'rxjs';

import {FeedbackService} from '../services/feedback_service';
import {NoteType, SurveyTrigger} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {PredefinedMessagesResponse, PredefinedMessageType} from '../services/tfc_models';
import {newMockDeviceNote, newMockHostNote, newMockPredefinedMessage, newMockPredefinedMessagesResponse} from '../testing/mtt_lab_mocks';

import {NoteDialogParams, NoteDialogState} from './notes_dialog';
import {NotesEditor} from './notes_editor';
import {NotesModule} from './notes_module';

describe('NotesEditor', () => {
  const offlineReasonValue = 'offline1';
  const recoveryActionValue = 'recovery1';
  const messageValue = 'message text';

  let feedbackService: jasmine.SpyObj<FeedbackService>;
  let params: NoteDialogParams;
  let notesEditor: NotesEditor;
  let notesEditorFixture: ComponentFixture<NotesEditor>;
  let tfcClient: jasmine.SpyObj<TfcClient>;
  let el: DebugElement;

  beforeEach(() => {
    feedbackService = jasmine.createSpyObj('feedbackService', ['startSurvey']);
    params = {
      dialogState: NoteDialogState.EDITOR,
      ids: ['target1', 'target2'],
      labName: 'lab 1',
      noteType: NoteType.HOST,
    };
    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        NotesModule,
      ],
      providers: [
        {provide: FeedbackService, useValue: feedbackService},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });
  });

  describe('When edit note type is host', () => {
    beforeEach(() => {
      params = {
        dialogState: NoteDialogState.EDITOR,
        ids: ['target1', 'target2'],
        labName: 'lab 1',
        noteType: NoteType.HOST,
      };
    });

    it('initializes a component', () => {
      tfcClient = jasmine.createSpyObj('tfcClient', {
        'batchCreateOrUpdateDevicesNotesWithPredefinedMessage':
            observableOf({}),
        'batchCreateOrUpdateHostsNotesWithPredefinedMessage': observableOf({}),
        'batchGetDeviceNotes': observableOf({}),
        'batchGetHostNotes': observableOf({}),
        'createOrUpdateNote': observableOf({}),
        'getPredefinedMessages': observableOf({}),
      });

      TestBed.overrideProvider(TfcClient, {useValue: tfcClient});

      notesEditorFixture = TestBed.createComponent(NotesEditor);
      notesEditor = notesEditorFixture.componentInstance;
      notesEditor.params = params;
      el = notesEditorFixture.debugElement;
      notesEditorFixture.detectChanges();

      expect(notesEditor).toBeTruthy();
    });

    it('should get note info correctly', () => {
      const targetId = ['host1'];

      notesEditor.forms.setValue({
        offlineReasonFormControl: offlineReasonValue,
        recoveryActionFormControl: recoveryActionValue,
        messageFormControl: messageValue,
      });

      const notesInfo =
          notesEditor.getBatchCreateOrUpdateNotesInfo(targetId, NoteType.HOST);

      expect(notesInfo.notes[0].hostname).toBe(targetId[0]);
      expect(notesInfo.offline_reason).toBe(offlineReasonValue);
      expect(notesInfo.recovery_action).toBe(recoveryActionValue);
      expect(notesInfo.message).toBe(messageValue);
    });

    it('should loads existed host note correctly', () => {
      const noteId = 123;
      notesEditor.params.noteType = NoteType.HOST;
      notesEditor.loadExitedNoteData(params.ids[0], noteId);
      expect(tfcClient.batchGetHostNotes).toHaveBeenCalledTimes(1);
    });

    it('should loads existed device note correctly', () => {
      const noteId = 123;
      notesEditor.params.noteType = NoteType.DEVICE;
      notesEditor.loadExitedNoteData(params.ids[0], noteId);
      expect(tfcClient.batchGetDeviceNotes).toHaveBeenCalledTimes(1);
    });

    it('should set input fields value with existed note data correctly', () => {
      const noteId = 123;

      // Set input fields from device note data.
      const deviceNote = newMockDeviceNote(noteId);
      notesEditor.setDefaultValue(deviceNote);

      expect(notesEditor.forms.get('offlineReasonFormControl')!.value)
          .toEqual(deviceNote.offline_reason);
      expect(notesEditor.forms.get('recoveryActionFormControl')!.value)
          .toEqual(deviceNote.recovery_action);
      expect(notesEditor.forms.get('messageFormControl')!.value)
          .toEqual(deviceNote.message);

      // Set input fields from host note data.
      const hostNote = newMockHostNote(noteId);
      notesEditor.setDefaultValue(hostNote);

      expect(notesEditor.forms.get('offlineReasonFormControl')!.value)
          .toEqual(hostNote.offline_reason);
      expect(notesEditor.forms.get('recoveryActionFormControl')!.value)
          .toEqual(hostNote.recovery_action);
      expect(notesEditor.forms.get('messageFormControl')!.value)
          .toEqual(hostNote.message);
    });

    it('should save device/host notes correctly when predefinedMessage exists',
       () => {
         notesEditor.forms.setValue({
           offlineReasonFormControl: offlineReasonValue,
           recoveryActionFormControl: recoveryActionValue,
           messageFormControl: messageValue,
         });
         notesEditor.offlineReasons = [
           newMockPredefinedMessage(
               1, undefined, PredefinedMessageType.DEVICE_OFFLINE_REASON,
               offlineReasonValue, undefined, undefined),
         ];
         notesEditor.recoveryActions = [
           newMockPredefinedMessage(
               2, undefined, PredefinedMessageType.DEVICE_RECOVERY_ACTION,
               recoveryActionValue, undefined, undefined),
         ];
         notesEditor.params.noteType = NoteType.DEVICE;
         notesEditor.saveNotes();
         expect(tfcClient.batchCreateOrUpdateDevicesNotesWithPredefinedMessage)
             .toHaveBeenCalledTimes(1);

         notesEditor.offlineReasons = [
           newMockPredefinedMessage(
               1, undefined, PredefinedMessageType.HOST_OFFLINE_REASON,
               offlineReasonValue, undefined, undefined),
         ];
         notesEditor.recoveryActions = [
           newMockPredefinedMessage(
               2, undefined, PredefinedMessageType.HOST_RECOVERY_ACTION,
               recoveryActionValue, undefined, undefined),
         ];
         notesEditor.params.noteType = NoteType.HOST;
         notesEditor.saveNotes();
         expect(tfcClient.batchCreateOrUpdateHostsNotesWithPredefinedMessage)
             .toHaveBeenCalledTimes(1);
       });

    it('should loads offline reasons correctly', () => {
      const messageType = PredefinedMessageType.HOST_OFFLINE_REASON;
      const predefinedMessagesResponse =
          newMockPredefinedMessagesResponse(messageType);
      params.noteType = NoteType.HOST;
      bootstrapNoteType(params, predefinedMessagesResponse);

      expect(tfcClient.getPredefinedMessages).toHaveBeenCalledTimes(2);
      expect(tfcClient.getPredefinedMessages)
          .toHaveBeenCalledWith(params.labName, messageType);
      expect(notesEditor.offlineReasons)
          .toEqual(predefinedMessagesResponse.predefined_messages!);
    });

    it('should loads recovery actions correctly', () => {
      const messageType = PredefinedMessageType.HOST_RECOVERY_ACTION;
      const predefinedMessagesResponse =
          newMockPredefinedMessagesResponse(messageType);
      params.noteType = NoteType.HOST;
      bootstrapNoteType(params, predefinedMessagesResponse);

      expect(tfcClient.getPredefinedMessages).toHaveBeenCalledTimes(2);
      expect(tfcClient.getPredefinedMessages)
          .toHaveBeenCalledWith(params.labName, messageType);
      expect(notesEditor.recoveryActions)
          .toEqual(predefinedMessagesResponse.predefined_messages!);
    });
  });

  describe('When edit note type is device', () => {
    beforeEach(() => {
      params = {
        dialogState: NoteDialogState.EDITOR,
        ids: ['device1', 'device2'],
        deviceHostMap:
            [['device1', 'host1'], ['device2', 'host1'], ['device3', 'host2']],
        labName: 'lab 1',
        noteType: NoteType.DEVICE,
      };
    });

    it('should get notes info correctly', () => {
      notesEditorFixture = TestBed.createComponent(NotesEditor);
      notesEditor = notesEditorFixture.componentInstance;
      notesEditor.params = params;
      el = notesEditorFixture.debugElement;
      notesEditorFixture.detectChanges();

      notesEditor.forms.setValue({
        offlineReasonFormControl: offlineReasonValue,
        recoveryActionFormControl: recoveryActionValue,
        messageFormControl: messageValue,
      });

      const deviceSerials = ['device2'];
      const devicesNotesInfo = notesEditor.getBatchCreateOrUpdateNotesInfo(
          deviceSerials, NoteType.DEVICE);
      expect(devicesNotesInfo.notes[0].device_serial).toBe(deviceSerials[0]);
      expect(devicesNotesInfo.offline_reason).toBe(offlineReasonValue);
      expect(devicesNotesInfo.recovery_action).toBe(recoveryActionValue);
      expect(devicesNotesInfo.message).toBe(messageValue);

      const hostnames = ['host1'];
      const hostsNotesInfo =
          notesEditor.getBatchCreateOrUpdateNotesInfo(hostnames, NoteType.HOST);
      expect(hostsNotesInfo.notes[0].hostname).toBe(hostnames[0]);
      expect(hostsNotesInfo.offline_reason).toBe(offlineReasonValue);
      expect(hostsNotesInfo.recovery_action).toBe(recoveryActionValue);
      expect(hostsNotesInfo.message).toBe(messageValue);
    });

    it('should loads offline reasons correctly', () => {
      const messageType = PredefinedMessageType.DEVICE_OFFLINE_REASON;
      const predefinedMessagesResponse =
          newMockPredefinedMessagesResponse(messageType);

      params.noteType = NoteType.DEVICE;
      bootstrapNoteType(params, predefinedMessagesResponse);

      expect(tfcClient.getPredefinedMessages).toHaveBeenCalledTimes(2);
      expect(tfcClient.getPredefinedMessages)
          .toHaveBeenCalledWith(params.labName, messageType);
      expect(notesEditor.offlineReasons)
          .toEqual(predefinedMessagesResponse.predefined_messages!);
    });

    it('should loads recovery actions correctly', () => {
      const messageType = PredefinedMessageType.DEVICE_RECOVERY_ACTION;
      const predefinedMessagesResponse =
          newMockPredefinedMessagesResponse(messageType);
      params.noteType = NoteType.DEVICE;
      bootstrapNoteType(params, predefinedMessagesResponse);

      expect(tfcClient.getPredefinedMessages).toHaveBeenCalledTimes(2);
      expect(tfcClient.getPredefinedMessages)
          .toHaveBeenCalledWith(params.labName, messageType);
      expect(notesEditor.recoveryActions)
          .toEqual(predefinedMessagesResponse.predefined_messages!);
    });

    it('should call notes editor HaTS correctly', () => {
      bootstrapNoteType(params);
      notesEditor.startSurvey();
      expect(feedbackService.startSurvey)
          .toHaveBeenCalledWith(SurveyTrigger.NOTES_EDITOR);
    });

    it('should get hostname from deviceHostMap correctly', () => {
      const deviceHostMap = notesEditor.params.deviceHostMap![2];
      const deviceSerial = deviceHostMap[0];
      const hostname = notesEditor.getHostnameFromDeviceHostMap(deviceSerial);
      expect(hostname).toEqual(deviceHostMap[1]);
    });
  });

  it('should add event time correctly', () => {
    notesEditor.addEventTime();
    expect(notesEditor.eventDateTime).toBeDefined();
    expect(notesEditor.eventDateTimeFormControl.value).toBeDefined();
    expect(notesEditor.eventDateTimeFormControl.dirty).toBeTrue();
  });

  it('should update event time correctly', () => {
    notesEditor.updateEventTime();
    expect(notesEditor.eventDateTime).toBeDefined();
    expect(notesEditor.eventDateTimeFormControl.value).toBeDefined();
    expect(notesEditor.eventDateTimeFormControl.dirty).toBeTrue();
  });

  it('should edit event time correctly', () => {
    notesEditor.editEventTime();
    expect(notesEditor.isEditEventDate).toBeTrue();
  });

  it('should remove event time correctly', () => {
    notesEditor.removeEventTime();
    expect(notesEditor.isEditEventDate).toBeFalse();
    expect(notesEditor.eventDateTime).toBeUndefined();
    expect(notesEditor.eventDateTimeFormControl.value).toEqual('');
    expect(notesEditor.eventDateTimeFormControl.dirty).toBeTrue();
  });

  function bootstrapNoteType(
      params: NoteDialogParams, response: PredefinedMessagesResponse = {}) {
    tfcClient = jasmine.createSpyObj(
        'tfcClient', ['getPredefinedMessages', 'createOrUpdateNote']);
    tfcClient.getPredefinedMessages.and.returnValue(observableOf(response));
    TestBed.overrideProvider(TfcClient, {useValue: tfcClient});

    notesEditorFixture = TestBed.createComponent(NotesEditor);
    notesEditor = notesEditorFixture.componentInstance;
    notesEditor.params = params;
    notesEditorFixture.detectChanges();
  }
});
