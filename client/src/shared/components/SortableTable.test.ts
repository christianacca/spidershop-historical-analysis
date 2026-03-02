import { render, fireEvent } from '@testing-library/svelte';
import { vi, beforeAll, afterAll, beforeEach } from 'vitest';
import SortableTable from './SortableTable.svelte';

// ── Shared fixtures ───────────────────────────────────────────────────────────

// Mock URL.createObjectURL / revokeObjectURL — not available in happy-dom
beforeAll(() => {
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:mock-url'),
    revokeObjectURL: vi.fn(),
  });
});
beforeEach(() => {
  (URL.createObjectURL as ReturnType<typeof vi.fn>).mockClear();
});
afterAll(() => vi.unstubAllGlobals());

const ROWS = [
  { Species: 'Alpha Spider', Signal: '🔥', 'Stock Pattern': 'Sustained', Price: '15.00', 'Wishlist Count': '3' },
  { Species: 'Beta Spider', Signal: '⚠️', 'Stock Pattern': 'Emerging', Price: '25.00', 'Wishlist Count': '7' },
  { Species: 'Gamma Spider', Signal: '❌', 'Stock Pattern': 'Cyclical', Price: '35.00', 'Wishlist Count': '1' },
];

const COLUMNS = [
  { key: 'Species', label: 'Species' },
  { key: 'Signal', label: 'Signal' },
  { key: 'Stock Pattern', label: 'Stock Pattern' },
  { key: 'Price', label: 'Price' },
];

function renderTable(extraFilterConfig = {}) {
  return render(SortableTable, {
    tableId: 'test-table',
    rows: ROWS,
    columns: COLUMNS,
    filterConfig: {
      signalFilter: { column: 'Signal', top10: true },
      stockPatternFilter: { column: 'Stock Pattern' },
      showSearch: true,
      ...extraFilterConfig,
    },
  });
}

function tbody(container: HTMLElement): HTMLTableRowElement[] {
  return Array.from(container.querySelectorAll('tbody tr'));
}

// ── Render ────────────────────────────────────────────────────────────────────

test('renders all rows initially', () => {
  const { container } = renderTable();
  expect(tbody(container)).toHaveLength(3);
});

test('renders correct column headers', () => {
  const { container } = renderTable();
  const headers = Array.from(container.querySelectorAll('thead th')).map((th) =>
    th.textContent?.trim(),
  );
  expect(headers).toEqual(['Species', 'Signal', 'Stock Pattern', 'Price']);
});

test('visible count reflects total rows initially', () => {
  const { container } = renderTable();
  expect(container.querySelector('#visible-count-test-table')?.textContent).toBe('3');
});

test('table element has id matching tableId', () => {
  const { container } = renderTable();
  expect(container.querySelector('#test-table')).not.toBeNull();
});

// ── Sort ──────────────────────────────────────────────────────────────────────

test('clicking a header sorts rows ascending on first click', async () => {
  const { container } = renderTable();
  const speciesHeader = container.querySelector('thead th') as HTMLElement;

  await fireEvent.click(speciesHeader);

  const cells = Array.from(container.querySelectorAll('tbody tr td:first-child')).map(
    (td) => td.textContent?.trim(),
  );
  expect(cells).toEqual(['Alpha Spider', 'Beta Spider', 'Gamma Spider']);
  expect(speciesHeader.getAttribute('data-sort-direction')).toBe('asc');
});

// ── Rows with missing price/wishlist cells (covers ?? '0' fallback) ───────────

test('rows with undefined price cell do not throw during range computation', () => {
  // Some rows are missing the Price cell — exercises r[col] ?? '0' fallback
  const sparseRows = [
    { Species: 'Alpha Spider', Signal: '🔥', 'Stock Pattern': 'Sustained', 'Wishlist Count': '3' },
    { Species: 'Beta Spider', Signal: '⚠️', 'Stock Pattern': 'Emerging', Price: '25.00', 'Wishlist Count': '7' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'test-table',
    rows: sparseRows,
    columns: COLUMNS,
    filterConfig: {
      signalFilter: { column: 'Signal', top10: true },
      priceColumn: 'Price',
      wishlistColumn: 'Wishlist Count',
    },
  });
  // Both rows rendered without error
  expect(tbody(container)).toHaveLength(2);
});

