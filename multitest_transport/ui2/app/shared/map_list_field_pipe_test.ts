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

import {MapListFieldPipe} from './map_list_field_pipe';

declare interface TestObject {
  field1?: string;
  field2?: string;
}

describe('MapListFieldPipe', () => {
  let pipe: MapListFieldPipe;
  let obj1: TestObject;
  let obj2: TestObject;
  let objMissingData: TestObject;

  beforeEach(() => {
    obj1 = {field1: 'abc', field2: 'def'};
    obj2 = {field1: 'ghi', field2: 'jkl'};
    objMissingData = {field2: 'mno'};

    pipe = new MapListFieldPipe();
  });

  it('returns the correct values', () => {
    const objList = [obj1, obj2];
    expect(pipe.transform(objList, 'field1')).toEqual(['abc', 'ghi']);
    expect(pipe.transform(objList, 'field2')).toEqual(['def', 'jkl']);
  });

  it('handles missing data', () => {
    const objListMissingData = [obj1, objMissingData, obj2];
    expect(pipe.transform(objListMissingData, 'field1')).toEqual([
      'abc', undefined, 'ghi'
    ]);
    expect(pipe.transform(objListMissingData, 'field2')).toEqual([
      'def', 'mno', 'jkl'
    ]);
  });

  it('handles a null list', () => {
    expect(pipe.transform(null, '')).toEqual([]);
  });
});
