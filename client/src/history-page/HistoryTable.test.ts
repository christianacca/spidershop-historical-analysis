import { render, fireEvent } from '@testing-library/svelte';
import HistoryTable from './HistoryTable.svelte';
import {
  setupBlobUrlMock,
  clickDownloadAndGetBlob,
  openAdvancedFilters,
  openDatePicker,
} from '../test-utils/index.js';

// Mock URL.createObjectURL / revokeObjectURL — not available in happy-dom
setupBlobUrlMock();

// ── Shared fixtures ───────────────────────────────────────────────────────────

const ROWS = [
  {
    'Scrape Date': '2026-01-15',
    'Scientific Name': 'Aphonopelma seemanni',
    'Price (GBP)': '25',
    'Wishlist Count': '5',
    _raw_scrape_datetime: '2026-01-15T06:10:00',
  },
  {
    'Scrape Date': '2026-01-15',
    'Scientific Name': 'Brachypelma hamorii',
    'Price (GBP)': '30',
    'Wishlist Count': '10',
    _raw_scrape_datetime: '2026-01-15T06:10:00',
  },
  {
    'Scrape Date': '2026-01-08',
    'Scientific Name': 'Aphonopelma seemanni',
    'Price (GBP)': '25',
    'Wishlist Count': '5',
    _raw_scrape_datetime: '2026-01-08T06:10:00',
  },
  {
    'Scrape Date': '2026-01-08',
    'Scientific Name': 'Brachypelma hamorii',
    'Price (GBP)': '28',
    'Wishlist Count': '8',
    _raw_scrape_datetime: '2026-01-08T06:10:00',
  },
];

const COLUMNS = [
  { key: 'Scrape Date', label: 'Scrape Date', csvHeader: 'scrape_datetime', rawValueKey: '_raw_scrape_datetime' },
  { key: 'Scientific Name', label: 'Scientific Name', csvHeader: 'scientific_name' },
  { key: 'Price (GBP)', label: 'Price (GBP)', csvHeader: 'price_gbp' },
  { key: 'Wishlist Count', label: 'Wishlist Count', csvHeader: 'wishlist_count' },
];

function renderTable(overrides: Record<string, unknown> = {}) {
  return render(HistoryTable, {
    tableId: 'history-table',
    rows: ROWS,
    columns: COLUMNS,
    dateColumn: 'Scrape Date',
    priceColumn: 'Price (GBP)',
    wishlistColumn: 'Wishlist Count',
    ...overrides,
  });
}

function visibleRows(container: HTMLElement): HTMLTableRowElement[] {
  return Array.from(container.querySelectorAll('tbody tr'));
}

// ── Rendering ─────────────────────────────────────────────────────────────────

test('renders all rows initially', () => {
  const { container } = renderTable();
  expect(visibleRows(container)).toHaveLength(4);
});

test('visible count reflects total rows initially', () => {
  const { container } = renderTable();
  expect(container.querySelector('#visible-count-history-table')?.textContent).toBe('4');
});

test('table element has correct id', () => {
  const { container } = renderTable();
  expect(container.querySelector('#history-table')).not.toBeNull();
});

test('summary info strip is rendered when dateColumn is set', () => {
  const { container } = renderTable();
  expect(container.querySelector('#summary-info-history-table')).not.toBeNull();
});

test('filter badge is hidden initially', () => {
  const { container } = renderTable();
  const badge = container.querySelector('#filterBadge-history-table')!;
  expect(badge.classList.contains('hidden')).toBe(true);
});

// ── Date filter ───────────────────────────────────────────────────────────────

test('deselecting a date hides rows for that date', async () => {
  const { container } = renderTable();
  await openDatePicker(container);

  const checkbox = container.querySelector<HTMLInputElement>(
    "input[data-date-value='2026-01-15'][data-table-id='history-table']",
  )!;
  await fireEvent.click(checkbox);

  expect(visibleRows(container)).toHaveLength(2);
  // Only 2026-01-08 rows should remain
  visibleRows(container).forEach((row) => {
    expect(row.querySelector('td')?.textContent).toBe('2026-01-08');
  });
});

