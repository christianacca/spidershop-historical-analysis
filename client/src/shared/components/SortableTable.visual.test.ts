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

  it('td::before has display: block at mobile viewport (≤ 768 px)', async () => {
    await page.viewport(390, 844);
    const { container } = render(SortableTable, {
      tableId: 'mobile-label-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
    });
    // TEST_COLUMNS have no cardHeader/cardSubheader — all cells show the eyebrow label.
    const td = container.querySelectorAll('tbody td')[0] as HTMLElement;
    expect(td).not.toBeNull();
    const before = window.getComputedStyle(td, '::before');
    expect(before.display).toBe('block');
  });

  it('td[data-card-role="header"]::before has display: none at mobile (header suppresses eyebrow)', async () => {
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

  it('td::before has display: none at desktop viewport (> 768 px)', async () => {
    await page.viewport(1280, 720);
    const { container } = render(SortableTable, {
      tableId: 'desktop-label-test',
      rows: TEST_ROWS,
      columns: TEST_COLUMNS,
    });
    const td = container.querySelectorAll('tbody td')[0] as HTMLElement;
    expect(td).not.toBeNull();
    const before = window.getComputedStyle(td, '::before');
    // At desktop widths (> 768 px) the media-query block does not apply,
    // so ::before has no content and no explicit display → browser default (none or inline).
    // We assert it is NOT block, which is the mobile-only stacked layout.
    expect(before.display).not.toBe('block');
  });
});
