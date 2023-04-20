/**
 * @license
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

import {Clipboard} from '@angular/cdk/clipboard';
import {DebugElement, SimpleChange} from '@angular/core';
import {ComponentFixture, fakeAsync, flush, TestBed, tick} from '@angular/core/testing';
import {MatDialog, MatDialogRef} from '@angular/material/dialog';
import {MatSnackBar} from '@angular/material/snack-bar';
import {By} from '@angular/platform-browser';
import {getEl, getEls} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {of as observableOf} from 'rxjs';

import {AoaDevice, Key, Point} from '../device/device';
import {FindDeviceDialog} from '../device/find_device_dialog';

import {BackAction, ClickAction, HomeAction, KeyAction, SleepAction, WakeAction, WriteAction} from './action';
import {AoaActionEditor, AoaActionEditorResult} from './action_editor';
import {EditorModule} from './editor_module';
import {ExecutionWakeLock} from './wake_lock';
import {ACTION_DELAY_MILLIS, MAX_KEY_COMBINATION_MILLIS, WorkflowEditor} from './workflow_editor';

/**
 * Set the date returned by new Date() or Date.now() without installing
 * jasmine.clock() which clashes with zone.js.
 * @param timestamp value to set
 */
function mockDate(timestamp: number) {
  jasmine.clock().mockDate(new Date(timestamp));
}

