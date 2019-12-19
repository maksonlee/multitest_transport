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

import {HttpEvent, HttpHandler, HttpInterceptor, HttpParameterCodec, HttpParams, HttpRequest} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

/** Applies strict parameter encoding. */
@Injectable()
export class StrictParamsInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<{}>, next: HttpHandler):
      Observable<HttpEvent<{}>> {
    const params = new HttpParams(
        {encoder: new StrictParameterCodec(), fromObject: toMap(req.params)});
    return next.handle(req.clone({params}));
  }
}

/** Converts parameters to an object. */
function toMap(params: HttpParams): {[key: string]: string[]} {
  const map: {[key: string]: string[]} = {};
  for (const key of params.keys()) {
    map[key] = params.getAll(key)!;
  }
  return map;
}

/**
 * Encode parameters using a stricter approach than Angular's default codec.
 * https://github.com/angular/angular/blob/5ae9b76a9b/packages/common/http/src/params.ts#L81-L92
 */
class StrictParameterCodec implements HttpParameterCodec {
  encodeKey = (key: string) => encodeURIComponent(key);
  encodeValue = (value: string) => encodeURIComponent(value);
  decodeKey = (key: string) => decodeURIComponent(key);
  decodeValue = (value: string) => decodeURIComponent(value);
}
