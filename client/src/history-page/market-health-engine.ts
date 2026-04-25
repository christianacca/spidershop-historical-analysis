/**
 * Client-side Market Health computation engine (Phase 11).
 *
 * Ports all KPI computation from src/website/market_health_dto.py to TypeScript.
 * Receives MarketHealthRawData (variant-level records) and produces
 * MarketHealthPayload objects consumed by Svelte components without modification.
 *
 * Public API — two exports only. All internal functions are unexported.
 */

import type {
  MarketHealthPayload,
  MarketHealthRawData,
  RawRunRecord,
  WindowId,
  KpiCardData,
  SparklineSeries,
  MarketEventsData,
  EventTile,
} from './types.js';

// ---------------------------------------------------------------------------
// Constants — string values must match market_health_dto.py exactly
// ---------------------------------------------------------------------------

const ALL_WINDOW_IDS: WindowId[] = [
  'this-month',
  'last-month',
  'current-quarter',
  'last-quarter',
  'this-year',
  'last-year',
  'all-time',
];

const WINDOW_LABELS: Record<WindowId, string> = {
  'this-month': 'This month',
  'last-month': 'Last month',
  'current-quarter': 'Current quarter',
  'last-quarter': 'Last quarter',
  'this-year': 'This year',
  'last-year': 'Last year',
  'all-time': 'All time',
};

const PRIOR_LABELS: Record<WindowId, string> = {
  'this-month': 'the same point last month',
  'last-month': 'the prior full month',
  'current-quarter': 'the same point last quarter',
  'last-quarter': 'the prior full quarter',
  'this-year': 'the same point last year',
  'last-year': 'the prior full year',
  'all-time': '',
};

const PRIOR_DELTA_LABELS: Record<WindowId, string> = {
  'this-month': 'prior month MTD',
  'last-month': 'prior full month',
  'current-quarter': 'prior quarter QTD',
  'last-quarter': 'prior full quarter',
  'this-year': 'prior year YTD',
  'last-year': 'prior full year',
  'all-time': '',
};

// In-progress windows use dynamic notes from buildInprogressBasisNotes; static entries are unused.
const SPARKLINE_BASIS_NOTES: Record<WindowId, string> = {
  'this-month': '',
  'last-month':
    'Compare within a row. Solid shows last month; dashed shows the prior full month.',
  'current-quarter': '',
  'last-quarter':
    'Compare within a row. Solid shows last quarter; dashed shows the prior full quarter.',
  'this-year': '',
  'last-year':
    'Compare within a row. Solid shows last year; dashed shows the prior full year.',
  'all-time':
    'All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale.',
};

const WINDOW_BASIS_NOTES: Record<WindowId, string> = {
  'this-month': '',
  'last-month': 'Comparison basis: last full month vs prior full month.',
  'current-quarter': '',
  'last-quarter': 'Comparison basis: last full quarter vs prior full quarter.',
  'this-year': '',
  'last-year': 'Comparison basis: last full year vs year before.',
  'all-time': 'Comparison basis: structural context only, with no prior-period delta.',
};

const EVENTS_TITLES: Record<WindowId, string> = {
  'this-month': 'Run-to-run market events this month',
  'last-month': 'Run-to-run market events last month',
  'current-quarter': 'Run-to-run market events this quarter',
  'last-quarter': 'Run-to-run market events last quarter',
  'this-year': 'Run-to-run market events this year',
  'last-year': 'Run-to-run market events last year',
  'all-time': 'Market events across all time',
};

const EVENTS_SUBTITLES: Record<WindowId, string> = {
  'this-month': 'This month event totals against the same point last month.',
  'last-month': 'Last month event totals against the prior full month.',
  'current-quarter':
    'Current-quarter event totals against the same point last quarter.',
  'last-quarter': 'Last-quarter event totals against the prior full quarter.',
  'this-year': 'Year-to-date event totals against the same point last year.',
  'last-year': 'Last-year event totals against the prior full year.',
  'all-time': 'All-time event totals as structural context only.',
};

const INPROGRESS_WINDOW_IDS: ReadonlySet<WindowId> = new Set([
  'this-month',
  'current-quarter',
  'this-year',
]);

// Abbreviated month names — matches Python's strftime('%b')
const MONTH_ABBREVS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------

function fmtDate(dt: Date): string {
  return `${MONTH_ABBREVS[dt.getMonth()]} ${dt.getDate()}`;
}

function daysInMonth(month: number, year: number): number {
  // month is 0-based (JS Date convention). new Date(year, month+1, 0) = last day.
  return new Date(year, month + 1, 0).getDate();
}

function quarterStart(dt: Date): Date {
  const month = Math.floor(dt.getMonth() / 3) * 3;
  return new Date(dt.getFullYear(), month, 1, 0, 0, 0, 0);
}

function parseIso(s: string): Date | null {
  if (!s) return null;
  const ms = Date.parse(s);
  return isNaN(ms) ? null : new Date(ms);
}

// ---------------------------------------------------------------------------
// Window bounds
// ---------------------------------------------------------------------------

interface WindowBounds {
  winStart: Date;
  winEnd: Date;
  priorStart: Date | null;
  priorEnd: Date | null;
  showPrior: boolean;
}

