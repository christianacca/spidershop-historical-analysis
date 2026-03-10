import { describe, expect, test } from 'vitest';
import { computeRange, sortRows, buildCsv, triggerDownload, applySearchFilter } from './table-utils.js';
import { setupBlobUrlMock } from '../test-utils/index.js';

// ── computeRange ─────────────────────────────────────────────────────────────

describe('computeRange', () => {
  test('returns {0,0} when col is undefined', () => {
    const rows = [{ price: '10.5' }];
    expect(computeRange(rows, undefined, 'float')).toEqual({ min: 0, max: 0 });
  });

  test('returns {0,0} when col is empty string', () => {
    const rows = [{ price: '10.5' }];
    expect(computeRange(rows, '', 'float')).toEqual({ min: 0, max: 0 });
  });

  test('returns {0,0} when rows is empty', () => {
    expect(computeRange([], 'price', 'float')).toEqual({ min: 0, max: 0 });
  });

  test('returns {0,0} when no valid numeric values found', () => {
    const rows = [{ price: 'N/A' }, { price: '-' }];
    expect(computeRange(rows, 'price', 'float')).toEqual({ min: 0, max: 0 });
  });

  test('float mode: floors min and ceils max', () => {
    const rows = [
      { price: '10.3' },
      { price: '25.7' },
      { price: '15.0' },
    ];
    expect(computeRange(rows, 'price', 'float')).toEqual({ min: 10, max: 26 });
  });

  test('float mode: single value rows', () => {
    const rows = [{ price: '12.5' }];
    expect(computeRange(rows, 'price', 'float')).toEqual({ min: 12, max: 13 });
  });

  test('int mode: returns exact min and max', () => {
    const rows = [
      { wishlist: '3' },
      { wishlist: '10' },
      { wishlist: '7' },
    ];
    expect(computeRange(rows, 'wishlist', 'int')).toEqual({ min: 3, max: 10 });
  });

  test('int mode: single value', () => {
    const rows = [{ wishlist: '5' }];
    expect(computeRange(rows, 'wishlist', 'int')).toEqual({ min: 5, max: 5 });
  });

  test('skips NaN values in float mode', () => {
    const rows = [{ price: '10.0' }, { price: 'bad' }, { price: '20.0' }];
    expect(computeRange(rows, 'price', 'float')).toEqual({ min: 10, max: 20 });
  });

  // G7: price values with currency symbol and trend arrow, e.g. "£25.00 ↑"
  test('float mode: strips leading currency symbol from "£XX.XX ↑" values', () => {
    const rows = [
      { price: '£15.00 ↑' },
      { price: '£25.00 →' },
      { price: '£10.50 ↓' },
    ];
    expect(computeRange(rows, 'price', 'float')).toEqual({ min: 10, max: 25 });
  });
});

// ── sortRows ──────────────────────────────────────────────────────────────────

