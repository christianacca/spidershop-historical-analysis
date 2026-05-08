import { mount } from 'svelte';
import { HISTORY_PAGE_CONFIG } from './config.js';
import { bootstrapSortableTablePage } from '../shared/page-entry.js';
import HistoryInsightsRoot from './HistoryInsightsRoot.svelte';
import type { MarketHealthRawData } from './types.js';

bootstrapSortableTablePage(HISTORY_PAGE_CONFIG);

// Mount the HistoryInsightsRoot island if the mount point and raw data exist.
const historyInsightsRoot = document.getElementById('history-insights-root');
if (historyInsightsRoot) {
  const rawData = (window as unknown as Record<string, unknown>)
    .marketHealthRawData as MarketHealthRawData | undefined;

  if (rawData && rawData.records.length > 0) {
    mount(HistoryInsightsRoot, {
      target: historyInsightsRoot,
      props: { rawData },
    });
  }
}
