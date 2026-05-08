<script lang="ts">
  import MarketHealthSection from './MarketHealthSection.svelte';
  import FiltersPanel from './FiltersPanel.svelte';
  import type { MarketHealthRawData, MarketHealthPayload, WindowId } from './types.js';
  import { buildMarketHealthPayload } from './market-health-engine.js';

  interface Props {
    rawData: MarketHealthRawData;
  }

  let { rawData }: Props = $props();

  let selectedGenera: string[] = $state([]);
  let isAllSelected: boolean = $state(true);
  let windowId: WindowId = $state('current-quarter');

  const payload: MarketHealthPayload = $derived(
    buildMarketHealthPayload(rawData, windowId, { selectedGenera, isAllSelected })
  );

  const availableGenera = $derived(
    [...new Set(rawData.records.map(r => r.scientificName.split(' ')[0]))].sort()
  );

  const mostObservedGenera = $derived(
    (() => {
      const counts = new Map<string, number>();
      for (const r of rawData.records) {
        const genus = r.scientificName.split(' ')[0];
        counts.set(genus, (counts.get(genus) ?? 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 12)
        .map(([g]) => g);
    })()
  );
</script>

<div class="hero">
  <div class="hero-panel">
    <h1 class="hero-heading">Understand market conditions for the genera you care about.</h1>
    <p class="hero-copy">Use the filters to narrow the time window and genus scope. Every section on this page reflects the same selection.</p>
  </div>
  <FiltersPanel
    {availableGenera}
    {selectedGenera}
    {isAllSelected}
    {mostObservedGenera}
    {windowId}
    basisNote={payload.windowBasisNote}
    windowLabel={payload.windowLabel}
    scopeLabel={payload.scopeLabel}
    onSelectionChange={(genera, isAll) => { selectedGenera = genera; isAllSelected = isAll; }}
    onWindowChange={(id) => { windowId = id; }}
  />
</div>
<MarketHealthSection {payload} />

<style>
  .hero {
    display: grid;
    grid-template-columns: 1.35fr 0.9fr;
    gap: 24px;
    margin-bottom: 24px;
  }

  .hero-heading {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--color-text);
    margin: 0 0 12px;
    line-height: 1.3;
  }

  .hero-copy {
    color: var(--color-text-label);
    font-size: 0.96rem;
    margin: 0;
    line-height: 1.5;
  }

  @media (max-width: 1100px) {
    .hero {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 760px) {
    .hero-panel {
      padding: 18px;
    }
  }
</style>
