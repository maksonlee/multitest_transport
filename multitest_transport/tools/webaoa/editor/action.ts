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

import {AoaDevice, Key, Point} from '../device/device';

/** Case-insensitive comparison of two strings. */
function equalsIgnoreCase(left: string, right: string) {
  return left.localeCompare(right, undefined, {sensitivity: 'accent'}) === 0;
}

/** List of AOA action commands. */
export const COMMANDS =
    ['sleep', 'click', 'swipe', 'write', 'key', 'wake', 'back', 'home'] as
    const;
/** AOA action command union type. */
export type AoaActionCommand = typeof COMMANDS[number];

// Map of command keywords to action parsers.
const PARSERS = new Map<AoaActionCommand, AoaActionParser>();

/** Converts string expressions into AOA actions. */
interface AoaActionParser {
  /** Parses a string and converts it to an AOA action if valid. */
  parse(value: string): AoaAction;
}

/** Executable AOA device action. */
export abstract class AoaAction {
  /** Parses an expression and converts it to an action. */
  static parse(value: string): AoaAction {
    const command = value.split(' ', 1)[0].toLowerCase();
    const parser = PARSERS.get(command as AoaActionCommand);
    if (!parser) {
      throw new Error(`Unknown command '${command}'`);
    }
    return parser.parse(value);
  }

  /**
   * Asynchronously executes the action.
   * @param device target device
   */
  abstract execute(device: AoaDevice): Promise<void>;

  /** @return associated AOA action command. */
  abstract get command(): AoaActionCommand;

  /** @return serialized action with a "<command>( <arguments>)?" format. */
  abstract toString(): string;
}

/** Does nothing for a specified duration. */
export class SleepAction implements AoaAction {
  private static readonly REGEXP = /^sleep (\d+)$/i;
  readonly command = 'sleep';

  /** @nocollapse */
  static parse(value: string): SleepAction {
    const result = SleepAction.REGEXP.exec(value);
    if (!result) {
      throw new Error(`Invalid sleep action '${value}'`);
    }
    return new SleepAction(Number(result[1]));
  }

  constructor(readonly millis: number) {}

  async execute(device: AoaDevice): Promise<void> {
    await device.sleep(this.millis);
  }

  toString(): string {
    return `sleep ${this.millis}`;
  }
}
PARSERS.set('sleep', SleepAction);

/** Clicks on a point. */
export class ClickAction implements AoaAction {
  private static readonly REGEXP = /^click (\d{1,3}) (\d{1,3})$/i;
  readonly command = 'click';

  /** @nocollapse */
  static parse(value: string): ClickAction {
    const result = ClickAction.REGEXP.exec(value);
    if (!result) {
      throw new Error(`Invalid click action '${value}'`);
    }
    const point = new Point(Number(result[1]), Number(result[2]));
    return new ClickAction(point);
  }

  constructor(readonly point: Point) {}

  async execute(device: AoaDevice): Promise<void> {
    await device.click(this.point);
  }

  toString(): string {
    return `click ${this.point.x} ${this.point.y}`;
  }
}
PARSERS.set('click', ClickAction);

/** Performs a swipe gesture. */
export class SwipeAction implements AoaAction {
  private static readonly REGEXP =
      /^swipe (\d{1,3}) (\d{1,3}) (\d+) (\d{1,3}) (\d{1,3})$/i;
  readonly command = 'swipe';

  /** @nocollapse */
  static parse(value: string): SwipeAction {
    const result = SwipeAction.REGEXP.exec(value);
    if (!result) {
      throw new Error(`Invalid swipe action '${value}'`);
    }
    const from = new Point(Number(result[1]), Number(result[2]));
    const to = new Point(Number(result[4]), Number(result[5]));
    const millis = Number(result[3]);
    return new SwipeAction(from, to, millis);
  }

  constructor(
      readonly from: Point, readonly to: Point, readonly millis: number) {}

  async execute(device: AoaDevice): Promise<void> {
    await device.swipe(this.from, this.to, this.millis);
  }