function getWindowBounds(windowId: WindowId, ref: Date): WindowBounds {
  const y = ref.getFullYear();
  const m = ref.getMonth(); // 0-based
  const d = ref.getDate();

  if (windowId === 'this-month') {
    const winStart = new Date(y, m, 1, 0, 0, 0, 0);
    const winEnd = ref;
    const priorMonth = m === 0 ? 11 : m - 1;
    const priorYear = m === 0 ? y - 1 : y;
    const priorStart = new Date(priorYear, priorMonth, 1, 0, 0, 0, 0);
    const priorDay = Math.min(d, daysInMonth(priorMonth, priorYear));
    const priorEnd = new Date(priorYear, priorMonth, priorDay, 23, 59, 59, 999);
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  if (windowId === 'last-month') {
    const lm = m === 0 ? 11 : m - 1;
    const ly = m === 0 ? y - 1 : y;
    const winStart = new Date(ly, lm, 1, 0, 0, 0, 0);
    const winEnd = new Date(ly, lm, daysInMonth(lm, ly), 23, 59, 59, 999);
    const pm = lm === 0 ? 11 : lm - 1;
    const py = lm === 0 ? ly - 1 : ly;
    const priorStart = new Date(py, pm, 1, 0, 0, 0, 0);
    const priorEnd = new Date(py, pm, daysInMonth(pm, py), 23, 59, 59, 999);
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  if (windowId === 'current-quarter') {
    const qs = quarterStart(ref);
    const winStart = qs;
    const winEnd = ref;
    // Prior quarter start: quarter containing (qs - 1 day)
    const dayBeforeQs = new Date(qs.getTime() - 24 * 60 * 60 * 1000);
    const prevQs = quarterStart(dayBeforeQs);
    const dayOffset = Math.floor((ref.getTime() - qs.getTime()) / (24 * 60 * 60 * 1000));
    const priorStart = prevQs;
    const priorEndCandidate = new Date(prevQs.getTime() + dayOffset * 24 * 60 * 60 * 1000);
    const priorEnd = new Date(
      priorEndCandidate.getFullYear(),
      priorEndCandidate.getMonth(),
      priorEndCandidate.getDate(),
      23, 59, 59, 999,
    );
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  if (windowId === 'last-quarter') {
    const qs = quarterStart(ref);
    const dayBeforeQs = new Date(qs.getTime() - 24 * 60 * 60 * 1000);
    const prevQs = quarterStart(dayBeforeQs);
    const winStart = prevQs;
    const winEnd = new Date(qs.getTime() - 1); // 1 ms before quarter start
    const dayBeforePrevQs = new Date(prevQs.getTime() - 24 * 60 * 60 * 1000);
    const priorQs = quarterStart(dayBeforePrevQs);
    const priorStart = priorQs;
    const priorEnd = new Date(prevQs.getTime() - 1);
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  if (windowId === 'this-year') {
    const winStart = new Date(y, 0, 1, 0, 0, 0, 0);
    const winEnd = ref;
    const priorStart = new Date(y - 1, 0, 1, 0, 0, 0, 0);
    const dayOfYear = Math.floor((ref.getTime() - winStart.getTime()) / (24 * 60 * 60 * 1000));
    const priorEndCandidate = new Date(priorStart.getTime() + dayOfYear * 24 * 60 * 60 * 1000);
    const priorEnd = new Date(
      priorEndCandidate.getFullYear(),
      priorEndCandidate.getMonth(),
      priorEndCandidate.getDate(),
      23, 59, 59, 999,
    );
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  if (windowId === 'last-year') {
    const winStart = new Date(y - 1, 0, 1, 0, 0, 0, 0);
    const winEnd = new Date(y - 1, 11, 31, 23, 59, 59, 999);
    const priorStart = new Date(y - 2, 0, 1, 0, 0, 0, 0);
    const priorEnd = new Date(y - 2, 11, 31, 23, 59, 59, 999);
    return { winStart, winEnd, priorStart, priorEnd, showPrior: true };
  }

  // all-time: sentinel start, no prior
  const sentinel = new Date(1970, 0, 1, 0, 0, 0, 0);
  return { winStart: sentinel, winEnd: ref, priorStart: null, priorEnd: null, showPrior: false };
}

// ---------------------------------------------------------------------------
// Row filtering helpers
// ---------------------------------------------------------------------------

function filterToWindow(records: RawRunRecord[], winStart: Date, winEnd: Date): RawRunRecord[] {
  return records.filter(r => {
    const dt = parseIso(r.scrapeDatetime);
    return dt !== null && dt >= winStart && dt <= winEnd;
  });
}

function applyGenusFilter(
  records: RawRunRecord[],
  selectedGenera: string[],
  isAllSelected: boolean,
): RawRunRecord[] {
  if (isAllSelected || selectedGenera.length === 0) return records;
  const generaSet = new Set(selectedGenera);
  return records.filter(r => {
    const genus = r.scientificName.split(' ')[0];
    return generaSet.has(genus);
  });
}

// ---------------------------------------------------------------------------
// Run-level helpers
// ---------------------------------------------------------------------------

function getSortedRuns(records: RawRunRecord[]): string[] {
  const runs = new Set(records.map(r => r.scrapeDatetime));
  return [...runs].sort();
}

function speciesInRun(records: RawRunRecord[], runDt: string): Set<string> {
  const result = new Set<string>();
  for (const r of records) {
    if (r.scrapeDatetime === runDt) result.add(r.scientificName);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Median utility
// ---------------------------------------------------------------------------

function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 1) return sorted[mid];
  return (sorted[mid - 1] + sorted[mid]) / 2;
}

// ---------------------------------------------------------------------------
// KPI metric computation
// ---------------------------------------------------------------------------

function getLatestRun(records: RawRunRecord[]): string {
  return records.reduce((max, r) => (r.scrapeDatetime > max ? r.scrapeDatetime : max), '');
}

function computeMedianBySpecies(
  records: RawRunRecord[],
  getValue: (r: RawRunRecord) => number,
): number {
  if (records.length === 0) return 0;
  const latestRun = getLatestRun(records);
  const latestRecords = records.filter(r => r.scrapeDatetime === latestRun);
  const bySpecies = new Map<string, number>();
  for (const r of latestRecords) {
    bySpecies.set(r.scientificName, Math.max(bySpecies.get(r.scientificName) ?? 0, getValue(r)));
  }
  return median([...bySpecies.values()]);
}

function computeObserved(records: RawRunRecord[]): number {
  return new Set(records.map(r => r.scientificName)).size;
}

function computeStockRate(records: RawRunRecord[]): number {
  if (records.length === 0) return 0;
  const allSpecies = new Set(records.map(r => r.scientificName));
  const latestRun = getLatestRun(records);
  const speciesAtLatest = speciesInRun(records, latestRun);
  return Math.round((speciesAtLatest.size / allSpecies.size) * 100);
}

function computeMedianWishlist(records: RawRunRecord[]): number {
  return Math.round(computeMedianBySpecies(records, r => r.wishlistCount));
}

function computeMedianPrice(records: RawRunRecord[]): number {
  return computeMedianBySpecies(records, r => r.priceGbp);
}

// ---------------------------------------------------------------------------
// Sparkline series computation
// ---------------------------------------------------------------------------

/**
 * For in-progress windows, return the end of the *full* prior period rather than
 * the matched-span end.  This lets the dashed prior line span the entire prior
 * period for context while click-comparison dates still come from the matched span.
 *
 * Examples (ref = 22 Apr 2026):
 *   current-quarter → full Q1 end = 31 Mar 2026 23:59:59 (= qs - 1 ms)
 *   this-month      → full March end = 31 Mar 2026 23:59:59
 *   this-year       → full 2025 end  = 31 Dec 2025 23:59:59
 */
function computePriorFullEnd(windowId: WindowId, winStart: Date): Date {
  if (windowId === 'current-quarter') {
    // winStart = start of current quarter → 1 ms before it = end of last quarter
    return new Date(winStart.getTime() - 1);
  }
  if (windowId === 'this-month') {
    // winStart = 1st of current month → prior month = month before
    const priorMonth = winStart.getMonth() === 0 ? 11 : winStart.getMonth() - 1;
    const priorYear  = winStart.getMonth() === 0 ? winStart.getFullYear() - 1 : winStart.getFullYear();
    return new Date(priorYear, priorMonth, daysInMonth(priorMonth, priorYear), 23, 59, 59, 999);
  }
  if (windowId === 'this-year') {
    // winStart = 1 Jan of current year → full prior year = Dec 31 last year
    return new Date(winStart.getFullYear() - 1, 11, 31, 23, 59, 59, 999);
  }
  // Fallback (should not be reached for in-progress windows)
  return winStart;
}

function resampleTo12(values: number[]): number[] {
  const n = values.length;
  if (n === 0) return [];
  if (n >= 12) {
    const indices = Array.from({ length: 12 }, (_, i) => Math.round((i * (n - 1)) / 11));
    return indices.map(idx => values[idx]);
  }
  // n < 12: return as-is — the sparkline renders a truncated line for in-progress windows
  return values;
}

function resampleDatesTo12(dates: string[]): string[] {
  const n = dates.length;
  if (n === 0) return [];
  if (n >= 12) {
    const indices = Array.from({ length: 12 }, (_, i) => Math.round((i * (n - 1)) / 11));
    return indices.map(idx => dates[idx]);
  }
  // n < 12: return as-is — truncated to match actual run count
  return dates;
}

function buildSparklineDatesForWindow(records: RawRunRecord[]): string[] {
  const runs = getSortedRuns(records);
  return resampleDatesTo12(runs);
}

function valueAtRun(records: RawRunRecord[], runDt: string, metric: string): number {
  const runRecords = records.filter(r => r.scrapeDatetime === runDt);
  if (runRecords.length === 0) return 0;

  if (metric === 'observed') {
    return new Set(runRecords.map(r => r.scientificName)).size;
  }
  if (metric === 'stock') {
    const allUpTo = new Set(
      records.filter(r => r.scrapeDatetime <= runDt).map(r => r.scientificName),
    );
    const inRun = new Set(runRecords.map(r => r.scientificName));
    return Math.round((inRun.size / allUpTo.size) * 100);
  }
  if (metric === 'wishlist') {
    const bySpecies = new Map<string, number>();
    for (const r of runRecords) {
      bySpecies.set(r.scientificName, Math.max(bySpecies.get(r.scientificName) ?? 0, r.wishlistCount));
    }
    return Math.round(median([...bySpecies.values()]));
  }
  if (metric === 'price') {
    const bySpecies = new Map<string, number>();
    for (const r of runRecords) {
      bySpecies.set(r.scientificName, Math.max(bySpecies.get(r.scientificName) ?? 0, r.priceGbp));
    }
    return Math.round(median([...bySpecies.values()]));
  }
  return 0;
}

function buildSparklineForMetric(records: RawRunRecord[], metric: string): number[] {
  const runs = getSortedRuns(records);
  if (runs.length === 0) return [];
  const rawValues = runs.map(runDt => valueAtRun(records, runDt, metric));
  return resampleTo12(rawValues);
}

// ---------------------------------------------------------------------------
// Size-transition detection
// ---------------------------------------------------------------------------

function isSizeTransition(
  species: string,
  runs: string[],
  prevRunIdx: number,
  currRunIdx: number,
  records: RawRunRecord[],
  maxGap = 3,
): boolean {
  if (currRunIdx - prevRunIdx > maxGap) return false;
  const prevRows = records.filter(
    r => r.scrapeDatetime === runs[prevRunIdx] && r.scientificName === species,
  );
  const currRows = records.filter(
    r => r.scrapeDatetime === runs[currRunIdx] && r.scientificName === species,
  );
  const prevUrls = new Set(prevRows.map(r => r.pageUrl));
  const currUrls = new Set(currRows.map(r => r.pageUrl));

  for (const url of prevUrls) {
    if (!currUrls.has(url)) continue;
    const prevSizes = new Set(prevRows.filter(r => r.pageUrl === url).map(r => r.sizeVariant));
    const currSizes = new Set(currRows.filter(r => r.pageUrl === url).map(r => r.sizeVariant));
    // Different sizes at the same URL = size transition
    if ([...prevSizes].some(s => !currSizes.has(s)) || [...currSizes].some(s => !prevSizes.has(s))) {
      return true;
    }
  }
  return false;
}

function findLastSeenIdx(
  species: string,
  runs: string[],
  beforeIdx: number,
  records: RawRunRecord[],
): number | null {
  for (let i = beforeIdx; i >= 0; i--) {
    if (speciesInRun(records, runs[i]).has(species)) return i;
  }
  return null;
}

function findNextSeenIdx(
  species: string,
  runs: string[],
  afterIdx: number,
  records: RawRunRecord[],
): number | null {
  for (let i = afterIdx; i < runs.length; i++) {
    if (speciesInRun(records, runs[i]).has(species)) return i;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Events computation
// ---------------------------------------------------------------------------

function eventsCopyNewListings(count: number, isAllTime: boolean): string {
  if (isAllTime) return 'Use this as background volume, not as a directional comparison.';
  if (count >= 5) {
    return (
      'Introductions are materially ahead of the matched point last period,'
      + ' which supports the breadth expansion visible in the chart.'
    );
  }
  return (
    'Fresh introductions are only slightly ahead, so the catalog is still'
    + ' expanding but not surging.'
  );
}

function eventsCopyDropped(isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'All-time churn is useful for scale, but weak for saying what changed recently.'
    );
  }
  return (
    'Churn also rose, but the balance still favors broader assortment rather than retreat.'
  );
}

function eventsCopyRestocks(count: number, isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'This shows how much movement exists in the market overall, not whether it is improving now.'
    );
  }
  if (count === 0) {
    return (
      'No OUT-to-IN restocks occurred this period. If the in-stock rate is'
      + ' also falling, supply may have stalled rather than just tightened.'
    );
  }
  return (
    'Movement is active; stock is not simply frozen, even though the in-stock'
    + ' rate may be weaker than last period.'
  );
}

function eventsCopyOosFlips(isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'Use this as structural supply-friction context, not as a directional'
      + ' signal about what changed recently.'
    );
  }
  return (
    'More listings are moving from IN to OUT than at the same point last period,'
    + ' which helps explain why availability may be softer.'
  );
}

function computeEvents(
  records: RawRunRecord[],
  windowId: WindowId,
  deltaLabel: string,
): MarketEventsData {
  const runs = getSortedRuns(records);
  const isAllTime = windowId === 'all-time';

  let newListingsCount = 0;
  let droppedListingsCount = 0;
  let restockCount = 0;
  let oosFlipCount = 0;

  if (runs.length >= 2) {
    for (let i = 1; i < runs.length; i++) {
      const prevSpecies = speciesInRun(records, runs[i - 1]);
      const currSpecies = speciesInRun(records, runs[i]);

      const appeared = [...currSpecies].filter(s => !prevSpecies.has(s));
      const disappeared = [...prevSpecies].filter(s => !currSpecies.has(s));

      for (const sp of appeared) {
        const lastSeenIdx = findLastSeenIdx(sp, runs, i - 1, records);
        if (lastSeenIdx === null) {
          newListingsCount++;
        } else if (isSizeTransition(sp, runs, lastSeenIdx, i, records)) {
          // size transition — not a restock
        } else {
          restockCount++;
        }
      }

      for (const sp of disappeared) {
        const nextSeenIdx = findNextSeenIdx(sp, runs, i, records);
        if (nextSeenIdx === null) {
          droppedListingsCount++;
          oosFlipCount++;
        } else if (isSizeTransition(sp, runs, i - 1, nextSeenIdx, records)) {
          // size transition — not an OOS flip
        } else {
          oosFlipCount++;
        }
      }
    }
  }

  const eventValue = (count: number, prefix: string): string =>
    isAllTime ? `${count} total` : `${prefix}${count} vs ${deltaLabel}`;

  return {
    title: EVENTS_TITLES[windowId],
    subtitle: EVENTS_SUBTITLES[windowId],
    newListings: {
      label: 'Listings added',
      value: eventValue(newListingsCount, '+'),
      copy: eventsCopyNewListings(newListingsCount, isAllTime),
    },
    droppedListings: {
      label: 'Listings removed',
      value: eventValue(droppedListingsCount, ''),
      copy: eventsCopyDropped(isAllTime),
    },
    restocks: {
      label: 'OUT \u2192 IN restocks',
      value: eventValue(restockCount, ''),
      copy: eventsCopyRestocks(restockCount, isAllTime),
    },
    oosFlips: {
      label: 'IN \u2192 OUT stockouts',
      value: eventValue(oosFlipCount, '+'),
      copy: eventsCopyOosFlips(isAllTime),
    },
  };
}

// ---------------------------------------------------------------------------
// Copy selection
// ---------------------------------------------------------------------------

function observedCopy(delta: number | null, priorLabel: string, isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'All-time view is best read as structural context: the catalog is broad'
      + ' enough to support opportunity hunting, but this lens is not about recent acceleration.'
    );
  }
  if (delta === null) {
    return (
      'Breadth within the selected window gives a picture of available assortment,'
      + ' but no prior period is available for comparison.'
    );
  }
  if (delta >= 3) {
    return (
      `Breadth is ahead of ${priorLabel}, so the market still looks alive on`
      + ' assortment even while actual stock is getting tighter.'
    );
  }
  if (delta >= 0) {
    return (
      `Breadth is only slightly ahead of ${priorLabel}, so the catalog still`
      + ' looks broad without signalling a step-change in assortment.'
    );
  }
  return (
    `Fewer species are being seen in-stock than at ${priorLabel}, which may`
    + ' suggest some genera are becoming harder to source.'
  );
}

