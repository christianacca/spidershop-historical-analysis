/**
 * Pure utility functions for the History page.
 * No Svelte reactives — all functions are plain TypeScript.
 */

/**
 * Collect unique date values from `dateColumn` across `rows`, returning
 * them in ascending order (oldest first).
 *
 * Rows are iterated from the end so that the first time a date is
 * encountered it is the oldest occurrence, preserving natural insertion
 * order for duplicates.  Rows where the date value is absent or empty
 * are skipped.
 */
export function collectAllDates(
  rows: Record<string, unknown>[],
  dateColumn: string | undefined,
): string[] {
  if (!dateColumn) return [];
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (let i = rows.length - 1; i >= 0; i--) {
    const d = String(rows[i][dateColumn] ?? '');
    if (d && !seen.has(d)) {
      seen.add(d);
      ordered.push(d);
    }
  }
  return ordered;
}
