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

import {Component} from '@angular/core';
import {MatDialog, MatDialogRef} from '@angular/material/dialog';
import {first} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {PrivateNodeConfig} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import * as util from '../shared/util';

import {SetupWizardStepper} from './setup_wizard_stepper';

/**
 * A component for the setup wizard overlay
 */
@Component({
  selector: 'setup-wizard-dialog',
  styleUrls: ['setup_wizard_dialog.css'],
  templateUrl: './setup_wizard_dialog.ng.html',
})
export class SetupWizardDialog {
  enableMetrics = true;
  stepperDialog!: MatDialogRef<SetupWizardStepper>;

  constructor(
      private readonly dialog: MatDialog, private readonly mtt: MttClient,
      private readonly notifier: Notifier) {}

  submitMetrics(enableMetrics: boolean) {
    // Get current node config
    this.mtt.getPrivateNodeConfig().pipe(first()).subscribe(
        result => {
          const privateNodeConfig: PrivateNodeConfig = result;
          privateNodeConfig.metrics_enabled = enableMetrics;

          // Mark setup wizard as completed
          privateNodeConfig.setup_wizard_completed = true;

          // Update node config
          this.mtt.updatePrivateNodeConfig(privateNodeConfig)
              .pipe(first())
              .subscribe(
                  result => {
                    util.reloadPage(100);

                    // TODO: Hide the rest of the setup wizard
                    // until it is completed
                    // this.openStepper();
                  },
                  error => {
                    this.notifier.showError(
                        'Failed to save metric collection settings.',
                        util.buildApiErrorMessage(error));
                  });
        },
        error => {
          this.notifier.showError(
              'Failed to load current settings.',
              util.buildApiErrorMessage(error));
        });
  }

  openStepper() {
    this.stepperDialog = this.dialog.open(SetupWizardStepper, {
      disableClose: true,
      height: '1000px',
      width: '1000px',
    });
  }
}
