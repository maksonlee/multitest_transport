/**
 * @license
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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {getEl} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';

import {Point} from '../device/device';

import {ClickAction, SwipeAction} from './action';
import {EditorModule} from './editor_module';
import {TouchScreen} from './touch_screen';

/**
 * Set the date returned by new Date() or Date.now() without installing
 * jasmine.clock() which clashes with zone.js.
 * @param timestamp value to set
 */
function mockDate(timestamp: number) {
  jasmine.clock().mockDate(new Date(timestamp));
}

describe('TouchScreen', () => {
  let fixture: ComponentFixture<TouchScreen>;
  let element: DebugElement;
  let component: TouchScreen;
  let target: HTMLElement;

  beforeEach(() => {
    mockDate(Date.now());

    TestBed.configureTestingModule({
      imports: [EditorModule],
      });

    fixture = TestBed.createComponent(TouchScreen);
    element = fixture.debugElement;
    target = getEl(element, '.target');
    component = fixture.componentInstance;
    spyOn(component.action, 'emit');
  });

  /** Trigger a mouse event on the touch screen's target element. */
  function dispatchMouseEvent(type: string, offsetX = 0, offsetY = 0) {
    const {left, top} = target.getBoundingClientRect();
    target.dispatchEvent(new MouseEvent(
        type, {clientX: left + offsetX, clientY: top + offsetY}));
  }

  it('should track the cursor position', () => {
    // Hover over (123, 456)
    dispatchMouseEvent('mousemove', 123, 456);
    fixture.detectChanges();
    expect(component.currentPoint).toEqual(new Point(123, 456));
    const coordinates = getEl(element, '.target .coordinates');
    expect(coordinates.textContent).toEqual('X: 123 Y: 456');
  });

  it('should detect clicks', () => {
    // Hold on (123, 456) for 50ms (short duration)
    dispatchMouseEvent('mousedown', 123, 456);
    mockDate(Date.now() + 50);
    dispatchMouseEvent('mouseup', 123, 456);
    const expected = new ClickAction(new Point(123, 456));
    expect(component.action.emit).toHaveBeenCalledWith(expected);
  });

  it('should detect swipes', () => {
    // Move from (12, 34) to (56, 78) in 200ms (long duration)
    dispatchMouseEvent('mousedown', 12, 34);
    mockDate(Date.now() + 200);
    dispatchMouseEvent('mouseup', 56, 78);
    const expected = new SwipeAction(new Point(12, 34), new Point(56, 78), 200);
    expect(component.action.emit).toHaveBeenCalledWith(expected);
  });

  it('should cancel out-of-bounds gestures', () => {
    // Start at (123, 456) and exit target
    dispatchMouseEvent('mousedown', 123, 456);
    dispatchMouseEvent('mouseleave');
    expect(component.action.emit).not.toHaveBeenCalled();
  });
});
