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
    windowScopeLabel: 'current quarter',
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

describe('MarketKpiCard — sparkline shell and box (spec §4.6)', () => {
  it('renders .metric-sparkline-shell wrapper', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    expect(container.querySelector('.metric-sparkline-shell')).toBeTruthy();
  });

  it('.metric-sparkline-shell is a direct child of .kpi-card', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const card = container.querySelector('.kpi-card') as HTMLElement;
    const directChildren = Array.from(card.children).map(el => el.className.replace(/svelte-\w+\s*/g, '').trim());
    expect(directChildren).toContain('metric-sparkline-shell');
  });

  it('renders .metric-sparkline box inside the shell', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const shell = container.querySelector('.metric-sparkline-shell') as HTMLElement;
    expect(shell.querySelector('.metric-sparkline')).toBeTruthy();
  });

  it('sparkline SVG is inside the .metric-sparkline box', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const box = container.querySelector('.metric-sparkline') as HTMLElement;
    expect(box.querySelector('svg')).toBeTruthy();
  });

  it('renders .sparkline-readout below the box', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const shell = container.querySelector('.metric-sparkline-shell') as HTMLElement;
    expect(shell.querySelector('.sparkline-readout')).toBeTruthy();
  });
});

describe('MarketKpiCard — sparkline readout text (spec §4.5)', () => {
  it('no run, showPrior true → shows active window vs prior overlay text', () => {
    const { container } = render(MarketKpiCard, defaultProps());
    const readout = container.querySelector('.sparkline-readout') as HTMLElement;
    expect(readout.textContent).toBe('Observed species shown as active window vs matched prior-period overlay.');
  });

  it('no run, showPrior false → shows all-time scope label text', () => {
    const { container } = render(MarketKpiCard, defaultProps(
      {},
      { showPrior: false, series: { current: SERIES.current, prior: [] }, windowScopeLabel: 'all time' },
    ));
    const readout = container.querySelector('.sparkline-readout') as HTMLElement;
    expect(readout.textContent).toBe('Observed species shown as all time context with no prior-period overlay.');
  });

  it('run selected, showPrior true → shows run N: current vs prior text', () => {
    const { container } = render(MarketKpiCard, defaultProps(
      {},
      { selectedRun: 2 },
    ));
    const readout = container.querySelector('.sparkline-readout') as HTMLElement;
    // Run 3 (index 2): current=173, prior=168
    expect(readout.textContent).toBe('Run 3: 173 current vs 168 matched prior period.');
  });

  it('run selected, showPrior false → shows run N within scope text', () => {
    const { container } = render(MarketKpiCard, defaultProps(
      {},
      { showPrior: false, selectedRun: 0, series: { current: SERIES.current, prior: [] }, windowScopeLabel: 'all time' },
    ));
    const readout = container.querySelector('.sparkline-readout') as HTMLElement;
    // Run 1 (index 0): current=170
    expect(readout.textContent).toBe('Run 1: 170 within all time, with no prior-period overlay.');
  });

  it('stock card formats values with % suffix in readout', () => {
    const stockSeries: SparklineSeries = {
      current: [67, 66, 66, 65, 64, 63, 63, 62, 62, 61, 61, 61],
      prior: [69, 68, 68, 67, 67, 66, 66, 65, 65, 65, 65, 65],
    };
    const { container } = render(MarketKpiCard, {
      card: makeCard({ id: 'stock', title: 'In-stock rate' }),
      series: stockSeries,
      showPrior: true,
      selectedRun: 0,
      onRunSelect: vi.fn(),
      windowScopeLabel: 'current quarter',
    });
    const readout = container.querySelector('.sparkline-readout') as HTMLElement;
    // Run 1 (index 0): current=67%, prior=69%
    expect(readout.textContent).toBe('Run 1: 67% current vs 69% matched prior period.');
  });
});
