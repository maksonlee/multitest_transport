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
import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MatSelectChange} from '@angular/material/select';

import {PeriodicTimeType, ScheduleTimeType} from '../services/mtt_models';
import {continuousNumberArray} from './util';

const periodicRegExps: Array<[PeriodicTimeType, RegExp]> = [
  [PeriodicTimeType.MINUTE, /^(\*\s){4}(\*){1}$/],
  [PeriodicTimeType.HOUR, /^\d{1,2}\s(\*\s){3}(\*){1}$/],
  [PeriodicTimeType.DAY, /^(\d{1,2}\s){2}(\*\s){2}(\*){1}$/],
  [PeriodicTimeType.WEEK, /^(\d{1,2}\s){2}(\*\s){2}\d{1,2}$/],
  [PeriodicTimeType.MONTH, /^(\d{1,2}\s){3}(\*\s){1}(\*){1}$/],
  [PeriodicTimeType.YEAR, /^(\d{1,2}\s){4}(\*){1}$/],
];

/**
 * This component takes user's input schedule time and generate cron expression.
 */
@Component({
  selector: 'schedule-time-form',
  styleUrls: ['schedule_time_form.css'],
  templateUrl: './schedule_time_form.ng.html',
})
export class ScheduleTimeForm implements OnInit {
  @Input() cronExpression!: string;
  @Output() cronExpressionChange = new EventEmitter<string>();
  // Store a reference to the enum
  readonly ScheduleTimeType = ScheduleTimeType;
  readonly PeriodicTimeType = PeriodicTimeType;

  readonly scheduleOptions = Object.values(ScheduleTimeType);
  readonly periodicTimeOptions = Object.values(PeriodicTimeType);
  readonly monthOptions = [
    'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'
  ];
  readonly monthDayOptions = continuousNumberArray(31, 1);
  readonly weekDayOptions = [
    WeekDay[0], WeekDay[1], WeekDay[2], WeekDay[3], WeekDay[4], WeekDay[5],
    WeekDay[6]
  ];
  readonly hourOptions = continuousNumberArray(24);
  readonly minuteOptions = continuousNumberArray(60);

  selectedScheduleTimeType = ScheduleTimeType.MANUAL;
  selectedPeriodicTimeType = PeriodicTimeType.HOUR;
  selectedMonth = 1;
  selectedMonthDay = 1;
  selectedWeekDay = WeekDay.Monday;
  selectedHour = 0;
  selectedMinute = 0;

  ngOnInit() {
    this.initInputSelector(this.cronExpression);
  }

  /**
   * On component init, update selector default value.
   */
  initInputSelector(cronExpression: string) {
    this.cronExpression = cronExpression;
    if (this.cronExpression) {
      const initPeriodicType =
          this.getCronPeriodicTimeType(this.cronExpression);
      if (initPeriodicType) {
        this.selectedScheduleTimeType = ScheduleTimeType.PERIODIC;
        this.selectedPeriodicTimeType = initPeriodicType;
        this.setInitPeriodicValue(initPeriodicType, this.cronExpression);
      } else {
        this.selectedScheduleTimeType = ScheduleTimeType.CUSTOM;
      }
    } else {
      this.selectedScheduleTimeType = ScheduleTimeType.MANUAL;
    }
  }

  /**
   * On schedule time type selector value change.
   */
  scheduleSelectChange(event: MatSelectChange) {
    switch (event.value) {
      case ScheduleTimeType.MANUAL: {
        this.cronExpressionChange.emit('');
        break;
      }
      case ScheduleTimeType.PERIODIC: {
        const initPeriodicType =
            this.getCronPeriodicTimeType(this.cronExpression);
        if (initPeriodicType) {
          this.setInitPeriodicValue(initPeriodicType, this.cronExpression);
        }
        this.getCronExpression();
        break;
      }
      case ScheduleTimeType.CUSTOM: {
        this.cronExpressionChange.emit(this.cronExpression);
        break;
      }
      default: {
        throw new Error(`unexpected value ${event.value}!`);
        break;
      }
    }
  }