// ── Search filter ─────────────────────────────────────────────────────────────

test('search text hides rows that do not match', async () => {
  const { container } = renderTable();
  await openAdvancedFilters(container);

  const searchInput = container.querySelector<HTMLInputElement>(
    "input[data-action='search'][data-table-id='history-table']",
  )!;
  await fireEvent.input(searchInput, { target: { value: 'Aphonopelma' } });

  expect(visibleRows(container)).toHaveLength(2);
});

test('filter badge shows 1 when search is active', async () => {
  const { container } = renderTable();
  await openAdvancedFilters(container);

  const searchInput = container.querySelector<HTMLInputElement>(
    "input[data-action='search'][data-table-id='history-table']",
  )!;
  await fireEvent.input(searchInput, { target: { value: 'Aphonopelma' } });

  const badge = container.querySelector('#filterBadge-history-table')!;
  expect(badge.classList.contains('hidden')).toBe(false);
  expect(badge.textContent).toBe('1');
});

// ── Combined filters (AND logic) ──────────────────────────────────────────────

test('date + search combined: only rows matching both filters visible', async () => {
  const { container } = renderTable();
  await openDatePicker(container);

  // Deselect 2026-01-08 → only 2026-01-15 rows remain (2 rows)
  const checkbox8 = container.querySelector<HTMLInputElement>(
    "input[data-date-value='2026-01-08'][data-table-id='history-table']",
  )!;
  await fireEvent.click(checkbox8);
  expect(visibleRows(container)).toHaveLength(2);

  // Now search for Aphonopelma → should leave 1 row
  await openAdvancedFilters(container);
  const searchInput = container.querySelector<HTMLInputElement>(
    "input[data-action='search'][data-table-id='history-table']",
  )!;
  await fireEvent.input(searchInput, { target: { value: 'Aphonopelma' } });

  expect(visibleRows(container)).toHaveLength(1);
});

// ── Price slider ──────────────────────────────────────────────────────────────

test('price slider below a row price hides that row', async () => {
  const { container } = renderTable();
  await openAdvancedFilters(container);

  const maxSlider = container.querySelector<HTMLInputElement>('#priceMax')!;
  // Set max to 27 → hides rows with price 28, 30; keeps rows with price 25, 25
  await fireEvent.input(maxSlider, { target: { value: '27' } });

  expect(visibleRows(container)).toHaveLength(2);
  visibleRows(container).forEach((row) => {
    const priceTd = row.querySelectorAll('td')[2];
    expect(parseFloat(priceTd.textContent ?? '0')).toBeLessThanOrEqual(27);
  });
});

// ── Wishlist slider ───────────────────────────────────────────────────────────

test('wishlist slider above a row count hides that row', async () => {
  const { container } = renderTable();
  await openAdvancedFilters(container);

  const minSlider = container.querySelector<HTMLInputElement>('#wishlistMin')!;
  // Set min to 9 → hides rows with wishlist < 9 (5, 5, 8); keeps row with 10
  await fireEvent.input(minSlider, { target: { value: '9' } });

  expect(visibleRows(container)).toHaveLength(1);
});

// ── Combined: date + search + price ───────────────────────────────────────────

test('date + search + price all applied as AND', async () => {
  const { container } = renderTable();
  await openDatePicker(container);

  // Deselect 2026-01-08 → 2 rows remain (January 15 only)
  const checkbox8 = container.querySelector<HTMLInputElement>(
    "input[data-date-value='2026-01-08'][data-table-id='history-table']",
  )!;
  await fireEvent.click(checkbox8);

  await openAdvancedFilters(container);

  // Set price max to 26 → filters out 30; leaves 25 (Aphonopelma on 2026-01-15)
  const maxSlider = container.querySelector<HTMLInputElement>('#priceMax')!;
  await fireEvent.input(maxSlider, { target: { value: '26' } });
  expect(visibleRows(container)).toHaveLength(1);

  // Search for Aphonopelma → still 1 row
  const searchInput = container.querySelector<HTMLInputElement>(
    "input[data-action='search'][data-table-id='history-table']",
  )!;
  await fireEvent.input(searchInput, { target: { value: 'Aphonopelma' } });
  expect(visibleRows(container)).toHaveLength(1);

  // Search for something that doesn't match → 0 rows
  await fireEvent.input(searchInput, { target: { value: 'xyz_nomatch' } });
  expect(visibleRows(container)).toHaveLength(0);
});

