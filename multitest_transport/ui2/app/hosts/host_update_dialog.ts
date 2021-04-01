/**
 * Copyright 2021 Google LLC
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
import {Component, ElementRef, Inject, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {MatRadioChange} from '@angular/material/radio';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {ALL_OPTIONS_VALUE, HostUpdateStateSummary, LabInfo} from '../services/mtt_lab_models';
import {Notifier} from '../services/notifier';
import {TfcClient} from '../services/tfc_client';
import {BatchUpdateHostMetadataRequest, DEFAULT_ALL_COUNT, HostConfig, TestHarnessImage} from '../services/tfc_models';

/** Default count of test harness images to be selected from each time. */
const DEFAULT_TEST_HARNESS_IMAGE_COUNT = 30;

/**
 * Data to build the host update dialog.
 * 1. The name of selected lab,
 */
export interface HostUpdateDialogData {
  selectedLab: string;
}

/** The enum types to describe lab update mode. */
export enum UpdateMode {
  /** Update the entire lab. */
  LAB = 'LAB',
  /** Update a selected host group. */
  HOST_GROUP = 'HOST_GROUP',
  /** Update selected hosts. */
  HOSTS = 'HOSTS',
}

/** Component that manages host updates in a lab. */
@Component({
  selector: 'host-update-dialog',
  styleUrls: ['host_update_dialog.css'],
  templateUrl: './host_update_dialog.ng.html',
})
export class HostUpdateDialog implements OnInit, OnDestroy {
  selectedLab: string;
  selectedHostGroup = '';
  selectedHosts: string[] = [];
  hostConfigsInLab: HostConfig[] = [];
  candidateHostConfigs: HostConfig[] = [];
  hostGroupNames: string[] = [];
  hostNames: string[] = [];
  labInfo: LabInfo|null = null;
  selectedMode: UpdateMode = UpdateMode.LAB;
  selectedImage: TestHarnessImage|null = null;
  imageTagPrefix = '';
  testHarnessImages: TestHarnessImage[] = [];
  disableSetImageButton = false;
  readonly UpdateMode = UpdateMode;

  private readonly destroy = new ReplaySubject<void>(1);

  @ViewChild('update_summary_chart') updateSummaryChartElement!: ElementRef;

  constructor(
      public dialogRef: MatDialogRef<HostUpdateDialog>,
      @Inject(MAT_DIALOG_DATA) public data: HostUpdateDialogData,
      private readonly tfcClient: TfcClient,
      private readonly notifier: Notifier,
  ) {
    if (!data.selectedLab) {
      this.dialogRef.close(false);
    }
    this.selectedLab = data.selectedLab;
  }

  ngOnInit() {
    this.initLabInfo();
    this.initHostConfigsInLab();
    this.getTestHarnessImagesByTagPrefix();
  }

  ngOnDestroy() {
    this.destroy.next();
    this.destroy.complete();
  }

  initLabInfo() {
    return this.tfcClient.getLabInfo(this.selectedLab)
        .pipe(takeUntil(this.destroy))
        .subscribe(
            (result) => {
              this.labInfo = result;
              this.drawHostUpdateStateSummaryChart();
            },
            () => {
              this.notifier.showError('Failed to load lab info.');
            });
  }

  initHostConfigsInLab() {
    return this.tfcClient.getHostConfigs(this.selectedLab, DEFAULT_ALL_COUNT)
        .pipe(takeUntil(this.destroy))
        .subscribe(
            (result) => {
              if (!result.host_configs) {
                return;
              }
              this.hostConfigsInLab = result.host_configs.filter(
                  (config) => config.enable_ui_update);
              this.hostGroupNames = [...new Set(
                  this.hostConfigsInLab.map((config) => config.cluster_name))];
            },
            () => {
              this.notifier.showError('Failed to load host configs.');
            });
  }

  getTestHarnessImagesByTagPrefix() {
    return this.tfcClient
        .getTestHarnessImages(
            this.imageTagPrefix, DEFAULT_TEST_HARNESS_IMAGE_COUNT)
        .pipe(takeUntil(this.destroy))
        .subscribe(
            (result) => {
              if (!result.images) {
                return;
              }
              this.testHarnessImages = result.images;
            },
            () => {
              this.notifier.showError('Failed to load test harness images.');
            });
  }

  drawHostUpdateStateSummaryChart() {
    if (typeof google === 'undefined') {
      return;  // google === undefined in unit test env.
    }
    google.charts.safeLoad({'packages': ['corechart']});
    google.charts.setOnLoadCallback(() => {
      this.drawChartCallback(this.labInfo);
    });
  }