describe('WorkflowEditor', () => {
  let clipboard: jasmine.SpyObj<Clipboard>;
  let dialog: jasmine.SpyObj<MatDialog>;
  let snackBar: jasmine.SpyObj<MatSnackBar>;
  let wakeLock: jasmine.SpyObj<ExecutionWakeLock>;

  let fixture: ComponentFixture<WorkflowEditor>;
  let element: DebugElement;
  let component: WorkflowEditor;

  beforeEach(() => {
    clipboard = jasmine.createSpyObj<Clipboard>(['copy']);
    dialog = jasmine.createSpyObj<MatDialog>(['open']);
    snackBar = jasmine.createSpyObj<MatSnackBar>(['open']);
    wakeLock = jasmine.createSpyObj<ExecutionWakeLock>(['acquire', 'release']);

    TestBed.configureTestingModule({
      imports: [EditorModule],
      providers: [
        {provide: Clipboard, useValue: clipboard},
        {provide: MatDialog, useValue: dialog},
        {provide: MatSnackBar, useValue: snackBar},
        {provide: ExecutionWakeLock, useValue: wakeLock},
      ],
    });

    fixture = TestBed.createComponent(WorkflowEditor);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  describe('device preparation', () => {
    it('should open device when selected', async () => {
      const device = jasmine.createSpyObj<AoaDevice>(['open']);
      await component.ngOnChanges(
          {device: new SimpleChange(undefined, device, true)});
      expect(device.open).toHaveBeenCalled();
      expect(component.device).toEqual(device);
    });

    it('should close device when unselected', async () => {
      const device = jasmine.createSpyObj<AoaDevice>(['close']);
      await component.ngOnChanges(
          {device: new SimpleChange(device, undefined, true)});
      expect(device.close).toHaveBeenCalled();
      expect(component.device).toBeUndefined();
    });

    it('should prompt user and retry if an error occurs', async () => {
      // Create an invalid device which will fail when opened
      const invalidDevice = jasmine.createSpyObj<AoaDevice>(
          ['open'], {serialNumber: 'serialNumber'});
      invalidDevice.open.and.throwError(new Error('Open failed'));
      // Create a valid device which is returned by the find device dialog
      const validDevice = jasmine.createSpyObj<AoaDevice>(['open']);
      const dialogRef =
          jasmine.createSpyObj<MatDialogRef<FindDeviceDialog, AoaDevice>>(
              {afterClosed: observableOf(validDevice)});
      dialog.open.and.returnValue(dialogRef);

      // Pass in the invalid device
      await component.ngOnChanges(
          {device: new SimpleChange(undefined, invalidDevice, true)});
      // User prompted with the selected device's serial number
      expect(dialog.open)
          .toHaveBeenCalledWith(
              FindDeviceDialog,
              jasmine.objectContaining({data: 'serialNumber'}));
      // Valid device prepared and selected
      expect(validDevice.open).toHaveBeenCalled();
      expect(component.device).toEqual(validDevice);
    });
  });

  describe('action management', () => {
    let actionEditor:
        jasmine.SpyObj<MatDialogRef<AoaActionEditor, AoaActionEditorResult>>;

    beforeEach(() => {
      actionEditor = jasmine.createSpyObj<
          MatDialogRef<AoaActionEditor, AoaActionEditorResult>>(
          ['afterClosed']);
      spyOn(component, 'executeActions');
    });

    it('should render the action list', () => {
      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      const actions = getEls(element, '.action');
      expect(actions.length).toEqual(2);
      expect(actions[0].textContent).toContain('wake');
      expect(actions[1].textContent).toContain('back');
    });

    it('should append action when back button is clicked', () => {
      getEl(element, '.buttons .back').click();
      expect(component.actions).toEqual([new BackAction()]);
      expect(component.executeActions).toHaveBeenCalledWith([new BackAction()]);
    });

    it('should append action when home button is clicked', () => {
      getEl(element, '.buttons .home').click();
      expect(component.actions).toEqual([new HomeAction()]);
      expect(component.executeActions).toHaveBeenCalledWith([new HomeAction()]);
    });

    it('should append action when sleep button is clicked', () => {
      getEl(element, '.buttons .sleep-one').click();
      expect(component.actions).toEqual([new SleepAction(1000)]);
      expect(component.executeActions).not.toHaveBeenCalled();
    });

    it('should open action editor if write button is clicked', () => {
      const action = new WriteAction('test');
      dialog.open.and.returnValue(actionEditor);
      actionEditor.afterClosed.and.returnValue(
          observableOf({action, execute: true}));

      getEl(element, '.buttons .write').click();
      expect(dialog.open)
          .toHaveBeenCalledWith(
              AoaActionEditor, jasmine.objectContaining({data: 'write'}));
      expect(component.actions).toEqual([action]);
      expect(component.executeActions).toHaveBeenCalledWith([action]);
    });

    it('should ignore appending if writing is canceled', () => {
      dialog.open.and.returnValue(actionEditor);
      actionEditor.afterClosed.and.returnValue(observableOf(undefined));

      getEl(element, '.buttons .write').click();
      expect(component.actions).toEqual([]);
      expect(component.executeActions).not.toHaveBeenCalled();
    });

    it('should append action when key button is clicked', () => {
      mockDate(Date.now());
      getEl(element, '.buttons .key-up').click();
      expect(component.actions).toEqual([new KeyAction([Key.UP])]);
      expect(component.executeActions).toHaveBeenCalledWith([new KeyAction(
          [Key.UP])]);

      // key is added to the same combination, but only the new key is executed
      getEl(element, '.buttons .key-right').click();
      expect(component.actions).toEqual([new KeyAction([Key.UP, Key.RIGHT])]);
      expect(component.executeActions).toHaveBeenCalledWith([new KeyAction(
          [Key.RIGHT])]);

      // key is appended to a new action if the delay between keys was too long
      mockDate(Date.now() + MAX_KEY_COMBINATION_MILLIS);
      getEl(element, '.buttons .key-down').click();
      expect(component.actions).toEqual([
        new KeyAction([Key.UP, Key.RIGHT]), new KeyAction([Key.DOWN])
      ]);
      expect(component.executeActions).toHaveBeenCalledWith([new KeyAction(
          [Key.DOWN])]);
    });

    it('should append action when a touch screen gesture occurs', () => {
      const action = new ClickAction(new Point(123, 456));
      element.query(By.css('touch-screen'))
          .triggerEventHandler('action', action);
      expect(component.actions).toEqual([action]);
      expect(component.executeActions).toHaveBeenCalledWith([action]);
    });

    it('should open action editor if edit button is clicked', () => {
      const action = new ClickAction(new Point(123, 456));
      dialog.open.and.returnValue(actionEditor);
      actionEditor.afterClosed.and.returnValue(
          observableOf({action, execute: true}));

      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      getEl(element, '.action:first-of-type .edit').click();
      expect(dialog.open)
          .toHaveBeenCalledWith(
              AoaActionEditor, jasmine.objectContaining({data: 'wake'}));
      expect(component.actions).toEqual([action, new BackAction()]);
      expect(component.executeActions).toHaveBeenCalledWith([action]);
    });

    it('should ignore update if editing is canceled', () => {
      dialog.open.and.returnValue(actionEditor);
      actionEditor.afterClosed.and.returnValue(observableOf(undefined));

      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      getEl(element, '.action:first-of-type .edit').click();
      expect(component.actions).toEqual([new WakeAction(), new BackAction()]);
      expect(component.executeActions).not.toHaveBeenCalled();
    });

    it('should delete action when delete button is clicked', () => {
      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      getEl(element, '.action:first-of-type .delete').click();
      expect(component.actions).toEqual([new BackAction()]);
    });
  });

  describe('action execution', () => {
    let device: jasmine.SpyObj<AoaDevice>;

    beforeEach(fakeAsync(() => {
      device = jasmine.createSpyObj<AoaDevice>([
        'isAccessoryMode', 'isConnected', 'sleep', 'wakeUp', 'goBack', 'goHome'
      ]);
      device.isConnected.and.returnValue(true);
      device.sleep.and.callFake((millis) => new Promise((resolve) => {
                                  setTimeout(resolve, millis);
                                }));
      component.device = device;
      component.actions =
          [new WakeAction(), new BackAction(), new HomeAction()];
      fixture.detectChanges();
    }));

    it('should execute all actions when run all button is clicked',
       fakeAsync(() => {
         getEl(element, '.run-all').click();
         // Acquires execution wake lock
         expect(wakeLock.acquire).toHaveBeenCalled();
         expect(wakeLock.release).not.toHaveBeenCalled();
         // Executes first action and waits
         expect(component.executing).toEqual(new WakeAction());
         expect(device.wakeUp).toHaveBeenCalled();
         expect(device.goBack).not.toHaveBeenCalled();
         expect(device.goHome).not.toHaveBeenCalled();
         tick(ACTION_DELAY_MILLIS);
         // Executes second action and waits
         expect(component.executing).toEqual(new BackAction());
         expect(device.goBack).toHaveBeenCalled();
         expect(device.goHome).not.toHaveBeenCalled();
         tick(ACTION_DELAY_MILLIS);
         // Executes last action and releases wake lock
         expect(component.executing).toEqual(undefined);
         expect(device.goHome).toHaveBeenCalled();
         expect(wakeLock.release).toHaveBeenCalled();
       }));

    it('should stop execution when stop button is clicked', fakeAsync(() => {
         getEl(element, '.run-all').click();
         // Starts executing first action and renders the stop button
         expect(component.executing).toEqual(new WakeAction());
         fixture.detectChanges();

         getEl(element, '.stop').click();
         // Stop cancels the delay and prevents any further execution
         expect(() => {
           tick();
         }).toThrowError(/Execution cancelled/);
         expect(component.executing).toEqual(undefined);
         flush();  // Flush the pending delay timer
         expect(device.sleep).toHaveBeenCalledTimes(1);
         expect(device.goBack).not.toHaveBeenCalled();
         expect(device.goHome).not.toHaveBeenCalled();
       }));

    it('should execute an action when run button is clicked', fakeAsync(() => {
         getEl(element, '.action:nth-child(2) .run').click();
         // Executes second action only with no delay
         expect(component.executing).toEqual(new BackAction());
         expect(device.goBack).toHaveBeenCalled();
         tick();
         expect(component.executing).toEqual(undefined);
         expect(device.wakeUp).not.toHaveBeenCalled();
         expect(device.goHome).not.toHaveBeenCalled();
       }));

    it('should execute remaining actions when run from here button is clicked',
       fakeAsync(() => {
         getEl(element, '.action:nth-child(2) .run-from').click();
         // Executes second action and waits
         expect(component.executing).toEqual(new BackAction());
         expect(device.goBack).toHaveBeenCalled();
         tick(ACTION_DELAY_MILLIS);
         // Executes last action and returns
         expect(component.executing).toEqual(undefined);
         expect(device.goHome).toHaveBeenCalled();
         // First action was skipped
         expect(device.wakeUp).not.toHaveBeenCalled();
       }));
  });

  describe('workflow management', () => {
    it('should parse uploaded workflow file', async () => {
      const file = new File(['wake\n', 'back\n'], 'workflow');
      const input = getEl<HTMLInputElement>(element, '.empty input[type=file]');
      // TODO: Wait until b/208710526 is fixed, then remove this autogenerated
      // error suppression.
      //  @ts-ignore(go/unfork-jasmine-typings): Argument of type 'File[]' is
      //  not assignable to parameter of type 'FileList'.
      spyOnProperty(input, 'files').and.returnValue([file]);
      await component.uploadWorkflowFile();
      expect(component.actions).toEqual([new WakeAction(), new BackAction()]);
    });

    it('should parse drag-and-dropped workflow file', async () => {
      const file = new File(['wake\n', 'home\n'], 'workflow');
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      await component.dropWorkflowFile(new DragEvent('drop', {dataTransfer}));
      expect(component.actions).toEqual([new WakeAction(), new HomeAction()]);
    });

    it('should parse copy-pasted workflow', async () => {
      const clipboardData = new DataTransfer();
      clipboardData.setData('text/plain', 'back\nhome\n');
      component.pasteWorkflowData(new ClipboardEvent('paste', {clipboardData}));
      expect(component.actions).toEqual([new BackAction(), new HomeAction()]);
    });

    it('should throw if uploaded workflow is invalid', async () => {
      const file = new File(['invalid\n'], 'workflow');
      const input = getEl<HTMLInputElement>(element, '.empty input[type=file]');
      // TODO: Wait until b/208710526 is fixed, then remove this autogenerated
      // error suppression.
      //  @ts-ignore(go/unfork-jasmine-typings): Argument of type 'File[]' is
      //  not assignable to parameter of type 'FileList'.
      spyOnProperty(input, 'files').and.returnValue([file]);
      await expectAsync(component.uploadWorkflowFile())
          .toBeRejectedWithError(/Unknown command 'invalid'/);
    });

    it('should copy workflow to clipboard when copy button is clicked', () => {
      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      getEl(element, '.copy').click();
      expect(clipboard.copy).toHaveBeenCalledWith('wake\nback');
      expect(snackBar.open).toHaveBeenCalled();
    });

    it('should save workflow to file when save button is clicked', () => {
      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      const downloader = getEl<HTMLAnchorElement>(element, '.save a');
      spyOn(downloader, 'click');
      getEl(element, '.save').click();
      expect(downloader.download).toEqual('workflow');
      expect(downloader.href)
          .toEqual(`data:text/plain;base64,${btoa('wake\nback')}`);
      expect(downloader.click).toHaveBeenCalled();
    });

    it('should clear workflow when clear button is clicked', () => {
      component.actions = [new WakeAction(), new BackAction()];
      fixture.detectChanges();
      getEl(element, '.clear').click();
      expect(component.actions).toEqual([]);
    });
  });
});
