/**
 * Latest Snapshot Page
 *
 * Mounts the SortableTable Svelte component into the snapshot-table root element,
 * reading table data from the window global injected by the Python template.
 */

import { mount } from 'svelte';
import SortableTable from '../shared/components/SortableTable.svelte';
import type { ColumnConfig, FilterConfig } from '../shared/components/SortableTable.svelte';

const TABLE_ID = 'snapshot-table';

const COLUMNS: ColumnConfig[] = [
  { key: 'Common Name', label: 'Common Name' },
  { key: 'Scientific Name', label: 'Scientific Name' },
  { key: 'Size (cm)', label: 'Size (cm)' },
  { key: 'Price (GBP)', label: 'Price (GBP)' },
  { key: 'Wishlist Count', label: 'Wishlist Count' },
];

const FILTER_CONFIG: FilterConfig = {
  priceColumn: 'Price (GBP)',
  wishlistColumn: 'Wishlist Count',
  showSearch: true,
  statsLabel: 'species',
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
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
