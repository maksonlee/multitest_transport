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

import {DebugElement} from '@angular/core';
import {By} from '@angular/platform-browser';

/**
 * Get an HTMLElement
 *
 * el: DebugElement which we can query from
 * attribute: an attribute string
 *
 * Sample usage: getEl(el, "#deleteButton")
 */
export function getEl(el: DebugElement, attribute: string): HTMLElement {
  return el.query(By.css(attribute)).nativeElement as HTMLElement;
}

/**
 * Get a list of HTMLElement
 *
 * el: DebugElement which we can query from
 * attribute: an attribute string
 *
 * Sample usage: getEls(el, "mat-row")
 */
export function getEls(el: DebugElement, attribute: string): HTMLElement[] {
  return el.queryAll(By.css(attribute))
      .map(e => e.nativeElement as HTMLElement);
}

/**
 * Get text content from DebugElement
 *
 * el: DebugElement
 *
 * Sample usage: getTextContent(el)
 */
export function getTextContent(el: DebugElement): string {
  return el.nativeElement.textContent;
}
