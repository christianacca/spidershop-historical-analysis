import type { MarketHealthPayload } from '../types.js';

export const marketHealthAllTime: MarketHealthPayload = {
  windowId: 'all-time',
  windowLabel: 'All time',
  windowBasisNote: 'Comparison basis: structural context only, with no prior-period delta.',
  showPrior: false,
  sparklineBasisNote:
    'All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale.',
  isAllSelected: true,
  generaCount: 0,
  scopeLabel: '',

  kpis: {
    observed: {
      id: 'observed',
      title: 'Observed species',
      value: '184',
      delta: 'No prior comparison',
      deltaClass: 'flat',
      copy: 'All-time view is best read as structural context: the catalog is broad enough to support opportunity hunting, but this lens is not about recent acceleration.',
    },
    stock: {
      id: 'stock',
      title: 'In-stock rate',
      value: '61%',
      delta: 'No prior comparison',
      deltaClass: 'flat',
      copy: 'All-time availability smooths out short-term swings, so it is useful for background context rather than telling you what changed recently.',
    },
    wishlist: {
      id: 'wishlist',
      title: 'Median wishlist',
      value: '18',
      delta: 'No prior comparison',
      deltaClass: 'flat',
      copy: 'All-time wishlist levels show the long-run demand floor for your selected genera, not whether interest just strengthened this month or quarter.',
    },
    price: {
      id: 'price',
      title: 'Median price',
      value: 'GBP 22',
      delta: 'No prior comparison',
      deltaClass: 'flat',
      copy: 'All-time price mainly describes the market baseline. It is less useful than shorter windows when you are deciding whether recent conditions have shifted.',
    },
  },

  sparklineSeries: {
    observed: {
      current: [130, 140, 149, 156, 162, 167, 171, 175, 179, 181, 183, 184],
      prior: [],
      currentRunDates: [
        '2025-07-07T06:10:00', '2025-08-04T06:10:00', '2025-09-01T06:10:00', '2025-09-29T06:10:00',
        '2025-10-27T06:10:00', '2025-11-17T06:10:00', '2025-12-08T06:10:00', '2026-01-05T06:10:00',
        '2026-02-02T06:10:00', '2026-03-02T06:10:00', '2026-04-06T06:10:00', '2026-04-13T06:10:00',
      ],
      priorRunDates: [],
    },
    stock: {
      current: [72, 70, 69, 68, 67, 66, 65, 64, 63, 62, 62, 61],
      prior: [],
      currentRunDates: [
        '2025-07-07T06:10:00', '2025-08-04T06:10:00', '2025-09-01T06:10:00', '2025-09-29T06:10:00',
        '2025-10-27T06:10:00', '2025-11-17T06:10:00', '2025-12-08T06:10:00', '2026-01-05T06:10:00',
        '2026-02-02T06:10:00', '2026-03-02T06:10:00', '2026-04-06T06:10:00', '2026-04-13T06:10:00',
      ],
      priorRunDates: [],
    },
    wishlist: {
      current: [8, 10, 11, 13, 14, 15, 16, 17, 17, 18, 18, 18],
      prior: [],
      currentRunDates: [
        '2025-07-07T06:10:00', '2025-08-04T06:10:00', '2025-09-01T06:10:00', '2025-09-29T06:10:00',
        '2025-10-27T06:10:00', '2025-11-17T06:10:00', '2025-12-08T06:10:00', '2026-01-05T06:10:00',
        '2026-02-02T06:10:00', '2026-03-02T06:10:00', '2026-04-06T06:10:00', '2026-04-13T06:10:00',
      ],
      priorRunDates: [],
    },
    price: {
      current: [19, 20, 21, 21, 22, 22, 23, 23, 24, 24, 24, 24],
      prior: [],
      currentRunDates: [
        '2025-07-07T06:10:00', '2025-08-04T06:10:00', '2025-09-01T06:10:00', '2025-09-29T06:10:00',
        '2025-10-27T06:10:00', '2025-11-17T06:10:00', '2025-12-08T06:10:00', '2026-01-05T06:10:00',
        '2026-02-02T06:10:00', '2026-03-02T06:10:00', '2026-04-06T06:10:00', '2026-04-13T06:10:00',
      ],
      priorRunDates: [],
    },
  },

  events: {
    title: 'Market events across all time',
    subtitle: 'All-time event totals as structural context only.',
    newListings: {
      label: 'Listings added',
      value: '286 total',
      copy: 'Use this as background volume, not as a directional comparison.',
    },
    droppedListings: {
      label: 'Listings removed',
      value: '172 total',
      copy: 'All-time churn is useful for scale, but weak for saying what changed recently.',
    },
    restocks: {
      label: 'OUT → IN restocks',
      value: '391 total',
      copy: 'This shows how much movement exists in the market overall, not whether it is improving now.',
    },
    oosFlips: {
      label: 'IN → OUT stockouts',
      value: '214 total',
      copy: 'Use this as structural supply-friction context, not as a directional signal about what changed recently.',
    },
  },
};
