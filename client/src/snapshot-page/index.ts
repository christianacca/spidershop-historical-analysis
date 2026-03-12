/**
 * Latest Snapshot Page
 *
 * Mounts the SortableTable Svelte component into the snapshot-table root element,
 * reading table data from the window global injected by the Python template.
 */

import type { ColumnConfig, FilterConfig } from '../shared/components/SortableTable.svelte';
import { initSortableTablePage, registerPageInit } from '../shared/page-init.js';

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

registerPageInit(() => {
  initSortableTablePage({
    tableId: TABLE_ID,
    columns: COLUMNS,
    filterConfig: FILTER_CONFIG,
    primaryToggle: true,
  });
});
