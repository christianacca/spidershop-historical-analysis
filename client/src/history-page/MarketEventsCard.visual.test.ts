/**
 * MarketEventsCard — browser-backed visual contracts.
 *
 * Phase 10b gap verification:
 * - Gap 1: Event tile labels must NOT be uppercase (text-transform: none)
 * - Gap 2: Event tiles must have large card border-radius (~16px), not small radius
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import MarketEventsCard from './MarketEventsCard.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';

const currentEvents = marketHealthCurrentQuarter.events;

describe('MarketEventsCard — Gap 1: event label text-transform', () => {
  it('event labels are NOT uppercase (text-transform: none)', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const label = container.querySelector('.event-label') as HTMLElement;
    const textTransform = window.getComputedStyle(label).textTransform;
    expect(textTransform).toBe('none');
  });
});

describe('MarketEventsCard — Gap 2: event tile border-radius', () => {
  it('event tiles have border-radius matching --radius-card-lg (16px)', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const tile = container.querySelector('.event-tile') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(tile).borderRadius);
    expect(radius).toBe(16);
  });

  it('event tiles have a visible border', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const tile = container.querySelector('.event-tile') as HTMLElement;
    const borderWidth = parseFloat(window.getComputedStyle(tile).borderTopWidth);
    expect(borderWidth).toBeGreaterThan(0);
  });
});
