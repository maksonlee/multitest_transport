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

import {joinPath} from '../services/file_service';
import {BuildChannel, TestResourceDef, TestResourceObj} from '../services/mtt_models';
import {FormChangeTracker} from '../shared/can_deactivate';
import {assertRequiredInput} from '../shared/util';

import {BuildPicker, BuildPickerData, BuildPickerTabState} from './build_picker';

/** Class of test resources being used in this form */
export enum TestResourceClassType {
  TEST_RESOURCE_DEF = 'TestResourceDef',
  TEST_RESOURCE_OBJ = 'TestResourceObj',
}

/**
 * Form for Test Resource Definition
 */
@Component({
  selector: 'test-resource-form',
  styleUrls: ['test_resource_form.css'],
  templateUrl: './test_resource_form.ng.html',
  providers: [{provide: FormChangeTracker, useExisting: TestResourceForm}]
})
export class TestResourceForm extends FormChangeTracker implements OnInit {
  @Input() data!: TestResourceObj[]|TestResourceDef[];
  @Input() buildChannels!: BuildChannel[];
  @Input() options: string[] = [];
  @Input() testResourceClassType!: TestResourceClassType;
  @Input() canAdd = true;
  @Input() canDelete = true;

  @Output() addTestResource = new EventEmitter();
  @Output() removeTestResource = new EventEmitter<number>();

  // Whenever an event fired such as add or remove, it will set this value to
  // true
  hasContentChanged = false;

  ngOnInit() {
    assertRequiredInput(this.data, 'data', 'test-resource-form');
    assertRequiredInput(
        this.testResourceClassType, 'testResourceClassType',
        'test-resource-form');
    assertRequiredInput(
        this.buildChannels, 'buildChannels', 'test-resource-form');
  }

  constructor(public dialog: MatDialog) {
    super();
  }

  openBuildPicker(testResource: TestResourceObj|TestResourceDef) {
    const urlComponent = this.decodeUrl(this.getUrl(testResource));

    const data: BuildPickerData = {
      searchBarUrlValue: urlComponent.searchBarUrlValue,
      searchBarFilenameValue: urlComponent.searchBarFilenameValue,
      buildChannelId: urlComponent.buildChannelId,
      buildChannels: this.buildChannels
    };
    const dialogRef = this.dialog.open(BuildPicker, {
      width: '800px',
      panelClass: 'build-picker-container',
      data
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        testResource = this.setUrl(testResource, this.encodeUrl(result));
      }
    });
  }

  decodeUrl(url?: string) {
    let buildChannelId = '';
    let searchBarUrlValue = '';
    let searchBarFilenameValue = '';
    if (!url) {
      return {buildChannelId, searchBarUrlValue, searchBarFilenameValue};
    }
    const m = url.match(/mtt:\/\/\/([^\/]+)\/(.*)/i);
    // Web url won't match
    if (!m) {
      return {
        buildChannelId,
        searchBarUrlValue: url,
        searchBarFilenameValue,
      };
    }
    // For all other case, it will be started with mtt:///
    buildChannelId = m[1];
    const path = m[2];
    // Find last unescaped slash
    const idx = path.lastIndexOf('/');
    if (idx === -1) {
      // No path, only filename
      searchBarFilenameValue = decodeURIComponent(path);
    } else {
      searchBarUrlValue = path.substring(0, idx);
      searchBarFilenameValue = decodeURIComponent(path.substring(idx + 1));
    }
    return {searchBarUrlValue, searchBarFilenameValue, buildChannelId};
  }

  encodeUrl(state: BuildPickerTabState) {
    if (state.searchBarFilenameValue) {
      return joinPath(
          state.searchBarUrlValue,
          encodeURIComponent(state.searchBarFilenameValue));
    }
    // Web url don't have filename
    return state.searchBarUrlValue;
  }

  getUrl(testResource: TestResourceDef|TestResourceObj): string|undefined {
    if (this.isDef(testResource)) {
      return testResource.default_download_url;
    } else {
      return testResource.url;
    }
  }

  setUrl(testResource: TestResourceDef|TestResourceObj, url: string):
      TestResourceDef|TestResourceObj {
    if (this.isDef(testResource)) {
      testResource.default_download_url = url;
    } else {
      testResource.url = url;
    }
    return testResource;
  }

  isDef(testResource: TestResourceDef|
        TestResourceObj): testResource is TestResourceDef {
    return this.testResourceClassType ===
        TestResourceClassType.TEST_RESOURCE_DEF;
  }

  isFormDirty(): boolean {
    return super.isFormDirty() || this.hasContentChanged;
  }

  resetForm() {
    super.resetForm();
    this.hasContentChanged = false;
  }
}
