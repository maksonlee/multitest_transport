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

import {FileNode, FileService, FileType, joinPath, PROXY_PATH} from './file_service';
import {TestRun} from './mtt_models';
import {CommandAttempt, CommandState} from './tfc_models';
import {AppData} from './app_data';

describe('FileService', () => {
  let http: jasmine.SpyObj<HttpClient>;
  let fs: FileService;

  beforeEach(() => {
    const appData: AppData = {
      fileBrowseUrl: 'browse',
      fileOpenUrl: 'open',
      fileServerRoot: '/root',
    };
    http = jasmine.createSpyObj<HttpClient>(['get', 'put', 'delete']);
    fs = new FileService(appData, http);
  });

  it('can get file URL for active attempts', () => {
    const testRun = {} as TestRun;
    const attempt = {
      command_id: 'command_id',
      attempt_id: 'attempt_id',
      state: CommandState.RUNNING
    } as CommandAttempt;
    const path = 'path/to/file';
    const expected = 'file:///root/tmp/attempt_id/path/to/file';
    expect(fs.getTestRunFileUrl(testRun, attempt, path)).toEqual(expected);
  });

  it('can get file URL for completed attempts', () => {
    const testRun = {output_url: 'output_url'} as TestRun;
    const attempt = {
      command_id: 'command_id',
      attempt_id: 'attempt_id',
      state: CommandState.COMPLETED
    } as CommandAttempt;
    const path = 'path/to/file';
    const expected = 'output_url/command_id/attempt_id/path/to/file';
    expect(fs.getTestRunFileUrl(testRun, attempt, path)).toEqual(expected);
  });

  it('can get file browse URL for absolute file URLs', () => {
    const url = 'file:///root/path/to/file';
    const expected = 'browse/path/to/file';
    expect(fs.getFileBrowseUrl(url)).toEqual(expected);
  });

  it('can get file browse URL for relative file paths', () => {
    const path = 'path/to/file';
    const expected = 'browse/path/to/file';
    expect(fs.getFileBrowseUrl(path)).toEqual(expected);
  });

  it('can get file open URL for absolute file URLs', () => {
    const url = 'file:///root/path/to/file';
    const expected = 'open/path/to/file';
    expect(fs.getFileOpenUrl(url)).toEqual(expected);
  });

  it('can get file open URL for relative file paths', () => {
    const path = 'path/to/file';
    const expected = 'open/path/to/file';
    expect(fs.getFileOpenUrl(path)).toEqual(expected);
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
    const file = new Blob(['test']);
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
    const file = new Blob([]);
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
    const file = new Blob(['test']);
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
    const file = new Blob(['test']);
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
    const file = new Blob(['test']);
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

  it('can delete a file', done => {
    http.delete.and.returnValue(observableOf(null));
    fs.deleteFile('path').subscribe(() => {
      expect(http.delete).toHaveBeenCalledWith(PROXY_PATH + '/file/path');
      done();
    });
  });
});

describe('joinPath', () => {
  it('can handle a single path substring', () => {
    expect(joinPath('one/two')).toBe('one/two');
  });

  it('can handle paths without leading/trailing slashes', () => {
    expect(joinPath('one/two', 'three/four')).toBe('one/two/three/four');
  });

  it('can handle paths with leading/trailing slashes', () => {
    expect(joinPath('one/two/', '/three/four')).toBe('one/two/three/four');
  });
});

/** Custom matcher for testing ArrayBuffer contents. */
function bufferOf(expected: string): jasmine.AsymmetricMatcher<ArrayBuffer> {
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
