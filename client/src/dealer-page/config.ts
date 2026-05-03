import type { SortableTablePageConfig } from '../shared/page-init.js';
import { createFilterConfig } from '../shared/filter-config.js';

export const DEALER_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'dealer-table',
  columns: [
    { key: 'Species', type: 'species-link', linkViewParam: 'dealer', cardHeader: true },
    { key: 'Size (cm)' },
    { key: 'Stock Reliability' },
    { key: 'Avg OOS Duration' },
    { key: 'Restock Speed' },
    { key: 'Price', label: 'Price Trend', showPriceWarning: true },
    { key: 'Price History', type: 'sparkline', showPriceWarning: true },
    { key: 'Wishlist' },
    { key: 'Wishlist History', type: 'sparkline' },
    { key: 'Stock Availability', type: 'sparkline' },
    { key: 'Dealer Risk' },
    { key: 'Dealer Recommendation' },
    { key: 'Drivers', hidden: true },
    { key: 'Lineage Status', hidden: true },
    { key: 'Price Evidence State', hidden: true },
    { key: 'Transition Message', hidden: true },
  ],
  filterConfig: createFilterConfig({
    signalFilter: { column: 'Dealer Risk', top10: true },
    driversKey: 'Drivers',
    priceWarningStateKey: 'Price Evidence State',
    transitionMessageKey: 'Transition Message',
  }),
};