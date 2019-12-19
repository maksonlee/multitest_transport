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

import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MatDialog} from '@angular/material/dialog';

import {initTestRunConfig, Test, TestRunConfig} from '../services/mtt_models';
import {assertRequiredInput} from '../shared/util';
import {TestRunConfigEditor, TestRunConfigEditorData} from './test_run_config_editor';

/**
 * A list to display test run config information with create and edit buttons.
 */
@Component({
  selector: 'test-run-config-list',
  styleUrls: ['test_run_config_list.css'],
  templateUrl: './test_run_config_list.ng.html',
})
export class TestRunConfigList implements OnInit {
  @Input() data: TestRunConfig[] = [];
  @Input() testMap: {[id: string]: Test} = {};
  @Output() dataChange = new EventEmitter();

  constructor(private readonly matDialog: MatDialog) {}

  ngOnInit() {
    assertRequiredInput(this.testMap, 'testMap', 'test-run-config-list');
  }

  add() {
    this.openTestRunConfigEditor();
  }

  edit(index: number) {
    this.openTestRunConfigEditor(index);
  }

  delete(index: number) {
    this.data.splice(index, 1);
    this.dataChange.emit(this.data);
  }

  private openTestRunConfigEditor(
      index?: number,
  ) {
    // If index is given, edit that config. Otherwise add a new config.
    const editMode = typeof index !== 'undefined';
    const testRunConfig = editMode ? this.data[index!] : initTestRunConfig();
    const testRunConfigEditorData: TestRunConfigEditorData = {
      editMode,
      testMap: this.testMap,
      testRunConfig,
    };

    const dialogRef = this.matDialog.open(TestRunConfigEditor, {
      width: '1200px',
      height: '600px',
      panelClass: 'no-padding-container',
      data: testRunConfigEditorData
    });

    dialogRef.componentInstance.configSubmitted.subscribe(
        (result: TestRunConfig) => {
          if (editMode) {
            this.data[index!] = result;
          } else {
            this.data.push(result);
          }
          this.dataChange.emit(this.data);
        });
  }
}
