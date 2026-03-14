import type { SortableTablePageConfig } from '../shared/page-init.js';

export const SNAPSHOT_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'snapshot-table',
  columns: [
    { key: 'Common Name' },
    { key: 'Scientific Name' },
    { key: 'Size (cm)' },
    { key: 'Price (GBP)' },
    { key: 'Wishlist Count' },
  ],
  filterConfig: {
    priceColumn: 'Price (GBP)',
    wishlistColumn: 'Wishlist Count',
    showSearch: true,
    statsLabel: 'species',
  },
  primaryToggle: true,
};