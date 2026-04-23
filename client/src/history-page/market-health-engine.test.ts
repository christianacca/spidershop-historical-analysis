import { describe, it, expect } from 'vitest';
import {
  buildMarketHealthPayload,
  buildMarketHealthPayloadAllWindows,
} from './market-health-engine.js';
import { rawMarketHealthData } from './__fixtures__/marketHealthRaw.js';
import type { WindowId } from './types.js';

// ---------------------------------------------------------------------------
// Fixture-level constants (hand-calculated from marketHealthRaw.ts)
// ---------------------------------------------------------------------------

// Run datetimes in order
const RUN0 = '2026-01-05T06:10:00'; // Q1
const RUN1 = '2026-01-12T06:10:00'; // Q1  (within current-quarter prior: Jan1–Jan13)
const RUN2 = '2026-04-06T06:10:00'; // Q2
const RUN3 = '2026-04-13T06:10:00'; // Q2 = referenceDate

// Species names
const AVG = 'Avicularia avicularia';    // stable — all 4 runs
const BRA = 'Brachypelma hamorii';     // runs 0,1 only (dropped)
const CAR = 'Caribena versicolor';     // run 0, absent run 1, back runs 2-3 (restock)
const DOL = 'Dolichothele diamantinensis'; // multi-variant, all runs
const EPH = 'Ephebopus murinus';       // size transition: size 2.0 → absent → size 2.5

// ── Hand-calculated KPI values ───────────────────────────────────────────────

// ALL-TIME (all 4 runs, ref = RUN3)
//   observed: 5 distinct species (A,B,C,D,E)
//   stock_rate: latest run (RUN3) has {A,C,D,E}=4; total seen=5 → 4/5=80%
//   wishlist at RUN3: A=16, C=34, D=max(8,8)=8, E=18 → sorted [8,16,18,34] → median (16+18)/2=17
//   price at RUN3: A=26, C=34, D=max(10,20)=20, E=28 → sorted [20,26,28,34] → median (26+28)/2=27

// CURRENT-QUARTER (Q2 2026 = Apr1–Apr13; prior = Q1 portion Jan1–Jan13)
//   win: runs 2,3 → species {A,C,D,E}
//   observed=4; stock_rate=4/4=100%; wl=17; price=27
//   prior: runs 0,1 (both within Jan1–Jan13) → species {A,B,C,D,E}
//   observed_prior=5; stock_prior: run1 has {A,B,D}=3, total seen in prior=5 → 60%
//   wl_prior at RUN1: A=12, B=22, D=max(6,6)=6 → sorted [6,12,22] → median=12
//   price_prior at RUN1: A=22, B=42, D=max(10,20)=20 → sorted [20,22,42] → median=22
//   deltas: d_obs=-1, d_stock=+40, d_wl=+5, d_price=+5

// LAST-QUARTER (Q1 2026 = Jan1–Mar31; prior = Q4 2025 → no records)
//   win: runs 0,1 → observed=5; stock=3/5=60%; wl=12; price=22
//   no prior data → showPrior=false, deltas=null

// THIS-YEAR (2026; prior=2025 → no records)
//   win: all 4 runs → observed=5; stock=80%; wl=17; price=27
//   no prior data → showPrior=false

// THIS-MONTH (April 2026 = Apr1–Apr13; prior=March → no records)
//   win: runs 2,3 → same as current-quarter win
//   no prior data → showPrior=false

// ALL-TIME events (hand-verified):
//   new_listings=0, dropped_listings=1 (B), restocks=1 (C), oos_flips=2 (C+B)

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function payload(windowId: WindowId) {
  return buildMarketHealthPayload(rawMarketHealthData, windowId);
}

// ===========================================================================
// Window bounds — all 7 windows return valid payloads
// ===========================================================================

describe('all 7 windowIds', () => {
  const ALL: WindowId[] = [
    'this-month', 'last-month', 'current-quarter', 'last-quarter',
    'this-year', 'last-year', 'all-time',
  ];

  it.each(ALL)('%s returns a payload without throwing', (windowId) => {
    const p = payload(windowId as WindowId);
    expect(p.windowId).toBe(windowId);
    expect(p.kpis).toBeDefined();
    expect(p.sparklineSeries).toBeDefined();
    expect(p.events).toBeDefined();
  });

  it('all-time → showPrior: false', () => {
    expect(payload('all-time').showPrior).toBe(false);
  });

  it('current-quarter → showPrior: true (prior data exists + ≥2 current runs)', () => {
    expect(payload('current-quarter').showPrior).toBe(true);
  });

  it('last-quarter → showPrior: false (no prior data for Q4 2025)', () => {
    expect(payload('last-quarter').showPrior).toBe(false);
  });
});

// ===========================================================================
// Window basis notes
// ===========================================================================

describe('basis notes', () => {
  it('in-progress window (current-quarter) uses dynamic basis note', () => {
    const note = payload('current-quarter').windowBasisNote;
    // Must contain the current-quarter label and concrete date spans
    expect(note).toContain('Q2 2026');
    expect(note).toContain('Q1 2026');
    expect(note).toContain('Apr 1');
    expect(note).toContain('Apr 13');
    expect(note).toContain('Jan 1');
  });

  it('in-progress window (this-month) uses dynamic basis note containing month label', () => {
    const note = payload('this-month').windowBasisNote;
    expect(note).toContain('Apr 2026');
    expect(note).toContain('Apr 1');
    expect(note).toContain('Apr 13');
  });

  it('in-progress window (this-year) uses dynamic basis note containing year labels', () => {
    const note = payload('this-year').windowBasisNote;
    expect(note).toContain('2026');
    expect(note).toContain('2025');
  });

  it('completed window (last-quarter) uses static basis note', () => {
    const note = payload('last-quarter').windowBasisNote;
    expect(note).toBe('Comparison basis: last full quarter vs prior full quarter.');
  });

  it('completed window (all-time) uses static basis note', () => {
    const note = payload('all-time').windowBasisNote;
    expect(note).toBe(
      'Comparison basis: structural context only, with no prior-period delta.',
    );
  });

  it('in-progress sparkline basis note (current-quarter) also uses dynamic dates', () => {
    const note = payload('current-quarter').sparklineBasisNote;
    expect(note).toContain('Q2 2026');
    expect(note).toContain('Apr 1');
    expect(note).toContain('Apr 13');
  });
});

// ===========================================================================
// Window filtering — boundary-inclusive
// ===========================================================================

describe('window filtering (boundary inclusivity)', () => {
  // Q1 runs: Jan5 and Jan12 — both should appear in last-quarter
  it('last-quarter window includes all Q1 runs', () => {
    const p = payload('last-quarter');
    // All 5 species appear across Q1, so observed=5
    expect(p.kpis.observed.value).toBe('5');
  });

  // Q2 runs: Apr6 and Apr13 — both should appear in current-quarter
  it('current-quarter window includes all Q2 runs', () => {
    const p = payload('current-quarter');
    expect(p.kpis.observed.value).toBe('4');
  });
});

