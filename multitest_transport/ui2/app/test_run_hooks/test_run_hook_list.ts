/**
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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {Component, OnDestroy, OnInit} from '@angular/core';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {TestRunHookConfig} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {buildApiErrorMessage} from '../shared/util';

/** Displays a list of test run hook configurations. */
@Component({
  selector: 'test-run-hook-list',
  styleUrls: ['test_run_hook_list.css'],
  templateUrl: './test_run_hook_list.ng.html',
})
export class TestRunHookList implements OnInit, OnDestroy {
  isLoading = false;
  hookConfigs: TestRunHookConfig[] = [];

  private readonly destroy = new ReplaySubject();

  constructor(
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly notifier: Notifier, private readonly mtt: MttClient) {}

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

    // Add short delay to allow device action changes to propagate.
    this.mtt.testRunHooks.list()
        .pipe(takeUntil(this.destroy))
        .pipe(finalize(() => {
          this.isLoading = false;
        }))
        .subscribe(
            hookConfigs => {
              this.hookConfigs = hookConfigs;
              this.liveAnnouncer.announce('Test run hooks loaded', 'assertive');
            },
            error => {
              this.notifier.showError(
                  'Failed to load test run hooks.',
                  buildApiErrorMessage(error));
            },
        );
  }

  /** Authorize a test run hook configuration and reload. */
  authorize(hookConfig: TestRunHookConfig) {
    this.mtt.testRunHooks.authorize(hookConfig.id)
        .subscribe(
            () => {
              this.load();
            },
            error => {
              this.notifier.showError(
                  'Failed to authorize test run hook.',
                  buildApiErrorMessage(error));
            });
  }

  /** Opens the test run hook editor to edit an existing hook configuration. */
  edit(hookConfig: TestRunHookConfig) {
    // TODO: implement test run hook editor
  }

  /** Delete a test run hook configuration after confirmation. */
  delete(hookConfig: TestRunHookConfig) {
    this.notifier
        .confirm(
            `Do you really want to delete test run hook '${hookConfig.name}'?`,
            'Delete test run hook')
        .subscribe(confirmed => {
          if (!confirmed) {
            return;
          }
          this.mtt.testRunHooks.delete(hookConfig.id)
              .subscribe(
                  () => {
                    const index = this.hookConfigs.findIndex(
                        hc => hc.id === hookConfig.id);
                    if (index !== -1) {
                      this.hookConfigs.splice(index, 1);
                    }
                    this.notifier.showMessage(
                        `Test run hook '${hookConfig.name}' deleted`);
                  },
                  error => {
                    this.notifier.showError(
                        `Failed to delete test run hook.`,
                        buildApiErrorMessage(error));
                  });
        });
  }

  /** Opens the test run hook editor to copy an existing hook configuration. */
  copy(hookConfig: TestRunHookConfig) {
    // TODO: implement test run hook editor
  }

  /** Opens the test run hook editor to create a new hook configuration. */
  create() {
    // TODO: implement test run hook editor
  }
}
