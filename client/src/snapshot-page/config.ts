import type { SortableTablePageConfig } from '../shared/page-init.js';
import { createFilterConfig } from '../shared/filter-config.js';

export const SNAPSHOT_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'snapshot-table',
  columns: [
    { key: 'Common Name' },
    { key: 'Scientific Name' },
    { key: 'Size (cm)' },
    { key: 'Price (GBP)' },
    { key: 'Wishlist Count' },
  ],
  filterConfig: createFilterConfig({
    priceColumn: 'Price (GBP)',
    wishlistColumn: 'Wishlist Count',
  }),
  primaryToggle: true,
};