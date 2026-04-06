<script lang="ts">
  import MarketKpiCard from './MarketKpiCard.svelte';
  import MarketEventsCard from './MarketEventsCard.svelte';
  import type { MarketHealthPayload } from './types.js';

  interface Props {
    payload: MarketHealthPayload;
    initialSelectedRun?: number;
  }

  let { payload, initialSelectedRun = undefined }: Props = $props();

  let selectedRun: number | null = $state(initialSelectedRun ?? null);

  function handleRunSelect(run: number | null): void {
    selectedRun = run === selectedRun ? null : run;
  }

  const selectionNote = $derived(
    selectedRun === null
      ? 'Optional: click a run to highlight that moment across all sparklines.'
      : `Run ${selectedRun + 1} selected. The same moment is now highlighted across all four KPI cards.`,
  );
</script>

<section class="market-health-section">
  <div class="kpi-grid">
    <MarketKpiCard
      card={payload.kpis.observed}
      series={payload.sparklineSeries.observed}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
    />
    <MarketKpiCard
      card={payload.kpis.stock}
      series={payload.sparklineSeries.stock}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
    />
    <MarketKpiCard
      card={payload.kpis.wishlist}
      series={payload.sparklineSeries.wishlist}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
    />
    <MarketKpiCard
      card={payload.kpis.price}
      series={payload.sparklineSeries.price}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
    />
  </div>

  <div class="sparkline-support-row">
    <div class="sparkline-legend">
      <span class="legend-current-key">
        <svg width="16" height="4" aria-hidden="true">
          <line x1="0" y1="2" x2="16" y2="2" stroke="currentColor" stroke-width="2" />
        </svg>
        Current
      </span>
      <span class="legend-prior-key" hidden={!payload.showPrior}>
        <svg width="16" height="4" aria-hidden="true">
          <line x1="0" y1="2" x2="16" y2="2" stroke="currentColor" stroke-width="2" stroke-dasharray="4 2" />
        </svg>
        Prior
      </span>
    </div>

    <p class="sparkline-basis-note">{payload.sparklineBasisNote}</p>

    <p class="pulse-selection-note">{selectionNote}</p>

    <button
      class="clear-run-btn"
      hidden={selectedRun === null}
      onclick={() => { selectedRun = null; }}
    >
      Clear run focus
    </button>
  </div>

  <MarketEventsCard eventsData={payload.events} />
</section>

<style>
  .market-health-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-sm);
  }

  @media (max-width: 760px) {
    .kpi-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .sparkline-support-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-sm);
    color: var(--color-text-muted);
    padding: var(--spacing-xs) 0;
    border-top: 1px solid var(--color-border-light);
    border-bottom: 1px solid var(--color-border-light);
  }

  .sparkline-legend {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .legend-current-key,
  .legend-prior-key {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--color-text-muted);
  }

  .sparkline-basis-note,
  .pulse-selection-note {
    margin: 0;
  }

  .clear-run-btn {
    margin-left: auto;
    font-size: var(--font-sm);
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border-light);
    background: var(--color-surface);
    color: var(--color-text-muted);
    cursor: pointer;
  }

  .clear-run-btn:hover {
    background: var(--color-surface-light);
  }

  /* Explicit override: scoped display rules have higher specificity than
     the UA-stylesheet [hidden] rule. Re-assert display:none here. */
  .legend-prior-key[hidden],
  .clear-run-btn[hidden] {
    display: none;
  }
</style>
