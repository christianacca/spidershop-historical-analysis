/**
 * Breeder Opportunities Page
 *
 * Mounts the SortableTable Svelte component into the breeder-table root element,
 * reading table data from the window global injected by the Python template.
 */

import { mount } from 'svelte';
import SortableTable from '../shared/components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from '../shared/components/SortableTable.svelte';
import { wireOpenDetailsLinks } from '../shared/dom-utils.js';

const TABLE_ID = 'breeder-table';

const COLUMNS: ColumnConfig[] = [
  { key: 'Species', label: 'Species', type: 'species-link', linkViewParam: 'breeder' },
  { key: 'Size (cm)', label: 'Size (cm)' },
  { key: 'OOS', label: 'OOS' },
  { key: 'OOS Runs', label: 'OOS Runs' },
  { key: 'Stock Pattern', label: 'Stock Pattern' },
  { key: 'Price', label: 'Price Trend' },
  { key: 'Price History', label: 'Price History', type: 'sparkline' },
  { key: 'Wishlist', label: 'Wishlist' },
  { key: 'Wishlist History', label: 'Wishlist History', type: 'sparkline' },
  { key: 'Signal', label: 'Signal' },
  { key: 'Recommendation', label: 'Recommendation' },
  { key: 'Drivers', label: 'Drivers', hidden: true },
];

const FILTER_CONFIG: FilterConfig = {
  signalFilter: { column: 'Signal', top10: true },
  stockPatternFilter: { column: 'Stock Pattern' },
  priceColumn: 'Price',
  wishlistColumn: 'Wishlist',
  showSearch: true,
  statsLabel: 'species',
  driversKey: 'Drivers',
};

function init(): void {
  const target = document.getElementById(`${TABLE_ID}-root`);
  if (!target) return;

  const rows = ((window as Record<string, unknown>)[`${TABLE_ID}Data`] ?? []) as Record<string, unknown>[];

  mount(SortableTable, {
    target,
    props: {
      tableId: TABLE_ID,
      rows,
      columns: COLUMNS,
      filterConfig: FILTER_CONFIG,
    },
  });
  wireOpenDetailsLinks();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
