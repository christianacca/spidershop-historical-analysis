import HistoryTable from './HistoryTable.svelte';
import type { SortableTablePageConfig } from '../shared/page-init.js';

export const HISTORY_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'history-table',
  columns: [
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
    {
      key: 'Page URL',
      label: 'Page URL',
      type: 'page-url',
      linkLabelKey: 'Scientific Name',
      csvHeader: 'page_url',
    },
  ],
  component: HistoryTable,
  additionalProps: {
    dateColumn: 'Scrape Date',
    priceColumn: 'Price (GBP)',
    wishlistColumn: 'Wishlist Count',
  },
};