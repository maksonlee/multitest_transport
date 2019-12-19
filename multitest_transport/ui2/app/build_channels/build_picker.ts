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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {SelectionModel} from '@angular/cdk/collections';
import {Component, Inject, OnDestroy, OnInit, ViewChild, ViewEncapsulation} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {MatTable} from '@angular/material/table';
import {MatTabChangeEvent} from '@angular/material/tabs';
import {ReplaySubject, Subject, Subscription} from 'rxjs';
import {debounceTime, delay, filter, finalize, first, takeUntil} from 'rxjs/operators';

import {AUTH_DELAY, AuthService} from '../services/auth_service';
import {AuthEventState} from '../services/auth_service';
import {MttClient} from '../services/mtt_client';
import {BuildChannel, BuildItem, isBuildChannelAvailable} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {InfiniteScrollLoadEvent} from '../shared/infinite_scroll';
import {isFnmatchPattern, buildApiErrorMessage} from '../shared/util';

enum ProviderType {
  LOCAL_STORE = 'Local File Store',
  GOOGLE_DRIVE = 'Google Drive',
  ANDROID = 'Android',
  GOOGLE_CLOUD_STORAGE = 'Google Cloud Storage'
}

/**
 * Data format when passed to BuildPicker
 * @param searchBarUrlValue: a web url or an mtt url directory displayed in
 * searchbar
 * @param searchBarFilenameValue: a filename displayed in search bar
 * @param buildChannelId: initial active build channel id
 * @param buildChannels: a list of build channel object
 */
export interface BuildPickerData {
  searchBarUrlValue: string;
  searchBarFilenameValue: string;
  buildChannelId: string;
  buildChannels: BuildChannel[];
}

/**
 * A state object for BuildPicker
 * @param searchBarUrlValue: an url which can be a path or full url
 * @param searchBarFilenameValue: a filename which can be glob pattern
 */
export interface BuildPickerTabState {
  searchBarUrlValue: string;
  searchBarFilenameValue: string;
}

/**
 * Build Picker
 * This component is used to select resource urls from build channels
 */
@Component({
  selector: 'build-picker',
  styleUrls: ['build_picker.css'],
  templateUrl: './build_picker.ng.html',
  encapsulation: ViewEncapsulation.None,
})
export class BuildPicker implements OnInit, OnDestroy {
  isBuildChannelAvailable = isBuildChannelAvailable;
  providerType = ProviderType;
  private readonly destroy = new ReplaySubject<void>();
  isFnmatchPattern = isFnmatchPattern;

  /** Tab related variable */
  selectedTabIndex = 0;
  selectedBuildChannel?: BuildChannel;

  /** Table related variable */
  buildItems: BuildItem[] = [];
  buildItemsSubscription?: Subscription;
  nextPageToken: string = '';
  isLoadingBuildItems = false;
  columnsToDisplay = ['name', 'description', 'timestamp', 'size', 'navIcon'];
  @ViewChild(MatTable, {static: false}) table!: MatTable<{}>;
  selection = new SelectionModel<BuildItem>(
      /*allow multi select*/ false, []);

  /** Search bar related variable */
  searchBarUrlValue = '';
  searchBarFilenameValue = '';

  /** Track build picker state when switch between tabs */
  buildPickerTabStateMap: {[key: number]: BuildPickerTabState} = {};

  private readonly searchUpdated = new Subject<string>();

  ngOnDestroy() {
    this.destroy.next();
  }

  constructor(
      public dialogRef: MatDialogRef<BuildPicker>,
      @Inject(MAT_DIALOG_DATA) public data: BuildPickerData,
      private readonly liveAnnouncer: LiveAnnouncer,
      private readonly mttClient: MttClient,
      private readonly authService: AuthService,
      private readonly notifier: Notifier) {
    // When search updated, reload the current build list
    this.searchUpdated.asObservable()
        .pipe(debounceTime(200), takeUntil(this.destroy))
        .subscribe(
            result => {
              this.loadBuildList();
            },
            error => {
              // TODO: Refine error handling in build picker
              console.error(error);
            });
  }

