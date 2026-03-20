import { mount } from 'svelte';
import SortableTable from './components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from './components/SortableTable.svelte';
import { assertPayload } from './payload-validation.js';

type TableRows = Record<string, unknown>[];
type TableComponent = Parameters<typeof mount>[0];
const MIN_SKELETON_DWELL_MS = 520;
const SKELETON_FADE_DURATION_MS = 260;

export interface SortableTablePageConfig {
  tableId: string;
  columns: ColumnConfig[];
  filterConfig?: FilterConfig;
  primaryToggle?: boolean;
  postMount?: () => void;
  component?: TableComponent;
  additionalProps?: Record<string, unknown>;
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
  const {
    tableId,
    columns,
    filterConfig,
    primaryToggle,
    postMount,
    component = SortableTable,
    additionalProps = {},
  } = config;
  const target = document.getElementById(`${tableId}-root`);
  if (!target) return;

  const rows = getWindowRows(tableId);
  assertPayload(tableId, rows);

  const props: Record<string, unknown> = {
    tableId,
    rows,
    columns,
    ...additionalProps,
  };

  if (filterConfig !== undefined) {
    props.filterConfig = filterConfig;
  }

  if (primaryToggle !== undefined) {
    props.primaryToggle = primaryToggle;
  }

  mount(component, { target, props });
  completeTableMount(tableId);
  postMount?.();
}

export function registerSortableTablePage(config: SortableTablePageConfig): void {
  registerPageInit(() => {
    initSortableTablePage(config);
  });
}

export function registerPageInit(init: () => void): void {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
    return;
  }

  init();
}