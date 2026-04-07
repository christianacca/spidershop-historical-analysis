/**
 * MarketHealthSection — browser-backed visual contracts.
 *
 * Phase 10 gap verification:
 * - G10.1: Section header background must NOT be dark navy (caused by <header> element conflict)
 * - G10.4: Section header must be a flex row, not stacked
 * - G10.5: Eyebrow must be a pill shape (border-radius: 999px)
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import MarketHealthSection from './MarketHealthSection.svelte';
import type { MarketHealthPayload } from './types.js';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';

function defaultProps(overrides: Partial<{ payload: MarketHealthPayload; initialSelectedRun: number }> = {}) {
  return {
    payload: marketHealthCurrentQuarter,
    ...overrides,
  };
}

describe('MarketHealthSection — G10.1 header background', () => {
  it('section header background is NOT dark navy (not rgb(44, 62, 80))', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const header = container.querySelector('.section-header') as HTMLElement;
    const bg = window.getComputedStyle(header).backgroundColor;
    // Dark navy = rgb(44, 62, 80) — this must not appear (caused by <header> element)
    expect(bg).not.toBe('rgb(44, 62, 80)');
  });
});

describe('MarketHealthSection — G10.4 flex row layout', () => {
  it('section header has flex-direction: row', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const header = container.querySelector('.section-header') as HTMLElement;
    const flexDir = window.getComputedStyle(header).flexDirection;
    expect(flexDir).toBe('row');
  });
});

describe('MarketHealthSection — G10.5 eyebrow pill', () => {
  it('eyebrow has border-radius 999px (pill shape)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const eyebrow = container.querySelector('.section-eyebrow') as HTMLElement;
    const radius = window.getComputedStyle(eyebrow).borderRadius;
    // 999px may be resolved to a pixel value; check it is very large
    const numericValue = parseFloat(radius);
    expect(numericValue).toBeGreaterThanOrEqual(999);
  });
});
