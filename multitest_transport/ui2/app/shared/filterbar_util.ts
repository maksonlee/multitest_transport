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

import {FilterOption} from '../services/mtt_lab_models';


/** Shared functions of the filter bar. */
export class FilterBarUtility {
  filterChanged = false;
  isAllSelected = false;
  searchCriteriaSnapshot = '';
  selectedColumn = '';
  /**
   * Avoid filtering again after setting the valueInput to the criteria string.
   */
  innerUpdate = false;

  constructor(
      public allOptions: FilterOption[],
      public filterBarColumns: string[],
      public searchCriteriaMapping: Map<string, string>,
      public maxDisplayOptions: number,
      public rootColumnType: string,
      public minKeywordLength: number,
      public columnsWithNoPreloadedOptions: string[],
  ) {}

  toggleAll() {
    this.isAllSelected = !this.isAllSelected;
    for (const option of this.getVisibleFilterOptions()) {
      option.selected = this.isAllSelected;
    }
    this.filterChanged = true;
    this.patchSelectAll();
  }

  patchSelectAll() {
    this.isAllSelected = this.getVisibleFilterOptions.length ===
        this.allOptions
            .filter((opt) => opt.selected && opt.type === this.selectedColumn)
            .length;
  }

  getVisibleFilterOptions(): FilterOption[] {
    return this.allOptions.filter(x => !x.hidden);
  }

  /** Whether a root column is selected. */
  isRoot(): boolean {
    return this.selectedColumn === '';
  }

  initFilterbarRoots() {
    const options = this.createFilterOptions(
        this.filterBarColumns.sort(), this.rootColumnType);
    this.appendFilterOptions(options);
  }

  appendFilterOptions(options: FilterOption[]) {
    this.allOptions = [...this.allOptions, ...options];
  }

  updateFilterOptions(options: FilterOption[], columnName: string) {
    this.allOptions = this.allOptions.filter(x => x.type !== columnName);
    this.appendFilterOptions(options);
  }

  createFilterOptions(
      values: string[], columnName: string, hidden: boolean = false,
      showCheckbox: boolean = false): FilterOption[] {
    const options: FilterOption[] = [];
    for (const value of values) {
      options.push(
          {value, selected: false, type: columnName, hidden, showCheckbox});
    }
    return options;
  }

  isRootColumn(value: string): boolean {
    return this.filterBarColumns.map(x => x.toLowerCase())
        .includes(value.toLowerCase());
  }

  hasFilter(): boolean {
    return this.allOptions.some((opt) => opt.selected);
  }

  /**
   * Filters search options for the filter bar.
   * @params searchingValue Search value on the property 'value'
   * @params searchingType Search value on the property 'type'
   */
  filterSearchOptions(searchingValue: string, searchingType: string = ''):
      FilterOption[] {
    if (this.innerUpdate) {
      this.innerUpdate = false;
      return this.allOptions;
    }
    if (!searchingValue && !searchingType) {
      // Makes all root options be visible
      for (const option of this.allOptions) {
        option.hidden = !(option.type === this.rootColumnType);
      }
    } else if (searchingValue && !searchingType) {
      // Does keyword search on root options and makes these root options be
      // visible
      for (const option of this.allOptions) {
        option.hidden = !(
            option.type === this.rootColumnType &&
            option.value.toLowerCase().includes(searchingValue.toLowerCase()));
      }
    } else if (!searchingValue && searchingType) {
      // Makes all leaf options of a specified root option be visible
      let count = 0;
      for (const option of this.allOptions) {
        if (option.type === searchingType && count < this.maxDisplayOptions) {
          option.hidden = false;
          count++;
        } else {
          option.hidden = true;
        }
      }
    } else if (searchingValue && searchingType) {
      // Does keyword search on leaf options of a specified root option and
      // makes these leaf options be visible
      if (searchingValue.length >= this.minKeywordLength) {
        let count = 0;
        for (const option of this.allOptions) {
          let hidden = true;
          if (option.type === searchingType &&
              option.value.toLowerCase().includes(
                  searchingValue.toLowerCase())) {
            if (count < this.maxDisplayOptions) {
              hidden = false;
              count++;
            }
          }
          option.hidden = hidden;
        }
      }
    }
    return this.allOptions;
  }
  getParameterName(columnName: string): string {
    return this.searchCriteriaMapping.get(columnName) || '';
  }

  setFilterOptionsSelected(columnName: string, options: string[]) {
    const filterOptions = this.allOptions.filter(
        x => x.type === columnName && options.includes(x.value));
    for (const option of filterOptions) {
      option.selected = true;
    }
  }

  displayRootFilterOptions() {
    this.filterSearchOptions('', '');
  }

  displayLeafFilterOptions(columnName: string) {
    this.selectedColumn = columnName;
    this.filterSearchOptions('', columnName);
    this.isAllSelected = false;
    this.innerUpdate = true;
  }
  toggleFilterOption(option: FilterOption) {
    const selectedOption = this.allOptions.find(
        (opt) => opt.value === option.value && opt.type === option.type);
    if (selectedOption) {
      selectedOption.selected = !selectedOption.selected;
      this.filterChanged = true;
    }
    this.patchSelectAll();
  }

