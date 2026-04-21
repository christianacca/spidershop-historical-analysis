import type { MarketHealthPayload } from '../types.js';

export const marketHealthCurrentQuarter: MarketHealthPayload = {
  windowId: 'current-quarter',
  windowLabel: 'Current quarter',
  windowBasisNote: "Quarter in progress (Q2 '26) — comparing Apr 1 – Apr 21 against the same span into Q1 '26 (Jan 1 – Jan 21).",
  showPrior: true,
  sparklineBasisNote:
    "Compare within a row. Solid shows Q2 '26 to date (Apr 1 – Apr 21); dashed shows the same span into Q1 '26 (Jan 1 – Jan 21).",
  isAllSelected: true,
  generaCount: 0,
  scopeLabel: '',

  kpis: {
    observed: {
      id: 'observed',
      title: 'Observed species',
      value: '184',
      delta: '+7 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Breadth is ahead of the same point last quarter, so the market still looks alive on assortment even while actual stock is getting tighter.',
    },
    stock: {
      id: 'stock',
      title: 'In-stock rate',
      value: '61%',
      delta: '-4 pts vs prior quarter QTD',
      deltaClass: 'down',
      copy: 'Availability is a touch weaker than the same point last quarter. That reads more like a near-term tightening than a structural collapse.',
    },
    wishlist: {
      id: 'wishlist',
      title: 'Median wishlist',
      value: '18',
      delta: '+3 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Median wishlist counts are modestly above the same point last quarter, which suggests demand is holding without obviously overheating.',
    },
    price: {
      id: 'price',
      title: 'Median price',
      value: 'GBP 24',
      delta: '+GBP 1 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Prices edged up a little relative to the same point last quarter, which fits a market that is tightening gradually rather than repricing sharply.',
    },
  },

  sparklineSeries: {
    observed: {
      current: [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184],
      prior: [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177],
    },
    stock: {
      current: [67, 66, 66, 65, 64, 63, 63, 62, 62, 61, 61, 61],
      prior: [69, 68, 68, 67, 67, 66, 66, 65, 65, 65, 65, 65],
    },
    wishlist: {
      current: [14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 18, 18],
      prior: [12, 12, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15],
    },
    price: {
      current: [23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24],
      prior: [22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23],
    },
  },

  events: {
    title: 'Run-to-run market events this quarter',
    subtitle: 'Current-quarter event totals against the same point last quarter.',
    newListings: {
      label: 'Listings added',
      value: '+29 vs prior quarter QTD',
      copy: 'Introductions are materially ahead of the matched point last quarter, which supports the breadth expansion visible in the chart.',
    },
    droppedListings: {
      label: 'Listings removed',
      value: '17 vs prior quarter QTD',
      copy: 'Churn also rose, but the balance still favors broader assortment rather than retreat.',
    },
    restocks: {
      label: 'OUT → IN restocks',
      value: '43 vs prior quarter QTD',
      copy: 'Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than last quarter.',
    },
    oosFlips: {
      label: 'IN → OUT stockouts',
      value: '+21 vs prior quarter QTD',
      copy: 'More listings are moving from IN to OUT than at the same point last quarter, which helps explain why availability is softer even while breadth is still expanding.',
    },
  },
};
