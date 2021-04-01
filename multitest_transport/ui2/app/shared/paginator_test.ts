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
import {By} from '@angular/platform-browser';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {Paginator} from './paginator';
import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';

describe('Paginator', () => {
  let fixture: ComponentFixture<Paginator>;
  let paginator: Paginator;
  let paginatorEl: DebugElement;
  let sizeSelectEl: DebugElement;
  let prevButtonEl: DebugElement;
  let nextButtonEl: DebugElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });

    // configure component
    fixture = TestBed.createComponent(Paginator);
    paginator = fixture.componentInstance;
    paginatorEl = fixture.debugElement;
    paginator.pageSizeOptions = [10, 20, 50];
    fixture.detectChanges();

    // fetch child elements
    sizeSelectEl = paginatorEl.query(By.css('mat-select'));
    prevButtonEl = paginatorEl.query(By.css('.previous-page'));
    nextButtonEl = paginatorEl.query(By.css('.next-page'));
  });

  it('can be initialized', () => {
    expect(paginatorEl).toBeTruthy();
    expect(sizeSelectEl).toBeTruthy();
    expect(prevButtonEl).toBeTruthy();
    expect(nextButtonEl).toBeTruthy();
  });

  it('can enable previous page button', () => {
    paginator.hasPrevious = false;
    fixture.detectChanges();
    expect(prevButtonEl.attributes['disabled']).toBeTruthy();

    paginator.hasPrevious = true;
    fixture.detectChanges();
    expect(prevButtonEl.attributes['disabled']).toBeFalsy();
  });

  it('can emit previous page event', () => {
    paginator.pageIndex = 2;
    spyOn(paginator.previous, 'emit');
    prevButtonEl.triggerEventHandler('click', null);
    fixture.detectChanges();
    expect(paginator.previous.emit).toHaveBeenCalled();
    expect(paginator.pageIndex).toEqual(1);
  });

  it('can enable next page button', () => {
    paginator.hasNext = false;
    fixture.detectChanges();
    expect(nextButtonEl.attributes['disabled']).toBeTruthy();

    paginator.hasNext = true;
    fixture.detectChanges();
    expect(nextButtonEl.attributes['disabled']).toBeFalsy();
  });

  it('can emit next page event', () => {
    spyOn(paginator.next, 'emit');
    nextButtonEl.triggerEventHandler('click', null);
    fixture.detectChanges();
    expect(paginator.next.emit).toHaveBeenCalled();
    expect(paginator.pageIndex).toEqual(2);
  });

  it('can hide size options', () => {
    paginator.pageSizeOptions = [];
    fixture.detectChanges();
    expect(paginatorEl.query(By.css('mat-select'))).toBeFalsy();
  });

  it('can emit size change event', () => {
    paginator.pageIndex = 2;
    spyOn(paginator.sizeChange, 'emit');
    sizeSelectEl.triggerEventHandler('selectionChange', {value: 50});
    expect(paginator.pageSize).toEqual(50);
    expect(paginator.sizeChange.emit).toHaveBeenCalledWith(50);
    expect(paginator.pageIndex).toEqual(1);
  });
});
