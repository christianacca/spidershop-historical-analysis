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

// ===========================================================================
// Truncated series (in-progress windows with fewer than 12 runs)
// ===========================================================================

describe('MarketSparkline — truncated series (fewer than 12 runs)', () => {
  // 4-element series simulates a window with only 4 scrape runs
  const SHORT = [10, 20, 15, 25];

  function shortProps(overrides: Record<string, unknown> = {}) {
    return defaultProps({ series: SHORT, priorSeries: [], showPrior: false, ...overrides });
  }

  it('renders exactly n hit areas for a short series', () => {
    const { container } = render(MarketSparkline, shortProps());
    const hitAreas = container.querySelectorAll('.sparkline-hit');
    expect(hitAreas.length).toBe(4);
  });

  it('renders exactly n current-series points for a short series', () => {
    const { container } = render(MarketSparkline, shortProps());
    const points = container.querySelectorAll('circle.sparkline-point-current');
    expect(points.length).toBe(4);
  });

  it('last point x for n=4 is at xAt(3), not xAt(11)', () => {
    // xAt(3) = LEFT_PAD + (3/11) * CHART_W = 14 + (3/11)*240 ≈ 79.45
    // xAt(11) = 14 + 240 = 254
    const { container } = render(MarketSparkline, shortProps());
    const points = container.querySelectorAll('circle.sparkline-point-current');
    const cx = parseFloat((points[3] as SVGCircleElement).getAttribute('cx')!);
    // Should be well left of 254 (the full-width right edge)
    expect(cx).toBeLessThan(254);
    // Should be at xAt(3) = 14 + (3/11)*240
    expect(cx).toBeCloseTo(14 + (3 / 11) * 240, 1);
  });

  it('renders 3 axis labels for n=4 with correct text', () => {
    const { container } = render(MarketSparkline, shortProps());
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect(labels.length).toBe(3);
    // n=4: mid = floor(3/2) = 1 → "Run 1", "Run 2", "Run 4"
    expect(labels[0].textContent).toBe('Run 1');
    expect(labels[1].textContent).toBe('Run 2');
    expect(labels[2].textContent).toBe('Run 4');
  });

  it('axis label x positions for n=4 match xAt(0), xAt(1), xAt(3)', () => {
    const { container } = render(MarketSparkline, shortProps());
    const labels = container.querySelectorAll('.sparkline-run-label');
    const x0 = parseFloat((labels[0] as SVGTextElement).getAttribute('x')!);
    const x1 = parseFloat((labels[1] as SVGTextElement).getAttribute('x')!);
    const x3 = parseFloat((labels[2] as SVGTextElement).getAttribute('x')!);
    expect(x0).toBeCloseTo(14, 1);
    expect(x1).toBeCloseTo(14 + (1 / 11) * 240, 1);
    expect(x3).toBeCloseTo(14 + (3 / 11) * 240, 1);
  });

  it('n=1 renders a single point and a single label "Run 1"', () => {
    const { container } = render(MarketSparkline, shortProps({ series: [42] }));
    const points = container.querySelectorAll('circle.sparkline-point-current');
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect(points.length).toBe(1);
    expect(labels.length).toBe(1);
    expect(labels[0].textContent).toBe('Run 1');
  });

  it('n=2 renders 2 labels "Run 1" and "Run 2"', () => {
    const { container } = render(MarketSparkline, shortProps({ series: [10, 20] }));
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect(labels.length).toBe(2);
    expect(labels[0].textContent).toBe('Run 1');
    expect(labels[1].textContent).toBe('Run 2');
  });

  it('full 12-run series still shows "Run 1", "Run 6", "Run 12" at positions 0, 5, 11', () => {
    // Regression guard: the dynamic label logic must reproduce the original hardcoded output for n=12
    const { container } = render(MarketSparkline, defaultProps());
    const labels = container.querySelectorAll('.sparkline-run-label');
    expect(labels.length).toBe(3);
    expect(labels[0].textContent).toBe('Run 1');
    expect(labels[1].textContent).toBe('Run 6');
    expect(labels[2].textContent).toBe('Run 12');
  });
});
