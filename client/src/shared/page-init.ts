import { mount } from 'svelte';
import SortableTable from './components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from './components/SortableTable.svelte';
import { assertPayload } from './payload-validation.js';

type TableRows = Record<string, unknown>[];
const MIN_SKELETON_DWELL_MS = 320;
const SKELETON_FADE_DURATION_MS = 220;

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

export function completeTableMount(tableId: string): void {
  const shell = document.querySelector<HTMLElement>(`[data-table-shell="${tableId}"]`);
  const skeleton = document.querySelector<HTMLElement>(`[data-table-skeleton-for="${tableId}"]`);

  const beginCrossFade = (): void => {
    shell?.setAttribute('data-table-ready', 'true');

    if (!skeleton) return;

    window.setTimeout(() => {
      skeleton.remove();
    }, SKELETON_FADE_DURATION_MS);
  };

  const elapsedSinceNavigationStart = performance.now();
  const remainingDwell = Math.max(0, MIN_SKELETON_DWELL_MS - elapsedSinceNavigationStart);

  if (remainingDwell === 0) {
    beginCrossFade();
    return;
  }

  window.setTimeout(beginCrossFade, remainingDwell);
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
  completeTableMount(tableId);
  postMount?.();
}

export function registerPageInit(init: () => void): void {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
    return;
  }

  init();
}