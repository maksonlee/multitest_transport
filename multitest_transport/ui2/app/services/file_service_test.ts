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

import {HttpClient} from '@angular/common/http';
import {of as observableOf, throwError} from 'rxjs';
import {toArray} from 'rxjs/operators';

import {FileNode, FileService, FileType, PROXY_PATH} from './file_service';

describe('FileService', () => {
  let http: jasmine.SpyObj<HttpClient>;
  let fs: FileService;

  beforeEach(() => {
    http = jasmine.createSpyObj<HttpClient>('HttpClient', ['get', 'put']);
    fs = new FileService(http);
  });

  it('can list files in a directory', done => {
    const node: FileNode = {
      path: 'path',
      name: 'name',
      type: FileType.OTHER,
      size: 1,
      access_time: 2,
      update_time: 3,
    };
    http.get.and.returnValue(observableOf([node]));

    fs.listFiles('path').subscribe(result => {
      expect(result).toEqual([node]);
      expect(http.get).toHaveBeenCalledWith(PROXY_PATH + '/dir/path');
      done();
    });
  });

  it('can upload an entire file', done => {
    const file = new File(['test'], 'filename');
    http.put.and.returnValue(observableOf(null));

    fs.uploadFile(file, 'path').pipe(toArray()).subscribe(events => {
      // Sent in a single request
      expect(events.length).toEqual(1);
      expect(events[0].done).toBeTruthy();
      expect(events[0].progress).toEqual(100);
      expect(events[0].uploaded).toEqual(4);  // 4 bytes uploaded
      expect(http.put).toHaveBeenCalledWith(
          PROXY_PATH + '/file/path', bufferOf('test'),
          jasmine.objectContaining(
              {headers: {'Content-Range': 'bytes 0-3/4'}}));
      done();
    });
  });

  it('can upload an empty file', done => {
    const file = new File([''], 'filename');
    http.put.and.returnValue(observableOf(null));

    fs.uploadFile(file, 'path').pipe(toArray()).subscribe(events => {
      // Sent in a single request
      expect(events.length).toEqual(1);
      expect(events[0].done).toBeTruthy();
      expect(events[0].progress).toEqual(100);  // Avoid divide by zero
      expect(events[0].uploaded).toEqual(0);    // No data uploaded
      expect(http.put).toHaveBeenCalledWith(
          PROXY_PATH + '/file/path', bufferOf(''),
          jasmine.objectContaining({headers: {}}));  // No content-range
      done();
    });
  });

  it('can upload a file in chunks', done => {
    const file = new File(['test'], 'filename');
    http.put.and.returnValue(observableOf(null));

    fs.uploadFile(file, 'path', 2).pipe(toArray()).subscribe(events => {
      // Sent in two requests
      expect(events.length).toEqual(2);
      // First sent half the content
      expect(events[0].done).toBeFalsy();
      expect(events[0].progress).toEqual(50);
      expect(events[0].uploaded).toEqual(2);
      expect(http.put).toHaveBeenCalledWith(
          PROXY_PATH + '/file/path', bufferOf('te'),
          jasmine.objectContaining(
              {headers: {'Content-Range': 'bytes 0-1/4'}}));
      // Second has the remaining content
      expect(events[1].done).toBeTruthy();
      expect(events[1].progress).toEqual(100);
      expect(events[1].uploaded).toEqual(4);
      expect(http.put).toHaveBeenCalledWith(
          PROXY_PATH + '/file/path', bufferOf('st'),
          jasmine.objectContaining(
              {headers: {'Content-Range': 'bytes 2-3/4'}}));
      done();
    });
  });

  it('can handle upload errors', done => {
    const file = new File(['test'], 'filename');
    http.put.and.returnValue(throwError(new Error()));

    fs.uploadFile(file, 'path')
        .subscribe(
            event => {
              fail(`Unexpected upload event: ${event}`);
            },
            error => {
              expect(error).toBeDefined();
              done();
            });
  });

  it('can handle read errors', done => {
    const file = new File(['test'], 'filename');
    // tslint:disable-next-line:no-any replace FileReader for testing
    spyOn(window as any, 'FileReader').and.returnValue(new FailingFileReader());

    fs.uploadFile(file, 'path')
        .subscribe(
            event => {
              fail(`Unexpected upload event: ${event}`);
            },
            error => {
              expect(error).toBeDefined();
              done();
            });
  });
});

/** Custom matcher for testing ArrayBuffer contents. */
// google3 local modification: Required for Jasmine typings.
function bufferOf(expected: string): jasmine.AsymmetricMatcher<unknown> {
  return {
    asymmetricMatch: (actual: ArrayBuffer) =>
        new TextDecoder().decode(actual) === expected,
    jasmineToString: () => `<bufferOf(${expected}) matcher>`,
  };
}

/** File reader which will always have an error. */
class FailingFileReader extends FileReader {
  get error() {
    return new DOMException();
  }
}
