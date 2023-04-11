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

import {WeekDay} from '@angular/common';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getPeriodicType, PeriodicType, ScheduleTimeForm, ScheduleType} from './schedule_time_form';
import {SharedModule} from './shared_module';

describe('PeriodicType', () => {
  it('can detect hourly expressions', () => {
    expect(getPeriodicType('0 * * * *')).toBe(PeriodicType.HOUR);
    expect(getPeriodicType('59 * * * *')).toBe(PeriodicType.HOUR);
    expect(getPeriodicType('60 * * * *')).toBeUndefined();
  });

  it('can detect daily expressions', () => {
    expect(getPeriodicType('0 0 * * *')).toBe(PeriodicType.DAY);
    expect(getPeriodicType('0 23 * * *')).toBe(PeriodicType.DAY);
    expect(getPeriodicType('0 24 * * *')).toBeUndefined();
  });

  it('can detect weekly expressions', () => {
    expect(getPeriodicType('0 0 * * 0')).toBe(PeriodicType.WEEK);
    expect(getPeriodicType('0 0 * * 6')).toBe(PeriodicType.WEEK);
    expect(getPeriodicType('0 0 * * 7')).toBeUndefined();
  });

  it('can detect monthly expressions', () => {
    expect(getPeriodicType('0 0 1 * *')).toBe(PeriodicType.MONTH);
    expect(getPeriodicType('0 0 31 * *')).toBe(PeriodicType.MONTH);
    expect(getPeriodicType('0 0 0 * *')).toBeUndefined();
    expect(getPeriodicType('0 0 32 * *')).toBeUndefined();
  });
});

describe('ScheduleTimeForm', () => {
  let component: ScheduleTimeForm;
  let fixture: ComponentFixture<ScheduleTimeForm>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      });

    fixture = TestBed.createComponent(ScheduleTimeForm);
    component = fixture.componentInstance;
    spyOn(component, 'onChange');
  });

  it('can initialize component', () => {
    expect(component).toBeTruthy();
  });

  it('can detect schedule type', () => {
    component.writeValue('');
    expect(component.selectedScheduleType).toEqual(ScheduleType.MANUAL);

    component.writeValue('0 * * * *');
    expect(component.selectedScheduleType).toEqual(ScheduleType.PERIODIC);

    component.writeValue('31/4 2 1 * *');
    expect(component.selectedScheduleType).toEqual(ScheduleType.CUSTOM);
  });

  it('outputs cron expression on schedule type change', () => {
    component.changeScheduleType(ScheduleType.MANUAL);
    expect(component.onChange).toHaveBeenCalledWith('');

    component.changeScheduleType(ScheduleType.PERIODIC);
    expect(component.onChange).toHaveBeenCalledWith('0 * * * *');

    component.cronExpression = '31/4 2 1 * *';
    component.changeScheduleType(ScheduleType.CUSTOM);
    expect(component.onChange).toHaveBeenCalledWith('31/4 2 1 * *');
  });

  it('can initialize periodic parameters', () => {
    component.writeValue('1 * * * *');
    expect(component.selectedPeriodicType).toEqual(PeriodicType.HOUR);
    expect(component.selectedMinute).toEqual(1);

    component.writeValue('2 3 * * *');
    expect(component.selectedPeriodicType).toEqual(PeriodicType.DAY);
    expect(component.selectedMinute).toEqual(2);
    expect(component.selectedHour).toEqual(3);

    component.writeValue('4 5 * * 6');
    expect(component.selectedPeriodicType).toEqual(PeriodicType.WEEK);
    expect(component.selectedMinute).toEqual(4);
    expect(component.selectedHour).toEqual(5);
    expect(component.selectedWeekDay).toEqual(WeekDay.Saturday);

    component.writeValue('7 8 9 * *');
    expect(component.selectedPeriodicType).toEqual(PeriodicType.MONTH);
    expect(component.selectedMinute).toEqual(7);
    expect(component.selectedHour).toEqual(8);
    expect(component.selectedMonthDay).toEqual(9);
  });

  it('can generate periodic expressions', () => {
    component.selectedPeriodicType = PeriodicType.HOUR;
    component.selectedMinute = 1;
    component.updatePeriodicCron();
    expect(component.onChange).toHaveBeenCalledWith('1 * * * *');

    component.selectedPeriodicType = PeriodicType.DAY;
    component.selectedHour = 2;
    component.updatePeriodicCron();
    expect(component.onChange).toHaveBeenCalledWith('1 2 * * *');

    component.selectedPeriodicType = PeriodicType.WEEK;
    component.selectedWeekDay = WeekDay.Wednesday;
    component.updatePeriodicCron();
    expect(component.onChange).toHaveBeenCalledWith('1 2 * * 3');

    component.selectedPeriodicType = PeriodicType.MONTH;
    component.selectedMonthDay = 4;
    component.updatePeriodicCron();
    expect(component.onChange).toHaveBeenCalledWith('1 2 4 * *');
  });

  it('can provide timezone options', () => {
    // Local timezone is America/Los_Angeles
    spyOn(Intl, 'DateTimeFormat').and.returnValue({
//TODO: Wait until b/208710526 is fixed, then remove this autogenerated error suppression.
// @ts-ignore(go/unfork-jasmine-typings): Type '{ timeZone: string; }' is missing the following properties from type 'ResolvedDateTimeFormatOptions': locale, calendar, numberingSystem
      resolvedOptions: () => ({timeZone: 'America/Los_Angeles'})
    });

    component.timezone = '';  // ignores empty values
    component.ngOnChanges();
    expect(component.timezoneOptions).toEqual(['UTC', 'America/Los_Angeles']);

    component.timezone = 'America/Los_Angeles';  // ignores duplicates
    component.ngOnChanges();
    expect(component.timezoneOptions).toEqual(['UTC', 'America/Los_Angeles']);

    component.timezone = 'Asia/Taipei';
    component.ngOnChanges();
    expect(component.timezoneOptions).toEqual([
      'UTC', 'America/Los_Angeles', 'Asia/Taipei'
    ]);
  });
});
