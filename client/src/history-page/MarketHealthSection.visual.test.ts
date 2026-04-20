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

describe('MarketHealthSection — Gap 3: clear-run button pill shape', () => {
  it('clear-run button has pill border-radius (999px)', () => {
    const { container } = render(MarketHealthSection, defaultProps({ initialSelectedRun: 0 }));
    const btn = container.querySelector('.clear-run-btn') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(btn).borderRadius);
    expect(radius).toBeGreaterThanOrEqual(999);
  });
});

describe('MarketHealthSection — sparkline support card shape (mock §4 legend area)', () => {
  it('support card has a card border (not hairlines)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const card = container.querySelector('.sparkline-support-card') as HTMLElement;
    const style = window.getComputedStyle(card);
    // Full card box — border must not be "none" or "0px"
    expect(style.borderTopWidth).toBe('1px');
    expect(style.borderRightWidth).toBe('1px');
    expect(style.borderBottomWidth).toBe('1px');
    expect(style.borderLeftWidth).toBe('1px');
  });

  it('support card has rounded card corners', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const card = container.querySelector('.sparkline-support-card') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(card).borderRadius);
    // Must be a card shape (≥14px), not hairline separator (0px)
    expect(radius).toBeGreaterThanOrEqual(14);
  });

  it('support card has translucent white background', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const card = container.querySelector('.sparkline-support-card') as HTMLElement;
    const bg = window.getComputedStyle(card).backgroundColor;
    // rgba(255,255,255,0.54) — must contain white channel, not transparent black
    expect(bg).toContain('255, 255, 255');
  });

  it('basis note is on a separate line below the legend row (column layout)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const card = container.querySelector('.sparkline-support-card') as HTMLElement;
    const flexDir = window.getComputedStyle(card).flexDirection;
    // column layout ensures legend row and notes stack vertically
    expect(flexDir).toBe('column');
  });
});

describe('MarketHealthSection — sparkline legend swatches (mock line-swatch spec)', () => {
  it('solid swatch has pill-shaped ends (border-radius ≥ 999px)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const swatch = container.querySelector('.line-swatch:not(.line-swatch--dashed)') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(swatch).borderRadius);
    expect(radius).toBeGreaterThanOrEqual(999);
  });

  it('solid swatch opacity is less than 1 (not fully opaque)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const swatch = container.querySelector('.line-swatch:not(.line-swatch--dashed)') as HTMLElement;
    const opacity = parseFloat(window.getComputedStyle(swatch).opacity);
    expect(opacity).toBeLessThan(1);
    expect(opacity).toBeGreaterThan(0.5); // visually solid, not faded
  });

  it('dashed swatch is significantly more muted than solid swatch', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const solid = container.querySelector('.line-swatch:not(.line-swatch--dashed)') as HTMLElement;
    const dashed = container.querySelector('.line-swatch--dashed') as HTMLElement;
    const solidOpacity = parseFloat(window.getComputedStyle(solid).opacity);
    const dashedOpacity = parseFloat(window.getComputedStyle(dashed).opacity);
    // Dashed must be at most half the opacity of solid (mock: 0.42 vs 0.9)
    expect(dashedOpacity).toBeLessThan(solidOpacity * 0.6);
  });
});

describe('MarketHealthSection — sparkline legend label typography (mock chart-compare-item)', () => {
  it('legend labels are bold (font-weight 700)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const label = container.querySelector('.legend-current-key') as HTMLElement;
    const weight = window.getComputedStyle(label).fontWeight;
    expect(weight).toBe('700');
  });

  it('legend labels are smaller than the base font size (≤ 0.85rem equivalent)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const label = container.querySelector('.legend-current-key') as HTMLElement;
    const size = parseFloat(window.getComputedStyle(label).fontSize);
    // 0.84rem at 16px base = 13.44px; must be less than 14px
    expect(size).toBeLessThan(14);
  });

  it('basis note font size matches label size or smaller', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const label = container.querySelector('.legend-current-key') as HTMLElement;
    const note = container.querySelector('.sparkline-basis-note') as HTMLElement;
    const labelSize = parseFloat(window.getComputedStyle(label).fontSize);
    const noteSize = parseFloat(window.getComputedStyle(note).fontSize);
    expect(noteSize).toBeLessThanOrEqual(labelSize);
  });
});
