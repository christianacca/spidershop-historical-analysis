import { wireOpenDetailsLinks } from '../shared/dom-utils.js';
import type { SortableTablePageConfig } from '../shared/page-init.js';

export const DEALER_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'dealer-table',
  columns: [
    { key: 'Species', type: 'species-link', linkViewParam: 'dealer' },
    { key: 'Size (cm)' },
    { key: 'Stock Reliability' },
    { key: 'Avg OOS Duration' },
    { key: 'Restock Speed' },
    { key: 'Price', label: 'Price Trend' },
    { key: 'Price History', type: 'sparkline' },
    { key: 'Wishlist' },
    { key: 'Wishlist History', type: 'sparkline' },
    { key: 'Stock Availability', type: 'sparkline' },
    { key: 'Dealer Risk' },
    { key: 'Dealer Recommendation' },
    { key: 'Drivers', hidden: true },
  ],
  filterConfig: {
    signalFilter: { column: 'Dealer Risk', top10: true },
    priceColumn: 'Price',
    wishlistColumn: 'Wishlist',
    showSearch: true,
    statsLabel: 'species',
    driversKey: 'Drivers',
  },
  postMount: wireOpenDetailsLinks,
};