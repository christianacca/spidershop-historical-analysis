/**
 * Shared table utilities
 *
 * Pure functions used by both SortableTable and HistoryTable.
 * No Svelte reactives — all functions are plain TypeScript.
 */

export interface CsvColumn {
  key: string;
  /** Download CSV header (defaults to `key` when not set). */
  csvHeader?: string;
  /** Row key holding the raw export value (defaults to `key` when not set). */
  rawValueKey?: string;
}

/**
 * Compute the min / max range of a numeric column across all rows.
 *
 * @param rows  - Raw row data (from Python payload).
 * @param col   - Column key to inspect. Returns `{0,0}` when falsy.
 * @param mode  - `'float'` floors min / ceils max; `'int'` returns exact integers.
 */
export function computeRange(
  rows: Record<string, unknown>[],
  col: string | undefined,
  mode: 'float' | 'int',
): { min: number; max: number } {
  if (!col) return { min: 0, max: 0 };

  /** Strip leading non-numeric characters (e.g. currency symbol '£') so that
   *  values like "£25.00 ↑" parse as 25.0 rather than NaN.
   *  Undefined/null values fall back to '0' (treated as 0 in range calculations). */
  const toNumericStr = (raw: unknown): string =>
    String(raw ?? '0').replace(/^[^0-9.]*/, '');

  if (mode === 'float') {
    const vals = rows
      .map((r) => parseFloat(toNumericStr(r[col])))
      .filter((v) => !isNaN(v));
    return vals.length
      ? { min: Math.floor(Math.min(...vals)), max: Math.ceil(Math.max(...vals)) }
      : { min: 0, max: 0 };
  } else {
    const vals = rows
      .map((r) => parseInt(toNumericStr(r[col]), 10))
      .filter((v) => !isNaN(v));
    return vals.length ? { min: Math.min(...vals), max: Math.max(...vals) } : { min: 0, max: 0 };
  }
}

/**
 * Return a new sorted copy of `rows` by `key` in the given direction.
 *
 * Numeric detection: if both `a[key]` and `b[key]` parse as finite numbers,
 * numeric comparison is used; otherwise `localeCompare` for strings.
 * The original array is never mutated.
 */
export function sortRows(
  rows: Record<string, unknown>[],
  key: string,
  dir: 'asc' | 'desc',
): Record<string, unknown>[] {
  return [...rows].sort((a, b) => {
    const aRaw = a[key] ?? '';
    const bRaw = b[key] ?? '';
    const aNum = parseFloat(String(aRaw));
    const bNum = parseFloat(String(bRaw));
    const isNumeric = !isNaN(aNum) && !isNaN(bNum);
    const cmp = isNumeric ? aNum - bNum : String(aRaw).localeCompare(String(bRaw));
    return dir === 'asc' ? cmp : -cmp;
  });
}

/**
 * Serialise `visibleRows` to a CSV string using `escapeFn` for RFC-4180 encoding.
 *
 * Headers  → `col.csvHeader ?? col.key`
 * Values   → `col.rawValueKey ?? col.key`
 * Lines are joined with CRLF (`\r\n`).
 */
export function buildCsv(
  columns: CsvColumn[],
  visibleRows: Record<string, unknown>[],
  escapeFn: (values: string[]) => string,
): string {
  const headers = columns.map((col) => col.csvHeader ?? col.key);
  const lines: string[] = [escapeFn(headers)];
  for (const row of visibleRows) {
    const values = columns.map((col) => {
      if (col.rawValueKey) {
        return String(row[col.rawValueKey] ?? row[col.key] ?? '');
      }
      return String(row[col.key] ?? '');
    });
    lines.push(escapeFn(values));
  }
  return lines.join('\r\n');
}

/**
 * Filter `rows` to those where any column value contains `searchText`
 * (case-insensitive substring match).  Returns `rows` unchanged when
 * `searchText` is blank or whitespace-only.
 */
export function applySearchFilter(
  rows: Record<string, unknown>[],
  columns: { key: string }[],
  searchText: string,
): Record<string, unknown>[] {
  const q = searchText.trim().toLowerCase();
  if (!q) return rows;
  return rows.filter((r) =>
    columns.some((col) => String(r[col.key] ?? '').toLowerCase().includes(q)),
  );
}

/**
 * Create a temporary `<a download>` link, trigger a click, then clean up.
 *
 * Uses `URL.createObjectURL` / `URL.revokeObjectURL` for in-memory blob delivery.
 */
export function triggerDownload(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
