/**
 * CSV serialisation utilities shared across page slices.
 */

/**
 * Serialise a single row of values into a CSV-safe string.
 *
 * Values that contain a comma, double-quote, carriage-return, or newline are
 * wrapped in double-quotes.  Any double-quote characters within the value are
 * escaped by doubling them (`"` → `""`).
 */
export function escapeCsvRow(values: string[]): string {
  return values
    .map(value => {
      const str = String(value ?? '');
      if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
        return '"' + str.replace(/"/g, '""') + '"';
      }
      return str;
    })
    .join(',');
}
