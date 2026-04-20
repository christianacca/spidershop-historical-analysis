/**
 * MarketKpiCard — browser-backed visual contracts.
 *
 * Phase 10c gap verification (against docs/ux/history-page/history-kpi-concepts-mockup.html):
 * - Card border-radius 18px (mock) not 16px
 * - Card border warm sand (#d7cfc0)
 * - Card background is a gradient (not solid white)
 * - metric-value font-size 32px (2rem)
 * - metric-info-button 24×24px
 * - metric-info-button closed-state background is white (not teal-tinted)
 * - metric-info-button closed-state color is --color-text-label (not teal)
 * - metric-delta display is inline-flex
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import MarketKpiCard from './MarketKpiCard.svelte';
import type { KpiCardData, SparklineSeries } from './types.js';

const SERIES: SparklineSeries = {
  current: [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184],
  prior:   [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177],
};

function defaultProps(cardOverrides: Partial<KpiCardData> = {}) {
  return {
    card: {
      id: 'observed' as KpiCardData['id'],
      title: 'Observed species',
      value: '184',
      delta: '+7 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Breadth is ahead.',
      ...cardOverrides,
    },
    series: SERIES,
    showPrior: true,
    selectedRun: null as number | null,
    onRunSelect: () => {},
    windowScopeLabel: 'current quarter',
  };
}

describe('MarketKpiCard — card shape (border-radius)', () => {
  it('kpi-card has border-radius 18px (not 16px from --radius-card-lg)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(card).borderRadius);
    expect(radius).toBe(18);
  });
});

describe('MarketKpiCard — card border color (warm sand)', () => {
  it('kpi-card border-color is warm sand rgb(215, 207, 192)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const borderColor = window.getComputedStyle(card).borderTopColor;
    expect(borderColor).toBe('rgb(215, 207, 192)');
  });
});

describe('MarketKpiCard — card background (gradient)', () => {
  it('kpi-card background-image is a gradient (not solid white)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const bgImage = window.getComputedStyle(card).backgroundImage;
    expect(bgImage).toContain('gradient');
  });
});

describe('MarketKpiCard — metric-value size', () => {
  it('metric-value font-size is 32px (2rem)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const value = container.querySelector('.metric-value') as HTMLElement;
    const fontSize = parseFloat(window.getComputedStyle(value).fontSize);
    expect(fontSize).toBe(32);
  });
});

describe('MarketKpiCard — info button size', () => {
  it('metric-info-button is 24×24px', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const btn = container.querySelector('.metric-info-button') as HTMLElement;
    const s = window.getComputedStyle(btn);
    expect(parseFloat(s.width)).toBe(24);
    expect(parseFloat(s.height)).toBe(24);
  });
});

describe('MarketKpiCard — info button closed-state appearance', () => {
  it('metric-info-button background is white (not teal-tinted) when closed', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const btn = container.querySelector('.metric-info-button') as HTMLElement;
    const bg = window.getComputedStyle(btn).backgroundColor;
    // rgb(255, 255, 255) is white — must NOT be teal rgba(31, 122, 107, ...)
    // getComputedStyle resolves rgba(255,255,255,0.9) as rgba(255,255,255,0.9) or rgb(255,255,255)
    expect(bg).not.toContain('31, 122, 107');
  });

  it('metric-info-button color is --color-text-label (not teal) when closed', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const btn = container.querySelector('.metric-info-button') as HTMLElement;
    const color = window.getComputedStyle(btn).color;
    // --color-text-label = #5d6a6d = rgb(93, 106, 109)
    expect(color).toBe('rgb(93, 106, 109)');
  });

  it('details.metric-info has no background or border (global details CSS rule is scoped to explicit classes; must not apply here)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const details = container.querySelector('details.metric-info') as HTMLElement;
    const s = window.getComputedStyle(details);
    expect(s.backgroundColor).toBe('rgba(0, 0, 0, 0)');
    expect(s.borderTopWidth).toBe('0px');
    expect(s.padding).toBe('0px');
  });
});

describe('MarketKpiCard — delta display', () => {
  it('metric-delta is NOT a full-width block (width is fit-content)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const delta = container.querySelector('.metric-delta') as HTMLElement;
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const deltaWidth = parseFloat(window.getComputedStyle(delta).width);
    const cardWidth = parseFloat(window.getComputedStyle(card).width);
    // delta should be noticeably narrower than card (fit-content, not full-width block)
    expect(deltaWidth).toBeLessThan(cardWidth * 0.9);
  });
});

// ── Typography polish (mock alignment) ──────────────────────────────────────
// The mock uses --ink (#1f2a2c) for the big metric number — warm dark,
// not the navy --color-text-heading (#2c3e50).
// Since we updated --color-text to #1f2a2c, metric-value should use --color-text.

describe('MarketKpiCard — metric-value colour (warm dark, not navy)', () => {
  it('metric-value color is warm dark rgb(31, 42, 44), not navy rgb(44, 62, 80)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const value = container.querySelector('.metric-value') as HTMLElement;
    const color = window.getComputedStyle(value).color;
    // Navy (#2c3e50) = rgb(44, 62, 80) — must NOT be that
    expect(color).not.toBe('rgb(44, 62, 80)');
    // Warm dark (#1f2a2c) = rgb(31, 42, 44) — must be that
    expect(color).toBe('rgb(31, 42, 44)');
  });
});

describe('MarketKpiCard — card elevation (box-shadow lifts card off section surface)', () => {
  it('kpi-card has a visible box-shadow (not \'none\')', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const shadow = window.getComputedStyle(card).boxShadow;
    // Card must have elevation so it visually pops off the warm-white section surface
    expect(shadow).not.toBe('none');
    expect(shadow).not.toBe('');
  });
});

describe('MarketKpiCard — sparkline box visual (spec §4.6)', () => {
  it('.metric-sparkline has border-radius 14px', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const box = container.querySelector('.metric-sparkline') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(box).borderRadius);
    expect(radius).toBe(14);
  });

  it('.metric-sparkline border-color is warm sand rgba(215, 207, 192, 0.9)', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const box = container.querySelector('.metric-sparkline') as HTMLElement;
    const borderColor = window.getComputedStyle(box).borderTopColor;
    // Chromium preserves rgba() with alpha channel rather than normalizing to rgb()
    expect(borderColor).toMatch(/rgba?\(215,\s*207,\s*192/);
  });

  it('.metric-sparkline background is a semi-transparent white', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const box = container.querySelector('.metric-sparkline') as HTMLElement;
    const bg = window.getComputedStyle(box).backgroundColor;
    // rgba(255, 255, 255, 0.72) — white channels
    expect(bg).toContain('255, 255, 255');
  });
});
