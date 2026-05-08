import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import HistoryInsightsRoot from './HistoryInsightsRoot.svelte';
import { rawMarketHealthData } from './__fixtures__/marketHealthRaw.js';

describe('HistoryInsightsRoot', () => {
  it('renders MarketHealthSection when rawData has records', () => {
    const { container } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    expect(container.querySelectorAll('.kpi-card').length).toBeGreaterThan(0);
  });

  it('defaults to current-quarter window', () => {
    const { getByText } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    expect(getByText('Current quarter').getAttribute('aria-pressed')).toBe('true');
  });

  it('defaults to all-mode (isAllSelected: true)', () => {
    const { container } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    const heading = container.querySelector('#market-health-heading');
    expect(heading?.textContent).toContain('wider tarantula market');
  });

  it('clicking a window button updates the active window', async () => {
    const { getByText } = render(HistoryInsightsRoot, { rawData: rawMarketHealthData });
    await fireEvent.click(getByText('All time'));
    expect(getByText('All time').getAttribute('aria-pressed')).toBe('true');
    expect(getByText('Current quarter').getAttribute('aria-pressed')).toBe('false');
  });
});
