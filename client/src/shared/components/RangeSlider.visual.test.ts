/**
 * RangeSlider — browser-backed visual contracts. (Phase 6, step 38)
 *
 * Verifies that label text, range value display, and current-value strip
 * resolve their colours from the correct CSS design tokens.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import { vi } from 'vitest';
import { tokenRgb } from '../../test-utils/token-colors';
import RangeSlider from './RangeSlider.svelte';

describe('RangeSlider — label and text colours', () => {
  it('label color uses --color-primary token', () => {
    const { container } = render(RangeSlider, {
      min: 0, max: 100, label: 'Price Range', onchange: vi.fn(),
    });
    const label = container.querySelector('.label') as HTMLElement;
    expect(window.getComputedStyle(label).color).toBe(tokenRgb('--color-primary'));
  });

  it('slider value text uses --color-text-muted token', () => {
    const { container } = render(RangeSlider, {
      min: 0, max: 100, label: 'Price Range', onchange: vi.fn(),
    });
    const values = container.querySelector('.slider-values') as HTMLElement;
    expect(window.getComputedStyle(values).color).toBe(tokenRgb('--color-text-muted'));
  });

  it('slider current display uses --color-primary token', () => {
    const { container } = render(RangeSlider, {
      min: 0, max: 100, label: 'Price Range', onchange: vi.fn(),
    });
    const current = container.querySelector('.slider-current') as HTMLElement;
    expect(window.getComputedStyle(current).color).toBe(tokenRgb('--color-primary'));
  });
});
