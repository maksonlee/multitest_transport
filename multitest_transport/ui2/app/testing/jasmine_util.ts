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
 * Find a child HTML element that matches a CSS selector or throw an exception.
 *
 * el: element to query from
 * selector: CSS selector
 */
export function getEl<T extends Element = HTMLElement>(
    el: DebugElement, selector: string): T {
  return el.query(By.css(selector)).nativeElement;
}

/**
 * Find all child HTML elements that match a CSS selector.
 *
 * el: element to query from
 * selector: CSS selector
 */
export function getEls<T extends Element = HTMLElement>(
    el: DebugElement, selector: string): T[] {
  return el.queryAll(By.css(selector)).map(e => e.nativeElement);
}

/**
 * Check whether any child HTML element matches a CSS selector.
 *
 * el: element to query from
 * selector: CSS selector
 */
export function hasEl(el: DebugElement, selector: string): boolean {
  return getEls(el, selector).length > 0;
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
