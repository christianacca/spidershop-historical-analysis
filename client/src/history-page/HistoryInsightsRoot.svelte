<script lang="ts">
  import MarketHealthSection from './MarketHealthSection.svelte';
  import TimeWindowSelector from './TimeWindowSelector.svelte';
  import type { MarketHealthRawData, MarketHealthPayload, WindowId } from './types.js';
  import { buildMarketHealthPayload } from './market-health-engine.js';

  interface Props {
    rawData: MarketHealthRawData;
    /** Exposed for test-time control only. Do not pass at runtime. */
    initialWindowId?: WindowId;
  }

  let { rawData, initialWindowId = 'current-quarter' }: Props = $props();

  let selectedGenera: string[] = $state([]);
  let isAllSelected: boolean = $state(true);
  let windowId: WindowId = $state(initialWindowId);

  const payload: MarketHealthPayload = $derived(
    buildMarketHealthPayload(rawData, windowId, { selectedGenera, isAllSelected })
  );
</script>

<TimeWindowSelector
  {windowId}
  basisNote={payload.windowBasisNote}
  onWindowChange={(id) => { windowId = id; }}
/>
<MarketHealthSection {payload} />
