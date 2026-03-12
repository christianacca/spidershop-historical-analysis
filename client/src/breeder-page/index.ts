/**
 * Breeder Opportunities Page
 *
 * Mounts the SortableTable Svelte component into the breeder-table root element,
 * reading table data from the window global injected by the Python template.
 */

import type { ColumnConfig, FilterConfig } from '../shared/components/SortableTable.svelte';
import { wireOpenDetailsLinks } from '../shared/dom-utils.js';
import { initSortableTablePage, registerPageInit } from '../shared/page-init.js';

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

registerPageInit(() => {
  initSortableTablePage({
    tableId: TABLE_ID,
    columns: COLUMNS,
    filterConfig: FILTER_CONFIG,
    postMount: wireOpenDetailsLinks,
  });
});