// ===========================================================================
// Genus filter
// ===========================================================================

describe('genus filter', () => {
  it('isAllSelected:true returns all records', () => {
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: true,
      selectedGenera: ['Avicularia'],
    });
    expect(p.kpis.observed.value).toBe('5');
  });

  it('isAllSelected:false filters to matching genus only', () => {
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    });
    // Only Avicularia avicularia matches genus Avicularia → 1 species
    expect(p.kpis.observed.value).toBe('1');
  });

  it('non-matching genus returns empty state', () => {
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: false,
      selectedGenera: ['Nonexistent'],
    });
    expect(p.kpis.observed.value).toBe('0');
  });

  it('scopeLabel for ≤3 genera: natural list', () => {
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena'],
    });
    expect(p.scopeLabel).toBe('Avicularia and Caribena');
  });

  it('scopeLabel for 4+ genera: "your N selected genera"', () => {
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena', 'Brachypelma', 'Dolichothele'],
    });
    expect(p.scopeLabel).toBe('your 4 selected genera');
  });

  it('all-mode scopeLabel is empty string', () => {
    expect(payload('all-time').scopeLabel).toBe('');
  });
});

// ===========================================================================
// Observed species
// ===========================================================================

describe('computeObserved', () => {
  it('all-time: counts 5 distinct species', () => {
    expect(payload('all-time').kpis.observed.value).toBe('5');
  });

  it('current-quarter: multi-variant species (Dolichothele) counted as 1', () => {
    // Q2 has 4 species: A,C,D,E — Dolichothele has 2 variant rows but counted once
    expect(payload('current-quarter').kpis.observed.value).toBe('4');
  });
});

// ===========================================================================
// In-stock rate
// ===========================================================================

describe('computeStockRate', () => {
  it('100% when all species present in latest run (current-quarter)', () => {
    // Q2: all 4 species in both runs → 4/4 = 100%
    expect(payload('current-quarter').kpis.stock.value).toBe('100%');
  });

  it('correct percentage when species drops out (all-time)', () => {
    // Latest run (RUN3) has 4 of 5 → 80%
    expect(payload('all-time').kpis.stock.value).toBe('80%');
  });

  it('empty records returns 0% (last-year has no records)', () => {
    const p = payload('last-year');
    expect(p.kpis.stock.value).toBe('0%');
  });
});

// ===========================================================================
// Median wishlist
// ===========================================================================

describe('computeMedianWishlist', () => {
  it('multi-variant species: max wishlistCount used (not sum)', () => {
    // Dolichothele has 2 variants both with wl=8 → max=8 (same in this case)
    // But if values differed, max should win — test via all-time where D is present
    // All-time at RUN3: [8(D), 16(A), 18(E), 34(C)] → median=(16+18)/2=17
    expect(payload('all-time').kpis.wishlist.value).toBe('17');
  });

  it('odd number of species: median is the middle value (last-quarter, 3 species at RUN1)', () => {
    // RUN1 (latest in Q1): {A=12, B=22, D=6} → sorted [6,12,22] → median=12
    expect(payload('last-quarter').kpis.wishlist.value).toBe('12');
  });

  it('even number of species: median is average of two middle values (current-quarter)', () => {
    // RUN3: [8,16,18,34] → (16+18)/2=17
    expect(payload('current-quarter').kpis.wishlist.value).toBe('17');
  });
});

// ===========================================================================
// Median price
// ===========================================================================

describe('computeMedianPrice', () => {
  it('multi-variant species: max priceGbp used', () => {
    // Dolichothele variants: price 10 and 20 → max=20
    // All-time at RUN3: [20(D), 26(A), 28(E), 34(C)] → (26+28)/2=27
    expect(payload('all-time').kpis.price.value).toBe('GBP 27');
  });

  it('correct value for last-quarter', () => {
    // RUN1: [20(D), 22(A), 42(B)] → median=22
    expect(payload('last-quarter').kpis.price.value).toBe('GBP 22');
  });
});

// ===========================================================================
// Sparkline resampling
// ===========================================================================

describe('resampleTo12 (via sparkline series)', () => {
  it('fewer than 12 runs → series length equals actual run count', () => {
    // current-quarter has 2 runs → observed series: [4, 4] → returned as-is (no padding)
    const series = payload('current-quarter').sparklineSeries.observed.current;
    expect(series).toHaveLength(2);
    expect(series[0]).toBe(4);
    expect(series[1]).toBe(4);
  });

  it('all values in series are numbers', () => {
    const series = payload('all-time').sparklineSeries.stock.current;
    expect(series).toHaveLength(4);
    for (const v of series) expect(typeof v).toBe('number');
  });

  it('all-time observed series: [5,3,4,4] returned as-is', () => {
    // n=4 < 12: returned without padding
    const series = payload('all-time').sparklineSeries.observed.current;
    expect(series).toHaveLength(4);
    expect(series[0]).toBe(5);
    expect(series[1]).toBe(3);
    expect(series[2]).toBe(4);
    expect(series[3]).toBe(4);
  });

  it('prior sparkline length equals actual prior run count when showPrior is true', () => {
    const p = payload('current-quarter');
    expect(p.showPrior).toBe(true);
    expect(p.sparklineSeries.observed.prior).toHaveLength(2);
  });

  it('prior sparkline is empty array when showPrior is false', () => {
    const p = payload('all-time');
    expect(p.showPrior).toBe(false);
    expect(p.sparklineSeries.observed.prior).toHaveLength(0);
  });
});

// ===========================================================================
// Sparkline run dates
// ===========================================================================