function stockCopy(
  delta: number | null,
  valuePct: number,
  priorLabel: string,
  isAllTime: boolean,
): string {
  if (isAllTime) {
    return (
      'All-time availability smooths out short-term swings, so it is useful for'
      + ' background context rather than telling you what changed recently.'
    );
  }
  if (delta === null) {
    return `Availability is at ${valuePct}% for the selected window.`;
  }
  if (delta <= -7) {
    return (
      `${valuePct}% of listings are available now. That is ${Math.abs(delta)}`
      + ` percentage points lower than ${priorLabel}, so availability is slipping`
      + ' even while the species count remains broad.'
    );
  }
  if (delta <= -1) {
    return (
      `Availability is a touch weaker than ${priorLabel}. That reads more like`
      + ' a near-term tightening than a structural collapse.'
    );
  }
  if (delta === 0) {
    return `The in-stock rate is holding steady vs ${priorLabel}.`;
  }
  return (
    `Availability is firmer than ${priorLabel}, which suggests supply is keeping`
    + ' pace with demand.'
  );
}

function wishlistCopy(delta: number | null, priorLabel: string, isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'All-time wishlist levels show the long-run demand floor for your selected'
      + ' genera, not whether interest just strengthened this month or quarter.'
    );
  }
  if (delta === null) {
    return (
      'Wishlist interest is visible for the selected window,'
      + ' but no prior period is available for comparison.'
    );
  }
  if (delta >= 4) {
    return (
      `Median wishlist counts are ahead of ${priorLabel}, reinforcing the idea`
      + ' that interest is improving while availability slips.'
    );
  }
  if (delta >= 1) {
    return (
      `Median wishlist counts are modestly above ${priorLabel}, which suggests`
      + ' demand is holding without obviously overheating.'
    );
  }
  if (delta === 0) {
    return `Median wishlist demand is stable vs ${priorLabel}.`;
  }
  return `Demand looks softer than ${priorLabel}.`;
}

