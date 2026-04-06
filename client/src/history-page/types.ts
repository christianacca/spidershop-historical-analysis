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
  current: number[];    // 12 values
  prior: number[];      // 12 values; empty array [] when showPrior = false
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