  resetSearchSteps() {
    this.selectedColumn = '';
    this.isAllSelected = false;
    this.resetFilterBar();
  }

  /** Resets filterBar to initial display status. */
  resetFilterBar() {
    const leafItems = this.allOptions.filter(x => !x.hidden);
    for (const item of leafItems) {
      item.hidden = true;
    }
    const rootItems =
        this.allOptions.filter(x => x.type === this.rootColumnType && x.hidden);
    for (const item of rootItems) {
      item.hidden = false;
    }
  }

  getInputFilterOption(type: string): string {
    const option = this.allOptions.find(x => x.type === type);
    return option?.value || '';
  }

  getFilterBarColumnName(text: string): string {
    return this.filterBarColumns.find(
               x => x.toLowerCase() === text.toLowerCase().trim()) ||
        '';
  }


  /** Gets an existing filterOption or a new one. */
  getFilterOption(type: string, value: string, selected: boolean = false):
      FilterOption {
    return this.getVisibleFilterOptions().find(
               x => x.type === type && x.value === value) ||
        {
          value,
          selected,
          type,
          hidden: false,
          showCheckbox: false,
        };
  }

  /** Return the options belong to the 'type'. */
  getFilterOptions(type: string, selected: boolean): FilterOption[] {
    return this.allOptions.filter(
        x => x.type === type && x.selected === selected);
  }


  /** Unselects all options and removes input values. */
  resetFilterOptions() {
    this.clearSelectedFilterOptions();
    this.allOptions = this.allOptions.filter(
        x => this.columnsWithNoPreloadedOptions.includes(x.type) === false);
  }

  /** Unselects filter options. */
  clearSelectedFilterOptions(columnName: string = '') {
    const options = columnName ?
        this.allOptions.filter(x => x.type === columnName && x.selected) :
        this.allOptions.filter(x => x.selected);
    for (const option of options) {
      option.selected = false;
    }
  }

  /**
   * Removes input options by the column name.
   * @params columnName The column that allows users input their criteria. i.e.
   * Device serial
   */
  clearInputOption(columnName: string) {
    this.allOptions = this.allOptions.filter(x => x.type !== columnName);
  }

  /**
   * Renders selected options to a string. i.e. Hostname: (HOST-1)
   * Pool:(Pool-3).
   */
  getSelectedOptionString(): string {
    const result: string[] = [];
    for (const column of this.filterBarColumns) {
      const options = this.getFilterOptions(column, true);
      if (options.length) {
        if (this.isInputColumn(column)) {
          result.push(
              `${column}: (${options.map((opt) => opt.value).join(' | ')})`);
        } else {
          result.push(
              `${column}: (${options.map((opt) => opt.value).join(' | ')})`);
        }
      }
    }
    return result.join(' ');
  }

  /**
   * Whether the user has selected an input column and then is editing the input
   * value or not.
   */
  isEditingInputColumn(): boolean {
    return this.isInputColumn(this.selectedColumn);
  }

  isInputColumn(name: string): boolean {
    return this.columnsWithNoPreloadedOptions.indexOf(name) > -1;
  }

  /**
   * Whether the selected filter options match the input values of a specified
   * column (e.g. Pool) in the search criteria string.
   */
  isSelectedFilterOptionsMatchInputValues(
      newSelectedValues: string[], columnName: string): boolean {
    const oldValues =
        this.allOptions.filter(x => x.type === columnName && x.selected)
            .map(x => x.value);
    if (!newSelectedValues || oldValues.length !== newSelectedValues.length ||
        !newSelectedValues.every(x => oldValues.includes(x))) {
      return true;
    }
    return false;
  }

  /**
   * Applies new selection on the filter options. Which includes clear all
   * selection and apply new one.
   */
  applySelection(newOptions: string[], columnName: string) {
    this.filterChanged = true;
    this.clearSelectedFilterOptions(columnName);
    this.selectFilterOptions(newOptions, columnName);
  }

  selectFilterOptions(newOptions: string[], columnName: string) {
    newOptions = newOptions.map(x => x.toLowerCase());
    const options = this.allOptions.filter(
        x => x.type === columnName &&
            newOptions.includes(x.value.toLowerCase()) && !x.selected);
    for (const option of options) {
      option.selected = true;
    }
  }

  /**
   * Adds a new filter option. When there is no options of a specified column
   * can be provided by the filter menu, users can input the option by
   * themselves.
   */
  addNewFilterOption(value: string, columnName: string) {
    value = value.replace('=', ':').trim();
    const filterOption = this.getFilterOption(columnName, value, true);
    const oldOption = this.allOptions.findIndex(x => x.type === columnName);
    if (oldOption > -1) {
      this.allOptions.splice(oldOption, 1);
    }
    this.allOptions.push(filterOption);
    this.filterChanged = true;
  }