function priceCopy(delta: number | null, priorLabel: string, isAllTime: boolean): string {
  if (isAllTime) {
    return (
      'All-time price mainly describes the market baseline. It is less useful than'
      + ' shorter windows when you are deciding whether recent conditions have shifted.'
    );
  }
  if (delta === null) {
    return (
      'Price data is available for the selected window,'
      + ' but no prior period is available for comparison.'
    );
  }
  if (delta >= 2) {
    return (
      `Prices are somewhat firmer than ${priorLabel}, but the move is still`
      + ' smaller than the availability shift. Supply pressure remains the more important signal.'
    );
  }
  if (delta === 1) {
    return (
      `Prices edged up a little relative to ${priorLabel}, which fits a market`
      + ' that is tightening gradually rather than repricing sharply.'
    );
  }
  if (delta === 0) {
    return (
      'Price is steady, so the main movement appears to be availability rather than inflation.'
    );
  }
  return (
    `Prices have softened vs ${priorLabel}, which runs counter to the tighter-supply read.`
  );
}

// ---------------------------------------------------------------------------
// Delta formatting helpers
// ---------------------------------------------------------------------------

function formatDelta(
  delta: number | null,
  isAllTime: boolean,
  deltaLabel: string,
  formatValue: (delta: number) => string,
  showPlusForZero: boolean = false,
): [string, KpiCardData['deltaClass']] {
  if (isAllTime || delta === null) return ['No prior comparison', 'flat'];
  const sign = (delta > 0 || (delta === 0 && showPlusForZero)) ? '+' : '';
  const cls: KpiCardData['deltaClass'] = delta === 0 ? 'flat' : delta < 0 ? 'down' : '';
  return [`${sign}${formatValue(delta)} vs ${deltaLabel}`, cls];
}

