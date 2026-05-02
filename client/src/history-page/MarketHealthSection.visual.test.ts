/**
 * MarketHealthSection — browser-backed visual contracts.
 *
 * Phase 10 gap verification:
 * - G10.1: Section header background must NOT be dark navy (caused by <header> element conflict)
 * - G10.4: Section header must be a flex row (desktop), column (mobile ≤ 480 px)
 * - G10.5: Eyebrow must be a pill shape (border-radius: 999px)
 *
 * Phase 13: mobile responsive contracts
 * - At ≤ 480 px: section header stacks vertically (flex-direction: column)
 * - At > 480 px: 2-column or 4-column KPI grid (flex-direction: row)
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
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
  afterEach(async () => {
    // Restore a wide desktop viewport after any viewport-sensitive test.
    await page.viewport(1280, 720);
  });

  it('section header has flex-direction: row at desktop viewport (> 480 px)', async () => {
    await page.viewport(1280, 720);
    const { container } = render(MarketHealthSection, defaultProps());
    const header = container.querySelector('.section-header') as HTMLElement;
    const flexDir = window.getComputedStyle(header).flexDirection;
    expect(flexDir).toBe('row');
  });

  it('section header stacks vertically at mobile viewport (≤ 480 px)', async () => {
    await page.viewport(390, 844);
    const { container } = render(MarketHealthSection, defaultProps());
    const header = container.querySelector('.section-header') as HTMLElement;
    const flexDir = window.getComputedStyle(header).flexDirection;
    expect(flexDir).toBe('column');
  });

  it('kpi-grid is single-column at mobile viewport (≤ 480 px)', async () => {
    await page.viewport(390, 844);
    const { container } = render(MarketHealthSection, defaultProps());
    const grid = container.querySelector('.kpi-grid') as HTMLElement;
    const cols = window.getComputedStyle(grid).gridTemplateColumns;
    // Single column resolves to exactly one track value
    const trackCount = cols.trim().split(/\s+/).length;
    expect(trackCount).toBe(1);
  });

  it('kpi-grid is two-column at tablet viewport (481–760 px)', async () => {
    await page.viewport(600, 900);
    const { container } = render(MarketHealthSection, defaultProps());
    const grid = container.querySelector('.kpi-grid') as HTMLElement;
    const cols = window.getComputedStyle(grid).gridTemplateColumns;
    // Two equal columns resolve to two track values
    const trackCount = cols.trim().split(/\s+/).length;
    expect(trackCount).toBe(2);
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

// ── Typography polish (mock alignment) ───────────────────────────────────────
// These tests codify the differences identified between the mock and actual:
// - Section container must have a non-transparent background (warm surface)
// - Section container border must be warm sand, not cold grey
// - Section note must NOT be italic

describe('MarketHealthSection — section container card style (mock §2 alignment)', () => {
  it('section container has a non-transparent background (elevated warm-white surface card)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const section = container.querySelector('.market-health-section') as HTMLElement;
    const bg = window.getComputedStyle(section).backgroundColor;
    // --color-surface = #fffaf2 warm white — section is elevated above the page bg
    // KPI cards get box-shadow to pop off this surface
    expect(bg).not.toBe('rgba(0, 0, 0, 0)');
    expect(bg).toBe('rgb(255, 250, 242)');
  });

  it('section container border is warm sand (not cold grey #ddd)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const section = container.querySelector('.market-health-section') as HTMLElement;
    const borderColor = window.getComputedStyle(section).borderTopColor;
    // Cold grey #ddd = rgb(221, 221, 221) — must NOT be that
    expect(borderColor).not.toBe('rgb(221, 221, 221)');
    // Warm sand --color-border-warm = #d7cfc0 = rgb(215, 207, 192)
    expect(borderColor).toBe('rgb(215, 207, 192)');
  });

  it('section container has a visible box-shadow (card elevation)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const section = container.querySelector('.market-health-section') as HTMLElement;
    const shadow = window.getComputedStyle(section).boxShadow;
    // Must not be 'none' — the section card should have elevation
    expect(shadow).not.toBe('none');
    expect(shadow).not.toBe('');
  });
});

describe('MarketHealthSection — section note typography (mock §2.1)', () => {
  it('section note is NOT italic (mock uses regular weight)', () => {
    const { container } = render(MarketHealthSection, defaultProps());
    const note = container.querySelector('.section-note') as HTMLElement;
    const fontStyle = window.getComputedStyle(note).fontStyle;
    expect(fontStyle).not.toBe('italic');
    expect(fontStyle).toBe('normal');
  });
});
