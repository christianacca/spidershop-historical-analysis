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
