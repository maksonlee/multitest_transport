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

import {clearSelectedFilterOptions, detectFilterOptionsChanged, extractSection, extractValues, FilterBarUtility, filterSearchOptions, resetFilterBar, selectFilterOptions} from './filterbar_util';

describe('filterbar util test', () => {
  const rootType = 'ROOT';
  const maxCount = 30;
  const minLength = 2;
  const columnName = 'category1';
  const value1 = 'value1';
  const value2 = 'value2';
  const inputColumn = 'inputColumn';
  const allOptions: FilterOption[] = [
    {
      value: columnName,
      selected: false,
      type: rootType,
      hidden: false,
      showCheckbox: false,
    },
    {
      value: 'category2',
      selected: false,
      type: rootType,
      hidden: false,
      showCheckbox: false,
    },
    {
      value: inputColumn,
      selected: false,
      type: rootType,
      hidden: false,
      showCheckbox: false,
    },
    {
      value: value1,
      selected: true,
      type: columnName,
      hidden: false,
      showCheckbox: false,
    },
    {
      value: value2,
      selected: false,
      type: columnName,
      hidden: false,
      showCheckbox: false,
    },
    {
      value: 'value3',
      selected: false,
      type: 'abc',
      hidden: false,
      showCheckbox: false,
    },
  ];
  const searchCriteriaMapping = new Map<string, string>([
    ['Device', columnName],
    ['Host', 'category2'],
  ]);
  const filterBarUtility = new FilterBarUtility(
      allOptions, [columnName, 'category2', inputColumn], searchCriteriaMapping,
      30, rootType, 1, [inputColumn]);

  it('extracts section from input string correctly', () => {
    const input = 'Pool:(Pool-1|Pool-2) Lab:(Lab-1)';
    const result = extractSection(input, 'Pool');
    expect(result).toEqual('Pool:(Pool-1|Pool-2)');
  });

  it('extracts values from section correctly', () => {
    const section = 'Pool:(Pool-1|Pool-2)';
    const result = extractValues(section);
    expect(result.length).toEqual(2);
    expect(result[0]).toEqual('Pool-1');
    expect(result[1]).toEqual('Pool-2');
  });

  it('detects filter options changed correctly', () => {
    expect(detectFilterOptionsChanged(allOptions, ['value2'], columnName))
        .toEqual(true);
    expect(detectFilterOptionsChanged(allOptions, ['value1'], columnName))
        .toEqual(false);
  });

  it('clears selected filter options correctly', () => {
    const result = clearSelectedFilterOptions(allOptions, columnName);
    expect(result).toEqual(true);
  });

  it('selects filter options correctly', () => {
    const newValues = [value1, value2];
    const result = selectFilterOptions(allOptions, newValues, columnName);
    expect(result.filter(x => x.selected).length).toEqual(newValues.length);
  });

  it('returns root options correctly', () => {
    let options =
        filterSearchOptions(allOptions, '', '', rootType, maxCount, minLength);
    options = options.filter(x => !x.hidden);
    expect(options.length).toEqual(3);
    expect(options[0].value).toEqual('category1');
    expect(options[1].value).toEqual('category2');
  });

  it('should search root options correctly', () => {
    let options =
        filterSearchOptions(allOptions, '1', '', rootType, maxCount, minLength);
    options = options.filter(x => !x.hidden);
    expect(options.length).toEqual(1);
    expect(options[0].value).toEqual(columnName);
  });

  it('returns options belong to the type correctly', () => {
    let options = filterSearchOptions(
        allOptions, '', columnName, rootType, maxCount, minLength);
    options = options.filter(x => !x.hidden);
    expect(options.length).toEqual(2);
    expect(options[0].value).toEqual(value1);
    expect(options[1].value).toEqual(value2);
  });

  it('should search keyword with type correctly', () => {
    let options = filterSearchOptions(
        allOptions, value2, columnName, rootType, maxCount, minLength);
    options = options.filter(x => !x.hidden);
    expect(options.length).toEqual(1);
    expect(options[0].value).toEqual(value2);
  });

  it('can reset filterbar display status', () => {
    const newOptions = resetFilterBar(allOptions, rootType);
    expect(newOptions.filter(x => x.type === rootType && !x.hidden).length)
        .toEqual(3);
    expect(newOptions.filter(x => x.type !== rootType && x.hidden).length)
        .toEqual(3);
    expect(
        filterBarUtility.allOptions.filter(x => x.type !== rootType && x.hidden)
            .length)
        .toEqual(3);
  });

  it('can run toggleAll correctly', () => {
    filterBarUtility.isAllSelected = false;
    filterBarUtility.toggleAll();
    expect(filterBarUtility.isAllSelected).toEqual(true);
  });

  it('can get isRoot correctly when selectedColumn is empty', () => {
    filterBarUtility.selectedColumn = '';
    expect(filterBarUtility.isRoot()).toEqual(true);
  });

  it('can get isRoot correctly when selectedColumn is Pool', () => {
    filterBarUtility.selectedColumn = 'Pool';
    expect(filterBarUtility.isRoot()).toEqual(false);
  });

  it('calls createFilterOptions correctly', () => {
    const options =
        filterBarUtility.createFilterOptions([value1, value2], columnName);
    expect(options.length).toEqual(2);
  });

  it('gets isRootColumn correctly', () => {
    expect(filterBarUtility.isRootColumn('test')).toEqual(false);
    expect(filterBarUtility.isRootColumn(columnName)).toEqual(true);
  });

  it('calls getParameterName correctly', () => {
    const key = 'Host Group';
    const value = searchCriteriaMapping.get(key) || '';
    expect(filterBarUtility.getParameterName(key)).toEqual(value);
  });

  it('sets the options to selected correctly', () => {
    filterBarUtility.setFilterOptionsSelected(columnName, [value2]);
    expect(
        filterBarUtility.allOptions
            .filter(
                x => x.type === columnName && x.value === value2 && x.selected)
            .length)
        .toEqual(1);
  });

  it('sets the leaf options correctly', () => {
    filterBarUtility.displayLeafFilterOptions(columnName);
    const options = filterBarUtility.getVisibleFilterOptions();
    expect(options.length).toEqual(2);
    expect(options[0].value).toEqual(value1);
    expect(options[1].value).toEqual(value2);
  });

  it('calls toggleFilterOption correctly', () => {
    const option =
        filterBarUtility.createFilterOptions([value1], columnName)[0];
    filterBarUtility.toggleFilterOption(option);
    expect(filterBarUtility.allOptions
               .filter(x => x.type === columnName && x.value === value1)
               .length)
        .toEqual(1);
    expect(filterBarUtility.filterChanged).toEqual(true);
  });

  it('resets the search steps correctly', () => {
    filterBarUtility.resetSearchSteps();
    expect(filterBarUtility.selectedColumn).toEqual('');
    expect(filterBarUtility.isAllSelected).toEqual(false);
    expect(filterBarUtility.allOptions
               .filter(x => x.type === rootType && x.hidden === false)
               .length)
        .toEqual(3);
  });

  it('calls getFilterBarColumnName correctly', () => {
    const name = filterBarUtility.getFilterBarColumnName(columnName);
    expect(name).toEqual(columnName);
  });

  it('gets the criteria string from the selected options correctly', () => {
    filterBarUtility.clearSelectedFilterOptions(columnName);
    const option = filterBarUtility.getFilterOption(columnName, value1);
    filterBarUtility.toggleFilterOption(option);
    const selectedString = filterBarUtility.getSelectedOptionString();
    expect(selectedString).toEqual(`${columnName}: (${value1})`);
  });

  it('gets isEditingInputColumn correctly', () => {
    const result = filterBarUtility.isEditingInputColumn();
    expect(result).toEqual(false);
  });

  it('resets filter options correctly', () => {
    filterBarUtility.resetFilterOptions();
    expect(filterBarUtility.allOptions.filter(x => x.selected).length)
        .toEqual(0);
  });

  it('applies selection correctly', () => {
    filterBarUtility.applySelection([value2], columnName);
    expect(filterBarUtility.filterChanged).toBeTrue();
    const option = filterBarUtility.allOptions.filter(
        x => x.selected && x.type === columnName);
    expect(option.length).toEqual(1);
    expect(option[0].value).toEqual(value2);
  });

  it('adds new filter option correctly', () => {
    const newValue = 'ABC';
    filterBarUtility.addNewFilterOption(newValue, inputColumn);
    expect(
        filterBarUtility.allOptions.filter(x => x.value === newValue)[0].value)
        .toEqual(newValue);
    expect(filterBarUtility.filterChanged).toBeTrue();
  });

  it('detects if the filter options should be changed correctly', () => {
    filterBarUtility.resetFilterOptions();
    const option =
        filterBarUtility.createFilterOptions([value1], columnName)[0];
    filterBarUtility.toggleFilterOption(option);
    expect(filterBarUtility.isSelectedFilterOptionsMatchInputValues(
               [value1], columnName))
        .toBeFalse();
    expect(filterBarUtility.isSelectedFilterOptionsMatchInputValues(
               [value2], columnName))
        .toBeTrue();
  });

  it('extracts section from input string correctly', () => {
    const input = 'Pool:(Pool-1|Pool-2) Lab:(Lab-1)';
    const result = filterBarUtility.extractSection(input, 'Pool');
    expect(result).toEqual('Pool:(Pool-1|Pool-2)');
  });

  it('extracts values from section correctly', () => {
    const section = 'Pool:(Pool-1|Pool-2)';
    const result = filterBarUtility.extractValues(section);
    expect(result.length).toEqual(2);
    expect(result[0]).toEqual('Pool-1');
    expect(result[1]).toEqual('Pool-2');
  });

  it('can update filter options correctly', () => {
    const newOptions: FilterOption[] = [
      {
        value: value1,
        selected: true,
        type: columnName,
        hidden: false,
        showCheckbox: false,
      },
      {
        value: value2,
        selected: true,
        type: columnName,
        hidden: false,
        showCheckbox: false,
      },
      {
        value: 'new value',
        selected: true,
        type: columnName,
        hidden: false,
        showCheckbox: false,
      },
    ];
    filterBarUtility.updateFilterOptions(newOptions, columnName);
    expect(filterBarUtility.allOptions.filter(x => x.type === columnName))
        .toEqual(newOptions);
  });
});
