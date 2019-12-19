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

import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

const MAX_CHUNK_SIZE = 16 * 1024 * 1024;  // 16MB
const DEFAULT_OFFSET = 0;

/** Allows reading a file in chunks. */
@Injectable({providedIn: 'root'})
export class FileReaderService {
  /**
   * Read one chunk from a file.
   * @param file file to read from
   * @param offset position from where to begin reading
   */
  readChunk(file: File, offset = DEFAULT_OFFSET) {
    return new Observable<ArrayBuffer>((subscriber) => {
      const chunk = file.slice(offset, offset + MAX_CHUNK_SIZE);
      const reader = new FileReader();
      reader.onloadend = () => {
        if (reader.error) {
          subscriber.error(reader.error);
        } else {
          subscriber.next(reader.result as ArrayBuffer);
          subscriber.complete();
        }
      };
      reader.readAsArrayBuffer(chunk);
    });
  }
}
