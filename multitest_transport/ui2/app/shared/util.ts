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

// This util file will include helper functions used across mtt ui2
import {HttpErrorResponse} from '@angular/common/http';
import {ElementRef} from '@angular/core';
import * as moment from 'moment';

// A custom interface for moment-duration-format.
interface Duration extends moment.Duration {
  // tslint:disable-next-line:no-any
  format(template: string, precision?: string, settings?: any): string;
}

/**
 * Convert string array to string
 *
 * @param arr: a string array
 * @param delimiter: a delimiter for connecting string
 * @return a string by connecting array from delimiter
 */
export function arrayToString(arr: string[], delimiter: string) {
  arr = arr || [];
  return arr.join(delimiter);
}

/**
 * Assert whether obj is defined or not
 *
 * @param obj: any object type
 * @param fieldName: name of the object you are asserting
 * @param componentName: name of the component this object resides in
 */
export function assertRequiredInput(
    obj: unknown, fieldName: string, componentName: string) {
  if (obj === undefined) {
    throw new Error(`[${fieldName}] is a required field in ${componentName}`);
  }
}

/** Create a continuous number array */
export function continuousNumberArray(length: number, prefix = 0): number[] {
  return Array.from<number>({length}).map((unused, i) => i + prefix);
}

/** Returns a deep copy of the specified value. */
export function deepCopy<T>(value: T): T {
  return value && JSON.parse(JSON.stringify(value)) as T;
}

const FNMATCH_PATTERN = /(\*|\?|\[.*\])/;
/**
 * Check whether the user provided text is a pattern that fnmatch would
 * match or not
 *
 * Supported syntax: https://docs.python.org/2/library/fnmatch.html
 */
export const isFnmatchPattern = (s: string) => FNMATCH_PATTERN.test(s);

/**
 * Convert milliseconds to a time duration in format HHH:MM:SS
 */
export function millisToDuration(millis?: number): string {
  if (millis || millis === 0) {
    return (moment.duration(millis) as Duration).format('hh:mm:ss', undefined, {
      trim: false
    });
  }
  return '';
}

/** Scroll to the first element in the ElementRef List */
export function navigateToFirstElement(inputs: ElementRef[]) {
  if (!inputs || !inputs.length) {
    return;
  }
  inputs[0].nativeElement.scrollIntoView({behavior: 'smooth', block: 'center'});
}

/** Noop function to ignore awaiting promises */
export function noAwait(result: {then: Function}) {}

/** Reloads the page after an optional delay (milliseconds) */
export async function reloadPage(delayMs?: number) {
  if (delayMs) {
    await sleep(delayMs);
  }
  window.location.reload();
}

/**
 * Mark all steps (optionally starting from a given index) as incomplete.
 * This function is used across stepper.
 */
export function resetStepCompletion(
    startingIndex: number = 0,
    stepCompletionStatusMap: {[stepIndex: number]: boolean},
    totalSteps: number) {
  for (let i = startingIndex; i < totalSteps; i++) {
    stepCompletionStatusMap[i] = false;
  }
}

/** Returns a promise that resolves after the given time in milliseconds */
export function sleep(ms: number) {
  return new Promise(resolve => {
    setTimeout(resolve, ms);
  });
}

/** Return an array with unique values. */
export function distinctArray<T>(source: T[]): T[] {
  return [...new Set(source)];
}

/**
 * Return the messages contained in HttpErrorResponse if there's any
 */
export function buildApiErrorMessage(errorResponse: HttpErrorResponse) {
  // Endpoint error
  const error = errorResponse.error && errorResponse.error.error;
  if (error) {
    try {
      const errorObj = JSON.parse(error.message);
      return {
        message: errorObj['message'],
        stacktrace: formatStackTrace(errorObj['stacktrace'])
      };
    } catch {
      return {message: error.message};
    }
  }
  // If endpoint didn't raise an exception, display the general error message
  return {message: errorResponse.message};
}

function formatStackTrace(stackTraces: string[][]) {
  return stackTraces.reduce((acc: string, entry: string[]) => {
    return acc +
        `File ${entry[0]}, line ${entry[1]}, in ${entry[2]}, ${entry[3]}\n`;
  }, `Traceback (most recent call last):\n`);
}

/**
 * Gets the value by key in a key value object({key:key,value:value}) array.
 */
export function getKeyValue(source: KeyValuePair[], key: string): string {
  const keyValue = source.find((x: KeyValuePair) => x.key === key);
  return keyValue ? keyValue.value : '';
}

/**
 * An interface that includes key and value properties.
 */
export declare interface KeyValuePair {
  readonly key: string;
  readonly value: string;
}
