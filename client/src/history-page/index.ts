/**
 * Historical Data Page
 *
 * Mounts the HistoryTable Svelte component into the history-table root element,
 * reading table data from the window global injected by the Python template.
 */

import { mount } from 'svelte';
import HistoryTable from './HistoryTable.svelte';
import type { ColumnConfig } from '../shared/components/SortableTable.svelte';

const TABLE_ID = 'history-table';

const COLUMNS: ColumnConfig[] = [
  {
    key: 'Scrape Date',
    label: 'Scrape Date',
    csvHeader: 'scrape_datetime',
    rawValueKey: '_raw_scrape_datetime',
  },
  { key: 'Scientific Name', label: 'Scientific Name', csvHeader: 'scientific_name' },
  { key: 'Common Name', label: 'Common Name', csvHeader: 'common_name' },
  { key: 'Size (cm)', label: 'Size (cm)', csvHeader: 'size_cm' },
  { key: 'Price (GBP)', label: 'Price (GBP)', csvHeader: 'price_gbp' },
  { key: 'Wishlist Count', label: 'Wishlist Count', csvHeader: 'wishlist_count' },
  { key: 'Page URL', label: 'Page URL', type: 'page-url', csvHeader: 'page_url' },
];

function init(): void {
  const target = document.getElementById(`${TABLE_ID}-root`);
  if (!target) return;

  const rows = ((window as Record<string, unknown>)[`${TABLE_ID}Data`] ?? []) as Record<
    string,
    unknown
  >[];

  mount(HistoryTable, {
    target,
    props: {
      tableId: TABLE_ID,
      rows,
      columns: COLUMNS,
      dateColumn: 'Scrape Date',
      priceColumn: 'Price (GBP)',
      wishlistColumn: 'Wishlist Count',
    },
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