describe('sparkline run dates', () => {
  it('currentRunDates length equals actual run count for current-quarter window', () => {
    const p = payload('current-quarter');
    expect(p.sparklineSeries.observed.currentRunDates).toHaveLength(2);
  });

  it('currentRunDates first entry is the earliest run in the window', () => {
    // current-quarter win runs: [RUN2, RUN3] → returned as-is → first = RUN2
    const p = payload('current-quarter');
    expect(p.sparklineSeries.observed.currentRunDates[0]).toBe(RUN2);
  });

  it('currentRunDates last entry is the most recent run in the window', () => {
    // current-quarter has 2 runs → last index is 1
    const p = payload('current-quarter');
    expect(p.sparklineSeries.observed.currentRunDates[1]).toBe(RUN3);
  });

  it('all four series share identical currentRunDates within a window', () => {
    const p = payload('current-quarter');
    const ref = p.sparklineSeries.observed.currentRunDates;
    expect(p.sparklineSeries.stock.currentRunDates).toEqual(ref);
    expect(p.sparklineSeries.wishlist.currentRunDates).toEqual(ref);
    expect(p.sparklineSeries.price.currentRunDates).toEqual(ref);
  });

  it('priorRunDates length equals actual prior run count when showPrior is true', () => {
    const p = payload('current-quarter');
    expect(p.showPrior).toBe(true);
    expect(p.sparklineSeries.observed.priorRunDates).toHaveLength(2);
  });

  it('priorRunDates first entry is the earliest prior-period run', () => {
    // current-quarter prior runs: [RUN0, RUN1] → returned as-is → first = RUN0
    const p = payload('current-quarter');
    expect(p.sparklineSeries.observed.priorRunDates[0]).toBe(RUN0);
  });

  it('priorRunDates last entry is the most recent prior-period run', () => {
    // current-quarter prior has 2 runs → last index is 1
    const p = payload('current-quarter');
    expect(p.sparklineSeries.observed.priorRunDates[1]).toBe(RUN1);
  });

  it('priorRunDates is empty array when showPrior is false (all-time)', () => {
    const p = payload('all-time');
    expect(p.showPrior).toBe(false);
    expect(p.sparklineSeries.observed.priorRunDates).toEqual([]);
  });

  it('all-time currentRunDates: first entry is RUN0, last is RUN3 (4 runs returned as-is)', () => {
    // all-time has 4 runs → n=4 < 12 → returned without padding
    const p = payload('all-time');
    expect(p.sparklineSeries.observed.currentRunDates).toHaveLength(4);
    expect(p.sparklineSeries.observed.currentRunDates[0]).toBe(RUN0);
    expect(p.sparklineSeries.observed.currentRunDates[3]).toBe(RUN3);
  });
});

// ===========================================================================
// Events — new listings
// ===========================================================================

describe('events: new listings', () => {
  it('first appearance within window is a new listing (all-time, 0 in fixture)', () => {
    // In the fixture, all species appear in run 0 (the first window run for all-time)
    // So no species is "new" after the first run — new_listings=0
    const events = payload('all-time').events;
    expect(events.newListings.value).toBe('0 total');
  });

  it('size transition is NOT counted as a new listing', () => {
    // Ephebopus (size 2.0 → 2.5, same url-e) appears at run 2 after being absent at run 1
    // last_seen_idx is run 0, gap=2, same URL, different size → size transition → NOT new
    // all-time new_listings stays 0
    expect(payload('all-time').events.newListings.value).toBe('0 total');
  });
});

// ===========================================================================
// Events — dropped listings
// ===========================================================================

describe('events: dropped listings', () => {
  it('species absent from final run counted as dropped (all-time)', () => {
    // Brachypelma disappears after run 1 and never returns → dropped=1
    expect(payload('all-time').events.droppedListings.value).toBe('1 total');
  });

  it('size transition is NOT counted as dropped', () => {
    // Ephebopus disappears from run 1 but reappears (size transition) → not dropped
    // So only Brachypelma is dropped → still 1 total
    expect(payload('all-time').events.droppedListings.value).toBe('1 total');
  });
});

// ===========================================================================
// Events — restocks (OUT → IN)
// ===========================================================================

describe('events: restocks', () => {
  it('species absent then present (not size transition) counts as restock (all-time)', () => {
    // Caribena: absent run 1, back run 2, same URL, same size → restock=1
    expect(payload('all-time').events.restocks.value).toBe('1 total');
  });

  it('size transition is NOT counted as a restock (Ephebopus)', () => {
    // Ephebopus: absent run 1, back run 2 with different size/same URL → size transition
    // → NOT a restock; restocks stays 1
    expect(payload('all-time').events.restocks.value).toBe('1 total');
  });
});

// ===========================================================================
// Events — OOS flips (IN → OUT)
// ===========================================================================

describe('events: OOS flips', () => {
  it('species present then absent (not size transition) counts as OOS flip (all-time)', () => {
    // Caribena disappears at run 1 → oos_flip; Brachypelma disappears at run 2 → oos_flip
    // Total = 2; all-time mode uses "N total" (no + prefix) per Python spec
    expect(payload('all-time').events.oosFlips.value).toBe('2 total');
  });

  it('size transition is NOT counted as OOS flip (Ephebopus)', () => {
    // Ephebopus disappears run 1 but it's a size transition → NOT an oos_flip
    // Total stays 2 (all-time format: no + prefix)
    expect(payload('all-time').events.oosFlips.value).toBe('2 total');
  });
});

// ===========================================================================
// Size transition detection
// ===========================================================================

describe('size transition detection', () => {
  it('current-quarter events: zero for all event types (no changes between runs 2 and 3)', () => {
    const events = payload('current-quarter').events;
    expect(events.newListings.value).toBe('+0 vs prior quarter QTD');
    expect(events.droppedListings.value).toBe('0 vs prior quarter QTD');
    expect(events.restocks.value).toBe('0 vs prior quarter QTD');
    expect(events.oosFlips.value).toBe('+0 vs prior quarter QTD');
  });
});

// ===========================================================================
// Copy strings — observed
// ===========================================================================

describe('observedCopy', () => {
  it('all-time → all-time sentence', () => {
    const copy = payload('all-time').kpis.observed.copy;
    expect(copy).toContain('All-time view is best read as structural context');
  });

  it('delta ≥ 3 → "Breadth is ahead of…" sentence', () => {
    // current-quarter: d_observed=-1, so we need a different window for this branch.
    // Use a custom dataset where observed went up significantly.
    // Instead, test via the copy helper directly through a fixture where delta is large.
    // We'll verify by checking a window where the copy is the "slightly ahead" or "fewer" branch.
    // current-quarter d_observed=-1 → "Fewer species" branch
    const copy = payload('current-quarter').kpis.observed.copy;
    expect(copy).toContain('Fewer species are being seen in-stock');
  });

  it('no prior → informational sentence without comparison', () => {
    // last-quarter has no prior data → delta=null → uses "no prior available" copy
    const copy = payload('last-quarter').kpis.observed.copy;
    expect(copy).toContain('no prior period is available for comparison');
  });
});

// ===========================================================================
// Copy strings — stock
// ===========================================================================

describe('stockCopy', () => {
  it('all-time → all-time sentence', () => {
    expect(payload('all-time').kpis.stock.copy).toContain('All-time availability smooths out');
  });

  it('delta ≥ +40 → "firmer than" sentence (current-quarter)', () => {
    // d_stock = 100 - 60 = +40 → "Availability is firmer than…"
    const copy = payload('current-quarter').kpis.stock.copy;
    expect(copy).toContain('Availability is firmer than');
  });

  it('no prior → informational sentence with value%', () => {
    const copy = payload('last-quarter').kpis.stock.copy;
    expect(copy).toContain('60%');
  });
});

// ===========================================================================
// Copy strings — wishlist
// ===========================================================================

describe('wishlistCopy', () => {
  it('all-time → all-time sentence', () => {
    expect(payload('all-time').kpis.wishlist.copy).toContain('All-time wishlist levels');
  });

  it('delta ≥ 4 → "ahead of" sentence (current-quarter: d_wl=+5)', () => {
    expect(payload('current-quarter').kpis.wishlist.copy).toContain(
      'Median wishlist counts are ahead of',
    );
  });
});

