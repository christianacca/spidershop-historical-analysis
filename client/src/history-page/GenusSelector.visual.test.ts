/**
 * GenusSelector — browser-backed visual contracts (P3-5).
 *
 * Verifies computed styles for key elements:
 * - .chip.selected background and border-color (warm orange tint)
 * - .scope-label background (teal tint)
 */
import { render } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import GenusSelector from './GenusSelector.svelte';

function defaultProps(overrides: Partial<{
  availableGenera: string[];
  selectedGenera: string[];
  isAllSelected: boolean;
  mostObservedGenera: string[];
  onSelectionChange: (genera: string[], isAll: boolean) => void;
  initialExpanded: boolean;
}> = {}) {
  return {
    availableGenera: ['Avicularia', 'Caribena', 'Grammostola'],
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: ['Avicularia'],
    onSelectionChange: vi.fn(),
    ...overrides,
  };
}

describe('GenusSelector — .chip.selected computed styles', () => {
  it('.chip.selected backgroundColor is rgba(204, 107, 73, 0.14)', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    }));
    const chip = container.querySelector('.chip.selected') as HTMLElement;
    expect(chip).not.toBeNull();
    const bg = window.getComputedStyle(chip).backgroundColor;
    // rgba(204, 107, 73, 0.14) — browsers may render with varying decimal precision
    expect(bg).toMatch(/rgba\(204,\s*107,\s*73,\s*0\.14\)/);
  });

  it('.chip.selected borderColor is rgba(204, 107, 73, 0.28)', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    }));
    const chip = container.querySelector('.chip.selected') as HTMLElement;
    expect(chip).not.toBeNull();
    const borderColor = window.getComputedStyle(chip).borderTopColor;
    expect(borderColor).toMatch(/rgba\(204,\s*107,\s*73,\s*0\.28\)/);
  });
});

describe('GenusSelector — .scope-label computed styles', () => {
  it('.scope-label backgroundColor is rgba(31, 122, 107, 0.12)', () => {
    const { container } = render(GenusSelector, defaultProps());
    const label = container.querySelector('.scope-label') as HTMLElement;
    expect(label).not.toBeNull();
    const bg = window.getComputedStyle(label).backgroundColor;
    expect(bg).toMatch(/rgba\(31,\s*122,\s*107,\s*0\.12\)/);
  });
});