  /**
   * On selecting an url, close the dialog
   */
  selectUrl(isWebUrl: boolean) {
    this.dialogRef.close({
      searchBarUrlValue: isWebUrl ? this.searchBarUrlValue :
                                    this.getBuildUrl(this.searchBarUrlValue),
      searchBarFilenameValue: this.searchBarFilenameValue
    });
  }

  ngOnInit() {
    // Monitor authorization service status.
    this.authService
        .getAuthProgress()
        // delay is needed for data to be populated in database
        .pipe(
            filter(x => x.type === AuthEventState.COMPLETE), delay(AUTH_DELAY),
            takeUntil(this.destroy))
        .subscribe(
            res => {
              if (res.type === AuthEventState.COMPLETE) {
                // reload build channel data
                this.loadBuildChannels();
              }
            },
            error => {
              this.notifier.showError(
                  'Authentication error.', buildApiErrorMessage(error));
            });

    this.searchBarUrlValue = this.data.searchBarUrlValue;
    this.searchBarFilenameValue = this.data.searchBarFilenameValue;

    // Record initial state
    this.buildPickerTabStateMap[this.selectedTabIndex] = {
      searchBarUrlValue: this.searchBarUrlValue,
      searchBarFilenameValue: this.searchBarFilenameValue
    };

    // Set the current tab based on buildChannelId
    if (this.data.buildChannelId.length) {
      const idx = this.data.buildChannels.map(x => x.id).indexOf(
          this.data.buildChannelId);
      this.selectedBuildChannel = this.data.buildChannels[idx];
      // Add 1 because the 0th index is web url
      this.selectedTabIndex = idx + 1;
      this.loadBuildList();
    }
  }

  loadBuildChannels() {
    this.mttClient.getBuildChannels().pipe(first()).subscribe(
        result => {
          this.data.buildChannels = result.build_channels || [];
          this.selectedBuildChannel =
              this.data.buildChannels[this.selectedTabIndex - 1];
          this.loadBuildList();
        },
        error => {
          this.notifier.showError(
              'Failed to load build channels.', buildApiErrorMessage(error));
        });
  }

  /**
   * Listener for selected tab change event
   * Note: 0th tab is always 'By Url' where user provide the web url
   * The other tabs could include Google Drive, Local file store, and more
   * @param tabEvent A tab change event
   */
  onSelectedTabChange(tabEvent: MatTabChangeEvent) {
    // When switching between tabs, it's possible that one subscription
    // is still loading while the second subscription started. Thus, it's
    // possible that first subscription finishes even later than then
    // second subscription, resulting in conflicting data. Unsubscribe can
    // resolve this issue.
    if (this.buildItemsSubscription) {
      this.isLoadingBuildItems = false;
      this.buildItemsSubscription.unsubscribe();
    }

    // Save the state before tab change
    this.buildPickerTabStateMap[this.selectedTabIndex] = {
      searchBarUrlValue: this.searchBarUrlValue,
      searchBarFilenameValue: this.searchBarFilenameValue
    };
    // Load old state if exist
    this.selectedTabIndex = tabEvent.index;
    const state = this.buildPickerTabStateMap[this.selectedTabIndex];
    if (state) {
      this.searchBarUrlValue = state.searchBarUrlValue || '';
      this.searchBarFilenameValue = state.searchBarFilenameValue || '';
    } else {
      this.searchBarUrlValue = '';
      this.searchBarFilenameValue = '';
    }
    this.nextPageToken = '';
    this.selection.clear();

    this.selectedBuildChannel = this.data.buildChannels[tabEvent.index - 1];
    this.loadBuildList();
  }

  onFilenameValueChange(newFilename: string) {
    this.searchBarFilenameValue = newFilename;
  }

  /**
   * In search bar, when the value changes, fire a searchUpdated event with
   * the updated searchValue
   * @param searchValue
   */
  onSearchBarValueChange(searchValue: string) {
    this.searchUpdated.next(searchValue);
    this.selection.clear();
  }

