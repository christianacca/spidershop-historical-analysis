import { render } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import HistoryInsightsRoot from './HistoryInsightsRoot.svelte';
import { rawMarketHealthData } from './__fixtures__/marketHealthRaw.js';

describe('HistoryInsightsRoot', () => {
  it('renders MarketHealthSection when rawData has records', () => {
    const { container } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    expect(container.querySelectorAll('.kpi-card').length).toBeGreaterThan(0);
  });

  it('defaults to current-quarter window', () => {
    const { container } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    // sparklineBasisNote is rendered in .sparkline-basis-note by MarketHealthSection
    const basisNote = container.querySelector('.sparkline-basis-note');
    expect(basisNote?.textContent).toContain('Q2');
  });

  it('defaults to all-mode (isAllSelected: true)', () => {
    const { container } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    const heading = container.querySelector('#market-health-heading');
    expect(heading?.textContent).toContain('wider tarantula market');
  });

  it('payload windowId changes when initialWindowId prop differs', () => {
    const { container } = render(HistoryInsightsRoot, {
      rawData: rawMarketHealthData,
      initialWindowId: 'all-time',
    });
    // all-time window has showPrior = false; the prior legend swatch is hidden
    const priorKey = container.querySelector('.legend-prior-key') as HTMLElement | null;
    expect(priorKey).not.toBeNull();
    expect(priorKey?.hidden).toBe(true);
  });
});