  drawChartCallback(labInfo: LabInfo|null) {
    if (!labInfo?.hostUpdateStateSummary) {
      return;
    }
    const summary = labInfo.hostUpdateStateSummary;
    const data = google.visualization.arrayToDataTable([
      ['Update State', 'Hosts'],
      ['Pending', summary.pending],
      ['Syncing', summary.syncing],
      ['Shutting Down', summary.shuttingDown],
      ['Restarting', summary.restarting],
      ['Succeeded', summary.succeeded],
      ['Timed Out', summary.timedOut],
      ['Errored', summary.errored],
      ['Unknown', summary.unknown],
      ['No Active Updates', this.getHostNoActiveUpdateCount(summary)],
    ]);
    const chart = new google.visualization.PieChart(
        this.updateSummaryChartElement.nativeElement);
    const options = {
      title: 'Hosts Update Summary',
      pieHole: 0.5,
      colors: [
        '#fcefc0',  // Light Yellow
        '#f7e5a1',  // Yellow
        '#f7e5a1',  // Yellow
        '#f7e5a1',  // Yellow
        '#9cf79f',  // Green
        '#ff754f',  // Red
        '#ff754f',  // Red
        '#ff754f',  // Red
        '#ffffff',  // White
      ],
      pieSliceText: 'none',
    };
    chart.draw(data, options);
  }

  getHostUpdatingCount(summary: HostUpdateStateSummary|null): number {
    return summary ?
        summary.syncing + summary.shuttingDown + summary.restarting :
        0;
  }

  getHostNoActiveUpdateCount(summary: HostUpdateStateSummary|null): number {
    return summary ? summary.total - summary.pending - summary.syncing -
            summary.shuttingDown - summary.restarting - summary.succeeded -
            summary.timedOut - summary.errored - summary.unknown :
                     0;
  }

  loadHostConfigsInSelectedHostGroup() {
    this.candidateHostConfigs = this.selectedHostGroup ?
        this.hostConfigsInLab.filter(
            (config) => config.cluster_name === this.selectedHostGroup) :
        this.hostConfigsInLab;
    this.hostNames =
        this.candidateHostConfigs.map((config) => config.hostname);
  }

  setSelectedHosts(hostNames: string[]) {
    this.selectedHosts =
        hostNames.includes(ALL_OPTIONS_VALUE) ? this.hostNames : hostNames;
  }

  onModeChange($event: MatRadioChange) {
    if ($event.value === UpdateMode.LAB) {
      this.selectedHostGroup = '';
      this.selectedHosts = [];
    } else if ($event.value === UpdateMode.HOST_GROUP) {
      this.selectedHosts = [];
    }
    this.loadHostConfigsInSelectedHostGroup();
  }

  getBatchUpdateHostMetadataRequest(): BatchUpdateHostMetadataRequest|null {
    if (!this.selectedImage) {
      this.notifier.showError('No test harness image is selected.');
      return null;
    }
    const selectedImageName = `${this.selectedImage.repo_name}:${
        this.selectedImage.test_harness_version}`;
    let hostnames: string[];
    if (this.selectedMode === UpdateMode.LAB) {
      hostnames = this.hostConfigsInLab.map(config => config.hostname);
    } else if (this.selectedMode === UpdateMode.HOST_GROUP) {
      hostnames = this.candidateHostConfigs.map(config => config.hostname);
    } else {
      hostnames = this.selectedHosts;
    }
    if (!hostnames || hostnames.length === 0) {
      this.notifier.showError('No host is selected.');
      return null;
    }
    return {
      hostnames,
      test_harness_image: selectedImageName,
    };
  }

  onConfirmSetImage() {
    this.disableSetImageButton = true;
    const requestBody = this.getBatchUpdateHostMetadataRequest();
    if (!requestBody) {
      this.disableSetImageButton = false;
      return;
    }
    this.tfcClient.batchUpdateHostMetadata(requestBody)
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.disableSetImageButton = false;
            }),
            )
        .subscribe(
            () => {
              this.notifier.showMessage(`Successfully set image <${
                  requestBody.test_harness_image}> on hosts: [${
                  requestBody.hostnames.join(', ')}]`);
            },
            (err) => {
              let message: string;
              if (err.error?.error?.errors) {
                // In production env, the error comes for TFC service behind
                // the API proxy, so it stores a structured error.
                message = err.error.error.errors[0].message;
              } else {
                // In dev or test env, the error is thrown directly from
                // the proxy request.
                message = err.message;
              }
              this.notifier.showError(
                  `Error when setting the image: ${message}`);
            },
        );
  }
}
