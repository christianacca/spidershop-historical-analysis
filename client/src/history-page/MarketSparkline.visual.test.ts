/**
 * MarketSparkline — browser-backed visual contracts.
 *
 * Verifies that the prior series polyline opacity resolves to 0.38 (spec §4.1)
 * and that the .is-subdued class resolves to opacity 0.16 (spec §4.2).
 * These require a real browser because happy-dom doesn't compute CSS classes
 * to opacity values reliably.
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import MarketSparkline from './MarketSparkline.svelte';

const SERIES = [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184];
const PRIOR  = [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177];

function defaultProps(overrides: Record<string, unknown> = {}) {
  return {
    series: SERIES,
    priorSeries: PRIOR,
    showPrior: true,
    color: '#1f7a6b',
    formatValue: (v: number) => String(v),
    selectedRun: null as number | null,
    onRunSelect: vi.fn(),
    ...overrides,
  };
}

describe('MarketSparkline — prior series opacity', () => {
  it('prior polyline has opacity 0.38 per spec §4.1', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const priorLine = container.querySelector('polyline.sparkline-prior') as SVGElement;
    const opacity = parseFloat(window.getComputedStyle(priorLine).opacity);
    expect(opacity).toBeCloseTo(0.38, 2);
  });

  it('prior circle elements have opacity 0.45 per spec §4.1', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const priorCircles = container.querySelectorAll('circle.sparkline-point-prior');
    expect(priorCircles.length).toBe(12);
    const opacity = parseFloat(window.getComputedStyle(priorCircles[0] as Element).opacity);
    expect(opacity).toBeCloseTo(0.45, 2);
  });
});

describe('MarketSparkline — run selection subdued opacity', () => {
  it('.is-subdued elements have opacity 0.16 per spec §4.2', () => {
    const { container } = render(MarketSparkline, defaultProps({ selectedRun: 5 }));
    const subduedCircles = container.querySelectorAll('.is-subdued');
    expect(subduedCircles.length).toBe(11);
    const opacity = parseFloat(window.getComputedStyle(subduedCircles[0] as Element).opacity);
    expect(opacity).toBeCloseTo(0.16, 2);
  });
});
