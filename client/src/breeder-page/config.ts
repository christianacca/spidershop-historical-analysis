import { wireOpenDetailsLinks } from '../shared/dom-utils.js';
import type { SortableTablePageConfig } from '../shared/page-init.js';

export const BREEDER_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'breeder-table',
  columns: [
    { key: 'Species', type: 'species-link', linkViewParam: 'breeder' },
    { key: 'Size (cm)' },
    { key: 'OOS' },
    { key: 'OOS Runs' },
    { key: 'Stock Pattern' },
    { key: 'Price', label: 'Price Trend' },
    { key: 'Price History', type: 'sparkline' },
    { key: 'Wishlist' },
    { key: 'Wishlist History', type: 'sparkline' },
    { key: 'Signal' },
    { key: 'Recommendation' },
    { key: 'Drivers', hidden: true },
  ],
  filterConfig: {
    signalFilter: { column: 'Signal', top10: true },
    stockPatternFilter: { column: 'Stock Pattern' },
    priceColumn: 'Price',
    wishlistColumn: 'Wishlist',
    showSearch: true,
    statsLabel: 'species',
    driversKey: 'Drivers',
  },
  postMount: wireOpenDetailsLinks,
};