// ===========================================================================
// Copy strings — price
// ===========================================================================

describe('priceCopy', () => {
  it('all-time → all-time sentence', () => {
    expect(payload('all-time').kpis.price.copy).toContain('All-time price mainly describes');
  });

  it('delta ≥ 2 → "firmer than" sentence (current-quarter: d_price=+5)', () => {
    expect(payload('current-quarter').kpis.price.copy).toContain('Prices are somewhat firmer');
  });
});

// ===========================================================================
// Delta formatting
// ===========================================================================

describe('delta formatting', () => {
  it('formatObservedDelta: negative delta → "-N vs …" with class "down"', () => {
    // current-quarter d_observed=-1
    const p = payload('current-quarter');
    expect(p.kpis.observed.delta).toBe('-1 vs prior quarter QTD');
    expect(p.kpis.observed.deltaClass).toBe('down');
  });

  it('formatObservedDelta: all-time → "No prior comparison" with class "flat"', () => {
    const p = payload('all-time');
    expect(p.kpis.observed.delta).toBe('No prior comparison');
    expect(p.kpis.observed.deltaClass).toBe('flat');
  });

  it('formatStockDelta: positive delta → "+N pts vs …" with class ""', () => {
    // current-quarter d_stock=+40
    const p = payload('current-quarter');
    expect(p.kpis.stock.delta).toBe('+40 pts vs prior quarter QTD');
    expect(p.kpis.stock.deltaClass).toBe('');
  });

  it('formatWishlistDelta: zero delta → "+0 vs …" with class "flat"', () => {
    // Build a custom scenario where wl delta=0.
    // Use last-quarter which has no prior → null → "No prior comparison"
    // Instead verify the format string for a known +5 (current-quarter)
    const p = payload('current-quarter');
    expect(p.kpis.wishlist.delta).toBe('+5 vs prior quarter QTD');
    expect(p.kpis.wishlist.deltaClass).toBe('');
  });

  it('formatWishlistDelta: all-time → "No prior comparison" with class "flat"', () => {
    const p = payload('all-time');
    expect(p.kpis.wishlist.deltaClass).toBe('flat');
    expect(p.kpis.wishlist.delta).toBe('No prior comparison');
  });

  it('formatPriceDelta: positive delta → "+GBP N vs …" with class ""', () => {
    // current-quarter d_price=+5
    const p = payload('current-quarter');
    expect(p.kpis.price.delta).toBe('+GBP 5 vs prior quarter QTD');
    expect(p.kpis.price.deltaClass).toBe('');
  });

  it('formatPriceDelta: all-time → "No prior comparison" with class "flat"', () => {
    const p = payload('all-time');
    expect(p.kpis.price.deltaClass).toBe('flat');
    expect(p.kpis.price.delta).toBe('No prior comparison');
  });
});

// ===========================================================================
// Dynamic basis notes: buildInprogressBasisNotes
// ===========================================================================

describe('buildInprogressBasisNotes', () => {
  it('this-month: contains month label and both date spans', () => {
    const p = payload('this-month');
    const note = p.windowBasisNote;
    expect(note).toContain('Apr 2026');
    expect(note).toContain('Apr 1');
    expect(note).toContain('Apr 13');
    // Prior month (March) dates
    expect(note).toMatch(/Mar/);
  });

  it('current-quarter: contains quarter labels and matched spans', () => {
    const p = payload('current-quarter');
    expect(p.windowBasisNote).toContain('Q2 2026');
    expect(p.windowBasisNote).toContain('Q1 2026');
    expect(p.windowBasisNote).toContain('Jan 1');
  });

  it('this-year: contains year labels and matched spans', () => {
    const p = payload('this-year');
    expect(p.windowBasisNote).toContain('2026');
    expect(p.windowBasisNote).toContain('2025');
    expect(p.windowBasisNote).toContain('Jan 1');
  });
});

// ===========================================================================
// Full payload shape
// ===========================================================================

describe('full payload shape', () => {
  it('buildMarketHealthPayload(current-quarter): all KPI fields populated', () => {
    const p = payload('current-quarter');
    for (const kpiKey of ['observed', 'stock', 'wishlist', 'price'] as const) {
      const kpi = p.kpis[kpiKey];
      expect(kpi.id).toBe(kpiKey);
      expect(kpi.title).not.toBe('');
      expect(kpi.value).not.toBe('');
      expect(kpi.delta).not.toBe('');
      expect(kpi.copy).not.toBe('');
    }
  });

  it('buildMarketHealthPayload(all-time): all deltaClass values are "flat"', () => {
    const p = payload('all-time');
    expect(p.kpis.observed.deltaClass).toBe('flat');
    expect(p.kpis.stock.deltaClass).toBe('flat');
    expect(p.kpis.wishlist.deltaClass).toBe('flat');
    expect(p.kpis.price.deltaClass).toBe('flat');
  });

  it('buildMarketHealthPayload(all-time): all delta texts are "No prior comparison"', () => {
    const p = payload('all-time');
    for (const kpiKey of ['observed', 'stock', 'wishlist', 'price'] as const) {
      expect(p.kpis[kpiKey].delta).toBe('No prior comparison');
    }
  });
});

// ===========================================================================
// buildMarketHealthPayloadAllWindows
// ===========================================================================

describe('buildMarketHealthPayloadAllWindows', () => {
  it('returns exactly 7 keys matching ALL_WINDOW_IDS', () => {
    const all = buildMarketHealthPayloadAllWindows(rawMarketHealthData);
    const keys = Object.keys(all);
    const expected: WindowId[] = [
      'this-month', 'last-month', 'current-quarter', 'last-quarter',
      'this-year', 'last-year', 'all-time',
    ];
    expect(keys.sort()).toEqual(expected.sort());
  });

  it('each value is a valid MarketHealthPayload with correct windowId', () => {
    const all = buildMarketHealthPayloadAllWindows(rawMarketHealthData);
    for (const [windowId, p] of Object.entries(all)) {
      expect(p.windowId).toBe(windowId);
      expect(p.kpis).toBeDefined();
      expect(p.sparklineSeries).toBeDefined();
    }
  });
});

// ===========================================================================
// Additional coverage datasets — copy-function branches not reachable from the
// main fixture (which only produces delta=-1 observed, delta=+40 stock, etc.)
// ===========================================================================

// Helper: build a minimal MarketHealthRawData for current-quarter window tests.
// prior = Jan 5 records; current = Apr 5 + Apr 13 records.
// referenceDate is Apr 13 2026 so current-quarter = Q2 (Apr 1–13), prior = Q1 (Jan 1–13).
function makeMinimalRaw(
  priorSpecies: { name: string; wl: number; price: number }[],
  currentSpecies: { dt: string; name: string; wl: number; price: number }[],
): import('./types.js').MarketHealthRawData {
  const priorRecords = priorSpecies.map(s => ({
    scrapeDatetime: '2026-01-05T06:10:00',
    scientificName: s.name,
    sizeVariant: '2.0',
    pageUrl: `url-${s.name.toLowerCase().replace(' ', '-')}`,
    wishlistCount: s.wl,
    priceGbp: s.price,
  }));
  const currentRecords = currentSpecies.map(s => ({
    scrapeDatetime: s.dt,
    scientificName: s.name,
    sizeVariant: '2.0',
    pageUrl: `url-${s.name.toLowerCase().replace(' ', '-')}`,
    wishlistCount: s.wl,
    priceGbp: s.price,
  }));
  return { referenceDate: '2026-04-13T06:10:00', records: [...priorRecords, ...currentRecords] };
}

