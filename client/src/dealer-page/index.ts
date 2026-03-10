/**
 * Dealer Supply Risk Page
 *
 * Mounts the SortableTable Svelte component into the dealer-table root element,
 * reading table data from the window global injected by the Python template.
 */

import { mount } from 'svelte';
import SortableTable from '../shared/components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from '../shared/components/SortableTable.svelte';
import { wireOpenDetailsLinks } from '../shared/dom-utils.js';
import { assertPayload } from '../shared/payload-validation.js';

const TABLE_ID = 'dealer-table';

const COLUMNS: ColumnConfig[] = [
  { key: 'Species', label: 'Species', type: 'species-link', linkViewParam: 'dealer' },
  { key: 'Size (cm)', label: 'Size (cm)' },
  { key: 'Stock Reliability', label: 'Stock Reliability' },
  { key: 'Avg OOS Duration', label: 'Avg OOS Duration' },
  { key: 'Restock Speed', label: 'Restock Speed' },
  { key: 'Price', label: 'Price Trend' },
  { key: 'Price History', label: 'Price History', type: 'sparkline' },
  { key: 'Wishlist', label: 'Wishlist' },
  { key: 'Wishlist History', label: 'Wishlist History', type: 'sparkline' },
  { key: 'Stock Availability', label: 'Stock Availability', type: 'sparkline' },
  { key: 'Dealer Risk', label: 'Dealer Risk' },
  { key: 'Dealer Recommendation', label: 'Dealer Recommendation' },
  { key: 'Drivers', label: 'Drivers', hidden: true },
];

const FILTER_CONFIG: FilterConfig = {
  signalFilter: { column: 'Dealer Risk', top10: true },
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
  assertPayload(TABLE_ID, rows);

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