test('clicking the same header twice sorts descending', async () => {
  const { container } = renderTable();
  const speciesHeader = container.querySelector('thead th') as HTMLElement;

  await fireEvent.click(speciesHeader);
  await fireEvent.click(speciesHeader);

  expect(speciesHeader.getAttribute('data-sort-direction')).toBe('desc');
  const cells = Array.from(container.querySelectorAll('tbody tr td:first-child')).map(
    (td) => td.textContent?.trim(),
  );
  expect(cells).toEqual(['Gamma Spider', 'Beta Spider', 'Alpha Spider']);
});

test('un-sorted headers have data-sort-direction="none"', () => {
  const { container } = renderTable();
  const headers = Array.from(container.querySelectorAll('thead th'));
  headers.forEach((th) => {
    expect(th.getAttribute('data-sort-direction')).toBe('none');
  });
});

test('numeric sort uses numeric ordering', async () => {
  const { container } = renderTable();
  const priceHeader = container.querySelectorAll('thead th')[3] as HTMLElement;

  await fireEvent.click(priceHeader);

  const cells = Array.from(container.querySelectorAll('tbody tr td:nth-child(4)')).map(
    (td) => td.textContent?.trim(),
  );
  expect(cells).toEqual(['15.00', '25.00', '35.00']);
});

// ── Signal filter ─────────────────────────────────────────────────────────────

test('clicking a signal filter button filters rows to that signal', async () => {
  const { container } = renderTable();
  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;

  await fireEvent.click(hotBtn);

  expect(tbody(container)).toHaveLength(1);
  expect(container.querySelector('tbody tr td')?.textContent?.trim()).toBe('Alpha Spider');
});

test('signal filter button gets is-active class when selected', async () => {
  const { container } = renderTable();
  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;

  await fireEvent.click(hotBtn);

  expect(hotBtn.classList.contains('is-active')).toBe(true);
});

test('"Show All" signal button resets filter and shows all rows', async () => {
  const { container } = renderTable();
  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;
  const showAllBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="all"]:not([data-limit])',
  ) as HTMLElement;

  await fireEvent.click(hotBtn);
  expect(tbody(container)).toHaveLength(1);

  await fireEvent.click(showAllBtn);
  expect(tbody(container)).toHaveLength(3);
});

test('visible count updates after signal filter', async () => {
  const { container } = renderTable();
  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;

  await fireEvent.click(hotBtn);

  expect(container.querySelector('#visible-count-test-table')?.textContent).toBe('1');
});

// ── Top-10 filter ─────────────────────────────────────────────────────────────

test('Top 10 button limits visible rows to at most 10', async () => {
  // Use 15 rows to test the cap
  const manyRows = Array.from({ length: 15 }, (_, i) => ({
    Species: `Spider ${i + 1}`,
    Signal: '🔥',
    'Stock Pattern': 'Sustained',
    Price: `${10 + i}.00`,
    'Wishlist Count': String(i),
  }));

  const { container } = render(SortableTable, {
    tableId: 'top10-table',
    rows: manyRows,
    columns: COLUMNS,
    filterConfig: { signalFilter: { column: 'Signal', top10: true } },
  });

  const top10Btn = container.querySelector('[data-limit="10"]') as HTMLElement;
  await fireEvent.click(top10Btn);

  expect(tbody(container).length).toBeLessThanOrEqual(10);
});

test('Top 10 button gets is-active class when enabled', async () => {
  const { container } = renderTable();
  const top10Btn = container.querySelector('[data-limit="10"]') as HTMLElement;

  await fireEvent.click(top10Btn);

  expect(top10Btn.classList.contains('is-active')).toBe(true);
});

// ── Stock pattern filter ──────────────────────────────────────────────────────

test('clicking a stock pattern filter button filters rows', async () => {
  const { container } = renderTable();
  const emergingBtn = container.querySelector(
    '[data-action="filter-stock-pattern"][data-stock-pattern="Emerging"]',
  ) as HTMLElement;

  await fireEvent.click(emergingBtn);

  expect(tbody(container)).toHaveLength(1);
  expect(container.querySelector('tbody tr td')?.textContent?.trim()).toBe('Beta Spider');
});

// ── Search ────────────────────────────────────────────────────────────────────