function formatObservedDelta(
  delta: number | null,
  isAllTime: boolean,
  deltaLabel: string,
): [string, KpiCardData['deltaClass']] {
  return formatDelta(delta, isAllTime, deltaLabel, d => String(d), true);
}

function formatStockDelta(
  delta: number | null,
  isAllTime: boolean,
  deltaLabel: string,
): [string, KpiCardData['deltaClass']] {
  return formatDelta(delta, isAllTime, deltaLabel, d => `${d} pts`, false);
}

function formatWishlistDelta(
  delta: number | null,
  isAllTime: boolean,
  deltaLabel: string,
): [string, KpiCardData['deltaClass']] {
  return formatDelta(delta, isAllTime, deltaLabel, d => String(d), true);
}

function formatPriceDelta(
  delta: number | null,
  isAllTime: boolean,
  deltaLabel: string,
): [string, KpiCardData['deltaClass']] {
  return formatDelta(delta, isAllTime, deltaLabel, d => `GBP ${d}`, false);
}

// ---------------------------------------------------------------------------
// Basis notes for in-progress windows
// ---------------------------------------------------------------------------

function buildInprogressBasisNotes(
  windowId: WindowId,
  winStart: Date,
  winEnd: Date,
  priorStart: Date,
  priorEnd: Date,
): [string, string] {
  const ws = fmtDate(winStart);
  const we = fmtDate(winEnd);
  const ps = fmtDate(priorStart);
  const pe = fmtDate(priorEnd);

  if (windowId === 'this-month') {
    const periodLabel = `${MONTH_ABBREVS[winStart.getMonth()]} ${winStart.getFullYear()}`;
    const windowNote =
      `Month in progress (${periodLabel}) — comparing ${ws} \u2013 ${we}`
      + ` against the same span last month (${ps} \u2013 ${pe}).`;
    const sparklineNote =
      `Compare within a row. Solid shows ${periodLabel} to date (${ws} \u2013 ${we});`
      + ` dashed shows the same span last month (${ps} \u2013 ${pe}).`;
    return [windowNote, sparklineNote];
  }

  if (windowId === 'current-quarter') {
    const qNum = Math.floor(winStart.getMonth() / 3) + 1;
    const qLabel = `Q${qNum} ${winStart.getFullYear()}`;
    const pqNum = Math.floor(priorStart.getMonth() / 3) + 1;
    const pqLabel = `Q${pqNum} ${priorStart.getFullYear()}`;
    const windowNote =
      `Quarter in progress (${qLabel}) — comparing ${ws} \u2013 ${we}`
      + ` against the same span into ${pqLabel} (${ps} \u2013 ${pe}).`;
    const sparklineNote =
      `Compare within a row. Solid shows ${qLabel} to date (${ws} \u2013 ${we});`
      + ` dashed shows the same span into ${pqLabel} (${ps} \u2013 ${pe}).`;
    return [windowNote, sparklineNote];
  }

  // this-year
  const yearLabel = String(winStart.getFullYear());
  const priorYearLabel = String(priorStart.getFullYear());
  const windowNote =
    `Year in progress (${yearLabel}) — comparing ${ws} \u2013 ${we}`
    + ` against the same span in ${priorYearLabel}.`;
  const sparklineNote =
    `Compare within a row. Solid shows ${yearLabel} to date (${ws} \u2013 ${we});`
    + ` dashed shows the same span in ${priorYearLabel}.`;
  return [windowNote, sparklineNote];
}

