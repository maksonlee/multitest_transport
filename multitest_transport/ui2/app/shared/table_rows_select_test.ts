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
  describe('TableRowSelect directive', () => {
    let tableRowSelect: TableRowSelect;
    let tableRowsSelectManager: TableRowsSelectManager;
    let evt: MouseEvent;

    beforeEach(() => {
      tableRowsSelectManager = new TableRowsSelectManager();
      tableRowSelect = new TableRowSelect(tableRowsSelectManager);
      evt = document.createEvent('MouseEvents');
    });

    it('removes or adds an item in selection correctly', () => {
      const expectedSelection = 'host1';
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowSelect.rowIndex = 0;
      tableRowSelect.rowIdFieldValue = 'host1';
      spyOn(tableRowsSelectManager.selectionChange, 'emit');
      evt.initMouseEvent(
          'click', true, true, window, 0, 0, 0, 0, 0, false, false, false,
          false, 0, null);

      // Selects the item.
      tableRowSelect.select(evt);

      expect(tableRowsSelectManager.selection.selected)
          .toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(1);

      // Deselects the item.
      tableRowSelect.select(evt);
      expect(tableRowsSelectManager.selection.selected)
          .not.toContain(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledTimes(2);
    });
  });

  describe('TableRowsSelectCheckbox directive', () => {
    let tableRowsSelectCheckbox: TableRowsSelectCheckbox;
    let tableRowsSelectManager: TableRowsSelectManager;

    beforeEach(() => {
      tableRowsSelectManager = new TableRowsSelectManager();
      tableRowsSelectCheckbox =
          new TableRowsSelectCheckbox(tableRowsSelectManager);
    });

    it('selects all correctly', () => {
      const expectedSelection =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      spyOn(tableRowsSelectManager.selectionChange, 'emit');

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
      spyOn(tableRowsSelectManager.selectionChange, 'emit');

      tableRowsSelectCheckbox.toggleAllSelection();

      expect(tableRowsSelectManager.selection.selected)
          .toEqual(expectedSelection);
      expect(tableRowsSelectManager.selectionChange.emit)
          .toHaveBeenCalledWith(expectedSelection);
    });
  });

  describe('TableRowSelectCheckbox directive', () => {
    let tableRowSelectCheckbox: TableRowSelectCheckbox;
    let tableRowsSelectManager: TableRowsSelectManager;

    let evt: MouseEvent;

    beforeEach(() => {
      tableRowsSelectManager = new TableRowsSelectManager();
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
      evt = document.createEvent('MouseEvents');
    });

    it('removes or adds an item in selection correctly', () => {
      const expectedSelection = 'host1';
      tableRowsSelectManager.rowIdFieldAllValues =
          ['host1', 'host2', 'host3', 'host4', 'host5', 'host6', 'host7'];
      tableRowSelectCheckbox.rowIndex = 0;
      tableRowSelectCheckbox.rowIdFieldValue = 'host1';
      spyOn(tableRowsSelectManager.selectionChange, 'emit');
      evt.initMouseEvent(
          'click', true, true, window, 0, 0, 0, 0, 0, false, false, false,
          false, 0, null);

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
