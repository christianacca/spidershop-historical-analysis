import type { MarketHealthPayload } from '../types.js';

// Stock-under-pressure scenario: stock delta ≤ −7 AND wishlist delta ≥ +3.
// This fixture exercises the maximum-tension KPI read (spec §3.2 delta ≤ −7 branch
// and §3.3 delta ≥ +4 branch).
export const marketHealthStockUnderPressure: MarketHealthPayload = {
  windowId: 'current-quarter',
  windowLabel: 'Current quarter',
  windowBasisNote: 'Comparison basis: quarter to date vs prior quarter QTD.',
  showPrior: true,
  sparklineBasisNote:
    'Compare within a row. Solid shows the current quarter; dashed shows the matched point last quarter.',
  isAllSelected: true,
  generaCount: 0,
  scopeLabel: '',

  kpis: {
    observed: {
      id: 'observed',
      title: 'Observed species',
      value: '187',
      delta: '+10 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Breadth is ahead of the same point last quarter, so the market still looks alive on assortment even while actual stock is getting tighter.',
    },
    stock: {
      id: 'stock',
      title: 'In-stock rate',
      value: '49%',
      delta: '-9 pts vs prior quarter QTD',
      deltaClass: 'down',
      copy: '49% of listings are available now. That is 9 percentage points lower than the same point last quarter, so availability is slipping even while the species count remains broad.',
    },
    wishlist: {
      id: 'wishlist',
      title: 'Median wishlist',
      value: '24',
      delta: '+5 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Across your selected genera, median wishlist demand is ahead of the same point last quarter, reinforcing the idea that interest is improving while availability slips.',
    },
    price: {
      id: 'price',
      title: 'Median price',
      value: 'GBP 27',
      delta: '+GBP 3 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Prices are somewhat firmer than the same point last quarter, but the move is still smaller than the availability shift. Supply pressure remains the more important signal.',
    },
  },

  sparklineSeries: {
    observed: {
      current: [170, 172, 174, 176, 178, 180, 182, 184, 186, 187, 187, 187],
      prior: [162, 164, 166, 167, 168, 169, 171, 173, 175, 177, 177, 177],
    },
    stock: {
      current: [61, 59, 57, 55, 53, 52, 51, 50, 49, 49, 49, 49],
      prior: [69, 68, 68, 67, 67, 67, 66, 66, 58, 58, 58, 58],
    },
    wishlist: {
      current: [17, 17, 18, 18, 19, 20, 21, 22, 23, 24, 24, 24],
      prior: [14, 14, 15, 15, 16, 16, 17, 17, 18, 19, 19, 19],
    },
    price: {
      current: [23, 23, 24, 24, 25, 25, 26, 26, 27, 27, 27, 27],
      prior: [22, 22, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24],
    },
  },

  events: {
    title: 'Run-to-run market events this quarter',
    subtitle: 'Current-quarter event totals against the same point last quarter.',
    newListings: {
      label: 'Listings added',
      value: '+35 vs prior quarter QTD',
      copy: 'Introductions are materially ahead of the matched point last quarter, which supports the breadth expansion visible in the chart.',
    },
    droppedListings: {
      label: 'Listings removed',
      value: '11 vs prior quarter QTD',
      copy: 'Some churn is present, but the removal count is too small to imply retreat.',
    },
    restocks: {
      label: 'OUT → IN restocks',
      value: '28 vs prior quarter QTD',
      copy: 'Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than last quarter.',
    },
    oosFlips: {
      label: 'IN → OUT stockouts',
      value: '+31 vs prior quarter QTD',
      copy: 'More listings are moving from IN to OUT than at the same point last quarter, which helps explain why availability is softer even while breadth is still expanding.',
    },
  },
};
