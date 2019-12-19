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

import {HttpResponse} from '@angular/common/http';
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {PartialObserver} from 'rxjs';

import {CouldNotStartUploadProcessError, FileUploadService} from './file_upload_service';

describe('FileUploadService', () => {
  const expectedLocationUrl = 'http://localhost/location';

  let observer: jasmine.SpyObj<PartialObserver<unknown>>;
  let uploadService: FileUploadService;
  let httpTestingController: HttpTestingController;
  beforeEach(() => {
    observer = jasmine.createSpyObj('observer', ['next', 'error', 'complete']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [FileUploadService],
    });
    // Keeping it compatible with Angular 8.
    // tslint:disable-next-line:deprecation
    httpTestingController = TestBed.get(HttpTestingController);
    // tslint:disable-next-line:deprecation
    uploadService = TestBed.get(FileUploadService);
  });

  describe('startUploadProcess', () => {
    const expectedUrl = 'http://localhost/_ah';
    beforeEach(() => {
      uploadService.startUploadProcess(expectedUrl).subscribe(observer);
    });

    it('thorw error on invalid response', () => {
      const req = httpTestingController.expectOne(
          req => req.method === 'POST' && req.url === expectedUrl);
      req.flush(null, {headers: {}});
      expect(observer.error)
          .toHaveBeenCalledWith(
              new CouldNotStartUploadProcessError(new HttpResponse()));
    });

    it('returns the correct location url on valid response', () => {
      const req = httpTestingController.expectOne(
          req => req.method === 'POST' && req.url === expectedUrl);
      req.flush(null, {headers: {location: expectedLocationUrl}});
      expect(observer.next).toHaveBeenCalledWith(expectedLocationUrl);
    });
  });

  describe('uploadChunk', () => {
    it('should return correct progress on successful upload', () => {
      const content = 'hello world';
      const buffer = new TextEncoder().encode(content);

      uploadService.uploadChunk(buffer, 0, expectedLocationUrl, content.length)
          .subscribe(observer);
      httpTestingController.expectOne(expectedLocationUrl).flush(null);
      expect(observer.next)
          .toHaveBeenCalledWith({type: 'complete', uploaded: content.length});
    });
  });
});