describe('sortRows', () => {
  const rows = [
    { name: 'Charlie', score: '30' },
    { name: 'Alice', score: '10' },
    { name: 'Beta', score: '20' },
  ];

  test('sorts numerically ascending', () => {
    const result = sortRows(rows, 'score', 'asc');
    expect(result.map((r) => r['score'])).toEqual(['10', '20', '30']);
  });

  test('sorts numerically descending', () => {
    const result = sortRows(rows, 'score', 'desc');
    expect(result.map((r) => r['score'])).toEqual(['30', '20', '10']);
  });

  test('sorts strings ascending', () => {
    const result = sortRows(rows, 'name', 'asc');
    expect(result.map((r) => r['name'])).toEqual(['Alice', 'Beta', 'Charlie']);
  });

  test('sorts strings descending', () => {
    const result = sortRows(rows, 'name', 'desc');
    expect(result.map((r) => r['name'])).toEqual(['Charlie', 'Beta', 'Alice']);
  });

  test('does not mutate the original array', () => {
    const original = [{ v: '3' }, { v: '1' }, { v: '2' }];
    sortRows(original, 'v', 'asc');
    expect(original.map((r) => r['v'])).toEqual(['3', '1', '2']);
  });

  test('mixed numeric and non-numeric — falls back to string compare', () => {
    const mixed = [{ v: '10' }, { v: 'abc' }];
    // aNum is valid, bNum is NaN → isNumeric false → localeCompare
    const result = sortRows(mixed, 'v', 'asc');
    expect(result).toHaveLength(2);
  });

  test('ascending sort strips leading currency symbol', () => {
    const priceRows = [
      { price: '£15.00 ↑' },
      { price: '£5.00 →' },
      { price: '£25.00 ↓' },
    ];
    const result = sortRows(priceRows, 'price', 'asc');
    expect(result.map((r) => r['price'])).toEqual(['£5.00 →', '£15.00 ↑', '£25.00 ↓']);
  });

  test('descending sort strips leading currency symbol', () => {
    const priceRows = [
      { price: '£15.00 ↑' },
      { price: '£5.00 →' },
      { price: '£25.00 ↓' },
    ];
    const result = sortRows(priceRows, 'price', 'desc');
    expect(result.map((r) => r['price'])).toEqual(['£25.00 ↓', '£15.00 ↑', '£5.00 →']);
  });

  test('species names with trailing numbers sort alphabetically, not numerically', () => {
    // Regression: "Hot Species 15" was parsed as 15, "Watch Species 03" as 3,
    // causing numeric sort to put Hot before Watch in descending order.
    const speciesRows = [
      { species: 'Hot Species 15' },
      { species: 'Hot Species 01' },
      { species: 'Watch Species 03' },
      { species: 'Avoid Species 02' },
    ];
    const result = sortRows(speciesRows, 'species', 'desc');
    // Alphabetical desc: W > H > A; within group order by full string
    expect(result.map((r) => r['species'])).toEqual([
      'Watch Species 03',
      'Hot Species 15',
      'Hot Species 01',
      'Avoid Species 02',
    ]);
  });

  test('empty rows returns empty array', () => {
    expect(sortRows([], 'price', 'asc')).toEqual([]);
  });

  test('single row returns unchanged single-element array', () => {
    const single = [{ price: '£10.00' }];
    const result = sortRows(single, 'price', 'asc');
    expect(result).toHaveLength(1);
    expect(result[0]['price']).toBe('£10.00');
  });
});

// ── buildCsv ─────────────────────────────────────────────────────────────────

describe('buildCsv', () => {
  const escape = (values: string[]) =>
    values.map((v) => (v.includes(',') ? `"${v}"` : v)).join(',');

  const columns = [
    { key: 'name', csvHeader: 'display_name' },
    { key: 'price' },
    { key: 'date', csvHeader: 'scrape_date', rawValueKey: 'raw_date' },
  ];

  const rows = [
    { name: 'Alpha Spider', price: '15.00', date: '01 Jan 2025', raw_date: '2025-01-01T10:00:00' },
    { name: 'Beta Spider', price: '25.00', date: '08 Jan 2025', raw_date: '2025-01-08T10:00:00' },
  ];

  test('header uses csvHeader when provided, key otherwise', () => {
    const csv = buildCsv(columns, rows, escape);
    const [header] = csv.split('\r\n');
    expect(header).toBe('display_name,price,scrape_date');
  });

  test('data cells use rawValueKey when provided', () => {
    const csv = buildCsv(columns, rows, escape);
    const [, row1] = csv.split('\r\n');
    expect(row1).toContain('2025-01-01T10:00:00');
    expect(row1).not.toContain('01 Jan 2025');
  });

  test('data cells fall back to key value when rawValueKey not set', () => {
    const csv = buildCsv(columns, rows, escape);
    const [, row1] = csv.split('\r\n');
    expect(row1).toContain('Alpha Spider');
    expect(row1).toContain('15.00');
  });

  test('empty visibleRows produces header line only', () => {
    const csv = buildCsv(columns, [], escape);
    expect(csv.split('\r\n')).toHaveLength(1);
  });

  test('passes through RFC-4180 comma quoting via escapeFn', () => {
    const rowsWithComma = [{ name: 'A, Spider', price: '10.00', date: 'd', raw_date: 'r' }];
    const csv = buildCsv(columns, rowsWithComma, escape);
    const [, row1] = csv.split('\r\n');
    expect(row1).toContain('"A, Spider"');
  });

  test('uses CRLF line endings', () => {
    const csv = buildCsv(columns, rows, escape);
    expect(csv).toContain('\r\n');
  });

  test('uses key as header when csvHeader not set', () => {
    const simpleCols = [{ key: 'species' }];
    const simpleRows = [{ species: 'Test Spider' }];
    const csv = buildCsv(simpleCols, simpleRows, escape);
    expect(csv.startsWith('species')).toBe(true);
  });
});

