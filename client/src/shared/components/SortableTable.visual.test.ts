/**
 * SortableTable — browser-backed visual contracts. (Phase 6, step 41)
 *
 * Covers layout behaviours that are hard to trust in happy-dom but critical
 * for the table to remain usable:
 *
 *   - The table scroll container must have overflow-x: auto so wide tables
 *     scroll horizontally rather than overflow the page.           (step 41)
 *
 *   - The controls row must use flex layout with wrapping so filter buttons
 *     reflow onto multiple lines on narrow viewports.              (step 41)
 *
 *   - Mobile card layout (≤ 768 px): td::before must use display: block so
 *     the eyebrow label sits above the value.                      (step 48)
 *
 * These are CSS structural properties — not colour contracts — which is why
 * they live in this file rather than alongside component colour tests.
 * happy-dom does expose getComputedStyle, but it does not model CSS cascade
 * reliably for layout properties on composed components.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
import { render, fireEvent } from '@testing-library/svelte';
import { tokenRgb } from '../../test-utils/token-colors';
import SortableTable from './SortableTable.svelte';

// ── Minimal fixtures ──────────────────────────────────────────────────────────

const TEST_COLUMNS = [
  { key: 'species', label: 'Species' },
  { key: 'price', label: 'Price' },
];

const TEST_ROWS = [
  { species: 'Test Spider', price: '£5.00' },
  { species: 'Another Spider', price: '£10.00' },
];

// ── Table scroll container (step 41) ─────────────────────────────────────────

describe('SortableTable — table scroll container', () => {
  it('table-scroll has overflow-x: auto', () => {
    const { container } = render(SortableTable, {
      tableId: 'visual-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
    });
    const scroll = container.querySelector('.table-scroll') as HTMLElement;
    expect(scroll).not.toBeNull();
    expect(window.getComputedStyle(scroll).overflowX).toBe('auto');
  });
});

// ── Controls row layout (step 41) ─────────────────────────────────────────────

describe('SortableTable — controls row layout', () => {
  // filterConfig: { showSearch: true } triggers hasAdvancedContent → renders .controls-row
  it('controls-row uses flex layout', () => {
    const { container } = render(SortableTable, {
      tableId: 'visual-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
      filterConfig: { showSearch: true },
    });
    const controls = container.querySelector('.controls-row') as HTMLElement;
    expect(controls).not.toBeNull();
    expect(window.getComputedStyle(controls).display).toBe('flex');
  });

  it('controls-row wraps to multiple lines (flex-wrap: wrap)', () => {
    const { container } = render(SortableTable, {
      tableId: 'visual-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
      filterConfig: { showSearch: true },
    });
    const controls = container.querySelector('.controls-row') as HTMLElement;
    expect(controls).not.toBeNull();
    expect(window.getComputedStyle(controls).flexWrap).toBe('wrap');
  });
});

// ── Active signal filter button colour (step 43) ──────────────────────────────

describe('SortableTable — active signal filter button', () => {
  it('active signal filter button background uses --color-accent token', async () => {
    const { container } = render(SortableTable, {
      tableId: 'visual-test',
      rows: [
        { species: 'Alpha Spider', Signal: '🔥' },
        { species: 'Beta Spider',  Signal: '⚠️' },
      ],
      columns: TEST_COLUMNS,
      filterConfig: { signalFilter: { column: 'Signal' } },
    });
    const hotBtn = container.querySelector(
      '[data-action="filter-signal"][data-signal="🔥"]',
    ) as HTMLElement;
    await fireEvent.click(hotBtn);
    expect(window.getComputedStyle(hotBtn).backgroundColor).toBe(tokenRgb('--color-accent'));
  });
});

// ── Mobile card layout — eyebrow label (step 48) ─────────────────────────────

describe('SortableTable — mobile card eyebrow label', () => {
  afterEach(async () => {
    await page.viewport(1280, 720);
  });

  it('td has display: flex at mobile viewport (≤ 768 px)', async () => {
    await page.viewport(390, 844);
    const { container } = render(SortableTable, {
      tableId: 'mobile-label-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
    });
    // TEST_COLUMNS have no cardHeader/cardSubheader — all cells use flex side-by-side layout.
    const td = container.querySelectorAll('tbody td')[0] as HTMLElement;
    expect(td).not.toBeNull();
    expect(window.getComputedStyle(td).display).toBe('flex');
  });

  it('td[data-card-role="header"]::before has display: none at mobile (header suppresses label)', async () => {
    await page.viewport(390, 844);
    const { container } = render(SortableTable, {
      tableId: 'mobile-header-role-test',
      rows: TEST_ROWS,
      columns: [{ key: 'species', label: 'Species', cardHeader: true }, { key: 'price', label: 'Price' }],
    });
    const headerTd = container.querySelector('tbody td[data-card-role="header"]') as HTMLElement;
    expect(headerTd).not.toBeNull();
    const before = window.getComputedStyle(headerTd, '::before');
    expect(before.display).toBe('none');
  });

  it('td does not have display: flex at desktop viewport (> 768 px)', async () => {
    await page.viewport(1280, 720);
    const { container } = render(SortableTable, {
      tableId: 'desktop-label-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
    });
    const td = container.querySelectorAll('tbody td')[0] as HTMLElement;
    expect(td).not.toBeNull();
    // At desktop widths the media-query block does not apply — td is not flex.
    expect(window.getComputedStyle(td).display).not.toBe('flex');
  });
});

// ── Signal cell desktop colours ────────────────────────────────────────────────
// Guards the per-signal border-left colour after the shared/per-signal dedup.

describe('SortableTable — signal cell desktop colours', () => {
  const SIGNAL_COLUMNS = [
    { key: 'species', label: 'Species' },
    { key: 'signal',  label: 'Signal' },
  ];
  const FILTER_CONFIG = { signalFilter: { column: 'signal' } };

  beforeEach(async () => {
    await page.viewport(1280, 900);
  });

  it('signal-hot td has border-left-color == --color-signal-hot', () => {
    const { container } = render(SortableTable, {
      tableId: 'signal-colour-hot',
      rows: [{ species: 'A', signal: '🔥' }],
      columns: SIGNAL_COLUMNS,
      filterConfig: FILTER_CONFIG,
    });
    const td = container.querySelector('td.signal-hot') as HTMLElement;
    expect(td).not.toBeNull();
    expect(window.getComputedStyle(td).borderLeftColor).toBe(tokenRgb('--color-signal-hot'));
  });

  it('signal-watch td has border-left-color == --color-signal-watch', () => {
    const { container } = render(SortableTable, {
      tableId: 'signal-colour-watch',
      rows: [{ species: 'A', signal: '⚠️' }],
      columns: SIGNAL_COLUMNS,
      filterConfig: FILTER_CONFIG,
    });
    const td = container.querySelector('td.signal-watch') as HTMLElement;
    expect(td).not.toBeNull();
    expect(window.getComputedStyle(td).borderLeftColor).toBe(tokenRgb('--color-signal-watch'));
  });

  it('signal-avoid td has border-left-color == --color-signal-avoid', () => {
    const { container } = render(SortableTable, {
      tableId: 'signal-colour-avoid',
      rows: [{ species: 'A', signal: '❌' }],
      columns: SIGNAL_COLUMNS,
      filterConfig: FILTER_CONFIG,
    });
    const td = container.querySelector('td.signal-avoid') as HTMLElement;
    expect(td).not.toBeNull();
    expect(window.getComputedStyle(td).borderLeftColor).toBe(tokenRgb('--color-signal-avoid'));
  });
});

// ── Signal cell mobile card layout ────────────────────────────────────────────
// Guards the mobile overrides after the td.signal-X + .signal-X merge.

describe('SortableTable — signal cell mobile card layout', () => {
  const SIGNAL_COLUMNS = [
    { key: 'species', label: 'Species' },
    { key: 'signal',  label: 'Signal' },
  ];
  const FILTER_CONFIG = { signalFilter: { column: 'signal' } };

  afterEach(async () => {
    await page.viewport(1280, 900);
  });

  it('signal-hot td is display:block on mobile (not flex)', async () => {
    await page.viewport(390, 844);
    const { container } = render(SortableTable, {
      tableId: 'signal-mobile-block',
      rows: [{ species: 'A', signal: '🔥' }],
      columns: SIGNAL_COLUMNS,
      filterConfig: FILTER_CONFIG,
    });
    const td = container.querySelector('td.signal-hot') as HTMLElement;
    expect(td).not.toBeNull();
    expect(window.getComputedStyle(td).display).toBe('block');
  });

  it('signal-hot td has full border (all sides) on mobile', async () => {
    await page.viewport(390, 844);
    const { container } = render(SortableTable, {
      tableId: 'signal-mobile-border',
      rows: [{ species: 'A', signal: '🔥' }],
      columns: SIGNAL_COLUMNS,
      filterConfig: FILTER_CONFIG,
    });
    const td = container.querySelector('td.signal-hot') as HTMLElement;
    expect(td).not.toBeNull();
    const style = window.getComputedStyle(td);
    // On mobile: border:2px solid replaces the desktop border-left:4px solid
    expect(style.borderTopStyle).toBe('solid');
    expect(style.borderTopWidth).toBe('2px');
    expect(style.borderBottomWidth).toBe('2px');
  });
});

// ── Signal cell visual contracts ──────────────────────────────────────────────
//
// Guards against regressions in the shared + per-signal signal-cell CSS after
// deduplication of .signal-hot / .signal-watch / .signal-avoid rules.

const SIGNAL_COLUMNS = [
  { key: 'species', label: 'Species' },
  { key: 'signal', label: 'Signal' },
];

const SIGNAL_ROWS = [
  { species: 'Alpha Spider', signal: '🔥' },
  { species: 'Beta Spider',  signal: '⚠️' },
  { species: 'Gamma Spider', signal: '❌' },
];

function renderSignalTable() {
  return render(SortableTable, {
    tableId: 'signal-visual-test',
    rows: SIGNAL_ROWS,
    columns: SIGNAL_COLUMNS,
    filterConfig: { signalFilter: { column: 'signal' } },
  });
}

function getSignalCell(container: HTMLElement, cls: string): HTMLElement {
  const cell = container.querySelector(`td.${cls}`) as HTMLElement;
  if (!cell) throw new Error(`No td.${cls} found`);
  return cell;
}

describe('SortableTable — signal cells desktop layout (shared properties)', () => {
  it('.signal-hot cell has text-align: center', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).textAlign).toBe('center');
  });

  it('.signal-hot cell has font-weight: bold (700)', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).fontWeight).toBe('700');
  });

  it('.signal-hot cell has white-space: nowrap', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).whiteSpace).toBe('nowrap');
  });

  it('.signal-watch cell has text-align: center', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-watch');
    expect(window.getComputedStyle(cell).textAlign).toBe('center');
  });

  it('.signal-avoid cell has text-align: center', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-avoid');
    expect(window.getComputedStyle(cell).textAlign).toBe('center');
  });
});

describe('SortableTable — signal cells desktop border colour (per-signal)', () => {
  it('.signal-hot cell border-left uses --color-signal-hot', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).borderLeftColor).toBe(tokenRgb('--color-signal-hot'));
  });

  it('.signal-watch cell border-left uses --color-signal-watch', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-watch');
    expect(window.getComputedStyle(cell).borderLeftColor).toBe(tokenRgb('--color-signal-watch'));
  });

  it('.signal-avoid cell border-left uses --color-signal-avoid', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-avoid');
    expect(window.getComputedStyle(cell).borderLeftColor).toBe(tokenRgb('--color-signal-avoid'));
  });

  it('.signal-hot cell has a background gradient', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).backgroundImage).toContain('gradient');
  });

  it('.signal-watch cell has a background gradient', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-watch');
    expect(window.getComputedStyle(cell).backgroundImage).toContain('gradient');
  });

  it('.signal-avoid cell has a background gradient', () => {
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-avoid');
    expect(window.getComputedStyle(cell).backgroundImage).toContain('gradient');
  });
});

describe('SortableTable — signal cells mobile card layout (≤768px)', () => {
  afterEach(async () => {
    await page.viewport(1280, 720);
  });

  it('.signal-hot cell has border-radius on mobile', async () => {
    await page.viewport(390, 844);
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    const radius = parseFloat(window.getComputedStyle(cell).borderRadius);
    expect(radius).toBeGreaterThan(0);
  });

  it('.signal-hot cell uses full border (all sides) on mobile, not just left', async () => {
    await page.viewport(390, 844);
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    const style = window.getComputedStyle(cell);
    // All four sides should have the same width (2px) — not just the left.
    expect(style.borderTopWidth).toBe('2px');
    expect(style.borderRightWidth).toBe('2px');
    expect(style.borderBottomWidth).toBe('2px');
    expect(style.borderLeftWidth).toBe('2px');
  });

  it('.signal-hot cell border-color uses --color-signal-hot on mobile', async () => {
    await page.viewport(390, 844);
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-hot');
    expect(window.getComputedStyle(cell).borderTopColor).toBe(tokenRgb('--color-signal-hot'));
  });

  it('.signal-watch cell border-color uses --color-signal-watch on mobile', async () => {
    await page.viewport(390, 844);
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-watch');
    expect(window.getComputedStyle(cell).borderTopColor).toBe(tokenRgb('--color-signal-watch'));
  });

  it('.signal-avoid cell border-color uses --color-signal-avoid on mobile', async () => {
    await page.viewport(390, 844);
    const { container } = renderSignalTable();
    const cell = getSignalCell(container, 'signal-avoid');
    expect(window.getComputedStyle(cell).borderTopColor).toBe(tokenRgb('--color-signal-avoid'));
  });
});
