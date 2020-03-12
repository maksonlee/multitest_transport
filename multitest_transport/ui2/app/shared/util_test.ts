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

import 'jasmine';

import {isFnmatchPattern} from './util';

describe('isFnmatchPattern', () => {
  it('should behave correctly on valid input', () => {
    expect(isFnmatchPattern('')).toBe(false);
    expect(isFnmatchPattern('folder')).toBe(false);
    expect(isFnmatchPattern('folder/fodler2')).toBe(false);
    expect(isFnmatchPattern('folder/fodler2/fodler3')).toBe(false);
    expect(isFnmatchPattern('*')).toBe(true);
    expect(isFnmatchPattern('/*')).toBe(true);
    expect(isFnmatchPattern('*/*')).toBe(true);
    expect(isFnmatchPattern('folder/*.img')).toBe(true);
    expect(isFnmatchPattern('folder/*.*img')).toBe(true);
    expect(isFnmatchPattern('folder/folder/*.*img')).toBe(true);
    expect(isFnmatchPattern('folder/folder/?img')).toBe(true);
    expect(isFnmatchPattern('folder/folder/[123]img')).toBe(true);
    expect(isFnmatchPattern('folder/folder/[img')).toBe(false);
    expect(isFnmatchPattern('folder/folder/img]')).toBe(false);
    expect(isFnmatchPattern('folder/folder/\img]')).toBe(false);
    expect(isFnmatchPattern('folder/folder/\\\\\img]')).toBe(false);
    expect(isFnmatchPattern('folder/folder/[*]')).toBe(true);
  });
});
