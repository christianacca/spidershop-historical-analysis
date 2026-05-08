<script lang="ts">
  import GenusSelector from './GenusSelector.svelte';
  import TimeWindowSelector from './TimeWindowSelector.svelte';
  import type { WindowId } from './types.js';

  interface Props {
    availableGenera: string[];
    selectedGenera: string[];
    isAllSelected: boolean;
    mostObservedGenera: string[];
    windowId: WindowId;
    basisNote: string;
    windowLabel: string;
    scopeLabel: string;
    onSelectionChange: (genera: string[], isAll: boolean) => void;
    onWindowChange: (id: WindowId) => void;
  }

  let {
    availableGenera,
    selectedGenera,
    isAllSelected,
    mostObservedGenera,
    windowId,
    basisNote,
    windowLabel,
    scopeLabel,
    onSelectionChange,
    onWindowChange,
  }: Props = $props();

  const globalScopeText = $derived(
    isAllSelected
      ? `Current market scope: all genera • ${windowLabel}`
      : `Current market scope: ${scopeLabel} • ${windowLabel}`
  );
</script>

<aside class="filters-panel">
  <div>
    <h2 class="panel-heading">Global filters</h2>
    <p class="filter-note">Both the time window and genus selection apply to every section on this page.</p>
  </div>
  <div class="scope-inline">
    <span class="scope-label">{globalScopeText}</span>
    <p class="filter-note">All KPIs, charts, preview rows, and CSV export reflect this scope.</p>
  </div>
  <div class="filter-group">
    <label>Genus multi-select</label>
    <GenusSelector
      {availableGenera}
      {selectedGenera}
      {isAllSelected}
      {mostObservedGenera}
      {onSelectionChange}
    />
    <p class="micro-note">Search or use shortcut groups such as lifestyle to narrow the genus list quickly.</p>
  </div>
  <div class="filter-group">
    <label>Time window</label>
    <TimeWindowSelector {windowId} {basisNote} {onWindowChange} />
  </div>
</aside>

<style>
  .filters-panel {
    display: grid;
    gap: 18px;
    padding: 24px;
    align-content: start;
    background: rgba(255, 253, 248, 0.92);
    border: 1px solid rgba(215, 207, 192, 0.95);
    border-radius: 18px;
    box-shadow: var(--shadow-popover);
  }

  .panel-heading {
    margin: 0 0 4px;
    font-size: 1rem;
    font-weight: 700;
    color: var(--color-text);
  }

  .filter-group {
    display: grid;
    gap: 10px;
  }

  .filter-group label {
    color: var(--color-text-label);
    font-size: 0.86rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
  }

  .scope-inline {
    display: grid;
    gap: 8px;
  }

  .filter-note {
    color: var(--color-text-label);
    font-size: 0.92rem;
    margin: 0;
  }

  .micro-note {
    color: var(--color-text-label);
    font-size: 0.84rem;
    margin: 0;
  }

  @media (max-width: 760px) {
    .filters-panel {
      padding: 18px;
    }
  }

  @media (max-width: 480px) {
    .filters-panel {
      background: none;
      border: none;
      border-radius: 0;
      box-shadow: none;
      padding: 0;
    }

    :global(.scope-label) {
      white-space: normal;
      border-radius: 12px;
    }
  }
</style>