  toString(): string {
    // TODO: Improve readability
    return `swipe ${this.from.x} ${this.from.y} ${this.millis} ${this.to.x} ${
        this.to.y}`;
  }
}
PARSERS.set('swipe', SwipeAction);

/** Writes alphanumeric text, e.g. write <text>. */
export class WriteAction implements AoaAction {
  private static readonly REGEXP = /^write ([ a-z0-9@\-_+.]+)$/i;
  readonly command = 'write';

  /** @nocollapse */
  static parse(value: string): WriteAction {
    const result = WriteAction.REGEXP.exec(value);
    if (!result) {
      throw new Error(`Invalid write action '${value}'`);
    }
    return new WriteAction(result[1]);
  }

  constructor(readonly text: string) {}

  async execute(device: AoaDevice): Promise<void> {
    const keys = this.text.split('').map(Key.get).filter(Boolean) as Key[];
    await device.pressKeys(keys);
  }

  toString(): string {
    return `write ${this.text}`;
  }
}
PARSERS.set('write', WriteAction);

/** Presses a sequence of keys, e.g. key <multiplier>*<keycode>. */
export class KeyAction implements AoaAction {
  private static readonly REGEXP = /^key(?: (?:\d+\*)?[a-z0-9@\-_+.]+)+$/i;
  readonly command = 'key';

  /** @nocollapse */
  static parse(value: string): KeyAction {
    if (!KeyAction.REGEXP.test(value)) {
      throw new Error(`Invalid key action '${value}'`);
    }
    const args = value.substring(4);
    const keys: Key[] = [];
    const re = /(?:(\d+)\*)?([a-z0-9@\-_+.]+)/ig;
    for (let match = re.exec(args); match; match = re.exec(args)) {
      const multiplier = match[1] ? Number(match[1]) : 1;
      const key = Key.get(match[2]);
      if (!key) {
        throw new Error(`Unknown key '${match[2]}'`);
      }
      for (let i = 0; i < multiplier; i++) {
        keys.push(key);
      }
    }
    return new KeyAction(keys);
  }

  constructor(readonly keys: Key[]) {}

  async execute(device: AoaDevice): Promise<void> {
    await device.pressKeys(this.keys);
  }

  toString(): string {
    const expression = ['key'];
    for (let i = 0, multiplier = 1; i < this.keys.length; i++) {
      const key = this.keys[i];
      if (key === this.keys[i + 1]) {
        multiplier++;
        continue;
      }
      expression.push(multiplier > 1 ? `${multiplier}*${key.code}` : key.code);
      multiplier = 1;
    }
    return expression.join(' ');
  }
}
PARSERS.set('key', KeyAction);

/** Presses the back button. */
export class BackAction implements AoaAction {
  readonly command = 'back';

  /** @nocollapse */
  static parse(value: string): BackAction {
    if (!equalsIgnoreCase('back', value)) {
      throw new Error(`Invalid back action '${value}'`);
    }
    return new BackAction();
  }

  async execute(device: AoaDevice): Promise<void> {
    await device.goBack();
  }

  toString(): string {
    return 'back';
  }
}
PARSERS.set('back', BackAction);

/** Presses the home button. */
export class HomeAction implements AoaAction {
  readonly command = 'home';

  /** @nocollapse */
  static parse(value: string): HomeAction {
    if (!equalsIgnoreCase('home', value)) {
      throw new Error(`Invalid home action '${value}'`);
    }
    return new HomeAction();
  }

  async execute(device: AoaDevice): Promise<void> {
    await device.goHome();
  }

  toString(): string {
    return 'home';
  }
}
PARSERS.set('home', HomeAction);

/** Wakes the device. */
export class WakeAction implements AoaAction {
  readonly command = 'wake';

  /** @nocollapse */
  static parse(value: string): WakeAction {
    if (!equalsIgnoreCase('wake', value)) {
      throw new Error(`Invalid wake action '${value}'`);
    }
    return new WakeAction();
  }

  async execute(device: AoaDevice): Promise<void> {
    await device.wakeUp();
  }

  toString(): string {
    return 'wake';
  }
}
PARSERS.set('wake', WakeAction);
