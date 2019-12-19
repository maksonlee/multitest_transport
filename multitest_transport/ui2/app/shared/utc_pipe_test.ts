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

import {UtcPipe} from './utc_pipe';

describe('UtcPipe', () => {
  let pipe: UtcPipe;

  beforeEach(() => {
    pipe = new UtcPipe();
  });

  it('can recognize invalid values', () => {
    expect(pipe.transform(undefined)).toBeUndefined();
    expect(pipe.transform('')).toBeUndefined();
    expect(pipe.transform(0)).toEqual(new Date(0));
  });

  it('does not modify date objects', () => {
    const date = new Date(1995, 12, 17, 3, 24, 0);
    expect(pipe.transform(date)).toEqual(date);
  });

  it('uses existing timezone', () => {
    const date = new Date('December 17, 1995 03:24:00 PST');
    expect(pipe.transform('1995-12-17T03:24:00-08:00')).toEqual(date);
  });

  it('uses GMT by default', () => {
    const date = new Date('December 17, 1995 03:24:00 GMT');
    expect(pipe.transform('1995-12-17T03:24:00')).toEqual(date);
  });
});
