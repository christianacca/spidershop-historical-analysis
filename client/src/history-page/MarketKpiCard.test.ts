import { render, fireEvent } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import MarketKpiCard from './MarketKpiCard.svelte';
import type { KpiCardData, SparklineSeries } from './types.js';

const SERIES: SparklineSeries = {
  current: [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184],
  prior:   [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177],
};

function makeCard(overrides: Partial<KpiCardData> = {}): KpiCardData {
  return {
    id: 'observed',
    title: 'Observed species',
    value: '184',
    delta: '+7 vs prior quarter QTD',
    deltaClass: '',
    copy: 'Breadth is ahead.',
    ...overrides,
  };
}

function defaultProps(cardOverrides: Partial<KpiCardData> = {}, extraProps: Record<string, unknown> = {}) {
  return {
    card: makeCard(cardOverrides),
    series: SERIES,
    showPrior: true,
    selectedRun: null as number | null,
    onRunSelect: vi.fn(),
    ...extraProps,
  };
}

describe('MarketKpiCard', () => {
  it('renders the card title', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('h3')?.textContent).toContain('Observed species');
  });

  it('renders the metric value', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('.metric-value')?.textContent).toContain('184');
  });

  it('renders the copy sentence', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('.kpi-copy')?.textContent).toContain('Breadth is ahead.');
  });

  it('delta class "" → .metric-delta has no modifier class', () => {
    const { container } = render(MarketKpiCard, defaultProps({ deltaClass: '' }));
    const badge = container.querySelector('.metric-delta') as HTMLElement;
    expect(badge).toBeTruthy();
    expect(badge.classList.contains('down')).toBe(false);
    expect(badge.classList.contains('flat')).toBe(false);
  });

  it('delta class "down" → .metric-delta.down in DOM', () => {
    const { container } = render(MarketKpiCard, defaultProps({ deltaClass: 'down' }));
    expect(container.querySelector('.metric-delta.down')).toBeTruthy();
  });

  it('delta class "flat" → .metric-delta.flat in DOM', () => {
    const { container } = render(MarketKpiCard, defaultProps({ deltaClass: 'flat' }));
    expect(container.querySelector('.metric-delta.flat')).toBeTruthy();
  });

  it('showPrior false → sparkline receives showPrior false (only 1 polyline)', () => {
    const { container } = render(MarketKpiCard, defaultProps(
      {},
      { showPrior: false, series: { current: SERIES.current, prior: [] } },
    ));
    expect(container.querySelectorAll('svg polyline').length).toBe(1);
  });

  it('forwards onRunSelect to the sparkline hit areas', async () => {
    const onRunSelect = vi.fn();
    const { container } = render(MarketKpiCard, defaultProps({}, { onRunSelect }));
    const hit = container.querySelector('.sparkline-hit') as Element;
    await fireEvent.click(hit);
    expect(onRunSelect).toHaveBeenCalled();
  });
});

describe('MarketKpiCard — ? info button (gap 5)', () => {
  it('each card contains a details.metric-info element', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('details.metric-info')).toBeTruthy();
  });

  it('summary has aria-label containing the card title', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const summary = container.querySelector('details.metric-info summary') as HTMLElement;
    expect(summary).toBeTruthy();
    expect(summary.getAttribute('aria-label')).toContain('Observed species');
  });

  it('summary text is "?"', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const summary = container.querySelector('details.metric-info summary') as HTMLElement;
    expect(summary.textContent?.trim()).toBe('?');
  });

  it('popover contains the tooltip text for the observed KPI', () => {
    const { container } = render(MarketKpiCard, defaultProps({ id: 'observed' }));
    const popover = container.querySelector('.metric-popover') as HTMLElement;
    expect(popover).toBeTruthy();
    expect(popover.textContent).toContain('distinct species');
  });

  it('popover contains the tooltip text for the stock KPI', () => {
    const { container } = render(MarketKpiCard, defaultProps({ id: 'stock' }));
    const popover = container.querySelector('.metric-popover') as HTMLElement;
    expect(popover.textContent).toContain('in-stock at the most recent run');
  });

  it('metric-title-row wraps both the h3 and the info button', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const titleRow = container.querySelector('.metric-title-row') as HTMLElement;
    expect(titleRow.querySelector('h3')).toBeTruthy();
    expect(titleRow.querySelector('details.metric-info')).toBeTruthy();
  });
});

describe('MarketKpiCard — card layout structure', () => {
  it('metric-value is NOT wrapped in a kpi-value-row element', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('.kpi-value-row')).toBeNull();
  });

  it('metric-value and metric-delta are direct children of kpi-card', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const directChildren = Array.from(card.children).map(el => el.className.replace(/svelte-\w+\s*/g, '').trim());
    expect(directChildren).toContain('metric-value');
    expect(directChildren.some(c => c.startsWith('metric-delta'))).toBe(true);
  });
});
