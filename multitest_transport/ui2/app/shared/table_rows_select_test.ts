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

import {QueryList} from '@angular/core';
import {TableRowSelect, TableRowSelectCheckbox, TableRowsSelectCheckbox, TableRowsSelectManager} from './table_rows_select';

describe('TableRowsSelect', () => {
  let tableRowsSelectManager: TableRowsSelectManager;

  beforeEach(() => {
    tableRowsSelectManager = new TableRowsSelectManager();
    spyOn(tableRowsSelectManager.selectionChange, 'emit');
  });

  it('selects correctly when calls selectSelection', () => {
    const expectedSelection = ['host2', 'host3', 'host4', 'host7'];

    tableRowsSelectManager.selectSelection(expectedSelection);

    expect(tableRowsSelectManager.selection.selected)
        .toEqual(expectedSelection);
    expect(tableRowsSelectManager.selectionChange.emit)
        .toHaveBeenCalledWith(expectedSelection);
  });

  it(`deselects items which don't exist in rowIdFieldAllValues correctly when 
     calls resetSelection`,
     () => {
       const expectedSelection = ['host7'];
       tableRowsSelectManager.selection.select(
           'host2', 'host3', 'host4', 'host7');
       tableRowsSelectManager.rowIdFieldAllValues = ['host5', 'host6', 'host7'];

       tableRowsSelectManager.resetSelection();

       expect(tableRowsSelectManager.selection.selected)
           .toEqual(expectedSelection);
       expect(tableRowsSelectManager.selectionChange.emit)
           .toHaveBeenCalledWith(expectedSelection);
     });

  describe('TableRowSelect directive', () => {
    const CLICK = new MouseEvent('click');
    const SHIFT_CLICK = new MouseEvent('click', {shiftKey: true});
    let tableRowSelect: TableRowSelect;

    beforeEach(() => {
      tableRowSelect = new TableRowSelect(tableRowsSelectManager);
    });

    it('removes or adds an item in selection correctly', () => {
      const expectedSelection = 'host1';
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowSelect.rowIndex = 0;
      tableRowSelect.rowIdFieldValue = 'host1';

      // Selects the item.
      tableRowSelect.select(CLICK);
      expect(tableRowsSelectManager.selection.selected)
          .toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(1);

      // Deselects the item.
      tableRowSelect.select(CLICK);
      expect(tableRowsSelectManager.selection.selected)
          .not.toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(2);
    });

    it('adds items by range in selection correctly', () => {
      const expectedSelection = ['host2', 'host3', 'host4', 'host5', 'host6'];
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowsSelectManager.prevClickedRowIndex = 1;
      tableRowsSelectManager.selection.select('host2');

      tableRowSelect.rowIndex = 5;
      tableRowSelect.rowIdFieldValue =
          tableRowsSelectManager.rowIdFieldAllValues[tableRowSelect.rowIndex];

      tableRowSelect.select(SHIFT_CLICK);
      expect(tableRowsSelectManager.selection.selected)
          .toEqual(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(1);
    });

    it('removes items by range in selection correctly', () => {
      const expectedSelection = ['host2', 'host3'];
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowsSelectManager.prevClickedRowIndex = 5;
      tableRowsSelectManager.selection.select(
          'host2', 'host3', 'host4', 'host5', 'host6');

      tableRowSelect.rowIndex = 3;
      tableRowSelect.rowIdFieldValue =
          tableRowsSelectManager.rowIdFieldAllValues[tableRowSelect.rowIndex];

      tableRowSelect.select(SHIFT_CLICK);
      expect(tableRowsSelectManager.selection.selected)
          .toEqual(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(1);
    });
  });

  describe('TableRowsSelectCheckbox directive', () => {
    let tableRowsSelectCheckbox: TableRowsSelectCheckbox;

    beforeEach(() => {
      tableRowsSelectCheckbox =
          new TableRowsSelectCheckbox(tableRowsSelectManager);
    });

    it('selects all correctly', () => {
      const expectedSelection =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];

      tableRowsSelectCheckbox.toggleAllSelection();

      expect(tableRowsSelectManager.selection.selected)
          .toEqual(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledWith(expectedSelection);
    });

    it('deselects all correctly', () => {
      const expectedSelection: string[] = [];
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowsSelectManager.selection.select(
          'host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7');

      tableRowsSelectCheckbox.toggleAllSelection();

      expect(tableRowsSelectManager.selection.selected)
          .toEqual(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledWith(expectedSelection);
    });
  });

  describe('TableRowSelectCheckbox directive', () => {
    let tableRowSelectCheckbox: TableRowSelectCheckbox;

    beforeEach(() => {
      const tableRowSelects: TableRowSelect[] = [];
      for (let i = 0; i < 7; i++) {
        tableRowSelects.push(new TableRowSelect(tableRowsSelectManager));
        tableRowSelects[i].rowIndex = i;
        tableRowSelects[i].rowIdFieldValue = `host${i + 1}`;
      }
      tableRowsSelectManager.tableRowSelects = new QueryList<TableRowSelect>();
      tableRowsSelectManager.tableRowSelects.reset(tableRowSelects);

      tableRowSelectCheckbox =
          new TableRowSelectCheckbox(tableRowsSelectManager);
    });

    it('removes or adds an item in selection correctly', () => {
      const expectedSelection = 'host1';
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowSelectCheckbox.rowIndex = 0;
      tableRowSelectCheckbox.rowIdFieldValue = 'host1';

      // Selects the item.
      tableRowSelectCheckbox.select();
      expect(tableRowsSelectManager.selection.selected)
          .toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(1);

      // Deselects the item.
      tableRowSelectCheckbox.select();
      expect(tableRowsSelectManager.selection.selected)
          .not.toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(2);
    });
  });
});
