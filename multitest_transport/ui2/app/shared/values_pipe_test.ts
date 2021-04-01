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

import {ValuesPipe} from './values_pipe';

describe('ValuesPipe', () => {
  it('can list the values in the dict', () => {
    const pipe = new ValuesPipe();
    const dict = {key1: 'value1', key2: 'value2'};
    expect(pipe.transform(dict)).toEqual(['value1', 'value2']);
  });
  it('can handle an empty dict', () => {
    const pipe = new ValuesPipe();
    const dict = {};
    expect(pipe.transform(dict)).toEqual([]);
  });
});