  /**
   * Output cron expression base on current selectors value.
   */
  getCronExpression() {
    const cronArray: string[] = Array.from<string>({length: 5}).fill('*');
    switch (this.selectedPeriodicTimeType) {
      case PeriodicTimeType.MINUTE: {
        break;
      }
      case PeriodicTimeType.HOUR: {
        cronArray[0] = String(this.selectedMinute);
        break;
      }
      case PeriodicTimeType.DAY: {
        cronArray[0] = String(this.selectedMinute);
        cronArray[1] = String(this.selectedHour);
        break;
      }
      case PeriodicTimeType.WEEK: {
        cronArray[0] = String(this.selectedMinute);
        cronArray[1] = String(this.selectedHour);
        cronArray[4] = String(this.selectedWeekDay);
        break;
      }
      case PeriodicTimeType.MONTH: {
        cronArray[0] = String(this.selectedMinute);
        cronArray[1] = String(this.selectedHour);
        cronArray[2] = String(this.selectedMonthDay);
        break;
      }
      case PeriodicTimeType.YEAR: {
        cronArray[0] = String(this.selectedMinute);
        cronArray[1] = String(this.selectedHour);
        cronArray[2] = String(this.selectedMonthDay);
        cronArray[3] = String(this.selectedMonth);
        break;
      }
      default: {
        throw new Error(`unexpected value ${this.selectedPeriodicTimeType}!`);
        break;
      }
    }

    this.cronExpression = cronArray.join(' ');
    this.cronExpressionChange.emit(this.cronExpression);
  }

  /**
   * Check format of initial cron value
   */
  getCronPeriodicTimeType(cronStr: string): PeriodicTimeType|undefined {
    const validCron =
        /^((\d{1,2}|\*)\s){2}((\d{1,2}|\*|\?)\s){1}((\d|\*)\s){1}(\d{1,2}|\*|\?){1}$/;
    if (!validCron.test(cronStr)) {
      return undefined;
    }
    // check actual cron values
    const cronArray = cronStr.split(' ');
    // mm, hh, DD, MM, DOW
    const minval = [0, 0, 1, 1, 0];
    const maxval = [59, 23, 31, 12, 6];
    for (let i = 0; i < cronArray.length; i++) {
      if (cronArray[i] === '*' || cronArray[i] === '?') continue;
      let v = Number(cronArray[i]);
      if (isNaN(v)) {
        return undefined;
      }
      v = Math.floor(v);
      if (v !== undefined && v <= maxval[i] && v >= minval[i]) continue;
      return undefined;
    }
    return this.testCronString(cronStr);
  }

  /**
   * Set selector value by given periodic time type and corn expression.
   */
  setInitPeriodicValue(type: PeriodicTimeType, cronExpression: string) {
    const cronArray: string[] = cronExpression.split(' ');
    this.selectedPeriodicTimeType = type;
    switch (this.selectedPeriodicTimeType) {
      case PeriodicTimeType.MINUTE: {
        break;
      }
      case PeriodicTimeType.HOUR: {
        this.selectedMinute = Number(cronArray[0]) || 0;
        break;
      }
      case PeriodicTimeType.DAY: {
        this.selectedMinute = Number(cronArray[0]) || 0;
        this.selectedHour = Number(cronArray[1]) || 0;
        break;
      }
      case PeriodicTimeType.WEEK: {
        this.selectedMinute = Number(cronArray[0]) || 0;
        this.selectedHour = Number(cronArray[1]) || 0;
        this.selectedWeekDay = Number(cronArray[4]) || WeekDay.Monday;
        break;
      }
      case PeriodicTimeType.MONTH: {
        this.selectedMinute = Number(cronArray[0]) || 0;
        this.selectedHour = Number(cronArray[1]) || 0;
        this.selectedMonthDay = Number(cronArray[2]) || 1;
        break;
      }
      case PeriodicTimeType.YEAR: {
        this.selectedMinute = Number(cronArray[0]) || 0;
        this.selectedHour = Number(cronArray[1]) || 0;
        this.selectedMonthDay = Number(cronArray[2]) || 1;
        this.selectedMonth = Number(cronArray[3]) || 1;
        break;
      }
      default: {
        throw new Error(`unexpected value ${this.selectedPeriodicTimeType}!`);
        break;
      }
    }
  }

  customInputChange(value: string) {
    this.cronExpressionChange.emit(value);
  }

  private testCronString(cronStr: string): PeriodicTimeType|undefined {
    let result = undefined;
    for (let i = 0; i < periodicRegExps.length; i++) {
      if ((periodicRegExps[i][1]).test(cronStr)) {
        result = periodicRegExps[i][0];
        break;
      }
    }
    return result;
  }
}