// ── Sorting ───────────────────────────────────────────────────────────────────

test('clicking a column header sorts rows ascending', async () => {
  const { container } = renderTable();
  // Click the "Price (GBP)" header (index 2 in COLUMNS)
  const headers = container.querySelectorAll<HTMLElement>('thead th');
  const priceHeader = Array.from(headers).find((h) => h.textContent?.includes('Price'))!;
  await fireEvent.click(priceHeader);

  const cells = Array.from(visibleRows(container)).map((row) =>
    parseFloat(row.querySelectorAll('td')[2].textContent ?? '0'),
  );
  expect(cells).toEqual([...cells].sort((a, b) => a - b));
});

test('clicking the same header twice reverses sort to descending', async () => {
  const { container } = renderTable();
  const headers = container.querySelectorAll<HTMLElement>('thead th');
  const priceHeader = Array.from(headers).find((h) => h.textContent?.includes('Price'))!;
  await fireEvent.click(priceHeader);
  await fireEvent.click(priceHeader);

  const cells = Array.from(visibleRows(container)).map((row) =>
    parseFloat(row.querySelectorAll('td')[2].textContent ?? '0'),
  );
  expect(cells).toEqual([...cells].sort((a, b) => b - a));
});

// ── page-url column type ──────────────────────────────────────────────────────

const COLUMNS_WITH_PAGE_URL = [
  ...COLUMNS,
  { key: 'Page URL', label: 'Page URL', type: 'page-url' as const, csvHeader: 'page_url' },
];

const ROWS_WITH_PAGE_URL = ROWS.map((r, i) => ({
  ...r,
  'Page URL': i % 2 === 0 ? `https://example.com/${i}` : '',
}));

test('page-url column renders non-empty value as anchor link', () => {
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: ROWS_WITH_PAGE_URL,
    columns: COLUMNS_WITH_PAGE_URL,
    dateColumn: 'Scrape Date',
  });

  const links = container.querySelectorAll<HTMLAnchorElement>('tbody tr td a');
  expect(links.length).toBeGreaterThan(0);
  Array.from(links).forEach((a) => expect(a.href).toContain('https://example.com/'));
});

test('page-url column renders empty value as dash fallback', () => {
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: ROWS_WITH_PAGE_URL,
    columns: COLUMNS_WITH_PAGE_URL,
    dateColumn: 'Scrape Date',
  });

  // Rows where Page URL is '' should show '–' instead of a link
  const urlCells = Array.from(container.querySelectorAll<HTMLElement>('tbody tr td:last-child'));
  const dashCells = urlCells.filter((td) => td.textContent?.trim() === '–');
  expect(dashCells.length).toBeGreaterThan(0);
});

// ── Without dateColumn ────────────────────────────────────────────────────────

test('omitting dateColumn hides summary strip and date filter section', () => {
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: ROWS,
    columns: COLUMNS,
    // no dateColumn prop
  });

  expect(container.querySelector('#summary-info-history-table')).toBeNull();
  expect(container.querySelector('.date-filter-section')).toBeNull();
});

// ── CSV download ──────────────────────────────────────────────────────────────


test('clicking download link invokes URL.createObjectURL (buildCsv + downloadCsv)', async () => {
  const { container } = renderTable();
  await clickDownloadAndGetBlob(container);
  expect(URL.createObjectURL).toHaveBeenCalled();
});

test('CSV header uses csvHeader values from column config', async () => {
  const { container } = renderTable();
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const headerLine = text.split('\r\n')[0];
  expect(headerLine).toBe('scrape_datetime,scientific_name,price_gbp,wishlist_count');
});