test('search input filters rows by text', async () => {
  const { container } = renderTable();
  const searchInput = container.querySelector('#search-test-table') as HTMLInputElement;

  await fireEvent.input(searchInput, { target: { value: 'Alpha' } });

  expect(tbody(container)).toHaveLength(1);
  expect(container.querySelector('tbody tr td')?.textContent?.trim()).toBe('Alpha Spider');
});

test('signal filter AND search are combined', async () => {
  // All three rows have different signals; only 'hot' rows match signal filter.
  // Search further narrows to species containing 'Alpha'.
  const { container } = renderTable();

  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;
  await fireEvent.click(hotBtn);

  const searchInput = container.querySelector('#search-test-table') as HTMLInputElement;
  await fireEvent.input(searchInput, { target: { value: 'Beta' } });

  // 'Beta Spider' is ⚠️, so signal=🔥 AND name=Beta → no results
  expect(tbody(container)).toHaveLength(0);
});

test('search that matches no rows shows zero visible count', async () => {
  const { container } = renderTable();
  const searchInput = container.querySelector('#search-test-table') as HTMLInputElement;

  await fireEvent.input(searchInput, { target: { value: 'xyzzy' } });

  expect(tbody(container)).toHaveLength(0);
  expect(container.querySelector('#visible-count-test-table')?.textContent).toBe('0');
});

// ── Advanced filters (price / wishlist sliders) ────────────────────────────────

test('advanced filters toggle button is rendered when priceColumn provided', () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  expect(container.querySelector('.advanced-filters-toggle')).not.toBeNull();
});

test('advanced filters panel is hidden initially', () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  expect(container.querySelector('#priceMin')).toBeNull();
});

test('clicking advanced filters toggle shows the panel', async () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  const toggleBtn = container.querySelector('.advanced-filters-toggle') as HTMLElement;

  await fireEvent.click(toggleBtn);

  expect(container.querySelector('#priceMin')).not.toBeNull();
  expect(container.querySelector('#priceMax')).not.toBeNull();
  expect(container.querySelector('#priceDisplay')).not.toBeNull();
});

test('clicking toggle again collapses the panel', async () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  const toggleBtn = container.querySelector('.advanced-filters-toggle') as HTMLElement;

  await fireEvent.click(toggleBtn);
  await fireEvent.click(toggleBtn);

  expect(container.querySelector('#priceMin')).toBeNull();
});

test('toggle button gets is-expanded class when panel is open', async () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  const toggleBtn = container.querySelector('.advanced-filters-toggle') as HTMLElement;

  await fireEvent.click(toggleBtn);

  expect(toggleBtn.classList.contains('is-expanded')).toBe(true);
});

test('filter badge is hidden when no advanced filters are active', () => {
  const { container } = renderTable({ priceColumn: 'Price' });
  const badge = container.querySelector('[id^="filterBadge"]') as HTMLElement;
  expect(badge?.classList.contains('hidden')).toBe(true);
});

// ── No filterConfig — minimal render ─────────────────────────────────────────

test('renders without filterConfig with all rows visible', () => {
  const { container } = render(SortableTable, {
    tableId: 'bare-table',
    rows: ROWS,
    columns: COLUMNS,
  });
  expect(tbody(container)).toHaveLength(3);
  // No signal filter row
  expect(container.querySelector('[data-action="filter-signal"]')).toBeNull();
  // No advanced filter toggle
  expect(container.querySelector('.advanced-filters-toggle')).toBeNull();
});

// ── Column type: species-link ─────────────────────────────────────────────────

const SPECIES_LINK_ROWS = [
  { Name: 'Aphonopelma seemanni', Signal: '🔥' },
  { Name: '', Signal: '⚠️' }, // empty name → slug is falsy
];

test('species-link column renders non-empty name as anchor link', () => {
  const columns = [
    { key: 'Name', label: 'Name', type: 'species-link' as const },
    { key: 'Signal', label: 'Signal' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'species-table',
    rows: SPECIES_LINK_ROWS,
    columns,
  });

  const links = container.querySelectorAll<HTMLAnchorElement>('tbody td a');
  expect(links.length).toBeGreaterThan(0);
  expect(links[0].href).toContain('species/aphonopelma-seemanni.html');
});

