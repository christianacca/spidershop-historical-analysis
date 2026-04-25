import { mount } from 'svelte';
import { HISTORY_PAGE_CONFIG } from './config.js';
import { bootstrapSortableTablePage } from '../shared/page-entry.js';
import MarketHealthSection from './MarketHealthSection.svelte';
import type { MarketHealthRawData } from './types.js';
import { buildMarketHealthPayloadAllWindows } from './market-health-engine.js';

bootstrapSortableTablePage(HISTORY_PAGE_CONFIG);

// Mount the MarketHealthSection island if the mount point and raw data exist.
const marketHealthRoot = document.getElementById('market-health-root');
if (marketHealthRoot) {
  const rawData = (window as unknown as Record<string, unknown>)
    .marketHealthRawData as MarketHealthRawData | undefined;

  if (rawData && rawData.records.length > 0) {
    const allPayloads = buildMarketHealthPayloadAllWindows(rawData);
    const initialPayload = allPayloads['current-quarter'];
    mount(MarketHealthSection, {
      target: marketHealthRoot,
      props: { payload: initialPayload },
    });
  }
}