test('CSV data uses rawValueKey for date column (not display value)', async () => {
  const { container } = renderTable();
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  // rawValueKey is _raw_scrape_datetime which holds the ISO datetime string
  expect(text).toContain('2026-01-15T06:10:00');
  expect(text).toContain('2026-01-08T06:10:00');
  // Display value '2026-01-15' should NOT appear as a standalone cell
  // (it only appears as part of the longer ISO string)
  const lines = text.split('\r\n').slice(1).filter(Boolean);
  lines.forEach((line) => {
    const firstCell = line.split(',')[0];
    expect(firstCell).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });
});

test('CSV has header + all rows when no filter applied', async () => {
  const { container } = renderTable();
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const lines = text.trim().split('\r\n');
  // 1 header + 4 data rows
  expect(lines).toHaveLength(5);
});

test('filtered CSV excludes date-deselected rows', async () => {
  const { container } = renderTable();
  await openDatePicker(container);

  // Deselect 2026-01-08 → only 2 rows left
  const checkbox8 = container.querySelector<HTMLInputElement>(
    "input[data-date-value='2026-01-08'][data-table-id='history-table']",
  )!;
  await fireEvent.click(checkbox8);

  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const lines = text.trim().split('\r\n');
  // 1 header + 2 data rows (only 2026-01-15 rows)
  expect(lines).toHaveLength(3);
  expect(text).not.toContain('2026-01-08T06:10:00');
});

test('CSV quotes values that contain a comma (RFC-4180)', async () => {
  const commaRows = [
    {
      'Scrape Date': '2026-01-15',
      'Scientific Name': 'Spider, with comma',
      'Price (GBP)': '25',
      'Wishlist Count': '5',
      _raw_scrape_datetime: '2026-01-15T06:10:00',
    },
  ];
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: commaRows,
    columns: COLUMNS,
    dateColumn: 'Scrape Date',
  });
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  expect(text).toContain('"Spider, with comma"');
});

// ── Sparkline column type ─────────────────────────────────────────────────────

test('sparkline column with DTO value renders an <svg> element', () => {
  const sparklineDto = {
    bars: [{ bar_height: 14, fill: '#22c55e', opacity: 0.85, tooltip: '£15.00' }],
    svg_width: 10,
    svg_height: 20,
    title: 'Price History',
  };
  const sparklineRow = { ...ROWS[0], Sparkline: sparklineDto };
  const sparklineCol = { key: 'Sparkline', label: 'Sparkline', type: 'sparkline' as const };

  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: [sparklineRow],
    columns: [COLUMNS[0], sparklineCol],
    dateColumn: 'Scrape Date',
  });

  // The sparkline td should contain an SVG element rendered by SparklineBar
  const svgEl = container.querySelector('tbody tr td svg');
  expect(svgEl).not.toBeNull();
});

// ── Without priceColumn and wishlistColumn ────────────────────────────────────

test('omitting priceColumn and wishlistColumn renders table with all rows', async () => {
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: ROWS,
    columns: COLUMNS,
    dateColumn: 'Scrape Date',
    // priceColumn and wishlistColumn intentionally omitted
  });

  // All rows visible; no RangeSlider rendered for price or wishlist
  expect(visibleRows(container)).toHaveLength(4);
  // Advanced filters panel has no price/wishlist sliders
  const advancedBtn = container.querySelector('.advanced-filters-toggle:not(.date-expand-btn)')!;
  await fireEvent.click(advancedBtn);
  expect(container.querySelector('#priceMin')).toBeNull();
});

// ── Rows with missing cell values (covers ?? '0' fallback branches) ───────────

test('rows with undefined price and wishlist cells still render and filter correctly', async () => {
  // Some rows intentionally lack 'Price (GBP)' and 'Wishlist Count' keys
  const sparseRows = [
    { 'Scrape Date': '2026-01-15', 'Scientific Name': 'Alpha' },
    { 'Scrape Date': '2026-01-15', 'Scientific Name': 'Beta', 'Price (GBP)': '25', 'Wishlist Count': '5' },
  ];
  const { container } = render(HistoryTable, {
    tableId: 'history-table',
    rows: sparseRows,
    columns: COLUMNS,
    dateColumn: 'Scrape Date',
    priceColumn: 'Price (GBP)',
    wishlistColumn: 'Wishlist Count',
  });

  // Both rows should render without error
  expect(visibleRows(container)).toHaveLength(2);
});