// ── triggerDownload ───────────────────────────────────────────────────────────

describe('triggerDownload', () => {
  setupBlobUrlMock();

  test('calls URL.createObjectURL once', () => {
    triggerDownload('col1,col2\r\nval1,val2', 'test.csv');
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  });

  test('calls URL.revokeObjectURL after download', () => {
    triggerDownload('col1,col2\r\nval1,val2', 'test.csv');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  test('creates a Blob with text/csv mime type', () => {
    const createObjectURL = URL.createObjectURL as ReturnType<typeof vi.fn>;
    triggerDownload('content', 'out.csv');
    const blob = createObjectURL.mock.calls[0][0] as Blob;
    expect(blob.type).toBe('text/csv;charset=utf-8;');
  });
});

// ── applySearchFilter ─────────────────────────────────────────────────────

describe('applySearchFilter', () => {
  const columns = [{ key: 'Species' }, { key: 'Signal' }];

  const rows = [
    { Species: 'Alpha Spider', Signal: '🔥' },
    { Species: 'Beta Spider', Signal: '⚠️' },
    { Species: 'Gamma Spider', Signal: '❌' },
  ];

  test('returns all rows when searchText is empty', () => {
    expect(applySearchFilter(rows, columns, '')).toEqual(rows);
  });

  test('returns all rows when searchText is whitespace only', () => {
    expect(applySearchFilter(rows, columns, '   ')).toEqual(rows);
  });

  test('filters rows by partial case-insensitive match in a column', () => {
    const result = applySearchFilter(rows, columns, 'alpha');
    expect(result).toHaveLength(1);
    expect(result[0]['Species']).toBe('Alpha Spider');
  });

  test('matches against all supplied columns', () => {
    // Signal column contains emoji — search by signal value
    const result = applySearchFilter(rows, columns, '🔥');
    expect(result).toHaveLength(1);
    expect(result[0]['Species']).toBe('Alpha Spider');
  });

  test('returns empty array when no row matches', () => {
    expect(applySearchFilter(rows, columns, 'xyzzy')).toEqual([]);
  });

  test('returns the original array reference when query is blank (no-op)', () => {
    const result = applySearchFilter(rows, columns, '');
    expect(result).toBe(rows);
  });

  test('does not mutate the input array', () => {
    const original = [...rows];
    applySearchFilter(rows, columns, 'Beta');
    expect(rows).toEqual(original);
  });

  test('matches partial text across multiple columns — returns all rows where any column matches', () => {
    const multiColRows = [
      { Species: 'Alpha Spider', Info: 'red' },
      { Species: 'Blue Tarantula', Info: 'alpha' },
    ];
    const colDefs = [{ key: 'Species' }, { key: 'Info' }];
    // 'alpha' appears in Species of row 1 and Info of row 2
    const result = applySearchFilter(multiColRows, colDefs, 'alpha');
    expect(result).toHaveLength(2);
  });
});
