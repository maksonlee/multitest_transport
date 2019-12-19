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

import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';

import {getTextContent} from '../testing/jasmine_util';

import {SharedModule} from './shared_module';
import {SharedModuleNgSummary} from './shared_module.ngsummary';
import {TreeNode, TreeTable, TreeTableColumn} from './tree_table';

describe('TreeTable', () => {
  let treeTable: TreeTable;
  let treeTableFixture: ComponentFixture<TreeTable>;
  let el: DebugElement;

  let tree: TreeNode;
  let columns: TreeTableColumn[];

  beforeEach(() => {
    tree = newMockTree(5);
    columns = newMockTreeTableColumns();

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule, SharedModule],
      aotSummaries: SharedModuleNgSummary,
    });
    treeTableFixture = TestBed.createComponent(TreeTable);
    el = treeTableFixture.debugElement;
    treeTable = treeTableFixture.componentInstance;
    treeTable.data = [tree];
    treeTable.columns = columns;
    treeTableFixture.detectChanges();
  });

  it('initializes a component', () => {
    expect(treeTable).toBeTruthy();
  });

  it('displays headers correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain(columns[0].title);
    expect(textContent).toContain(columns[1].title);
  });

  it('displays data correctly', () => {
    const textContent = getTextContent(el);
    expect(textContent).toContain(tree.content[0]);
    expect(textContent).not.toContain(tree.children[0].content[0]);
  });
});

/** Creates a full binary tree structure */
function newMockTree(numNodes: number): TreeNode {
  const child = newMockTreeNode(['child'], 1);
  const parent = newMockTreeNode(['parent'], 0, [child]);
  return parent;
}

/** Creates a mock tree node */
function newMockTreeNode(
    content: string[], level: number, children: TreeNode[] = []): TreeNode {
  return {content, children, level};
}

/** Create mock tree table columns */
function newMockTreeTableColumns() {
  return [
    {title: 'column1', flexWidth: '40'}, {title: 'col2', flexWidth: '60'}
  ];
}
