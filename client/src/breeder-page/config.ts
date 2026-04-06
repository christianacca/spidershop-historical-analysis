import type { SortableTablePageConfig } from '../shared/page-init.js';
import { createFilterConfig } from '../shared/filter-config.js';

export const BREEDER_PAGE_CONFIG: SortableTablePageConfig = {
  tableId: 'breeder-table',
  columns: [
    { key: 'Species', type: 'species-link', linkViewParam: 'breeder' },
    { key: 'Size (cm)' },
    { key: 'OOS' },
    { key: 'OOS Runs' },
    { key: 'Stock Pattern' },
    { key: 'Price', label: 'Price Trend', showPriceWarning: true },
    { key: 'Price History', type: 'sparkline', showPriceWarning: true },
    { key: 'Wishlist' },
    { key: 'Wishlist History', type: 'sparkline' },
    { key: 'Signal' },
    { key: 'Recommendation' },
    { key: 'Drivers', hidden: true },
    { key: 'Lineage Status', hidden: true },
    { key: 'Price Evidence State', hidden: true },
    { key: 'Transition Message', hidden: true },
  ],
  filterConfig: createFilterConfig({
    signalFilter: { column: 'Signal', top10: true },
    stockPatternFilter: { column: 'Stock Pattern' },
    driversKey: 'Drivers',
    priceWarningStateKey: 'Price Evidence State',
    transitionMessageKey: 'Transition Message',
  }),
};