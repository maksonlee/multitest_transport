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

import {TestBed} from '@angular/core/testing';
import {DomSanitizer} from '@angular/platform-browser';

import {LinkifyPipe} from './linkify_pipe';

describe('LinkifyPipe', () => {
  let pipe: LinkifyPipe;

  beforeEach(() => {
    const sanitizer = TestBed.inject(DomSanitizer);
    pipe = new LinkifyPipe(sanitizer);
  });

  it('ignores values without URLs', () => {
    expect(pipe.transform(undefined)).toBe('');
    expect(pipe.transform('')).toBe('');
    expect(pipe.transform('hello world')).toBe('hello world');
  });

  it('converts URLs into anchor elements', () => {
    // single URL
    expect(pipe.transform('http://www.test.com'))
        .toBe(
            '<a href="http://www.test.com" target="_blank">' +
            'http://www.test.com</a>');
    // URL surrounded by text
    expect(pipe.transform('hello http://www.test.com world'))
        .toBe(
            'hello <a href="http://www.test.com" target="_blank">' +
            'http://www.test.com</a> world');
    // multiple URLs
    expect(pipe.transform('http://www.test.com https://www.google.com'))
        .toBe(
            '<a href="http://www.test.com" target="_blank">' +
            'http://www.test.com</a> <a href="https://www.google.com" ' +
            'target="_blank">https://www.google.com</a>');
  });

  it('sanitizes the value while keeping brackets', () => {
    expect(pipe.transform('<a href="test">test</a>'))
        .toBe('&lt;a href=&#34;test&#34;&gt;test&lt;/a&gt;');
  });
});
