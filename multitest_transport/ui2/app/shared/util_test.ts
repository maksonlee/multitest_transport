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

import {areArraysEqual, getFilterDefaultSingleValue, isFnmatchPattern, removeFirst} from './util';

describe('areArraysEqual', () => {
  const obj1 = {};
  const obj2 = {};

  it('should return true if the arrays are equal', () => {
    expect(areArraysEqual([obj1], [obj1])).toBe(true);
  });
  it('should return false if the arrays reference different objects', () => {
    expect(areArraysEqual([obj1], [obj2])).toBe(false);
  });
});

describe('removeFirst', () => {
  it('removes first instance of an element from an array', () => {
    const array = [1, 2, 3, 4, 3];
    // Removes first instance only if multiple are present.
    expect(removeFirst(array, 3)).toBeTrue();
    expect(array).toEqual([1, 2, 4, 3]);
    expect(removeFirst(array, 3)).toBeTrue();
    expect(array).toEqual([1, 2, 4]);
    // No-op if element is not present in the array.
    expect(removeFirst(array, 3)).toBeFalse();
    expect(array).toEqual([1, 2, 4]);
  });
});


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
    expect(isFnmatchPattern('folder/folder/img]')).toBe(false);
    expect(isFnmatchPattern('folder/folder/\\\\img]')).toBe(false);
    expect(isFnmatchPattern('folder/folder/[*]')).toBe(true);
  });
});

describe('getFilterDefaultSingleValue', () => {
  const options = ['lab-1', 'lab-2', 'lab-3'];

  it('should return urlParam when the urlParam and storedParam are specified',
     () => {
       const urlParam = 'lab-2';
       const storedParam = 'lab-3';
       const result =
           getFilterDefaultSingleValue(options, urlParam, storedParam);
       expect(result).toEqual(urlParam);
     });

  it('should return urlParam when the urlParam and storedParam are ' +
         'specified and the urlParam is All',
     () => {
       const urlParam = 'All';
       const storedParam = 'lab-3';
       const result =
           getFilterDefaultSingleValue(options, urlParam, storedParam);
       expect(result).toEqual(urlParam);
     });

  it('should return storedParam when the urlParam and storedParam are ' +
         'specified but urlParam value is invalid',
     () => {
       const urlParam = 'All';
       const storedParam = 'lab-3';
       const hasAllOption = false;
       const result = getFilterDefaultSingleValue(
           options, urlParam, storedParam, hasAllOption);
       expect(result).toEqual('lab-3');
     });

  it('should return first option when the urlParam is specified with invalid ' +
         'value',
     () => {
       const urlParam = 'All';
       const storedParam = '';
       const hasAllOption = false;
       const result = getFilterDefaultSingleValue(
           options, urlParam, storedParam, hasAllOption);
       expect(result).toEqual('lab-1');
     });

  it('should return storedParam when the storedParam is specified', () => {
    const storedParam = 'lab-3';
    const result = getFilterDefaultSingleValue(options, '', storedParam);
    expect(result).toEqual(storedParam);
  });

  it('should return storedParam when the storedParam is specified with All', () => {
    const storedParam = 'All';
    const result = getFilterDefaultSingleValue(options, '', storedParam);
    expect(result).toEqual(storedParam);
  });

  it('should return first option when the storedParam is specified with '+
         'invalid value', () => {
    const storedParam = 'lab-4';
    const hasAllOption = false;
    const result =
        getFilterDefaultSingleValue(options, '', storedParam, hasAllOption);
    expect(result).toEqual('lab-1');
  });
});