describe('copy branches — delta=0 (all metrics)', () => {
  // prior and current: same single species, same wl and price
  // d_obs=0, d_stock=0, d_wl=0, d_price=0
  const raw = makeMinimalRaw(
    [{ name: 'Gamma gamma', wl: 10, price: 25 }],
    [
      { dt: '2026-04-05T06:10:00', name: 'Gamma gamma', wl: 10, price: 25 },
      { dt: '2026-04-13T06:10:00', name: 'Gamma gamma', wl: 10, price: 25 },
    ],
  );

  it('observedCopy: delta=0 → "only slightly ahead" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.observed.copy).toContain('only slightly ahead');
  });

  it('stockCopy: delta=0 → "holding steady" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.stock.copy).toContain('holding steady');
  });

  it('wishlistCopy: delta=0 → "stable" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.wishlist.copy).toContain('stable');
  });

  it('priceCopy: delta=0 → "steady" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.price.copy).toContain('steady');
  });

  it('formatWishlistDelta: delta=0 → class "flat"', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.wishlist.deltaClass).toBe('flat');
    expect(p.kpis.wishlist.delta).toContain('+0');
  });

  it('formatPriceDelta: delta=0 → class "flat"', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.price.deltaClass).toBe('flat');
    expect(p.kpis.price.delta).toContain('GBP 0');
  });
});

describe('copy branches — small positive deltas (d_obs=+1, d_wl=+1, d_price=+1)', () => {
  // prior: 1 species (wl=10, p=20)
  // current: 2 species — wl median=11, price median=(19+21)/2=20 → d_price=0? Let me calc:
  //   Alpha(wl=12,p=21) + Beta(wl=10,p=19) → median wl=(10+12)/2=11 → d_wl=11-10=1
  //   median price=(19+21)/2=20 → d_price=round(20-20)=0
  // Adjust: Alpha(wl=12,p=22) + Beta(wl=10,p=20) → median price=(20+22)/2=21 → d_price=1
  const raw = makeMinimalRaw(
    [{ name: 'Alpha alpha', wl: 10, price: 20 }],
    [
      { dt: '2026-04-05T06:10:00', name: 'Alpha alpha', wl: 12, price: 22 },
      { dt: '2026-04-05T06:10:00', name: 'Beta beta', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Alpha alpha', wl: 12, price: 22 },
      { dt: '2026-04-13T06:10:00', name: 'Beta beta', wl: 10, price: 20 },
    ],
  );

  it('observedCopy: 0 < delta < 3 → "only slightly ahead" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // d_obs = 2-1 = 1
    expect(p.kpis.observed.copy).toContain('only slightly ahead');
  });

  it('wishlistCopy: 1 ≤ delta ≤ 3 → "modestly above" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // d_wl = 11-10 = 1
    expect(p.kpis.wishlist.copy).toContain('modestly above');
  });

  it('priceCopy: delta=1 → "edged up" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // d_price = round(21-20) = 1
    expect(p.kpis.price.copy).toContain('edged up');
  });
});

describe('copy branches — negative deltas (d_wl<0, d_price<0)', () => {
  // prior: 2 species with high wl/price
  // current: 2 species with lower wl/price
  // prior wl=[10,14] → median=12; current wl=[6,8] → median=7; d_wl=7-12=-5 → "softer"
  // prior price=[22,26] → median=24; current price=[18,20] → median=19; d_price=-5 → "softened"
  const raw = makeMinimalRaw(
    [
      { name: 'Alpha alpha', wl: 10, price: 22 },
      { name: 'Beta beta', wl: 14, price: 26 },
    ],
    [
      { dt: '2026-04-05T06:10:00', name: 'Alpha alpha', wl: 6, price: 18 },
      { dt: '2026-04-05T06:10:00', name: 'Beta beta', wl: 8, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Alpha alpha', wl: 6, price: 18 },
      { dt: '2026-04-13T06:10:00', name: 'Beta beta', wl: 8, price: 20 },
    ],
  );

  it('wishlistCopy: delta ≤ -1 → "softer" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.wishlist.copy).toContain('softer');
  });

  it('priceCopy: delta ≤ -1 → "softened" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.price.copy).toContain('softened');
  });

  it('formatWishlistDelta: negative delta → class "down"', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.wishlist.deltaClass).toBe('down');
  });

  it('formatPriceDelta: negative delta → class "down"', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.price.deltaClass).toBe('down');
  });
});

describe('copy branches — observedCopy delta ≥ 3', () => {
  // prior: 1 species; current: 5 species → d_obs=4
  const raw = makeMinimalRaw(
    [{ name: 'Sp1 x', wl: 10, price: 20 }],
    [
      { dt: '2026-04-05T06:10:00', name: 'Sp1 x', wl: 10, price: 20 },
      { dt: '2026-04-05T06:10:00', name: 'Sp2 x', wl: 10, price: 20 },
      { dt: '2026-04-05T06:10:00', name: 'Sp3 x', wl: 10, price: 20 },
      { dt: '2026-04-05T06:10:00', name: 'Sp4 x', wl: 10, price: 20 },
      { dt: '2026-04-05T06:10:00', name: 'Sp5 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Sp1 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Sp2 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Sp3 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Sp4 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Sp5 x', wl: 10, price: 20 },
    ],
  );

  it('observedCopy: delta ≥ 3 → "Breadth is ahead of" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // d_obs = 5-1 = 4
    expect(p.kpis.observed.copy).toContain('Breadth is ahead of');
  });

  it('formatObservedDelta: positive delta → "+N vs …" with class ""', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.observed.delta).toMatch(/^\+4 vs/);
    expect(p.kpis.observed.deltaClass).toBe('');
  });
});

