import type { MarketHealthPayload } from '../types.js';

// Last quarter = Q1 2026 (January–March 2026)
// Prior quarter = Q4 2025
export const marketHealthLastQuarter: MarketHealthPayload = {
  windowId: 'last-quarter',
  windowLabel: 'Last quarter',
  windowBasisNote: "Comparison basis: Q1 '26 full quarter vs Q4 '25.",
  showPrior: true,
  sparklineBasisNote:
    "Compare within a row. Solid shows last quarter; dashed shows the prior full quarter.",
  isAllSelected: true,
  generaCount: 0,
  scopeLabel: '',

  kpis: {
    observed: {
      id: 'observed',
      title: 'Observed species',
      value: '181',
      delta: "+4 vs Q4 '25",
      deltaClass: '',
      copy: "Breadth is only slightly ahead of Q4 '25, so the catalog still looks broad without signalling a step-change in assortment.",
    },
    stock: {
      id: 'stock',
      title: 'In-stock rate',
      value: '63%',
      delta: "-2 pts vs Q4 '25",
      deltaClass: 'down',
      copy: "Availability is a touch weaker than Q4 '25. That reads more like a near-term tightening than a structural collapse.",
    },
    wishlist: {
      id: 'wishlist',
      title: 'Median wishlist',
      value: '16',
      delta: "+2 vs Q4 '25",
      deltaClass: '',
      copy: "Median wishlist counts are modestly above Q4 '25, which suggests demand is holding without obviously overheating.",
    },
    price: {
      id: 'price',
      title: 'Median price',
      value: 'GBP 23',
      delta: "+GBP 1 vs Q4 '25",
      deltaClass: '',
      copy: "Prices edged up a little relative to Q4 '25, which fits a market that is tightening gradually rather than repricing sharply.",
    },
  },

  sparklineSeries: {
    observed: {
      current: [175, 175, 176, 177, 177, 178, 179, 180, 180, 181, 181, 181],
      prior: [169, 170, 171, 172, 173, 173, 174, 175, 176, 177, 177, 177],
      currentRunDates: [
        '2026-01-05T06:10:00', '2026-01-12T06:10:00', '2026-01-19T06:10:00', '2026-01-26T06:10:00',
        '2026-02-02T06:10:00', '2026-02-09T06:10:00', '2026-02-16T06:10:00', '2026-02-23T06:10:00',
        '2026-03-02T06:10:00', '2026-03-09T06:10:00', '2026-03-16T06:10:00', '2026-03-23T06:10:00',
      ],
      priorRunDates: [
        '2025-10-06T06:10:00', '2025-10-13T06:10:00', '2025-10-20T06:10:00', '2025-10-27T06:10:00',
        '2025-11-03T06:10:00', '2025-11-10T06:10:00', '2025-11-17T06:10:00', '2025-11-24T06:10:00',
        '2025-12-01T06:10:00', '2025-12-08T06:10:00', '2025-12-15T06:10:00', '2025-12-22T06:10:00',
      ],
    },
    stock: {
      current: [66, 66, 65, 65, 64, 64, 63, 63, 63, 63, 63, 63],
      prior: [68, 68, 67, 67, 66, 66, 66, 65, 65, 65, 65, 65],
      currentRunDates: [
        '2026-01-05T06:10:00', '2026-01-12T06:10:00', '2026-01-19T06:10:00', '2026-01-26T06:10:00',
        '2026-02-02T06:10:00', '2026-02-09T06:10:00', '2026-02-16T06:10:00', '2026-02-23T06:10:00',
        '2026-03-02T06:10:00', '2026-03-09T06:10:00', '2026-03-16T06:10:00', '2026-03-23T06:10:00',
      ],
      priorRunDates: [
        '2025-10-06T06:10:00', '2025-10-13T06:10:00', '2025-10-20T06:10:00', '2025-10-27T06:10:00',
        '2025-11-03T06:10:00', '2025-11-10T06:10:00', '2025-11-17T06:10:00', '2025-11-24T06:10:00',
        '2025-12-01T06:10:00', '2025-12-08T06:10:00', '2025-12-15T06:10:00', '2025-12-22T06:10:00',
      ],
    },
    wishlist: {
      current: [13, 13, 14, 14, 15, 15, 15, 16, 16, 16, 16, 16],
      prior: [11, 12, 12, 13, 13, 13, 14, 14, 14, 14, 14, 14],
      currentRunDates: [
        '2026-01-05T06:10:00', '2026-01-12T06:10:00', '2026-01-19T06:10:00', '2026-01-26T06:10:00',
        '2026-02-02T06:10:00', '2026-02-09T06:10:00', '2026-02-16T06:10:00', '2026-02-23T06:10:00',
        '2026-03-02T06:10:00', '2026-03-09T06:10:00', '2026-03-16T06:10:00', '2026-03-23T06:10:00',
      ],
      priorRunDates: [
        '2025-10-06T06:10:00', '2025-10-13T06:10:00', '2025-10-20T06:10:00', '2025-10-27T06:10:00',
        '2025-11-03T06:10:00', '2025-11-10T06:10:00', '2025-11-17T06:10:00', '2025-11-24T06:10:00',
        '2025-12-01T06:10:00', '2025-12-08T06:10:00', '2025-12-15T06:10:00', '2025-12-22T06:10:00',
      ],
    },
    price: {
      current: [22, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 23],
      prior: [21, 21, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22],
      currentRunDates: [
        '2026-01-05T06:10:00', '2026-01-12T06:10:00', '2026-01-19T06:10:00', '2026-01-26T06:10:00',
        '2026-02-02T06:10:00', '2026-02-09T06:10:00', '2026-02-16T06:10:00', '2026-02-23T06:10:00',
        '2026-03-02T06:10:00', '2026-03-09T06:10:00', '2026-03-16T06:10:00', '2026-03-23T06:10:00',
      ],
      priorRunDates: [
        '2025-10-06T06:10:00', '2025-10-13T06:10:00', '2025-10-20T06:10:00', '2025-10-27T06:10:00',
        '2025-11-03T06:10:00', '2025-11-10T06:10:00', '2025-11-17T06:10:00', '2025-11-24T06:10:00',
        '2025-12-01T06:10:00', '2025-12-08T06:10:00', '2025-12-15T06:10:00', '2025-12-22T06:10:00',
      ],
    },
  },

  events: {
    title: "Run-to-run market events last quarter",
    subtitle: "Last-quarter event totals against the prior full quarter.",
    newListings: {
      label: 'Listings added',
      value: "+18 vs Q4 '25",
      copy: "Fresh introductions are only slightly ahead of the same point last Q4 '25, so the catalog is still expanding but not surging.",
    },
    droppedListings: {
      label: 'Listings removed',
      value: "14 vs Q4 '25",
      copy: 'Some churn is present, but the removal count is too small to imply retreat.',
    },
    restocks: {
      label: 'OUT → IN restocks',
      value: "38 vs Q4 '25",
      copy: "Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than Q4 '25.",
    },
    oosFlips: {
      label: 'IN → OUT stockouts',
      value: "+16 vs Q4 '25",
      copy: "Fewer listings moved from IN to OUT than at the same point last Q4 '25, which is consistent with availability stabilising.",
    },
  },
};
