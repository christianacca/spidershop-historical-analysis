/**
 * Page-boundary payload validation.
 *
 * assertPayload() is called at entry-point mount time to detect Python template
 * injection drift early. It only runs in dev mode so no validation logic is
 * bundled into production builds.
 */

/**
 * Asserts that `rows` is a non-empty array, narrowing its type to TableRow[].
 *
 * Only active when `isDev` is true (defaults to `import.meta.env.DEV`). In
 * production the function returns immediately without checking anything, so
 * an empty or malformed payload renders a silent empty table rather than
 * crashing the page.
 *
 * @param tableId - The TABLE_ID constant from the calling entry point.
 *   Used to construct the window global key name in error messages.
 * @param rows - The raw value read from the window global before any cast.
 * @param isDev - Override for testability; defaults to `import.meta.env.DEV`.
 */
export function assertPayload(
  tableId: string,
  rows: unknown,
  isDev = import.meta.env.DEV
): asserts rows is TableRow[] {
  if (!isDev) return;

  if (!Array.isArray(rows)) {
    throw new Error(
      `assertPayload: window['${tableId}Data'] is not an array — got ${typeof rows}. ` +
        `Check that the Python template sets window['${tableId}Data'] before the bundle loads.`
    );
  }

  if (rows.length === 0) {
    throw new Error(
      `assertPayload: window['${tableId}Data'] is an empty array — ` +
        `template injection may have failed or the data file is empty.`
    );
  }
}
