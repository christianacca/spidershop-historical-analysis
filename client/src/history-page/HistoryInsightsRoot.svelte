<script lang="ts">
  import MarketHealthSection from './MarketHealthSection.svelte';
  import TimeWindowSelector from './TimeWindowSelector.svelte';
  import GenusSelector from './GenusSelector.svelte';
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

<GenusSelector
  {availableGenera}
  {selectedGenera}
  {isAllSelected}
  {mostObservedGenera}
  onSelectionChange={(genera, isAll) => { selectedGenera = genera; isAllSelected = isAll; }}
/>
<TimeWindowSelector
  {windowId}
  basisNote={payload.windowBasisNote}
  onWindowChange={(id) => { windowId = id; }}
/>
<MarketHealthSection {payload} />
