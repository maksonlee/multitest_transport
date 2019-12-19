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

import {finalize} from 'rxjs/operators';

import {newMockFile} from '../testing/test_util';

import {FileReaderService} from './file_reader_service';

describe('FileReaderService', () => {
  const FILE = newMockFile('hello world', 'test.txt');

  it('should read entire file', (done) => {
    const reader = new FileReaderService();
    reader.readChunk(FILE)
        .pipe(finalize(done))
        .subscribe(
            chunk => {
              expect(new TextDecoder().decode(chunk)).toEqual('hello world');
            },
            error => {
              fail(`Unexpected error: ${error}`);
            },
        );
  });

  it('should read a chunk from a file', (done) => {
    const reader = new FileReaderService();
    reader.readChunk(FILE, 6)
        .pipe(finalize(done))
        .subscribe(
            chunk => {
              expect(new TextDecoder().decode(chunk)).toEqual('world');
            },
            error => {
              fail(`Unexpected error: ${error}`);
            },
        );
  });

  it('should handle errors', (done) => {
    // tslint:disable-next-line:no-any replace FileReader for testing
    spyOn(window as any, 'FileReader').and.returnValue(new FailingFileReader());

    const reader = new FileReaderService();
    reader.readChunk(FILE)
        .pipe(finalize(done))
        .subscribe(
            chunk => {
              fail(`Unexpected chunk: ${chunk}`);
            },
            error => {
              expect(error).toBeDefined();
            },
        );
  });
});

// File reader which will always have an error.
class FailingFileReader extends FileReader {
  get error() {
    return new DOMException();
  }
}
