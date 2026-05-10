/**
 * FiltersPanel — browser-backed visual contracts (P4-3).
 *
 * Verifies computed styles for:
 * - .scope-label background and colour (teal tint)
 * - .filters-panel display: grid
 * - .panel-heading marginBottom is 4px (overrides global h2 20px)
 * - At mobile viewport (390×844): card chrome is stripped
 * - At mobile viewport: .scope-label white-space is "normal" and border-radius is 12px
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
import { render } from '@testing-library/svelte';
import FiltersPanel from './FiltersPanel.svelte';

function defaultProps(overrides: Partial<{
  isAllSelected: boolean;
  selectedGenera: string[];
  windowLabel: string;
  scopeLabel: string;
}> = {}) {
  return {
    availableGenera: ['Avicularia', 'Caribena', 'Grammostola'],
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: ['Avicularia'],
    windowId: 'current-quarter' as import('./types.js').WindowId,
    basisNote: 'Quarter in progress.',
    windowLabel: 'Current quarter',
    scopeLabel: '',
    onSelectionChange: vi.fn(),
    onWindowChange: vi.fn(),
    ...overrides,
  };
}

describe('FiltersPanel — .scope-label computed styles', () => {
  it('.scope-label backgroundColor is rgba(31, 122, 107, 0.12)', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const label = container.querySelector('.scope-label') as HTMLElement;
    expect(label).not.toBeNull();
    const bg = window.getComputedStyle(label).backgroundColor;
    expect(bg).toMatch(/rgba\(31,\s*122,\s*107,\s*0\.12\)/);
  });

  it('.scope-label color resolves to rgb(31, 122, 107)', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const label = container.querySelector('.scope-label') as HTMLElement;
    expect(label).not.toBeNull();
    const color = window.getComputedStyle(label).color;
    expect(color).toBe('rgb(31, 122, 107)');
  });
});

describe('FiltersPanel — .filters-panel layout', () => {
  it('.filters-panel display is "grid"', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    expect(panel).not.toBeNull();
    expect(window.getComputedStyle(panel).display).toBe('grid');
  });

  it('.panel-heading marginBottom is 0px', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const heading = container.querySelector('.panel-heading') as HTMLElement;
    expect(heading).not.toBeNull();
    expect(window.getComputedStyle(heading).marginBottom).toBe('0px');
  });
});

describe('FiltersPanel — mobile viewport (390×844)', () => {
  afterEach(async () => {
    await page.viewport(1280, 720);
  });

  it('.filters-panel card chrome is stripped (background transparent) at 390px', async () => {
    await page.viewport(390, 844);
    const { container } = render(FiltersPanel, defaultProps());
    const panel = container.querySelector('.filters-panel') as HTMLElement;
    const bg = window.getComputedStyle(panel).backgroundColor;
    // rgba(0,0,0,0) is the computed value for background: none / transparent
    expect(bg).toMatch(/rgba\(0,\s*0,\s*0,\s*0\)|transparent/);
  });

  it('.scope-label white-space is "normal" at 390px', async () => {
    await page.viewport(390, 844);
    const { container } = render(FiltersPanel, defaultProps());
    const label = container.querySelector('.scope-label') as HTMLElement;
    expect(window.getComputedStyle(label).whiteSpace).toBe('normal');
  });

  it('.scope-label border-radius is 12px at 390px', async () => {
    await page.viewport(390, 844);
    const { container } = render(FiltersPanel, defaultProps());
    const label = container.querySelector('.scope-label') as HTMLElement;
    expect(window.getComputedStyle(label).borderRadius).toBe('12px');
  });
});
