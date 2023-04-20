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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {getEl} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';

import {Point} from '../device/device';

import {ClickAction} from './action';
import {AoaActionEditor} from './action_editor';
import {EditorModule} from './editor_module';

describe('AoaActionEditor', () => {
  let dialogRef: jasmine.SpyObj<MatDialogRef<AoaActionEditor>>;
  let dialogData: string;

  let fixture: ComponentFixture<AoaActionEditor>;
  let element: DebugElement;
  let component: AoaActionEditor;

  beforeEach(() => {
    dialogRef = jasmine.createSpyObj<MatDialogRef<AoaActionEditor>>(['close']);

    TestBed.configureTestingModule({
      imports: [EditorModule, NoopAnimationsModule],
      providers: [
        {provide: MatDialogRef, useValue: dialogRef},
        {provide: MAT_DIALOG_DATA, useFactory: () => dialogData},
      ],
    });
  });

  /** Initializes the dialog component with input data. */
  function initComponent(data: string) {
    dialogData = data;
    fixture = TestBed.createComponent(AoaActionEditor);
    element = fixture.debugElement;
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  it('should parse command and arguments on init', () => {
    initComponent('write hello world');
    expect(component.valid).toBeTrue();
    expect(component.command).toEqual('write');
    expect(component.arguments).toEqual('hello world');
  });

  it('should default to click if command is invalid', () => {
    initComponent('invalid hello world');
    expect(component.valid).toBeFalse();
    expect(component.command).toEqual('click');
    expect(component.arguments).toEqual('hello world');
  });

  it('should close dialog when save button is clicked', () => {
    initComponent('click 123 456');
    expect(component.valid).toBeTrue();
    getEl(element, '.save').click();
    expect(dialogRef.close).toHaveBeenCalledWith({
      action: new ClickAction(new Point(123, 456)),
      execute: false,
    });
  });

  it('should close dialog when save and execute button is clicked', () => {
    initComponent('click 123 456');
    expect(component.valid).toBeTrue();
    getEl(element, '.save-execute').click();
    expect(dialogRef.close).toHaveBeenCalledWith({
      action: new ClickAction(new Point(123, 456)),
      execute: true,
    });
  });

  it('should disable save buttons if action is invalid', () => {
    initComponent('click 123');
    expect(component.valid).toBeFalse();
    expect(getEl<HTMLButtonElement>(element, '.save').disabled).toBeTrue();
    expect(getEl<HTMLButtonElement>(element, '.save-execute').disabled)
        .toBeTrue();
  });
});
