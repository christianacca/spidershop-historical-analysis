/**
 * DateFilter — browser-backed visual contracts. (Phase 6, step 40)
 *
 * Verifies that:
 *   - The date picker is absent when collapsed and present when expanded
 *     (open/closed state chrome).
 *   - The picker section border-top and quick-select bar each resolve their
 *     colour from --color-date-filter (the amber accent for date UI).
 *
 * These token assertions require a real browser — happy-dom cannot resolve
 * CSS custom properties in computed styles.
 */
import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import { tokenRgb } from '../test-utils/token-colors';
import DateFilter from './DateFilter.svelte';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const DATES = ['2026-01-15', '2026-01-08', '2026-01-01'];
const ROW_COUNTS: Record<string, number> = {
  '2026-01-15': 3,
  '2026-01-08': 3,
  '2026-01-01': 3,
};

async function openDatePicker(container: HTMLElement): Promise<void> {
  const btn = container.querySelector<HTMLButtonElement>(
    'button[data-action="toggle-date-picker"]',
  )!;
  await fireEvent.click(btn);
}

// ── Open / closed state ───────────────────────────────────────────────────────

describe('DateFilter — open/closed state', () => {
  it('date picker content is absent when collapsed (default)', () => {
    const { container } = render(DateFilter, {
      dates: DATES, rowCounts: ROW_COUNTS, tableId: 'test', onchange: vi.fn(),
    });
    expect(container.querySelector('.date-picker-content')).toBeNull();
  });

  it('date picker content is present after expanding', async () => {
    const { container } = render(DateFilter, {
      dates: DATES, rowCounts: ROW_COUNTS, tableId: 'test', onchange: vi.fn(),
    });
    await openDatePicker(container);
    expect(container.querySelector('.date-picker-content')).not.toBeNull();
  });
});

// ── Date filter token colours ─────────────────────────────────────────────────

describe('DateFilter — date filter token colours', () => {
  it('date picker border-top uses --color-date-filter token', async () => {
    const { container } = render(DateFilter, {
      dates: DATES, rowCounts: ROW_COUNTS, tableId: 'test', onchange: vi.fn(),
    });
    await openDatePicker(container);
    const content = container.querySelector('.date-picker-content') as HTMLElement;
    expect(window.getComputedStyle(content).borderTopColor).toBe(tokenRgb('--color-date-filter'));
  });

  it('quick-select bar top border uses --color-date-filter token', async () => {
    const { container } = render(DateFilter, {
      dates: DATES, rowCounts: ROW_COUNTS, tableId: 'test', onchange: vi.fn(),
    });
    await openDatePicker(container);
    const bar = container.querySelector('.quick-select-bar') as HTMLElement;
    expect(window.getComputedStyle(bar).borderTopColor).toBe(tokenRgb('--color-date-filter'));
  });
});

// ── Toggle button background in date-filter-section context ───────────────────

describe('DateFilter — expand toggle in date-filter-section context', () => {
  it('expanded toggle background uses --color-date-filter when --toggle-btn-bg is overridden by parent', async () => {
    // HistoryTable wraps DateFilter in a .date-filter-section div that sets
    // --toggle-btn-bg: var(--color-date-filter). This keeps the toggle button
    // amber (date-filter accent) rather than defaulting to --color-accent (blue)
    // when the picker is open. Simulate that context via an inline CSS var.
    const { container } = render(DateFilter, {
      dates: DATES, rowCounts: ROW_COUNTS, tableId: 'test', onchange: vi.fn(),
    });
    (container as HTMLElement).style.setProperty('--toggle-btn-bg', 'var(--color-date-filter)');
    await openDatePicker(container);
    const toggleBtn = container.querySelector<HTMLButtonElement>(
      'button[data-action="toggle-date-picker"]',
    )!;
    expect(window.getComputedStyle(toggleBtn).backgroundColor).toBe(tokenRgb('--color-date-filter'));
  });
});
