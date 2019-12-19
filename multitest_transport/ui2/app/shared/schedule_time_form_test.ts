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
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {PeriodicTimeType, ScheduleTimeType} from '../services/mtt_models';
import {getEl} from '../testing/jasmine_util';

import {ScheduleTimeForm} from './schedule_time_form';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('ScheduleTimeForm', () => {
  let scheduleTimeForm: ScheduleTimeForm;
  let scheduleTimeFormFixture: ComponentFixture<ScheduleTimeForm>;
  let el: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });
    scheduleTimeFormFixture = TestBed.createComponent(ScheduleTimeForm);
    el = scheduleTimeFormFixture.debugElement;
    scheduleTimeForm = scheduleTimeFormFixture.componentInstance;
    scheduleTimeForm.cronExpression = '';
    scheduleTimeFormFixture.detectChanges();
  });

  it('should get initialized correctly', () => {
    expect(scheduleTimeForm).toBeTruthy();
  });

  it('should display the right schedule time type', () => {
    expect(scheduleTimeForm.selectedScheduleTimeType)
        .toEqual(ScheduleTimeType.MANUAL);

    scheduleTimeForm.cronExpression = '* * * * *';
    scheduleTimeForm.initInputSelector(scheduleTimeForm.cronExpression);
    expect(scheduleTimeForm.selectedScheduleTimeType)
        .toEqual(ScheduleTimeType.PERIODIC);

    scheduleTimeForm.cronExpression = '31/4 2 1 * *';
    scheduleTimeForm.initInputSelector(scheduleTimeForm.cronExpression);
    expect(scheduleTimeForm.selectedScheduleTimeType)
        .toEqual(ScheduleTimeType.CUSTOM);
  });

  it('should output cron expression string on schedule selector change', () => {
    spyOn(scheduleTimeForm.cronExpressionChange, 'emit');
    getEl(el, 'mat-select').click();
    scheduleTimeFormFixture.detectChanges();
    getEl(el, 'mat-option').click();
    scheduleTimeFormFixture.detectChanges();
    expect(scheduleTimeForm.cronExpressionChange.emit).toHaveBeenCalledWith('');
  });

  it('should return the right periodic time type', () => {
    const minuteResult = scheduleTimeForm.getCronPeriodicTimeType('* * * * *');
    expect(minuteResult).toEqual(PeriodicTimeType.MINUTE);

    const hourResult = scheduleTimeForm.getCronPeriodicTimeType('1 * * * *');
    expect(hourResult).toEqual(PeriodicTimeType.HOUR);

    const dayResult = scheduleTimeForm.getCronPeriodicTimeType('1 1 * * *');
    expect(dayResult).toEqual(PeriodicTimeType.DAY);

    const weekResult = scheduleTimeForm.getCronPeriodicTimeType('1 1 * * 2');
    expect(weekResult).toEqual(PeriodicTimeType.WEEK);

    const monthResult = scheduleTimeForm.getCronPeriodicTimeType('0 0 1 * *');
    expect(monthResult).toEqual(PeriodicTimeType.MONTH);

    const yearResult = scheduleTimeForm.getCronPeriodicTimeType('3 3 1 1 *');
    expect(yearResult).toEqual(PeriodicTimeType.YEAR);
  });

  it('should generate the correct cron expression', () => {
    spyOn(scheduleTimeForm.cronExpressionChange, 'emit');

    scheduleTimeForm.selectedPeriodicTimeType = PeriodicTimeType.MINUTE;
    scheduleTimeForm.getCronExpression();
    expect(scheduleTimeForm.cronExpressionChange.emit)
        .toHaveBeenCalledWith('* * * * *');

    scheduleTimeForm.selectedPeriodicTimeType = PeriodicTimeType.HOUR;
    scheduleTimeForm.getCronExpression();
    expect(scheduleTimeForm.cronExpressionChange.emit)
        .toHaveBeenCalledWith(
            String(scheduleTimeForm.selectedMinute) + ' * * * *');
  });
});
