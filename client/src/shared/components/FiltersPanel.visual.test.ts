/**
 * FiltersPanel — browser-backed visual contracts. (Phase 6, steps 37 + 42)
 *
 * Step 37: Background and border use the correct design tokens.
 * Step 42: Responsive layout contract — the panel stacks its children
 *          vertically (flex-direction: column) at all viewport widths.
 *
 * The flex-direction contract is meaningful because it prevents a future CSS
 * change from accidentally switching the filters to a horizontal layout,
 * which would break the filter bar on narrow viewports.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import { tokenRgb } from '../../test-utils/token-colors';
import FiltersPanel from './FiltersPanel.svelte';

const testChildren = createRawSnippet(() => ({
  render: () => '<div class="test-content">Filter content</div>',
}));

// ── Container chrome ──────────────────────────────────────────────────────────

describe('FiltersPanel — container chrome', () => {
  it('background uses --color-surface token', () => {
    const { container } = render(FiltersPanel, { children: testChildren });
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    expect(window.getComputedStyle(panel).backgroundColor).toBe(tokenRgb('--color-surface'));
  });

  it('border uses --color-border-light token', () => {
    const { container } = render(FiltersPanel, { children: testChildren });
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    expect(window.getComputedStyle(panel).borderTopColor).toBe(tokenRgb('--color-border-light'));
  });
});

// ── Responsive layout contract (step 42) ─────────────────────────────────────

describe('FiltersPanel — responsive layout', () => {
  it('panel uses flex layout', () => {
    const { container } = render(FiltersPanel, { children: testChildren });
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    expect(window.getComputedStyle(panel).display).toBe('flex');
  });

  it('stacks children vertically (flex-direction: column)', () => {
    const { container } = render(FiltersPanel, { children: testChildren });
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    expect(window.getComputedStyle(panel).flexDirection).toBe('column');
  });
});
