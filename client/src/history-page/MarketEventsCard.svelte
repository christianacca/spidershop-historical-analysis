<script lang="ts">
  import type { MarketEventsData } from './types.js';

  interface Props {
    eventsData: MarketEventsData;
  }

  let { eventsData }: Props = $props();
</script>

<article class="visual-card">
  <h3 class="events-title">{eventsData.title}</h3>
  <p class="events-subtitle">{eventsData.subtitle}</p>

  <div class="events-grid">
    {#snippet eventTile(tile: { label: string; value: string; copy: string })}
      <div class="event-tile">
        <span class="event-label">{tile.label}</span>
        <strong class="event-value">{tile.value}</strong>
        <p class="event-copy">{tile.copy}</p>
      </div>
    {/snippet}
    {@render eventTile(eventsData.newListings)}
    {@render eventTile(eventsData.droppedListings)}
    {@render eventTile(eventsData.restocks)}
    {@render eventTile(eventsData.oosFlips)}
  </div>
</article>

<style>
  .visual-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-card-lg);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-sm);
  }

  .events-title {
    font-size: var(--font-base);
    font-weight: 600;
    color: var(--color-text-heading);
    margin: 0 0 var(--spacing-xs);
  }

  .events-subtitle {
    font-size: var(--font-sm);
    color: var(--color-text-muted);
    margin: 0 0 var(--spacing-md);
  }

  .events-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-sm);
  }

  @media (max-width: 480px) {
    .events-grid {
      grid-template-columns: 1fr;
    }
  }

  .event-tile {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 14px;
    background: rgba(255, 255, 255, 0.76); /* near-white — pops against the warm-white outer card; matches mock .mini-card */
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-card-lg);
  }

  .event-label {
    font-size: var(--font-sm);
    color: var(--color-text-muted);
    font-weight: 600;
  }

  .event-value {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--color-text-heading);
  }

  .event-copy {
    font-size: var(--font-sm);
    color: var(--color-text);
    line-height: 1.5;
    margin: 0;
  }
</style>