test('species-link column with empty name renders text fallback (slug falsy)', () => {
  const columns = [
    { key: 'Name', label: 'Name', type: 'species-link' as const },
    { key: 'Signal', label: 'Signal' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'species-table',
    rows: SPECIES_LINK_ROWS,
    columns,
  });

  // Row with empty Name: td should have no <a> tag, just empty text
  const nameCells = container.querySelectorAll<HTMLElement>('tbody tr td:first-child');
  const emptyCell = Array.from(nameCells).find((td) => !td.querySelector('a'));
  expect(emptyCell).not.toBeNull();
});

test('species-link with linkViewParam appends ?view= suffix to href', () => {
  const columns = [
    { key: 'Name', label: 'Name', type: 'species-link' as const, linkViewParam: 'breeder' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'species-table2',
    rows: [{ Name: 'Aphonopelma seemanni' }],
    columns,
  });

  const link = container.querySelector<HTMLAnchorElement>('tbody td a')!;
  expect(link.href).toContain('?view=breeder');
});

// ── CSV download ──────────────────────────────────────────────────────────────

async function clickDownloadAndGetBlob(container: HTMLElement): Promise<Blob> {
  const link = container.querySelector<HTMLAnchorElement>(
    "a[data-action='download-filtered-csv']",
  )!;
  await fireEvent.click(link);
  return (URL.createObjectURL as ReturnType<typeof vi.fn>).mock.calls[0][0] as Blob;
}

test('download link is rendered', () => {
  const { container } = renderTable();
  expect(container.querySelector("[data-action='download-filtered-csv']")).not.toBeNull();
});

test('clicking download link calls URL.createObjectURL', async () => {
  const { container } = renderTable();
  await clickDownloadAndGetBlob(container);
  expect(URL.createObjectURL).toHaveBeenCalled();
});

test('CSV has header row + all data rows when no filter active', async () => {
  const { container } = renderTable();
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const lines = text.trim().split('\r\n');
  // 1 header + 3 data rows
  expect(lines).toHaveLength(4);
});

test('CSV uses col.key as header when csvHeader not set', async () => {
  const { container } = renderTable();
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const headerLine = text.split('\r\n')[0];
  expect(headerLine).toBe('Species,Signal,Stock Pattern,Price');
});

test('filtered CSV excludes hidden rows', async () => {
  const { container } = renderTable();
  // Filter to 🔥 signal only → only Alpha Spider remains
  const hotBtn = container.querySelector(
    '[data-action="filter-signal"][data-signal="🔥"]',
  ) as HTMLElement;
  await fireEvent.click(hotBtn);

  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const lines = text.trim().split('\r\n');
  // 1 header + 1 data row
  expect(lines).toHaveLength(2);
  expect(text).toContain('Alpha Spider');
  expect(text).not.toContain('Beta Spider');
  expect(text).not.toContain('Gamma Spider');
});

test('CSV uses csvHeader for column headers when provided', async () => {
  const columnsWithCsvHeader = [
    { key: 'Species', label: 'Species', csvHeader: 'scientific_name' },
    { key: 'Signal', label: 'Signal', csvHeader: 'signal' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'csv-header-table',
    rows: ROWS,
    columns: columnsWithCsvHeader,
  });
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  const headerLine = text.split('\r\n')[0];
  expect(headerLine).toBe('scientific_name,signal');
});

test('CSV uses rawValueKey for cell values when provided', async () => {
  const rowsWithRaw = [
    { Species: 'Aphonopelma seemanni', _raw_species: 'aphonopelma_seemanni', Signal: '🔥' },
  ];
  const columnsWithRaw = [
    { key: 'Species', label: 'Species', rawValueKey: '_raw_species' },
    { key: 'Signal', label: 'Signal' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'raw-table',
    rows: rowsWithRaw,
    columns: columnsWithRaw,
  });
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  // Raw value used, not display key
  expect(text).toContain('aphonopelma_seemanni');
  expect(text).not.toContain('Aphonopelma seemanni');
});

test('CSV quotes values that contain a comma (RFC-4180)', async () => {
  const rowsWithComma = [
    { Species: 'Spider, tarantula', Signal: '🔥' },
  ];
  const simpleColumns = [
    { key: 'Species', label: 'Species' },
    { key: 'Signal', label: 'Signal' },
  ];
  const { container } = render(SortableTable, {
    tableId: 'comma-table',
    rows: rowsWithComma,
    columns: simpleColumns,
  });
  const blob = await clickDownloadAndGetBlob(container);
  const text = await blob.text();
  expect(text).toContain('"Spider, tarantula"');
});
