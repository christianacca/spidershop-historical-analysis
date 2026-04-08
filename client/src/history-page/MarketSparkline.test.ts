import { render, fireEvent } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
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

describe('MarketSparkline', () => {
  it('renders both polylines when showPrior is true', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const polylines = container.querySelectorAll('svg polyline');
    expect(polylines.length).toBe(2);
  });

  it('renders only one polyline when showPrior is false', () => {
    const { container } = render(MarketSparkline, defaultProps({ showPrior: false, priorSeries: [] }));
    const polylines = container.querySelectorAll('svg polyline');
    expect(polylines.length).toBe(1);
  });

  it('fires onRunSelect with the clicked run index', async () => {
    const onRunSelect = vi.fn();
    const { container } = render(MarketSparkline, defaultProps({ onRunSelect }));
    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[3]);
    expect(onRunSelect).toHaveBeenCalledWith(3);
  });

  it('fires onRunSelect(null) when clicking already-selected run', async () => {
    const onRunSelect = vi.fn();
    const { container } = render(MarketSparkline, defaultProps({ selectedRun: 3, onRunSelect }));
    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[3]);
    expect(onRunSelect).toHaveBeenCalledWith(null);
  });

  it('assigns larger radius to selected point and .is-subdued to others', () => {
    const { container } = render(MarketSparkline, defaultProps({ selectedRun: 5 }));
    // Circles with large radius on current series
    const largeCurrent = container.querySelectorAll('[r="4.4"]');
    expect(largeCurrent.length).toBeGreaterThanOrEqual(1);
    // Subdued class applied to non-selected current series points
    const subdued = container.querySelectorAll('.is-subdued');
    expect(subdued.length).toBe(11); // 11 of 12 current points subdued
  });

  it('renders baseline axis line', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const baseline = container.querySelector('.sparkline-baseline');
    expect(baseline).toBeTruthy();
  });

  it('renders three run-axis labels', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect(labels.length).toBe(3);
    expect(labels[0].textContent).toBe('Run 1');
    expect(labels[1].textContent).toBe('Run 6');
    expect(labels[2].textContent).toBe('Run 12');
  });
});

describe('MarketSparkline — SVG geometry (spec §4.1 / mock dimensions)', () => {
  it('SVG viewBox is "0 0 268 82" matching mock dimensions', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const svg = container.querySelector('svg') as SVGElement;
    expect(svg.getAttribute('viewBox')).toBe('0 0 268 82');
  });

  it('SVG width attribute is "100%" for responsive scaling', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const svg = container.querySelector('svg') as SVGElement;
    expect(svg.getAttribute('width')).toBe('100%');
  });

  it('first data point x starts at left padding (x = 14)', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const points = container.querySelectorAll('circle.sparkline-point-current');
    const cx = parseFloat((points[0] as SVGCircleElement).getAttribute('cx')!);
    expect(cx).toBe(14);
  });

  it('last data point x ends at right padding edge (x = 254 = 268 − 14)', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const points = container.querySelectorAll('circle.sparkline-point-current');
    const cx = parseFloat((points[11] as SVGCircleElement).getAttribute('cx')!);
    expect(cx).toBe(254);
  });

  it('run-axis label font-size is 10 matching mock CSS .sparkline-run-labels', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect((labels[0] as SVGTextElement).getAttribute('font-size')).toBe('10');
    expect((labels[1] as SVGTextElement).getAttribute('font-size')).toBe('10');
    expect((labels[2] as SVGTextElement).getAttribute('font-size')).toBe('10');
  });

  it('prior polyline stroke-dasharray is "5 4" matching mock', () => {
    const { container } = render(MarketSparkline, defaultProps());
    const priorLine = container.querySelector('polyline.sparkline-prior') as SVGPolylineElement;
    expect(priorLine.getAttribute('stroke-dasharray')).toBe('5 4');
  });
});

describe('MarketSparkline — y-coordinate placement', () => {
  // Without prior: series range [170..184], CHART_H=54, TOP_PAD=10
  // max (184) → y = 10 (TOP_PAD);  min (170) → y = 10 + 54 = 64 (BASELINE_Y)

  it('maximum-value point sits at TOP_PAD (y = 10)', () => {
    const { container } = render(MarketSparkline, defaultProps({ showPrior: false, priorSeries: [] }));
    const points = container.querySelectorAll('circle.sparkline-point-current');
    // SERIES[11] = 184 = max
    const cy = parseFloat((points[11] as SVGCircleElement).getAttribute('cy')!);
    expect(cy).toBe(10);
  });

  it('minimum-value point sits at BASELINE_Y (y = 64 = TOP_PAD + CHART_H)', () => {
    const { container } = render(MarketSparkline, defaultProps({ showPrior: false, priorSeries: [] }));
    const points = container.querySelectorAll('circle.sparkline-point-current');
    // SERIES[0] = 170 = min
    const cy = parseFloat((points[0] as SVGCircleElement).getAttribute('cy')!);
    expect(cy).toBe(64);
  });

  it('flat series at constant 100% renders at TOP_PAD (y = 10), not at baseline', () => {
    // Edge case that broke prior-line visibility: old yAt() placed flat max-value at BASELINE_Y
    const flat = Array(12).fill(100) as number[];
    const { container } = render(MarketSparkline, defaultProps({
      series: flat, priorSeries: [], showPrior: false,
    }));
    const points = container.querySelectorAll('circle.sparkline-point-current');
    const cy = parseFloat((points[0] as SVGCircleElement).getAttribute('cy')!);
    expect(cy).toBe(10);
  });

  it('when current and prior are both flat-100%, prior circles are visible (y same as current)', () => {
    // Regression: before Phase 10h, identical flat series placed both lines at BASELINE_Y
    // and the solid current line obscured the prior dashed line entirely.
    const flat = Array(12).fill(100) as number[];
    const { container } = render(MarketSparkline, defaultProps({
      series: flat, priorSeries: flat, showPrior: true,
    }));
    const currPoints  = container.querySelectorAll('circle.sparkline-point-current');
    const priorPoints = container.querySelectorAll('circle.sparkline-point-prior');
    expect(currPoints.length).toBe(12);
    expect(priorPoints.length).toBe(12);
    const currCy  = parseFloat((currPoints[0]  as SVGCircleElement).getAttribute('cy')!);
    const priorCy = parseFloat((priorPoints[0] as SVGCircleElement).getAttribute('cy')!);
    // Both at TOP_PAD — but the dashed prior polyline is still rendered (not at wrong y)
    expect(priorCy).toBe(10);
    expect(currCy).toBe(10);
  });
});