  /**
   * Load build item list.
   * @param nextPageToken Next page token indicate there's more content left
   * in the page
   */
  loadBuildList(nextPageToken?: string|undefined) {
    // Don't load if buildchannel is not defined
    // Don't load if the selectedBuildChannel is not available/not authenticated
    // Don't load if it's a glob pattern
    if (!this.selectedBuildChannel ||
        !isBuildChannelAvailable(this.selectedBuildChannel) ||
        isFnmatchPattern(this.searchBarUrlValue)) {
      return;
    }
    // Clear builds when nextPageToken is undefined (new path is being loaded)
    if (!nextPageToken) {
      this.buildItems.length = 0;
    }
    // Load build item
    const path =
        this.selectedBuildChannel.provider_name === ProviderType.LOCAL_STORE ?
        '' :
        this.searchBarUrlValue;

    this.isLoadingBuildItems = true;
    this.liveAnnouncer.announce('Loading', 'polite');
    this.buildItemsSubscription =
        this.mttClient
            .listBuildItems(this.selectedBuildChannel.id, path, nextPageToken)
            .pipe(takeUntil(this.destroy))
            .pipe(finalize(() => {
              this.isLoadingBuildItems = false;
            }))
            .subscribe(
                result => {
                  this.buildItems =
                      this.buildItems.concat(result.build_items || []);
                  this.nextPageToken = result.next_page_token || '';
                  if (this.table) {
                    this.table.renderRows();
                  }
                  this.liveAnnouncer.announce(
                      'Build items loaded', 'assertive');
                },
                error => {
                  // TODO: Refine error handling in build picker
                  this.buildItems.length = 0;
                  console.error(error);
                });
  }

  /**
   * In mat table, on clicking a row (a BuildItem), set selected item
   * to current item
   * @param row BuildItem
   */
  selectFile(row: BuildItem) {
    if (row.is_file) {
      this.selection.select(row);
      this.searchBarFilenameValue = row.name;
    }
  }

  /**
   * In mat table, on double clicking a row (a BuildItem), update breadcrumb
   * and searchbar
   * @param row
   */
  openFolder(row: BuildItem) {
    if (row.is_file) {
      // TODO: [MTT][UI2][Build Picker] Sync with design on double
      // click on a file
      return;
    }
    this.selection.clear();
    this.onBreadCrumbPathChange(row.path);
  }

  getBuildUrl(url: string) {
    return 'mtt:///' + this.selectedBuildChannel!.id + (url.length ? '/' : '') +
        url;
  }

  /**
   * Triggered when breadcrumb path has changed
   * @param updatedSearchBarValue Current Search Bar Value
   */
  onBreadCrumbPathChange(updatedSearchBarValue: string) {
    this.searchBarUrlValue = updatedSearchBarValue;
    this.searchBarFilenameValue = '';
    this.loadBuildList();
    this.selection.clear();
  }

  /**
   * When scrolling the table, this action will be triggered when more content
   * is needed.
   * @param event An InfiniteScrollLoadEvent event
   */
  onScrollLoad(event: InfiniteScrollLoadEvent) {
    event.completed = this.loadMore().then(() => this.nextPageToken.length > 0);
  }

  async loadMore() {
    // To avoid double loading, it's possible that multiple loads are happending
    // we only load if previous load finish
    if (this.isLoadingBuildItems) {
      return;
    }
    await this.loadBuildList(this.nextPageToken);
  }

  /**
   * Authorize Build Channel
   * @param buildChannelId A buildchannel id
   */
  authorize(buildChannelId: string) {
    this.authService.startAuthFlow(buildChannelId);
  }

  /**
   * Returns true if using a GCS build channel and the search bar is empty
   */
  isMissingGcsBucket(): boolean {
    if (this.selectedBuildChannel &&
        this.selectedBuildChannel.provider_name ===
            ProviderType.GOOGLE_CLOUD_STORAGE &&
        this.searchBarUrlValue === '') {
      return true;
    }
    return false;
  }
}
