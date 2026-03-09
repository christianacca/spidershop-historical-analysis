/**
 * Global type declarations for browser-injected data
 */

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

interface Window {
  /** Stable table payload keys (kebab-case TABLE_ID + 'Data') */
  'breeder-tableData'?: TableRow[];
  'dealer-tableData'?: TableRow[];
  'snapshot-tableData'?: TableRow[];
  'history-tableData'?: HistoryTableRow[];
  speciesChartData?: SpeciesChartData;
}
