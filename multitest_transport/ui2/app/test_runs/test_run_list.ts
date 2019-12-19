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
import {COMMA, ENTER} from '@angular/cdk/keycodes';
import {AfterViewInit, Component, ElementRef, HostListener, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {MatChipInputEvent} from '@angular/material/chips';
import {MatTableDataSource} from '@angular/material/table';
import {ActivatedRoute, Router} from '@angular/router';
import {ReplaySubject} from 'rxjs';
import {finalize, takeUntil} from 'rxjs/operators';

import {MttClient} from '../services/mtt_client';
import {TableColumn, TestRunState, TestRunSummary} from '../services/mtt_models';
import {Notifier} from '../services/notifier';
import {OverflowListType} from '../shared/overflow_list';
import {DEFAULT_PAGE_SIZE, Paginator} from '../shared/paginator';
import {buildApiErrorMessage} from '../shared/util';

/** A component for displaying a list of test runs. */
@Component({
  selector: 'test-run-list',
  styleUrls: ['test_run_list.css'],
  templateUrl: './test_run_list.ng.html',
})
export class TestRunList implements OnInit, AfterViewInit, OnDestroy {
  readonly PAGE_SIZE_OPTIONS = [10, 20, 50];
  readonly COLUMN_DISPLAY_STORAGE_KEY = 'TEST_RUN_LIST_COLUMN_DISPLAY';
  readonly OverflowListType = OverflowListType;

  // track whether the test runs were loaded at least once
  private initialized = false;
  // pagination tokens used to go backwards or forwards
  prevPageToken?: string;
  nextPageToken?: string;

  @Input() selectable = false;
  @Input()
  displayColumns = [
    'test_name', 'test_package', 'run_target', 'device_build', 'device_product',
    'labels', 'create_time', 'status', 'view'
  ];
  @Input() initialSelection = [];
  @Input() headerTitle = 'Test Runs';

  columns: TableColumn[] = [
    {fieldName: 'select', displayName: 'Select', removable: false, show: false},
    {fieldName: 'test_name', displayName: 'Test', removable: false, show: true},
    {
      fieldName: 'test_package',
      displayName: 'Test Package',
      removable: true,
      show: true
    },
    {
      fieldName: 'run_target',
      displayName: 'Run Targets',
      removable: true,
      show: true
    },
    {
      fieldName: 'device_build',
      displayName: 'Device Build',
      removable: true,
      show: true
    },
    {
      fieldName: 'device_product',
      displayName: 'Product',
      removable: true,
      show: true
    },
    {fieldName: 'labels', displayName: 'Labels', removable: true, show: true},
    {
      fieldName: 'create_time',
      displayName: 'Created',
      removable: true,
      show: true
    },
    {fieldName: 'status', displayName: 'Status', removable: false, show: true},
    {
      fieldName: 'failures',
      displayName: 'Test Failures',
      removable: false,
      show: true
    },
    {fieldName: 'view', displayName: 'View', removable: false, show: true},
  ];
  readonly separatorKeysCodes: number[] = [ENTER, COMMA];
  isLoading = false;
  dataSource = new MatTableDataSource<TestRunSummary>([]);
  selection = new SelectionModel<TestRunSummary>(true, this.initialSelection);
  filters: string[] = [];

  allStates: TestRunState[] = Object.values(TestRunState);
  selectedStates: TestRunState[] = [];

  @ViewChild('table', {static: false, read: ElementRef}) table!: ElementRef;
  isTableScrolled = false;

  @ViewChild(Paginator, {static: false}) paginator!: Paginator;

  private readonly destroy = new ReplaySubject();

  constructor(
      private readonly notifier: Notifier, private readonly mtt: MttClient,
      private readonly route: ActivatedRoute, private readonly router: Router,
      private readonly liveAnnouncer: LiveAnnouncer) {}

  ngOnInit() {
    if (this.selectable) {
      this.displayColumns.unshift('select');
    }
  }

  ngAfterViewInit() {
    // handle asynchronously to prevent modifying view in ngAfterViewInit
    setTimeout(() => this.route.queryParams.subscribe(params => {
      // parse parameters and check if the test runs should be reloaded
      const pageToken = params['page'];
      const size = params['size'] ? Number(params['size']) : DEFAULT_PAGE_SIZE;
      const filters = params['filter'] ? [].concat(params['filter']) : [];
      if (!this.initialized || this.shouldReload(size, filters, pageToken)) {
        // if not initialized or if parameters changed, reload test runs
        this.initialized = true;
        this.prevPageToken = undefined;
        this.nextPageToken = pageToken;
        this.paginator.pageSize = size;
        this.filters = filters;
        this.load(false);
      }
      // initialize display columns
      this.loadDisplayColumnFromLocalStorage();
      this.setDisplayColumn();
    }));
  }

  ngOnDestroy() {
    this.destroy.next();
  }

  @HostListener('window:resize', [])
  onWindowResize() {
    this.checkTableScrolled();
  }

  /** Checks whether the pagination parameters have changed. */
  private shouldReload(size: number, filters: string[], pageToken?: string) {
    return size !== this.paginator.pageSize ||
        pageToken !== this.prevPageToken ||
        !(this.filters.length === filters.length &&
          this.filters.every((item, index) => {
            return filters.indexOf(item) > -1;
          }));
  }

  /**
   * Loads a page of test runs according to the stored page tokens.
   * @param previous true to go to the previous page
   */
  load(previous = false) {
    this.isLoading = true;
    this.liveAnnouncer.announce('Loading', 'polite');
    this.mtt
        .getTestRuns(
            this.paginator.pageSize,
            previous ? this.prevPageToken : this.nextPageToken, previous,
            this.filters, this.selectedStates)
        .pipe(
            takeUntil(this.destroy),
            finalize(() => {
              this.isLoading = false;
            }),
            )
        .subscribe(
            result => {
              this.dataSource.data = result.test_runs || [];
              this.prevPageToken = result.prev_page_token || undefined;
              this.nextPageToken = result.next_page_token || undefined;
              this.updatePageParams();
              this.liveAnnouncer.announce('Test results loaded', 'assertive');
            },
            error => {
              this.notifier.showError(
                  'Failed to load test run list.', buildApiErrorMessage(error));
            },
        );
  }

  /** Updates the paginator and stores its parameters in the query string. */
  private updatePageParams() {
    // determine whether there are more results
    this.paginator.hasPrevious = !!this.prevPageToken;
    this.paginator.hasNext = !!this.nextPageToken;
    // store pagination parameters
    this.router.navigate([], {
      queryParams: {
        page: this.prevPageToken || null,
        size: this.paginator.pageSize !== DEFAULT_PAGE_SIZE ?
            this.paginator.pageSize :
            null,
        filter: this.filters.length > 0 ? this.filters : null,
      }
    });
  }

  /** Page size change handler, will reload the first page of results. */
  resetPageTokenAndReload() {
    this.prevPageToken = undefined;
    this.nextPageToken = undefined;
    this.load(false);
  }

  /** Check if table is scrolled to the right to update sticky styling. */
  checkTableScrolled() {
    const el = this.table.nativeElement;
    this.isTableScrolled = el.scrollLeft === el.scrollWidth - el.clientWidth;
  }

  /** Switch to the test run details page. */
  viewDetails(id: string) {
    this.router.navigate([`test_runs/${id}`], {queryParamsHandling: 'merge'});
  }

  /* Whether the number of selected elements matches the total number of rows */
  isAllSelected(): boolean {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  /* Selects all rows if they are not all selected; otherwise clear
   * selection */
  toggleSelected() {
    if (this.isAllSelected()) {
      this.selection.clear();
    } else {
      for (const row of this.dataSource.data) {
        this.selection.select(row);
      }
    }
  }

  /* Update column display data */
  toggleDisplayColumn(event: Event, show: boolean, columnIndex: number) {
    event.stopPropagation();
    this.columns[columnIndex].show = !show;
    this.setDisplayColumn();
  }

  /* Apply column display data */
  setDisplayColumn() {
    this.displayColumns =
        this.columns.filter(c => c.show).map(c => c.fieldName);
    this.storeDisplayColumnToLocalStorage();
    setTimeout(() => {
      this.checkTableScrolled();
    });
  }

  /* Store column display data to local storage */
  storeDisplayColumnToLocalStorage() {
    window.localStorage.setItem(
        this.COLUMN_DISPLAY_STORAGE_KEY, JSON.stringify(this.columns));
  }

  /* Loading column display data from local storage if there is any */
  loadDisplayColumnFromLocalStorage() {
    const storedData =
        window.localStorage.getItem(this.COLUMN_DISPLAY_STORAGE_KEY);

    if (storedData) {
      const storedTableColumns: TableColumn[] = JSON.parse(storedData);
      this.columns = this.columns.map((c) => {
        const storedColumn =
            storedTableColumns.find((s) => s.fieldName === c.fieldName);
        if (storedColumn) {
          c.show = storedColumn.show;
        }
        return c;
      });
    }
  }

  /* Add input to chips and reload */
  addFilter(event: MatChipInputEvent) {
    const input = event.input;
    const value = event.value;

    if ((value || '').trim() && this.filters.indexOf(value.trim()) === -1) {
      this.filters.push(value.trim());
      this.resetPageTokenAndReload();
    }

    if (input) {
      input.value = '';
    }
  }

  /* Remove filter and reload */
  removeFilter(filter: string) {
    const index = this.filters.indexOf(filter);
    if (index >= 0) {
      this.filters.splice(index, 1);
      this.resetPageTokenAndReload();
    }
  }

  /* When clicked on the chip, add it to filter and reload */
  chipClicked(label: string) {
    if (this.filters.indexOf(label) === -1) {
      this.filters.push(label);
      this.resetPageTokenAndReload();
    }
  }
}