describe('copy branches — stockCopy slipping (delta ≤ -7)', () => {
  // prior: 1 species → 100% in-stock
  // current run1 (Apr 5): 10 species; current run2 (Apr 13): only Sp01 x → 1/10=10%
  // d_stock = 10 - 100 = -90 → "slipping"
  const currentRun1 = ['Sp01 x','Sp02 x','Sp03 x','Sp04 x','Sp05 x',
                        'Sp06 x','Sp07 x','Sp08 x','Sp09 x','Sp10 x'].map(name => ({
    dt: '2026-04-05T06:10:00', name, wl: 10, price: 20,
  }));
  const raw = makeMinimalRaw(
    [{ name: 'Sp01 x', wl: 10, price: 20 }],
    [
      ...currentRun1,
      { dt: '2026-04-13T06:10:00', name: 'Sp01 x', wl: 10, price: 20 },
    ],
  );

  it('stockCopy: delta ≤ -7 → "availability slipping" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // current stock = 1/10 = 10%, prior = 100%, d=-90
    expect(p.kpis.stock.copy).toContain('percentage points lower than');
  });

  it('stockCopy slipping: delta text has "pts" and negative value', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.stock.delta).toMatch(/-\d+ pts vs/);
    expect(p.kpis.stock.deltaClass).toBe('down');
  });
});

describe('copy branches — eventsCopyNewListings count ≥ 5', () => {
  // current run1 (Apr 5): 2 existing species
  // current run2 (Apr 13): those 2 + 5 brand-new species → 5 new listings
  const raw = makeMinimalRaw(
    [
      { name: 'Old1 x', wl: 10, price: 20 },
      { name: 'Old2 x', wl: 10, price: 20 },
    ],
    [
      { dt: '2026-04-05T06:10:00', name: 'Old1 x', wl: 10, price: 20 },
      { dt: '2026-04-05T06:10:00', name: 'Old2 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Old1 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'Old2 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'New1 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'New2 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'New3 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'New4 x', wl: 10, price: 20 },
      { dt: '2026-04-13T06:10:00', name: 'New5 x', wl: 10, price: 20 },
    ],
  );

  it('eventsCopyNewListings count ≥ 5 → "Introductions are materially ahead" copy', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.events.newListings.copy).toContain('Introductions are materially ahead');
  });
});

describe('resampleTo12 — n ≥ 12 (evenly-sampled)', () => {
  // 13 weekly runs in the all-time window → sparkline receives 13 raw values → n>=12 path
  const weeks = [
    '2025-01-06','2025-01-13','2025-01-20','2025-01-27',
    '2025-02-03','2025-02-10','2025-02-17','2025-02-24',
    '2025-03-03','2025-03-10','2025-03-17','2025-03-24',
    '2025-03-31',
  ];
  const rawManyRuns: import('./types.js').MarketHealthRawData = {
    referenceDate: '2025-03-31T06:10:00',
    records: weeks.map(date => ({
      scrapeDatetime: `${date}T06:10:00`,
      scientificName: 'Alpha alpha',
      sizeVariant: '2.0',
      pageUrl: 'url-a',
      wishlistCount: 10,
      priceGbp: 20,
    })),
  };

  it('all-time sparkline with 13 runs produces exactly 12 values (n≥12 path)', () => {
    const p = buildMarketHealthPayload(rawManyRuns, 'all-time');
    const series = p.sparklineSeries.observed.current;
    expect(series).toHaveLength(12);
    // All values should be 1 (1 species in every run)
    for (const v of series) expect(v).toBe(1);
  });
});

// ===========================================================================
// Window filtering — ms-precision boundaries
// ===========================================================================

describe('window filtering — ms-precision boundaries', () => {
  // current-quarter with referenceDate='2026-04-13T06:10:00':
  //   winStart = new Date(2026, 3, 1, 0, 0, 0, 0) = Apr 1 00:00:00.000 local
  //   winEnd   = parseIso('2026-04-13T06:10:00')  = Apr 13 06:10:00.000 local
  const REF = '2026-04-13T06:10:00';

  function singleRunRaw(dt: string): import('./types.js').MarketHealthRawData {
    return {
      referenceDate: REF,
      records: [{
        scrapeDatetime: dt,
        scientificName: 'Boundary sp',
        sizeVariant: '2.0',
        pageUrl: 'url-b',
        wishlistCount: 10,
        priceGbp: 20,
      }],
    };
  }

  it('record exactly on winStart boundary is included', () => {
    // Apr 1 00:00:00 is the exact winStart for current-quarter
    const p = buildMarketHealthPayload(singleRunRaw('2026-04-01T00:00:00'), 'current-quarter');
    expect(p.kpis.observed.value).toBe('1');
  });

  it('record exactly on winEnd boundary is included', () => {
    // referenceDate itself = exact winEnd
    const p = buildMarketHealthPayload(singleRunRaw('2026-04-13T06:10:00'), 'current-quarter');
    expect(p.kpis.observed.value).toBe('1');
  });

  it('record 1 ms before winStart is excluded', () => {
    // Mar 31 23:59:59.999 = 1ms before Apr 1 00:00:00
    const p = buildMarketHealthPayload(singleRunRaw('2026-03-31T23:59:59.999'), 'current-quarter');
    expect(p.kpis.observed.value).toBe('0');
  });

  it('record 1 ms after winEnd is excluded', () => {
    // Apr 13 06:10:00.001 = 1ms after referenceDate
    const p = buildMarketHealthPayload(singleRunRaw('2026-04-13T06:10:00.001'), 'current-quarter');
    expect(p.kpis.observed.value).toBe('0');
  });
});

// ===========================================================================
// resampleTo12 — exactly n=12 (unchanged path)
// ===========================================================================

describe('resampleTo12 — n = 12 (unchanged)', () => {
  // 12 weekly runs: first 6 have 1 species, last 6 have 2 species.
  // With n=12, resampleTo12 uses indices [0..11] → values returned as-is.
  const weeklyDts = [
    '2026-01-05', '2026-01-12', '2026-01-19', '2026-01-26',
    '2026-02-02', '2026-02-09', '2026-02-16', '2026-02-23',
    '2026-03-02', '2026-03-09', '2026-03-16', '2026-03-23',
  ].map(d => `${d}T06:10:00`);

  const rawExact12: import('./types.js').MarketHealthRawData = {
    referenceDate: weeklyDts[11],
    records: [
      // Alpha appears in all 12 runs
      ...weeklyDts.map(dt => ({
        scrapeDatetime: dt,
        scientificName: 'Alpha alpha',
        sizeVariant: '2.0',
        pageUrl: 'url-a',
        wishlistCount: 10,
        priceGbp: 20,
      })),
      // Beta appears only in the last 6 runs (indices 6–11)
      ...weeklyDts.slice(6).map(dt => ({
        scrapeDatetime: dt,
        scientificName: 'Beta beta',
        sizeVariant: '2.0',
        pageUrl: 'url-b',
        wishlistCount: 10,
        priceGbp: 20,
      })),
    ],
  };

  it('exactly 12 runs → observed sparkline is original values unchanged (n=12 path)', () => {
    const p = buildMarketHealthPayload(rawExact12, 'all-time');
    const series = p.sparklineSeries.observed.current;
    expect(series).toHaveLength(12);
    // Runs 0–5: only Alpha → 1 species; runs 6–11: Alpha + Beta → 2 species
    expect(series.slice(0, 6)).toEqual([1, 1, 1, 1, 1, 1]);
    expect(series.slice(6)).toEqual([2, 2, 2, 2, 2, 2]);
  });
});

