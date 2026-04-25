import { render } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MarketEventsCard from './MarketEventsCard.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';
import { marketHealthAllTime } from './__fixtures__/marketHealth.allTime.js';

const currentEvents = marketHealthCurrentQuarter.events;
const allTimeEvents  = marketHealthAllTime.events;

describe('MarketEventsCard', () => {
  it('renders the title from events data', () => {
    const { getByRole } = render(MarketEventsCard, { eventsData: currentEvents });
    expect(getByRole('heading', { level: 3 })).toHaveTextContent(currentEvents.title);
  });

  it('renders the subtitle', () => {
    const { getByText } = render(MarketEventsCard, { eventsData: currentEvents });
    expect(getByText(currentEvents.subtitle)).toBeTruthy();
  });

  it('renders all 4 event tile labels', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const labels = container.querySelectorAll('.event-label');
    expect(labels).toHaveLength(4);
    expect(labels[0]).toHaveTextContent(currentEvents.newListings.label);
    expect(labels[1]).toHaveTextContent(currentEvents.droppedListings.label);
    expect(labels[2]).toHaveTextContent(currentEvents.restocks.label);
    expect(labels[3]).toHaveTextContent(currentEvents.oosFlips.label);
  });

  it('renders all 4 event tile values', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const values = container.querySelectorAll('.event-value');
    expect(values).toHaveLength(4);
    expect(values[0]).toHaveTextContent(currentEvents.newListings.value);
    expect(values[1]).toHaveTextContent(currentEvents.droppedListings.value);
    expect(values[2]).toHaveTextContent(currentEvents.restocks.value);
    expect(values[3]).toHaveTextContent(currentEvents.oosFlips.value);
  });

  it('renders all 4 event tile copy sentences', () => {
    const { container } = render(MarketEventsCard, { eventsData: currentEvents });
    const copies = container.querySelectorAll('.event-copy');
    expect(copies).toHaveLength(4);
    expect(copies[0]).toHaveTextContent(currentEvents.newListings.copy);
    expect(copies[1]).toHaveTextContent(currentEvents.droppedListings.copy);
    expect(copies[2]).toHaveTextContent(currentEvents.restocks.copy);
    expect(copies[3]).toHaveTextContent(currentEvents.oosFlips.copy);
  });

  it('renders all-time title and subtitle when given allTime fixture', () => {
    const { getByRole, getByText } = render(MarketEventsCard, { eventsData: allTimeEvents });
    expect(getByRole('heading', { level: 3 })).toHaveTextContent(allTimeEvents.title);
    expect(getByText(allTimeEvents.subtitle)).toBeTruthy();
  });

  it('renders all-time "N total" values for all 4 tiles', () => {
    const { container } = render(MarketEventsCard, { eventsData: allTimeEvents });
    const values = container.querySelectorAll('.event-value');
    expect(values[0]).toHaveTextContent(allTimeEvents.newListings.value);
    expect(values[1]).toHaveTextContent(allTimeEvents.droppedListings.value);
    expect(values[2]).toHaveTextContent(allTimeEvents.restocks.value);
    expect(values[3]).toHaveTextContent(allTimeEvents.oosFlips.value);
  });
});
