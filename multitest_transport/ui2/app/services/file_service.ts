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
import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

/** File server proxy path. */
export const PROXY_PATH = '/fs_proxy';
/** Default upload chunk size. */
export const CHUNK_SIZE = 16 * 1024 * 1024;  // 16MB

/** Performs file operations using a local file server and its proxy. */
@Injectable({providedIn: 'root'})
export class FileService {
  constructor(private readonly http: HttpClient) {}

  /**
   * List all the files in a local directory.
   * @param path directory relative to the file server root
   * @return list of file nodes
   */
  listFiles(path: string): Observable<FileNode[]> {
    return this.http.get<FileNode[]>(`${PROXY_PATH}/dir/${path}`);
  }

  /**
   * Upload a file to local storage.
   * @param file file to upload
   * @param path destination relative to file server root
   * @param chunkSize maximum request size
   * @return upload progress events
   */
  uploadFile(file: File, path: string, chunkSize = CHUNK_SIZE):
      Observable<FileUploadEvent> {
    return new Observable<FileUploadEvent>(observer => {
      const self = this;
      const reader = new FileReader();

      function readChunk(startByte: number) {
        const endByte = startByte + chunkSize;
        const chunk = file.slice(startByte, endByte);

        reader.onloadend = () => {
          if (reader.error) {
            observer.error(reader.error);
            return;
          }
          const data = reader.result as ArrayBuffer;
          self.uploadChunk(path, startByte, file.size, data)
              .subscribe(
                  () => {
                    if (endByte >= file.size) {
                      observer.next(new FileUploadEvent(file, file.size));
                      observer.complete();
                    } else {
                      observer.next(new FileUploadEvent(file, endByte));
                      readChunk(endByte);
                    }
                  },
                  error => {
                    observer.error(error);
                  });
        };

        reader.readAsArrayBuffer(chunk);
      }

      readChunk(0);
      return () => {
        reader.abort();  // Stop reading when unsubscribed
      };
    });
  }

  /** Upload a single file chunk. */
  private uploadChunk(
      path: string, startByte: number, totalSize: number,
      data: ArrayBuffer): Observable<void> {
    const headers: {[header: string]: string} = {};
    // Zero-byte files can't have a content range header
    if (data.byteLength > 0) {
      const endByte = Math.min(totalSize, startByte + data.byteLength) - 1;
      headers['Content-Range'] = `bytes ${startByte}-${endByte}/${totalSize}`;
    }
    return this.http.put<void>(`${PROXY_PATH}/file/${path}`, data, {headers});
  }
}

/** File types. */
export enum FileType {
  DIRECTORY = 'DIRECTORY',  // Directory
  FILE = 'FILE',            // Regular file
  OTHER = 'OTHER',          // Other type (e.g. symlink, special device)
}

/** File node model returned from directory list API. */
// tslint:disable:enforce-name-casing
export interface FileNode {
  path: string;         // Relative file path
  name: string;         // File name
  type: FileType;       // File type
  size: number;         // File size (bytes)
  access_time: number;  // Last access timestamp (epoch millis)
  update_time: number;  // Last update timestamp (epoch millis)
}
// tslint:enable:enforce-name-casing

/** File upload progress event. */
export class FileUploadEvent {
  readonly done: boolean;
  readonly progress: number;

  constructor(readonly file: File, readonly uploaded: number) {
    this.done = uploaded === file.size;
    this.progress = this.done ? 100 : uploaded / Math.max(file.size, 1) * 100;
  }
}
