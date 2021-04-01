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

import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';

import {FileService} from 'google3/third_party/py/multitest_transport/ui2/app/services/file_service';
import {EventLogLevel, TestRun} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_models';
import {CommandState, Request} from 'google3/third_party/py/multitest_transport/ui2/app/services/tfc_models';
import {TestRunsModule} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module';
import {TestRunsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/test_runs/test_runs_module.ngsummary';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';

describe('TestRunProgress', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
  });

  let fs: jasmine.SpyObj<FileService>;

  beforeEach(() => {
    fs = jasmine.createSpyObj(['getTestRunFileUrl', 'getFileBrowseUrl']);

    setupModule({
      imports: [
        TestRunsModule,
        NoopAnimationsModule,
      ],
      providers: [
        {provide: FileService, useValue: fs},
      ],
      summaries: [TestRunsModuleNgSummary],
    });
  });

  it.async('can display log entries', async () => {
    const testRun = {
      test_run_config: {
        command: 'command',
      },
      log_entries: [
        {
          create_time: '2000-01-01T09:12:34Z',
          level: EventLogLevel.INFO,
          message: '#1: info with link http://www.google.com',
        },
        {
          create_time: '2000-01-02T10:23:45Z',
          level: EventLogLevel.WARNING,
          message: '#2: warning',
        },
        {
          create_time: '2000-01-03T11:34:56Z',
          level: EventLogLevel.ERROR,
          message: '#3: error',
        },
      ]
    } as TestRun;
    bootstrapTemplate(
        `<test-run-progress [testRun]="testRun"></test-run-progress>`,
        {testRun});
    await env.verifyState('test-run-progress_log_entries', 'test-run-progress');
  });

  it.async('can display attempts', async () => {
    const testRun = {
      test_run_config: {
        command: 'command',
      }
    } as TestRun;
    const request = {
      command_attempts: [
        {
          attempt_id: '#1',
          create_time: '2000-01-01T09:12:34Z',
          state: CommandState.RUNNING,
        },
        {
          attempt_id: '#2',
          create_time: '2000-01-02T10:23:45Z',
          start_time: '2000-01-02T10:23:45Z',
          end_time: '2000-01-02T11:36:19Z',
          state: CommandState.COMPLETED,
          passed_test_count: 123,
          failed_test_count: 0,
          total_test_count: 123,
          summary: 'Summary with link http://www.google.com'
        },
        {
          attempt_id: '#2',
          create_time: '2000-01-03T11:34:56Z',
          state: CommandState.ERROR,
          passed_test_count: 12,
          failed_test_count: 34,
          total_test_count: 46,
          error: 'Error description'
        },
      ]
    } as Request;
    bootstrapTemplate(
        `<test-run-progress [testRun]="testRun" [request]="request">
         </test-run-progress>`,
        {testRun, request});
    await env.verifyState('test-run-progress_attempts', 'test-run-progress');
  });
});
