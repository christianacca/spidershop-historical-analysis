import { describe, expect, test, vi, beforeEach, afterAll } from 'vitest';
import { computeRange, sortRows, buildCsv, triggerDownload } from './table-utils.js';

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
  beforeEach(() => {
    (URL.createObjectURL as ReturnType<typeof vi.fn>).mockClear();
    (URL.revokeObjectURL as ReturnType<typeof vi.fn>).mockClear();
  });
  afterAll(() => vi.unstubAllGlobals());

  // Stub URL to avoid happy-dom navigation issues with anchor click
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:mock-url'),
    revokeObjectURL: vi.fn(),
  });

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
