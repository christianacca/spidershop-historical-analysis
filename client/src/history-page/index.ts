import { mount } from 'svelte';
import { HISTORY_PAGE_CONFIG } from './config.js';
import { bootstrapSortableTablePage } from '../shared/page-entry.js';
import MarketHealthSection from './MarketHealthSection.svelte';
import type { MarketHealthPayload, WindowId } from './types.js';

bootstrapSortableTablePage(HISTORY_PAGE_CONFIG);

// Mount the MarketHealthSection island if the mount point and payload data exist.
const marketHealthRoot = document.getElementById('market-health-root');
if (marketHealthRoot) {
  const globalPayloads = (window as unknown as Record<string, unknown>)
    .marketHealthPayloads as Record<WindowId, MarketHealthPayload> | undefined;

  const initialPayload = globalPayloads?.['current-quarter'];
  if (initialPayload) {
    mount(MarketHealthSection, {
      target: marketHealthRoot,
      props: { payload: initialPayload },
    });
  }
}
