/**
 * MarketEventsCard — browser-backed visual contracts.
 *
 * Phase 10b gap verification:
 * - Gap 1: Event tile labels must NOT be uppercase (text-transform: none)
 * - Gap 2: Event tiles must have large card border-radius (~16px), not small radius
 *
 * Typography polish (mock alignment):
 * - Gap 3: Outer .visual-card wrapper must have card-shaped corner radius (≥14px), not tight 6px
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

// ── Typography polish (mock alignment) ───────────────────────────────────────
// Gap 3: The outer .visual-card container had --radius-md (6px) which gave it
// a tight, boxy look. The mock shows large card rounding (~20px). We align to
// --radius-card-lg (16px) which is the established card-shape token.

describe('MarketEventsCard — Gap 3: outer visual-card border-radius', () => {
  it('outer visual-card wrapper has card-shaped border-radius (≥14px)', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const card = container.querySelector('.visual-card') as HTMLElement;
    const radius = parseFloat(window.getComputedStyle(card).borderRadius);
    // Must be a card shape, not the small --radius-md (6px) default
    expect(radius).toBeGreaterThanOrEqual(14);
  });
});