// ---------------------------------------------------------------------------
// Scope label
// ---------------------------------------------------------------------------

function buildScopeLabel(selectedGenera: string[], isAllSelected: boolean): string {
  if (isAllSelected) return '';
  if (selectedGenera.length === 0) return '';
  if (selectedGenera.length <= 3) {
    if (selectedGenera.length === 1) return selectedGenera[0];
    return selectedGenera.slice(0, -1).join(', ') + ` and ${selectedGenera[selectedGenera.length - 1]}`;
  }
  return `your ${selectedGenera.length} selected genera`;
}

// ---------------------------------------------------------------------------
// Empty payload helpers
// ---------------------------------------------------------------------------

function emptyKpi(id: KpiCardData['id'], title: string, value = '0'): KpiCardData {
  return { id, title, value, delta: 'No prior comparison', deltaClass: 'flat', copy: '' };
}

function emptySparklineSeries(): SparklineSeries {
  return { current: [], prior: [], currentRunDates: [], priorRunDates: [] };
}

// ---------------------------------------------------------------------------
// Main payload builder
// ---------------------------------------------------------------------------

/**
 * Build a MarketHealthPayload for the given window from raw variant-level records.
 *
 * @param rawData  - Raw records injected by Python as window.marketHealthRawData.
 * @param windowId - One of the seven WindowId values.
 * @param options  - Genus filter options. Defaults to all-mode.
 */
