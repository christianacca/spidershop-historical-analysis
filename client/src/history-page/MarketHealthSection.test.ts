import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MarketHealthSection from './MarketHealthSection.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';
import { marketHealthAllTime } from './__fixtures__/marketHealth.allTime.js';

describe('MarketHealthSection', () => {
  it('renders all 4 KPI cards with currentQuarter fixture', () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });
    expect(container.querySelectorAll('.kpi-card')).toHaveLength(4);
  });

  it('prior legend key is visible when showPrior is true', () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });
    const priorKey = container.querySelector('.legend-prior-key');
    expect(priorKey).toBeTruthy();
    expect((priorKey as HTMLElement).hidden).toBe(false);
  });

  it('prior legend key is hidden when showPrior is false', () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthAllTime,
    });
    const priorKey = container.querySelector('.legend-prior-key');
    expect(priorKey).toBeTruthy();
    expect((priorKey as HTMLElement).hidden).toBe(true);
  });

  it('selection note updates when a run is clicked', async () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });

    // Click the hit area at run index 5 in the first sparkline
    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[5]);

    const note = container.querySelector('.pulse-selection-note');
    expect(note?.textContent).toContain('Run 6 selected.');
    expect(note?.textContent).toContain('The same moment is now highlighted across all four KPI cards.');
  });

  it('clicking the same run again resets selection', async () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });

    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[5]);
    await fireEvent.click(hitAreas[5]);

    const note = container.querySelector('.pulse-selection-note');
    expect(note?.textContent).toContain('Optional: click a run');

    const clearBtn = container.querySelector<HTMLElement>('.clear-run-btn');
    expect(clearBtn?.hidden).toBe(true);
  });

  it('clear button resets selection when clicked', async () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });

    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[3]);

    const clearBtn = container.querySelector<HTMLElement>('.clear-run-btn');
    expect(clearBtn?.hidden).toBe(false);
    await fireEvent.click(clearBtn!);

    const note = container.querySelector('.pulse-selection-note');
    expect(note?.textContent).toContain('Optional: click a run');
    expect(container.querySelector<HTMLElement>('.clear-run-btn')?.hidden).toBe(true);
  });

  it('initialSelectedRun seeds the selection state', () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
      initialSelectedRun: 8,
    });

    const note = container.querySelector('.pulse-selection-note');
    expect(note?.textContent).toContain('Run 9 selected.');

    const clearBtn = container.querySelector<HTMLElement>('.clear-run-btn');
    expect(clearBtn?.hidden).toBe(false);
  });

  it('selectedRun propagates to all 4 sparklines', async () => {
    const { container } = render(MarketHealthSection, {
      payload: marketHealthCurrentQuarter,
    });

    const hitAreas = container.querySelectorAll('.sparkline-hit');
    await fireEvent.click(hitAreas[5]);

    // 11 subdued circles per card × 4 cards = 44
    const subdued = container.querySelectorAll('.is-subdued');
    expect(subdued).toHaveLength(44);
  });
});
