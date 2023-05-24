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

/** A module for notes function. */
import {NgModule} from '@angular/core';
import {ReactiveFormsModule} from '@angular/forms';
import {RouterModule} from '@angular/router';
import {ServicesModule} from 'google3/third_party/py/multitest_transport/ui2/app/services';
import {SharedModule} from 'google3/third_party/py/multitest_transport/ui2/app/shared';

import {AddNotesButton} from './add_notes_button';
import {NoteList} from './note_list';
import {NotesDialog} from './notes_dialog';
import {NotesEditor} from './notes_editor';
import {PredefinedMessageList} from './predefined_message_list';
import {PredefinedMessagesEditor} from './predefined_messages_editor';

const COMPONENTS = [
  AddNotesButton,
  NoteList,
  NotesDialog,
  NotesEditor,
  PredefinedMessageList,
  PredefinedMessagesEditor,
];

@NgModule({
  declarations: COMPONENTS,
  imports: [
    SharedModule,
    ReactiveFormsModule,
    RouterModule,
    ServicesModule,
  ],
  exports: COMPONENTS,
  })
export class NotesModule {
}