  /**
   * Extracts section string for the column.
   * @params inputValue The whole search criteria. i.e. Pool:(Pool-1|Pool-2)
   * Lab:(Lab-1)
   * @params columnName 'Pool' on the above example.
   */
  extractSection(inputValue: string, columnName: string): string {
    const pattern = new RegExp(`${columnName}:.+?\\)`, 'i');
    const result = inputValue.match(pattern);
    return result ? result[0] : '';
  }

  /**
   * Extracts unique values from the section.
   * @params section i.e. Pool:(Pool-1|Pool-2)
   */
  extractValues(section: string): string[] {
    const patternValue = new RegExp('\\(.+?\\)$', 'i');
    const values = section.match(patternValue);
    const matchedValueString = values ? values[0] : '';
    return matchedValueString.slice(1, matchedValueString.length - 1)
        .split('|')
        .map(x => x.trim())
        .filter((value, index, arr) => arr.indexOf(value) === index);
  }
}

// TODO: Remove below blocks after device list and host list use above functions
// instead.
/**
 * Extracts section string for the column.
 * @params inputValue The whole search criteria. i.e. Pool:(Pool-1|Pool-2)
 * Lab:(Lab-1)
 * @params columnName 'Pool' on the above example.
 */
export function extractSection(inputValue: string, columnName: string): string {
  const pattern = new RegExp(`${columnName}:.+?\\)`, 'i');
  const result = inputValue.match(pattern);
  return result ? result[0] : '';
}

/**
 * Extracts unique values from the section.
 * @params section i.e. Pool:(Pool-1|Pool-2)
 */
export function extractValues(section: string): string[] {
  const patternValue = new RegExp('\\(.+?\\)$', 'i');
  const values = section.match(patternValue);
  const matchedValueString = values ? values[0] : '';
  return matchedValueString.slice(1, matchedValueString.length - 1)
      .split('|')
      .map(x => x.trim())
      .filter((value, index, arr) => arr.indexOf(value) === index);
}

/** Detects any search criteria changed on the column. */
export function detectFilterOptionsChanged(
    allOptions: FilterOption[], newSelectedValues: string[],
    columnName: string): boolean {
  const oldValues = allOptions.filter(x => x.type === columnName && x.selected)
                        .map(x => x.value);
  if (!newSelectedValues || oldValues.length !== newSelectedValues.length ||
      !newSelectedValues.every(x => oldValues.includes(x))) {
    return true;
  }
  return false;
}

/** Unselects filter options. */
export function clearSelectedFilterOptions(
    allOptions: FilterOption[], columnName: string): boolean {
  const options = allOptions.filter(x => x.type === columnName && x.selected);
  for (const option of options) {
    option.selected = false;
  }
  return allOptions.every(x => !x.selected);
}

/** Selects filter options. */
export function selectFilterOptions(
    allOptions: FilterOption[], newOptions: string[],
    columnName: string): FilterOption[] {
  newOptions = newOptions.map(x => x.toLowerCase());
  const options = allOptions.filter(
      x => x.type === columnName &&
          newOptions.includes(x.value.toLowerCase()) && !x.selected);
  for (const option of options) {
    option.selected = true;
  }
  return allOptions;
}

/**
 * Filters search options for the filterbar.
 * @params allOptions Full unfiltered options
 * @params searchingValue Search value on the property 'value'
 * @params searchingType Search value on the property 'type'
 * @params rootType Root nodes' value on the property 'type'
 * @params maxFilterOptions Max display items
 * @params minLength The length to enable keyword search
 */
export function filterSearchOptions(
    allOptions: FilterOption[], searchingValue: string,
    searchingType: string = '', rootType: string, maxFilterOptions: number,
    minLength: number): FilterOption[] {
  if (!searchingValue && !searchingType) {
    for (const option of allOptions) {
      option.hidden = !(option.type === rootType);
    }
  } else if (searchingValue && !searchingType) {
    // keyword search on root
    for (const option of allOptions) {
      option.hidden =
          !(option.type === rootType &&
            option.value.toLowerCase().includes(searchingValue.toLowerCase()));
    }
  } else if (!searchingValue && searchingType) {
    // filter options belong to the root
    let count = 0;
    for (const option of allOptions) {
      if (option.type === searchingType && count < maxFilterOptions) {
        option.hidden = false;
        count++;
      } else {
        option.hidden = true;
      }
    }
  } else if (searchingValue && searchingType) {
    // keyword search on leaf
    if (searchingValue.length >= minLength) {
      let count = 0;
      for (const option of allOptions) {
        let hidden = true;
        if (option.type === searchingType &&
            option.value.toLowerCase().includes(searchingValue.toLowerCase())) {
          if (count < maxFilterOptions) {
            hidden = false;
            count++;
          }
        }
        option.hidden = hidden;
      }
    }
  }
  return allOptions;
}

/** Resets filterBar to initial display status. */
export function resetFilterBar(
    allOptions: FilterOption[], rootType: string): FilterOption[] {
  const leafItems = allOptions.filter(x => !x.hidden);
  for (const item of leafItems) {
    item.hidden = true;
  }
  const rootItems = allOptions.filter(x => x.type === rootType && x.hidden);
  for (const item of rootItems) {
    item.hidden = false;
  }
  return allOptions;
}
