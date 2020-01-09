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

import {convertToParamMap, ParamMap, Params} from '@angular/router';
import {ReplaySubject} from 'rxjs';

/**
 * An ActivateRoute test double with a `paramMap` observable.
 * Use the `setQueryParamMap()` method to add the next `paramMap` value.
 * https://angular.io/guide/testing#activatedroutestub
 */
export class ActivatedRouteStub {
  /**
   * Uses a ReplaySubject to share previous values with subscribers
   * and pumps new values into the `paramMap` observable.
   */
  private readonly subject = new ReplaySubject<ParamMap>();

  constructor(initialQueryParams?: Params) {
    if (initialQueryParams) {
      this.setQueryParamMap(initialQueryParams);
    }
  }

  /**
   * The mock paramMap observable.
   */
  readonly queryParamMap = this.subject.asObservable();

  /** Sets the paramMap observables's next value. */
  setQueryParamMap(params: Params) {
    this.subject.next(convertToParamMap(params));
  }
}