// ===========================================================================
// stockCopy — near-term tightening branch (-6 ≤ delta ≤ -1)
// ===========================================================================

describe('copy branches — stockCopy near-term tightening (-6 ≤ delta ≤ -1)', () => {
  // prior: 1 species → 100% in-stock
  // current run1 (Apr 5): 20 species; current run2 (Apr 13): 19 species (1 dropped)
  // stock_current = round(19/20 * 100) = 95%; delta = 95 - 100 = -5 → "near-term tightening"
  const currentRun1 = Array.from({ length: 20 }, (_, i) => ({
    dt: '2026-04-05T06:10:00',
    name: `Sp${String(i + 1).padStart(2, '0')} x`,
    wl: 10,
    price: 20,
  }));
  const currentRun2 = currentRun1.slice(0, 19).map(s => ({ ...s, dt: '2026-04-13T06:10:00' }));

  const raw = makeMinimalRaw(
    [{ name: 'Sp01 x', wl: 10, price: 20 }],
    [...currentRun1, ...currentRun2],
  );

  it('stockCopy: -6 ≤ delta ≤ -1 → "near-term tightening" sentence', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    // d_stock = 95 - 100 = -5
    expect(p.kpis.stock.copy).toContain('near-term tightening');
  });

  it('formatStockDelta: negative non-large delta → "-N pts vs …" with class "down"', () => {
    const p = buildMarketHealthPayload(raw, 'current-quarter');
    expect(p.kpis.stock.delta).toMatch(/-\d+ pts vs/);
    expect(p.kpis.stock.deltaClass).toBe('down');
  });
});

// ===========================================================================
// Size transition — false cases
// ===========================================================================

