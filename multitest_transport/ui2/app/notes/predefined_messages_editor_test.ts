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

import {HttpErrorResponse} from '@angular/common/http';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_DIALOG_DATA, MatLegacyDialog, MatLegacyDialogRef} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {of as observableOf, throwError} from 'rxjs';

import {CreatePredefinedMessageInfo, MessageCategory, MessageType} from '../services/mtt_lab_models';
import {TfcClient} from '../services/tfc_client';
import {PredefinedMessageType} from '../services/tfc_models';
import {newMockPredefinedMessage} from '../testing/mtt_lab_mocks';

import {NotesModule} from './notes_module';
import {PredefinedMessagesEditor, PredefinedMessagesEditorAction, PredefinedMessagesEditorDialogParams} from './predefined_messages_editor';


describe('PredefinedMessagesEditor', () => {
  let dialogRefSpy: jasmine.SpyObj<MatLegacyDialogRef<PredefinedMessagesEditor>>;
  let predefinedMessagesEditor: PredefinedMessagesEditor;
  let predefinedMessagesEditorFixture:
      ComponentFixture<PredefinedMessagesEditor>;
  const id = 123;
  const lab = 'OOO Lab';

  const dialogParams: PredefinedMessagesEditorDialogParams = {
    predefinedMessage: newMockPredefinedMessage(id),
    defaultMessageCategory: MessageCategory.HOST,
    defaultMessageType: MessageType.RECOVERY_ACTION,
    defaultLab: lab,
  };

  let tfcClient: jasmine.SpyObj<TfcClient>;

  beforeEach(() => {
    dialogRefSpy = jasmine.createSpyObj<MatLegacyDialogRef<PredefinedMessagesEditor>>(
        'dialogRefSpy', ['close']);
    tfcClient = jasmine.createSpyObj(
        'tfcClient', ['createPredefinedMessage', 'updatePredefinedMessage']);
    tfcClient.createPredefinedMessage.and.returnValue(observableOf({}));
    tfcClient.updatePredefinedMessage.and.returnValue(observableOf({}));

    TestBed.configureTestingModule({
      imports: [
        NoopAnimationsModule,
        NotesModule,
      ],
      providers: [
        {provide: MAT_DIALOG_DATA, useValue: {...dialogParams}},
        {provide: MatLegacyDialogRef, useValue: dialogRefSpy},
        {provide: TfcClient, useValue: tfcClient},
      ],
    });

    predefinedMessagesEditorFixture =
        TestBed.createComponent(PredefinedMessagesEditor);
    predefinedMessagesEditor =
        predefinedMessagesEditorFixture.componentInstance;
    predefinedMessagesEditorFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(predefinedMessagesEditor).toBeTruthy();

    // Determines is create mode or edit mode.
    expect(predefinedMessagesEditor.action)
        .toEqual(PredefinedMessagesEditorAction.UPDATE);

    // Sets category value on init.
    expect(
        predefinedMessagesEditor.forms.get('messageCategoryFormControl')!.value)
        .toEqual(MessageCategory.HOST);

    // Sets type value on init.
    expect(predefinedMessagesEditor.forms.get('messageTypeFormControl')!.value)
        .toEqual(MessageType.RECOVERY_ACTION);

    // Sets lab id on init.
    expect(predefinedMessagesEditor.selectedLab).toEqual(lab);
  });

  it('should close dialog correctly', () => {
    predefinedMessagesEditor.closeEditorDialog();
    expect(dialogRefSpy.close).toHaveBeenCalledTimes(1);
  });

  it('should get current predefinedMessageType currectly', () => {
    // DEVICE_OFFLINE_REASON
    dialogParams.defaultMessageCategory = MessageCategory.DEVICE;
    dialogParams.defaultMessageType = MessageType.OFFLINE_REASON;
    predefinedMessagesEditor.setDefaultValue(dialogParams);
    expect(predefinedMessagesEditor.getCurrentPredefinedMessageType())
        .toEqual(PredefinedMessageType.DEVICE_OFFLINE_REASON);

    // DEVICE_RECOVERY_ACTION
    dialogParams.defaultMessageType = MessageType.RECOVERY_ACTION;
    predefinedMessagesEditor.setDefaultValue(dialogParams);
    expect(predefinedMessagesEditor.getCurrentPredefinedMessageType())
        .toEqual(PredefinedMessageType.DEVICE_RECOVERY_ACTION);

    // HOST_OFFLINE_REASON
    dialogParams.defaultMessageCategory = MessageCategory.HOST;
    dialogParams.defaultMessageType = MessageType.OFFLINE_REASON;
    predefinedMessagesEditor.setDefaultValue(dialogParams);
    expect(predefinedMessagesEditor.getCurrentPredefinedMessageType())
        .toEqual(PredefinedMessageType.HOST_OFFLINE_REASON);

    // HOST_RECOVERY_ACTION
    dialogParams.defaultMessageType = MessageType.RECOVERY_ACTION;
    predefinedMessagesEditor.setDefaultValue(dialogParams);
    expect(predefinedMessagesEditor.getCurrentPredefinedMessageType())
        .toEqual(PredefinedMessageType.HOST_RECOVERY_ACTION);
  });

  it('should create predefined message correctly', () => {
    predefinedMessagesEditor.params.predefinedMessage = undefined;
    predefinedMessagesEditor.save();

    const predefinedMessageInfo: CreatePredefinedMessageInfo = {
      labName: predefinedMessagesEditor.forms.get('labFormControl')!.value,
      predefinedMessageType: PredefinedMessageType.HOST_RECOVERY_ACTION,
      content: predefinedMessagesEditor.forms.get('contentFormControl')!.value,
    };

    expect(tfcClient.createPredefinedMessage).toHaveBeenCalledTimes(1);
    expect(tfcClient.createPredefinedMessage)
        .toHaveBeenCalledWith(predefinedMessageInfo);
  });

  it('can show error when createPredefinedMessage returns 409', () => {
    const dialog = TestBed.inject(MatLegacyDialog);
    spyOn(dialog, 'open').and.callThrough();

    const errorResponse = new HttpErrorResponse({
      'error': {
        'error': {
          'code': 409,
        }
      }
    });

    tfcClient.createPredefinedMessage.and.returnValue(
        throwError(errorResponse));

    predefinedMessagesEditor.params.predefinedMessage = undefined;
    predefinedMessagesEditor.save();

    expect(dialog.open).toHaveBeenCalled();
  });

  it('should update predefined message correctly', () => {
    predefinedMessagesEditor.save();

    expect(tfcClient.updatePredefinedMessage).toHaveBeenCalledTimes(1);
    expect(tfcClient.updatePredefinedMessage)
        .toHaveBeenCalledWith(id, dialogParams.predefinedMessage!.content);
  });

  it('can show error when updatePredefinedMessage returns 404, 409', () => {
    const dialog = TestBed.inject(MatLegacyDialog);
    const dialogSpy = spyOn(dialog, 'open').and.callThrough();
    const errorCodes = [404, 409];

    for (const code of errorCodes) {
      dialogSpy.calls.reset();
      const errorResponse = new HttpErrorResponse({
        'error': {
          'error': {
            'code': code,
          }
        }
      });

      tfcClient.updatePredefinedMessage.and.returnValue(
          throwError(errorResponse));
      predefinedMessagesEditor.save();
      expect(dialog.open).toHaveBeenCalledTimes(1);
    }
  });
});
