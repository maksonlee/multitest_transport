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
import {AoaAction, BackAction, ClickAction, HomeAction, KeyAction, SleepAction, SwipeAction, WakeAction, WriteAction} from './action';

describe('SleepAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: SleepAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['sleep']);
    action = new SleepAction(123);
  });

  it('should sleep when executed', async () => {
    await action.execute(device);
    expect(device.sleep).toHaveBeenCalledWith(123);
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('sleep 123');
  });

  it('should parse sleep expressions', () => {
    expect(AoaAction.parse('sleep 123')).toEqual(action);
    // expression is invalid if the duration is missing
    expect(() => AoaAction.parse('sleep'))
        .toThrowError(/Invalid sleep action 'sleep'/);
  });
});

describe('ClickAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: ClickAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['click']);
    action = new ClickAction(new Point(123, 456));
  });

  it('should click when executed', async () => {
    await action.execute(device);
    expect(device.click).toHaveBeenCalledWith(new Point(123, 456));
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('click 123 456');
  });

  it('should parse click expressions', () => {
    expect(AoaAction.parse('click 123 456')).toEqual(action);
    // expression is invalid if one or both coordinates are missing
    expect(() => AoaAction.parse('click'))
        .toThrowError(/Invalid click action 'click'/);
    expect(() => AoaAction.parse('click 123'))
        .toThrowError(/Invalid click action 'click 123'/);
  });
});

describe('SwipeAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: SwipeAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['swipe']);
    action = new SwipeAction(new Point(12, 34), new Point(56, 78), 100);
  });

  it('should swipe when executed', async () => {
    await action.execute(device);
    expect(device.swipe)
        .toHaveBeenCalledWith(new Point(12, 34), new Point(56, 78), 100);
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('swipe 12 34 100 56 78');
  });

  it('should parse swipe expressions', () => {
    expect(AoaAction.parse('swipe 12 34 100 56 78')).toEqual(action);
    // expression is invalid if some coordinates are missing
    expect(() => AoaAction.parse('swipe'))
        .toThrowError(/Invalid swipe action 'swipe'/);
    expect(() => AoaAction.parse('swipe 12 34 100'))
        .toThrowError(/Invalid swipe action 'swipe 12 34 100'/);
  });
});

describe('WriteAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: WriteAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['pressKeys']);
    action = new WriteAction('Test 123');
  });

  it('should press keys when executed', async () => {
    await action.execute(device);
    expect(device.pressKeys).toHaveBeenCalledWith([
      Key.get('T')!, Key.get('e')!, Key.get('s')!, Key.get('t')!,
      Key.get('SPACE')!,
      Key.get('1')!, Key.get('2')!, Key.get('3')!,
    ]);
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('write Test 123');
  });

  it('should parse write expressions', () => {
    expect(AoaAction.parse('write Test 123')).toEqual(action);
    // expression is invalid if text is missing
    expect(() => AoaAction.parse('write'))
        .toThrowError(/Invalid write action 'write'/);
  });
});

describe('KeyAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: KeyAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['pressKeys']);
    action = new KeyAction(
        [Key.UP, Key.UP, Key.RIGHT, Key.DOWN, Key.DOWN, Key.DOWN]);
  });

  it('should press keys when executed', async () => {
    await action.execute(device);
    expect(device.pressKeys).toHaveBeenCalledWith([
      Key.UP, Key.UP, Key.RIGHT, Key.DOWN, Key.DOWN, Key.DOWN
    ]);
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('key 2*up right 3*down');
  });

  it('should parse key expressions', () => {
    expect(AoaAction.parse('key 2*up right 3*down')).toEqual(action);
    // expression is invalid if key combination is missing or unknown
    expect(() => AoaAction.parse('key'))
        .toThrowError(/Invalid key action 'key'/);
    expect(() => AoaAction.parse('key unknown'))
        .toThrowError(/Unknown key 'unknown'/);
  });
});

describe('BackAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: BackAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['goBack']);
    action = new BackAction();
  });

  it('should go back when executed', async () => {
    await action.execute(device);
    expect(device.goBack).toHaveBeenCalled();
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('back');
  });

  it('should parse back expressions', () => {
    expect(AoaAction.parse('back')).toEqual(action);
    // expression is invalid if there are extra arguments
    expect(() => AoaAction.parse('back 123'))
        .toThrowError(/Invalid back action 'back 123'/);
  });
});


describe('HomeAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: HomeAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['goHome']);
    action = new HomeAction();
  });

  it('should go home when executed', async () => {
    await action.execute(device);
    expect(device.goHome).toHaveBeenCalled();
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('home');
  });

  it('should parse home expressions', () => {
    expect(AoaAction.parse('home')).toEqual(action);
    // expression is invalid if there are extra arguments
    expect(() => AoaAction.parse('home 123'))
        .toThrowError(/Invalid home action 'home 123'/);
  });
});


describe('WakeAction', () => {
  let device: jasmine.SpyObj<AoaDevice>;
  let action: WakeAction;

  beforeEach(() => {
    device = jasmine.createSpyObj<AoaDevice>(['wakeUp']);
    action = new WakeAction();
  });

  it('should wake up when executed', async () => {
    await action.execute(device);
    expect(device.wakeUp).toHaveBeenCalled();
  });

  it('should be serializable', () => {
    expect(action.toString()).toEqual('wake');
  });

  it('should parse wake expressions', () => {
    expect(AoaAction.parse('wake')).toEqual(action);
    // expression is invalid if there are extra arguments
    expect(() => AoaAction.parse('wake 123'))
        .toThrowError(/Invalid wake action 'wake 123'/);
  });
});
