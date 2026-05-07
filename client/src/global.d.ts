/**
 * Global type declarations for browser-injected data
 */

/**
 * Build version string injected by Vite at build time.
 * Format: "{shortSha}-r{runId}" in CI (e.g. "abc1234-r25523830085").
 * Falls back to "local-dev" when built locally without VITE_BUILD_VERSION set.
 */
declare const __BUILD_VERSION__: string;

/**
 * Open structural type for a row read from a Python-generated table payload.
 * Deliberately wide because Python owns the column names and they differ per
 * page. TypeScript cannot enforce column names here — use assertPayload() in
 * dev mode to catch template injection drift at runtime.
 */
type TableRow = Record<string, unknown>;

/**
 * History table rows carry a hidden raw ISO datetime column required for
 * correct CSV export. The display column ('Scrape Date') formats the value
 * for readability; _raw_scrape_datetime must survive through to buildCsv()
 * to produce a machine-readable export.
 */
interface HistoryTableRow extends Record<string, unknown> {
  /**
   * Raw ISO datetime string (e.g. `"2026-01-15T06:10:00"`) required for
   * machine-readable CSV export.  The display column 'Scrape Date' formats
   * this value for readability; this field MUST be preserved through to
   * `buildCsv()` via `rawValueKey` so the exported CSV contains a
   * machine-parseable timestamp rather than the human display value.
   */
  _raw_scrape_datetime: string;
}

interface SpeciesRun {
  observed: boolean;
  price: string;
  wishlist: string;
}

interface SpeciesChartData {
  runs: SpeciesRun[];
}

/**
 * A single scrape observation for one species on one date, used by the
 * history chart/KPI layer. Mirrors the columns from the history CSV that
 * are relevant for time-series charting.
 */
interface HistoryChartRun {
  date: string;
  price_gbp: number | null;
  wishlist_count: number | null;
  in_stock: boolean;
}

/**
 * All chart runs for a single species, grouped together.
 */
interface HistoryChartSpecies {
  scientific_name: string;
  common_name: string;
  runs: HistoryChartRun[];
}

/**
 * Top-level payload for the history chart/KPI page.
 * `scrape_dates` is the chronologically sorted, deduplicated list of all
 * scrape dates across all species — used to align multi-series charts.
 */
interface HistoryChartData {
  species: HistoryChartSpecies[];
  scrape_dates: string[];
}

interface Window {
  /** Stable table payload keys (kebab-case TABLE_ID + 'Data') */
  'breeder-tableData'?: TableRow[];
  'dealer-tableData'?: TableRow[];
  'snapshot-tableData'?: TableRow[];
  'history-tableData'?: HistoryTableRow[];
  speciesChartData?: SpeciesChartData;
  historyChartData?: HistoryChartData;
}

// ── View Transitions Level 2 ─────────────────────────────────────────────────
// `types` is not in the standard TS DOM lib yet; declared here so that
// view-transitions-entry.ts can call vt.types.add() without casting.

interface ViewTransitionTypes {
  add(type: string): void;
  delete(type: string): void;
  has(type: string): boolean;
}

interface ViewTransition {
  // Augments the existing lib.dom.d.ts ViewTransition — TypeScript merges declarations.
  readonly types: ViewTransitionTypes;
}

interface PageRevealEvent extends Event {
  readonly viewTransition: ViewTransition | null;
}

// ── Navigation API (used by view-transitions-entry.ts) ──────────────────────
// window.navigation is Chrome 102+. These declarations are minimal and cover
// only the fields consumed by the direction-detection logic.

interface NavigationHistoryEntry {
  readonly url: string;
}

interface NavigationActivation {
  readonly entry: NavigationHistoryEntry;
  readonly from: NavigationHistoryEntry | null;
}