export function buildMarketHealthPayload(
  rawData: MarketHealthRawData,
  windowId: WindowId,
  options?: { selectedGenera?: string[]; isAllSelected?: boolean },
): MarketHealthPayload {
  const selectedGenera = options?.selectedGenera ?? [];
  const isAllSelected = options?.isAllSelected ?? true;

  // Parse reference date from the data (not new Date())
  const ref = parseIso(rawData.referenceDate) ?? new Date(0);

  const { winStart, winEnd, priorStart, priorEnd, showPrior } = getWindowBounds(windowId, ref);
  const isAllTime = windowId === 'all-time';

  // Filter records to the current window
  let winRecords = filterToWindow(rawData.records, winStart, winEnd);
  winRecords = applyGenusFilter(winRecords, selectedGenera, isAllSelected);

  // Filter records to the prior window (if applicable)
  let priorRecords: RawRunRecord[] = [];
  if (showPrior && priorStart !== null && priorEnd !== null) {
    priorRecords = filterToWindow(rawData.records, priorStart, priorEnd);
    priorRecords = applyGenusFilter(priorRecords, selectedGenera, isAllSelected);
  }

  // For in-progress windows, compute a second prior record set that spans the
  // *full* prior period (e.g. all of Q1, not just the matched span Jan 1–Jan 22).
  // This is used for the sparkline visual so the dashed line shows the full prior
  // period as context.  priorRecords (matched span) is still used for KPI deltas
  // and priorRunDates (click-comparison dates).
  let priorFullRecords: RawRunRecord[] = priorRecords;
  if (INPROGRESS_WINDOW_IDS.has(windowId) && priorStart !== null && showPrior) {
    const priorFullEnd = computePriorFullEnd(windowId, winStart);
    let fullPrior = filterToWindow(rawData.records, priorStart, priorFullEnd);
    fullPrior = applyGenusFilter(fullPrior, selectedGenera, isAllSelected);
    priorFullRecords = fullPrior;
  }

  const winRuns = getSortedRuns(winRecords);
  const hasPriorData = getSortedRuns(priorRecords).length >= 1;
  const effectiveShowPrior = showPrior && hasPriorData;

  // Edge case: no data in current window — return safe empty payload
  if (winRuns.length === 0) {
    let windowBasisNote = WINDOW_BASIS_NOTES[windowId] ?? '';
    let sparklineBasisNote = SPARKLINE_BASIS_NOTES[windowId] ?? '';
    if (
      INPROGRESS_WINDOW_IDS.has(windowId) &&
      priorStart !== null &&
      priorEnd !== null
    ) {
      [windowBasisNote, sparklineBasisNote] = buildInprogressBasisNotes(
        windowId, winStart, winEnd, priorStart, priorEnd,
      );
    }
    const deltaLabel = PRIOR_DELTA_LABELS[windowId];
    return {
      windowId,
      windowLabel: WINDOW_LABELS[windowId],
      windowBasisNote,
      showPrior: false,
      sparklineBasisNote,
      isAllSelected,
      generaCount: isAllSelected ? 0 : selectedGenera.length,
      scopeLabel: buildScopeLabel(selectedGenera, isAllSelected),
      kpis: {
        observed: emptyKpi('observed', 'Observed species'),
        stock: emptyKpi('stock', 'In-stock rate', '0%'),
        wishlist: emptyKpi('wishlist', 'Median wishlist'),
        price: emptyKpi('price', 'Median price', 'GBP 0'),
      },
      sparklineSeries: {
        observed: emptySparklineSeries(),
        stock: emptySparklineSeries(),
        wishlist: emptySparklineSeries(),
        price: emptySparklineSeries(),
      },
      events: computeEvents([], windowId, deltaLabel),
    };
  }

  // Compute current-period metrics
  const currObserved = computeObserved(winRecords);
  const currStock = computeStockRate(winRecords);
  const currWishlist = computeMedianWishlist(winRecords);
  const currPrice = computeMedianPrice(winRecords);

  // Compute prior metrics and deltas
  let dObserved: number | null = null;
  let dStock: number | null = null;
  let dWishlist: number | null = null;
  let dPrice: number | null = null;

  if (effectiveShowPrior) {
    const priorObserved = computeObserved(priorRecords);
    const priorStock = computeStockRate(priorRecords);
    const priorWishlist = computeMedianWishlist(priorRecords);
    const priorPrice = computeMedianPrice(priorRecords);

    dObserved = currObserved - priorObserved;
    dStock = currStock - priorStock;
    dWishlist = currWishlist - priorWishlist;
    dPrice = Math.round(currPrice - priorPrice);
  }

  const priorLabel = PRIOR_LABELS[windowId];
  const deltaLabel = PRIOR_DELTA_LABELS[windowId];

  const [obsDeltaText, obsDeltaCls] = formatObservedDelta(dObserved, isAllTime, deltaLabel);
  const [stockDeltaText, stockDeltaCls] = formatStockDelta(dStock, isAllTime, deltaLabel);
  const [wlDeltaText, wlDeltaCls] = formatWishlistDelta(dWishlist, isAllTime, deltaLabel);
  const [priceDeltaText, priceDeltaCls] = formatPriceDelta(dPrice, isAllTime, deltaLabel);

  // Sparklines — use priorFullRecords for the visual line (full prior period for
  // in-progress windows); use priorRunDates from priorRecords (matched span) so
  // clicking run N shows the correctly matched comparison date.
  const observedCurrent = buildSparklineForMetric(winRecords, 'observed');
  const stockCurrent = buildSparklineForMetric(winRecords, 'stock');
  const wishlistCurrent = buildSparklineForMetric(winRecords, 'wishlist');
  const priceCurrent = buildSparklineForMetric(winRecords, 'price');

  const observedPrior  = effectiveShowPrior ? buildSparklineForMetric(priorFullRecords, 'observed') : [];
  const stockPrior     = effectiveShowPrior ? buildSparklineForMetric(priorFullRecords, 'stock')    : [];
  const wishlistPrior  = effectiveShowPrior ? buildSparklineForMetric(priorFullRecords, 'wishlist') : [];
  const pricePrior     = effectiveShowPrior ? buildSparklineForMetric(priorFullRecords, 'price')    : [];

  // Sparkline run dates — all four series share the same window runs, so compute once
  const currentRunDates = buildSparklineDatesForWindow(winRecords);
  const priorRunDates   = effectiveShowPrior ? buildSparklineDatesForWindow(priorRecords) : [];

  // Events
  const events = computeEvents(winRecords, windowId, deltaLabel);

  // Scope label
  const scopeLabel = buildScopeLabel(selectedGenera, isAllSelected);

  // Basis notes
  let windowBasisNote: string;
  let sparklineBasisNote: string;
  if (INPROGRESS_WINDOW_IDS.has(windowId) && priorStart !== null && priorEnd !== null) {
    [windowBasisNote, sparklineBasisNote] = buildInprogressBasisNotes(
      windowId, winStart, winEnd, priorStart, priorEnd,
    );
  } else {
    windowBasisNote = WINDOW_BASIS_NOTES[windowId];
    sparklineBasisNote = SPARKLINE_BASIS_NOTES[windowId];
  }

  // showPrior: true only when effective prior exists AND current window has ≥ 2 runs
  const finalShowPrior = effectiveShowPrior && winRuns.length >= 2;

  return {
    windowId,
    windowLabel: WINDOW_LABELS[windowId],
    windowBasisNote,
    showPrior: finalShowPrior,
    sparklineBasisNote,
    isAllSelected,
    generaCount: isAllSelected ? 0 : selectedGenera.length,
    scopeLabel,
    kpis: {
      observed: {
        id: 'observed',
        title: 'Observed species',
        value: String(currObserved),
        delta: obsDeltaText,
        deltaClass: obsDeltaCls,
        copy: observedCopy(dObserved, priorLabel, isAllTime),
      },
      stock: {
        id: 'stock',
        title: 'In-stock rate',
        value: `${currStock}%`,
        delta: stockDeltaText,
        deltaClass: stockDeltaCls,
        copy: stockCopy(dStock, currStock, priorLabel, isAllTime),
      },
      wishlist: {
        id: 'wishlist',
        title: 'Median wishlist',
        value: String(currWishlist),
        delta: wlDeltaText,
        deltaClass: wlDeltaCls,
        copy: wishlistCopy(dWishlist, priorLabel, isAllTime),
      },
      price: {
        id: 'price',
        title: 'Median price',
        value: `GBP ${Math.round(currPrice)}`,
        delta: priceDeltaText,
        deltaClass: priceDeltaCls,
        copy: priceCopy(dPrice, priorLabel, isAllTime),
      },
    },
    sparklineSeries: {
      observed: { current: observedCurrent, prior: observedPrior, currentRunDates, priorRunDates },
      stock: { current: stockCurrent, prior: stockPrior, currentRunDates, priorRunDates },
      wishlist: { current: wishlistCurrent, prior: wishlistPrior, currentRunDates, priorRunDates },
      price: { current: priceCurrent, prior: pricePrior, currentRunDates, priorRunDates },
    },
    events,
  };
}

/**
 * Build MarketHealthPayload for all seven windows in one call.
 *
 * @param rawData  - Raw records injected by Python as window.marketHealthRawData.
 * @param options  - Genus filter options. Defaults to all-mode.
 */
export function buildMarketHealthPayloadAllWindows(
  rawData: MarketHealthRawData,
  options?: { selectedGenera?: string[]; isAllSelected?: boolean },
): Record<WindowId, MarketHealthPayload> {
  const result = {} as Record<WindowId, MarketHealthPayload>;
  for (const windowId of ALL_WINDOW_IDS) {
    result[windowId] = buildMarketHealthPayload(rawData, windowId, options);
  }
  return result;
}
