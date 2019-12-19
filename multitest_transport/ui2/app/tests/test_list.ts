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

/**
 * @fileoverview A test list component,
 */

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {Component, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MatTable, MatTableDataSource} from '@angular/material/table';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {Test} from '../services/mtt_models';
import {Notifier} from '../services/notifier';


/** A component for displaying a list of test runs. */
@Component({
  selector: 'test-list',
  templateUrl: './test_list.ng.html',
})
export class TestList implements OnInit, OnDestroy {
  @Input() columnsToDisplay = ['name', 'description', 'actions'];

  isLoading = false;
  tests: Test[] = [];
  dataSource = new MatTableDataSource<Test>(this.tests);

  @ViewChild(MatTable, {static: false}) table!: MatTable<{}>;

  private readonly destroy = new ReplaySubject();

  constructor(
      private readonly mttClient: MttClient,
      private readonly notifier: Notifier,
      private readonly liveAnnouncer: LiveAnnouncer,
  ) {}

  ngOnInit() {
    this.load();
  }

  ngOnDestroy() {
    this.destroy.next();
    this.liveAnnouncer.clear();
  }

  load() {
    this.isLoading = true;
    this.liveAnnouncer.announce('Loading', 'polite');
    setTimeout(() => {
      this.mttClient.getTests()
          .pipe(
              takeUntil(this.destroy),
              finalize(() => {
                this.isLoading = false;
              }),
              )
          .subscribe(
              result => {
                this.tests = result.tests || [];
                this.dataSource.data = this.tests;
                this.liveAnnouncer.announce('Tests loaded', 'assertive');
              },
              error => {
                this.notifier.showError('Unable to get test suites.');
              },
          );
    }, 100);
  }

  deleteTest(test: Test) {
    this.notifier
        .confirm(
            `Do you really want to delete test '${test.name}'?`, 'Delete test')
        .subscribe(result => {
          if (!result) {
            return;
          }
          this.mttClient.deleteTest(test.id!).subscribe(
              result => {
                this.notifier.showMessage(`Test '${test.name}' deleted`);
                // Remove the test from this.tests.
                const index = this.tests.findIndex(o => o === test);
                this.tests.splice(index, 1);
                this.table.renderRows();
              },
              error => {
                this.notifier.showError(`Failed to delete ${test.name}`);
              });
        });
  }
}
