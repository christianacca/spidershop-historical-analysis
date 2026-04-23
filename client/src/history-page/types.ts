// TypeScript interfaces for the Market Health KPI section (WP1).
// These are the canonical types used by Svelte components, Storybook fixtures,
// and Vitest tests. Python produces dicts that match this shape.

export type WindowId =
  | 'this-month'
  | 'last-month'
  | 'current-quarter'
  | 'last-quarter'
  | 'this-year'
  | 'last-year'
  | 'all-time';

export interface MarketHealthPayload {
  windowId: WindowId;
  windowLabel: string;          // window display name; available for client-side use but has no
                                // fixed DOM target in Market Health — do not require for rendering
  windowBasisNote: string;      // renders as filter-panel period summary below time-window buttons
                                // (#time-window-basis-note)
  showPrior: boolean;           // drives prior sparkline series visibility
  sparklineBasisNote: string;   // renders in sparkline support row (#market-sparkline-basis-note);
                                // values defined in spec §4.4
  isAllSelected: boolean;       // true = All-mode (all tracked species); false = genus-scoped
  generaCount: number;          // drives heading adaptation (0 = empty genus-scoped state)
  scopeLabel: string;           // ≤3 genera: "Avicularia, Caribena and Psalmopoeus";
                                // 4+: "your {N} selected genera"; All-mode: "" (empty)

  kpis: {
    observed: KpiCardData;
    stock: KpiCardData;
    wishlist: KpiCardData;
    price: KpiCardData;
  };

  sparklineSeries: {
    observed: SparklineSeries;
    stock: SparklineSeries;
    wishlist: SparklineSeries;
    price: SparklineSeries;
  };

  events: MarketEventsData;
}

export interface KpiCardData {
  id: 'observed' | 'stock' | 'wishlist' | 'price'; // used by MarketKpiCard to look up
                                                     // the constant tooltip text (see spec §7.2)
  title: string;                          // static heading e.g. "Observed species"
  value: string;                          // formatted value e.g. "184" or "61%"
  delta: string;                          // formatted delta e.g. "+7 vs prior quarter QTD"
  deltaClass: '' | 'down' | 'flat';       // maps to CSS modifier on .metric-delta
  copy: string;                           // one interpretation sentence (see spec §3);
                                          // fully resolved, no {token} substitution needed
}

export interface SparklineSeries {
  current: number[];            // 12 values
  prior: number[];              // 12 values; empty array [] when showPrior = false
  currentRunDates: string[];    // 12 ISO date strings, resampled at same indices as current[]
  priorRunDates: string[];      // 12 ISO date strings; empty array [] when showPrior = false
}

export interface MarketEventsData {
  title: string;
  subtitle: string;
  newListings: EventTile;
  droppedListings: EventTile;
  restocks: EventTile;
  oosFlips: EventTile;
}

export interface EventTile {
  label: string;
  value: string;
  copy: string;
}

/** One variant-level row from the history CSV, normalised for the engine. */
export interface RawRunRecord {
  scrapeDatetime: string;   // ISO 8601 string — e.g. "2026-04-14T06:10:00"
  scientificName: string;   // full binomial — e.g. "Avicularia avicularia"
  sizeVariant: string;      // size_cm field from CSV — e.g. "2.0"
  pageUrl: string;          // page_url field — used for size-transition detection
  wishlistCount: number;    // numeric (0 if missing/invalid in source)
  priceGbp: number;         // numeric (0.0 if missing/invalid in source)
}

/**
 * Raw market data injected by Python as window.marketHealthRawData.
 *
 * referenceDate is the ISO string of the most recent scrape_datetime in the
 * dataset. The engine uses it to compute window boundaries relative to the data
 * rather than new Date(), keeping the static page meaningful however old it is.
 */
export interface MarketHealthRawData {
  records: RawRunRecord[];
  referenceDate: string;
}
