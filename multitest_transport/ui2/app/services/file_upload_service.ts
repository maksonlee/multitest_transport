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

import {HttpClient} from '@angular/common/http';
import {HttpResponse} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {EMPTY, Observable, of as observableOf} from 'rxjs';
import {catchError, expand, map, switchMap} from 'rxjs/operators';

import {FileReaderService} from './file_reader_service';

/**
 * The GCS API returns this status code (which usually means Permanent
 * Redirect) when uploading a part of a file.
 */
const INCOMPLETE_UPLOAD_STATUS_CODE = 308;

/** File Upload Service  */
@Injectable({
  providedIn: 'root',
})
export class FileUploadService {
  constructor(
      private readonly http: HttpClient,
      private readonly fileReaderService: FileReaderService) {}

  /**
   * Start a upload process
   * @param url  A url for uploading a file (e.g.
   * /_ah/gcs/app_default_bucket/data/local_file_store/urllib_test.py)
   */
  startUploadProcess(url: string) {
    return this.http
        .post<never>(url, undefined, {
          observe: 'response',
        })
        .pipe(map(response => {
          /**
           * Location Url allow one know where the file will reside
           * Sample location url:  https://storage.googleapis.com//app_default
           * _bucket/data/local_file_store/urllib_test.py?upload_id=encoded_
           * gs_file%3AYXBwX2RlZmF1bHRfYnVja2V0L2RhdGEvbG9
           */
          let location = response.headers.get('location') ||
              response.headers.get('Location');
          if (!location) throw new CouldNotStartUploadProcessError(response);
          location =
              location.replace('https://storage.googleapis.com/', '/_ah/gcs');
          return location;
        }));
  }

  /**
   * Upload File
   * @param file The file to upload
   * @param location The location of where the file should be upload to
   * @return An Observable of FileUploadEvent
   */
  uploadFile(file: File, location: string): Observable<FileUploadEvent> {
    const initialFileUploadEvent = {type: 'progress', uploaded: 0} as
        FileUploadEvent;
    return observableOf<FileUploadEvent>(initialFileUploadEvent)
        .pipe(
            expand(uploadEvent => {
              if (uploadEvent.type === 'complete') {
                return EMPTY;
              }
              return this.readChunkAndUploadIt(
                  file, location, uploadEvent.uploaded);
            }),
        );
  }

  /**
   * Read a file in chunks and upload the file chunk by chunk
   * @param file The File to be read and uploaded
   * @param location The location of where the file to be uploaded to
   * @param offset The offset of where the file needs to be read and upload
   * @return An Observable of FileUploadEvent
   */
  readChunkAndUploadIt(file: File, location: string, offset: number) {
    return this.fileReaderService.readChunk(file, offset)
        .pipe(switchMap(
            chunk => this.uploadChunk(chunk, offset, location, file.size)));
  }

  /**
   * Upload the readed chunk as ArrayBuffer
   * @param chunk The chunk of data to be uploaded
   * @param offset Offset of where the chunk is located in file
   * @param location Location of where the chunk should be upload to
   * @param totalSize TotalSize of the file
   */
  uploadChunk(
      chunk: ArrayBuffer, offset: number, location: string,
      totalSize: number): Observable<FileUploadEvent> {
    const headers: {[header: string]: string} = {};
    // Zero-byte files can't have a content range header
    if (chunk.byteLength > 0) {
      const end = offset + chunk.byteLength - 1;
      const eof = (end + 1 === totalSize);
      const headerContent = `bytes ${offset}-${end}/${eof ? totalSize : '*'}`;
      headers['Content-Range'] = headerContent;
    }
    return this.http
        .put(location, chunk, {
          headers,
          observe: 'response',
        })
        .pipe(
            map<HttpResponse<unknown>, FileUploadComplete>(response => {
              return {type: 'complete', uploaded: totalSize};
            }),
            catchError((response: HttpResponse<never>) => {
              // HttpClient treats 308 as an error, while GCS uses this status
              // code for incomplete uploads.
              if (response.status !== INCOMPLETE_UPLOAD_STATUS_CODE) {
                throw response;
              }
              const uploaded = offset + chunk.byteLength - 1;
              return observableOf<FileUploadProgress>({
                type: 'progress',
                uploaded,
              });
            }),
        );
  }
}

/**
 * A CouldNotStartUploadProcessError Class
 * This error is thrown if a upload process can't be started
 */
export class CouldNotStartUploadProcessError extends Error {
  constructor(readonly response: HttpResponse<never>) {
    super();
    this.response = response;
  }
}

/**
 * File Upload Events
 */
export type FileUploadEvent = FileUploadProgress|FileUploadComplete;

/**
 * A sub event of FileUploadEvent containing information of uploaded progress
 */
export interface FileUploadProgress {
  type: 'progress';
  uploaded: number;
}

/**
 * A sub event of FileUploadEvent containing information of complete status
 */
export interface FileUploadComplete {
  type: 'complete';
  uploaded: number;
}