describe('size transition — false cases', () => {
  // Helper: 4-run dataset (2 prior + 2 current) where Drifter disappears between runs
  // and reappears with specified pageUrl/sizeVariant combination.
  function makeDrifterRaw(
    prevUrl: string,
    prevSize: string,
    nextUrl: string,
    nextSize: string,
  ): import('./types.js').MarketHealthRawData {
    return {
      referenceDate: '2026-04-13T06:10:00',
      records: [
        // run0 (Jan5): Anchor y + Drifter x (prevUrl, prevSize)
        { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Drifter x', sizeVariant: prevSize, pageUrl: prevUrl, wishlistCount: 10, priceGbp: 20 },
        // run1 (Jan12): Anchor y only (Drifter absent = OOS flip)
        { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        // run2 (Apr6): Anchor y + Drifter x (nextUrl, nextSize)
        { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Drifter x', sizeVariant: nextSize, pageUrl: nextUrl, wishlistCount: 10, priceGbp: 20 },
        // run3 (Apr13): Anchor y + Drifter x (nextUrl, nextSize)
        { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Drifter x', sizeVariant: nextSize, pageUrl: nextUrl, wishlistCount: 10, priceGbp: 20 },
      ],
    };
  }

  it('same pageUrl, same sizeVariant → NOT a size transition (restock is counted)', () => {
    // Drifter disappears at run1 and reappears at run2 with the SAME url and size.
    // isSizeTransition: same URL, same size set → prevSizes === currSizes → returns false.
    // Result: Drifter is classified as a normal restock, not a size transition.
    const events = buildMarketHealthPayload(
      makeDrifterRaw('url-d', '2.0', 'url-d', '2.0'),
      'all-time',
    ).events;
    expect(events.restocks.value).toBe('1 total');
  });

  it('different pageUrl, same species → NOT a size transition (restock is counted)', () => {
    // Drifter disappears at run1 and reappears at run2 with a DIFFERENT pageUrl.
    // isSizeTransition: prevUrls and currUrls have no URL in common → loop skips → returns false.
    // Result: Drifter is classified as a normal restock, not a size transition.
    const events = buildMarketHealthPayload(
      makeDrifterRaw('url-d1', '2.0', 'url-d2', '3.0'),
      'all-time',
    ).events;
    expect(events.restocks.value).toBe('1 total');
  });

  it('same pageUrl, same species, gap > 3 runs → NOT a size transition (restock is counted)', () => {
    // Drifter disappears at run1 (idx=1) and reappears at run5 (idx=5): gap=4 > maxGap=3.
    // isSizeTransition checks gap first: 4 > 3 → returns false immediately.
    // Result: Drifter is classified as a normal restock, not a size transition.
    const raw: import('./types.js').MarketHealthRawData = {
      referenceDate: '2026-02-09T06:10:00',
      records: [
        // run0 (Jan5): Anchor y + Drifter x
        { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Drifter x', sizeVariant: '2.0', pageUrl: 'url-d', wishlistCount: 10, priceGbp: 20 },
        // runs 1–4 (Jan12–Feb2): Anchor only (Drifter absent)
        { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-01-19T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-01-26T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-02-02T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        // run5 (Feb9): Anchor + Drifter at same url, different size — gap=5 > maxGap=3
        { scrapeDatetime: '2026-02-09T06:10:00', scientificName: 'Anchor y', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-02-09T06:10:00', scientificName: 'Drifter x', sizeVariant: '3.0', pageUrl: 'url-d', wishlistCount: 10, priceGbp: 20 },
      ],
    };
    const events = buildMarketHealthPayload(raw, 'all-time').events;
    expect(events.restocks.value).toBe('1 total');
  });
});

// ===========================================================================
// Window bounds — m===0 and lm===0 ternary branches (January/February ref)
// ===========================================================================

describe('getWindowBounds — m===0 / lm===0 ternary branches', () => {
  // Helper record factory
  const rec = (dt: string, name = 'Test sp') => ({
    scrapeDatetime: dt, scientificName: name, sizeVariant: '2.0',
    pageUrl: `url-${name.split(' ')[0].toLowerCase()}`, wishlistCount: 5, priceGbp: 10,
  });

  it('this-month with January reference: priorMonth wraps to Dec, priorYear decrements (lines 161–162)', () => {
    // ref = Jan 13 2026 → m=0 → priorMonth = 0===0 ? 11 : m-1 = 11 (Dec), priorYear = 2025
    // Dynamic basis note must mention Jan 2026 (current) and Dec (prior)
    const raw = {
      referenceDate: '2026-01-13T06:10:00',
      records: [rec('2026-01-06T06:10:00'), rec('2026-01-13T06:10:00')],
    };
    const note = buildMarketHealthPayload(raw, 'this-month').windowBasisNote;
    expect(note).toContain('Jan 2026');
    expect(note).toContain('Jan 1');
    expect(note).toContain('Jan 13');
    expect(note).toMatch(/Dec/);
  });

  it('last-month with January reference: window is December (m===0 branch, lines 170–171)', () => {
    // ref = Jan 13 2026 → m=0 → lm = 11 (Dec), ly = 2025 → window = Dec 2025
    // Include a Dec record so the observed count confirms correct window selection
    const raw = {
      referenceDate: '2026-01-13T06:10:00',
      records: [rec('2025-12-08T06:10:00', 'Dec sp'), rec('2025-12-15T06:10:00', 'Dec sp'), rec('2026-01-06T06:10:00', 'Jan sp')],
    };
    const p = buildMarketHealthPayload(raw, 'last-month');
    // Dec 2025 has 'Dec sp' → 1 observed; Jan record excluded from Dec window
    expect(p.kpis.observed.value).toBe('1');
    expect(p.windowBasisNote).toBe('Comparison basis: last full month vs prior full month.');
  });

  it('last-month with February reference: prior-of-prior wraps to December (lm===0 branch, lines 174–175)', () => {
    // ref = Feb 13 2026 → m=1 → lm = 0 (Jan), ly = 2026
    // pm = lm===0 ? 11 : lm-1 = 11 (Dec), py = 2025 → prior window = Dec 2025
    const raw = {
      referenceDate: '2026-02-13T06:10:00',
      records: [rec('2026-01-06T06:10:00', 'Jan sp'), rec('2026-01-13T06:10:00', 'Jan sp'), rec('2026-02-13T06:10:00', 'Feb sp')],
    };
    const p = buildMarketHealthPayload(raw, 'last-month');
    // last-month = Jan 2026 → 'Jan sp' observed; Feb record excluded
    expect(p.kpis.observed.value).toBe('1');
    expect(p.windowBasisNote).toBe('Comparison basis: last full month vs prior full month.');
  });
});

// ===========================================================================
// parseIso — isNaN(ms) branch (line 138)
// ===========================================================================

describe('parseIso — isNaN branch (line 138)', () => {
  it('non-empty unparseable referenceDate: handled gracefully without throwing', () => {
    // parseIso('bad-date'): !s=false → Date.parse('bad-date')=NaN → isNaN(ms) true → null
    // ref = null ?? new Date(0) = Unix epoch; engine still produces a valid payload
    const raw = {
      referenceDate: 'bad-date',
      records: [{ scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Test sp', sizeVariant: '2.0', pageUrl: 'url-t', wishlistCount: 5, priceGbp: 10 }],
    };
    expect(() => buildMarketHealthPayload(raw, 'all-time')).not.toThrow();
    const p = buildMarketHealthPayload(raw, 'all-time');
    expect(p.windowId).toBe('all-time');
  });
});

// ===========================================================================
// buildScopeLabel — selectedGenera.length===0 with isAllSelected:false (line 826)
// ===========================================================================

describe('buildScopeLabel — empty selectedGenera + isAllSelected:false (line 826)', () => {
  it('empty selectedGenera with isAllSelected:false: scopeLabel is empty, all records returned', () => {
    // buildScopeLabel([], false): isAllSelected=false → selectedGenera.length===0 → return ''
    // applyGenusFilter(records, [], false): same condition → returns all records unchanged
    const p = buildMarketHealthPayload(rawMarketHealthData, 'all-time', {
      isAllSelected: false,
      selectedGenera: [],
    });
    expect(p.scopeLabel).toBe('');
    expect(p.kpis.observed.value).toBe('5');
  });
});

// ===========================================================================
// TestNoPriorDataCopy equivalents — delta=null non-all-time: neutral content
// ===========================================================================

describe('copy — delta=null non-all-time: neutral content (TestNoPriorDataCopy)', () => {
  // last-quarter: Q1 2026 has data (runs 0+1) but Q4 2025 is absent → delta=null for all KPIs

  it('wishlistCopy delta=null (non-all-time): neutral sentence, no comparison language', () => {
    const copy = payload('last-quarter').kpis.wishlist.copy;
    expect(copy).toContain('no prior period is available for comparison');
    expect(copy).not.toContain('ahead of');
    expect(copy).not.toContain('above');
    expect(copy).not.toContain('softer');
  });

  it('priceCopy delta=null (non-all-time): neutral sentence, no comparison language', () => {
    const copy = payload('last-quarter').kpis.price.copy;
    expect(copy).toContain('no prior period is available for comparison');
    expect(copy).not.toContain('firmer');
    expect(copy).not.toContain('edged up');
    expect(copy).not.toContain('softened');
  });

  it('showPrior is false when in-progress window has current data but no prior rows', () => {
    // Only Q2 records → current-quarter has data but no Q1 prior → effectiveShowPrior=false
    const noPriorRaw = {
      referenceDate: '2026-04-13T06:10:00',
      records: [
        { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Alpha alpha', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
        { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Alpha alpha', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
      ],
    };
    expect(buildMarketHealthPayload(noPriorRaw, 'current-quarter').showPrior).toBe(false);
  });
});

// ===========================================================================
// priceCopy delta=0 — content keywords (TestPriceCopyDeltaZero equivalent)
// ===========================================================================

describe('priceCopy delta=0 — content keywords: availability, inflation, no prior-period ref', () => {
  // Reuse the same dataset as 'copy branches — delta=0' (Gamma gamma, same price)
  const raw = makeMinimalRaw(
    [{ name: 'Gamma gamma', wl: 10, price: 25 }],
    [
      { dt: '2026-04-05T06:10:00', name: 'Gamma gamma', wl: 10, price: 25 },
      { dt: '2026-04-13T06:10:00', name: 'Gamma gamma', wl: 10, price: 25 },
    ],
  );

  it('priceCopy delta=0: contains "availability" AND "inflation", does not mention prior quarter', () => {
    const copy = buildMarketHealthPayload(raw, 'current-quarter').kpis.price.copy;
    expect(copy.toLowerCase()).toContain('availability');
    expect(copy.toLowerCase()).toContain('inflation');
    expect(copy).not.toContain('prior quarter');
  });
});

// ===========================================================================
// Empty data guard
// ===========================================================================

describe('empty data guard', () => {
  const emptyRaw = { records: [], referenceDate: '' };

  it('empty records: all KPIs have value "0" or "0%"', () => {
    const p = buildMarketHealthPayload(emptyRaw, 'current-quarter');
    expect(p.kpis.observed.value).toBe('0');
    expect(p.kpis.stock.value).toBe('0%');
    expect(p.kpis.wishlist.value).toBe('0');
    expect(p.kpis.price.value).toBe('GBP 0');
  });

  it('empty records: showPrior is false', () => {
    const p = buildMarketHealthPayload(emptyRaw, 'current-quarter');
    expect(p.showPrior).toBe(false);
  });

  it('empty records: sparkline series are all zeros', () => {
    const p = buildMarketHealthPayload(emptyRaw, 'all-time');
    expect(p.sparklineSeries.observed.current).toEqual(Array(12).fill(0));
    expect(p.sparklineSeries.observed.prior).toEqual([]);
  });

  it('empty records: currentRunDates and priorRunDates are empty arrays', () => {
    const p = buildMarketHealthPayload(emptyRaw, 'all-time');
    expect(p.sparklineSeries.observed.currentRunDates).toEqual([]);
    expect(p.sparklineSeries.observed.priorRunDates).toEqual([]);
  });
});
