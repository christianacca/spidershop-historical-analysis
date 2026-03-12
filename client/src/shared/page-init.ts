import { mount } from 'svelte';
import SortableTable from './components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from './components/SortableTable.svelte';
import { assertPayload } from './payload-validation.js';

type TableRows = Record<string, unknown>[];

export interface SortableTablePageConfig {
  tableId: string;
  columns: ColumnConfig[];
  filterConfig: FilterConfig;
  primaryToggle?: boolean;
  postMount?: () => void;
}

function getWindowRows(tableId: string): TableRows {
  const globals = window as unknown as Record<string, unknown>;
  return (globals[`${tableId}Data`] ?? []) as TableRows;
}

export function initSortableTablePage(config: SortableTablePageConfig): void {
  const { tableId, columns, filterConfig, primaryToggle, postMount } = config;
  const target = document.getElementById(`${tableId}-root`);
  if (!target) return;

  const rows = getWindowRows(tableId);
  assertPayload(tableId, rows);

  const props =
    primaryToggle === undefined
      ? { tableId, rows, columns, filterConfig }
      : { tableId, rows, columns, filterConfig, primaryToggle };

  mount(SortableTable, { target, props });
  postMount?.();
}

export function registerPageInit(init: () => void): void {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
    return;
  }

  init();
}