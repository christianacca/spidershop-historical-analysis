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

  // Heading/copy logic per spec §2.1
  const heading = $derived((): string => {
    if (payload.isAllSelected) {
      return 'Is the wider tarantula market growing, becoming harder to source, or levelling off?';
    }
    if (payload.generaCount === 0) {
      return 'Add genera to see supply and demand health for your selection.';
    }
    if (payload.generaCount === 1) {
      return `Is ${payload.scopeLabel} supply growing, tightening, or levelling off?`;
    }
    if (payload.generaCount <= 3) {
      return `For ${payload.scopeLabel}: is supply growing, tightening, or levelling off?`;
    }
    return `How healthy is supply and demand across your ${payload.generaCount} selected genera?`;
  });

  const scopeCopy = $derived((): string => {
    if (payload.isAllSelected) {
      return 'These metrics cover all tracked species \u2014 the widest possible lens before you narrow to a genus.';
    }
    if (payload.generaCount === 0) {
      return 'Use the genus filter above to add genera. Market Health KPIs will reflect whichever genera are in scope.';
    }
    return 'These metrics ask whether supply and demand for your selected genera look healthy enough to support breeding investment.';
  });

  const sectionNote = $derived((): string => {
    if (payload.isAllSelected) {
      return 'If the overall market looks flat, treat individual genus comparisons cautiously.';
    }
    if (payload.generaCount === 0) {
      return 'Use the genus filter above to add genera before drawing conclusions.';
    }
    return 'If your selected genera look flat overall, treat any individual genus comparison cautiously.';
  });

  // Derived from windowId — converts e.g. "current-quarter" → "current quarter" for readout text
  const windowScopeLabel = $derived(payload.windowId.replaceAll('-', ' '));
</script>

<section class="market-health-section">
  <div class="section-header">
    <div class="section-title">
      <p class="section-eyebrow">1. Market Health KPIs</p>
      <h2 id="market-health-heading">{heading()}</h2>
      <p id="market-health-scope-copy" class="section-scope-copy">{scopeCopy()}</p>
    </div>
    <p class="section-note">{sectionNote()}</p>
  </div>

  <div class="kpi-grid">
    <MarketKpiCard
      card={payload.kpis.observed}
      series={payload.sparklineSeries.observed}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
      {windowScopeLabel}
    />
    <MarketKpiCard
      card={payload.kpis.stock}
      series={payload.sparklineSeries.stock}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
      {windowScopeLabel}
    />
    <MarketKpiCard
      card={payload.kpis.wishlist}
      series={payload.sparklineSeries.wishlist}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
      {windowScopeLabel}
    />
    <MarketKpiCard
      card={payload.kpis.price}
      series={payload.sparklineSeries.price}
      showPrior={payload.showPrior}
      {selectedRun}
      onRunSelect={handleRunSelect}
      {windowScopeLabel}
    />
  </div>

  <div class="sparkline-support-card">
    <div class="sparkline-support-row">
      <div class="sparkline-legend">
        <span class="legend-current-key">
          <span class="line-swatch" aria-hidden="true"></span>
          Active window
        </span>
        <span class="legend-prior-key" hidden={!payload.showPrior}>
          <span class="line-swatch line-swatch--dashed" aria-hidden="true"></span>
          Matched prior-period overlay
        </span>
      </div>

      <button
        class="clear-run-btn"
        hidden={selectedRun === null}
        onclick={() => { selectedRun = null; }}
      >
        Clear run focus
      </button>
    </div>

    <p class="sparkline-basis-note">{payload.sparklineBasisNote}</p>

    <p class="pulse-selection-note">{selectionNote}</p>
  </div>

  <MarketEventsCard eventsData={payload.events} />
</section>

<style>
  .market-health-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    background: var(--color-surface); /* warm white — elevated above the warm-cream page bg */
    border: 1px solid var(--color-border-warm);
    border-radius: var(--radius-card-lg);
    padding: var(--spacing-xl);
    box-shadow: var(--shadow-lg);
  }

  .section-header {
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    gap: var(--spacing-lg);
  }

  .section-title {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .section-eyebrow {
    display: inline-block;
    margin: 0;
    background: rgba(31, 122, 107, 0.1); /* tinted --color-market-health; rgba() required: no CSS-native opacity modifier for custom properties without color-mix() */
    color: var(--color-market-health);
    border-radius: var(--radius-pill);
    padding: 5px 9px;
    font-size: var(--font-sm);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .section-header h2 {
    margin: 0;
    font-size: var(--font-lg);
    color: var(--color-text-primary);
  }

  .section-scope-copy {
    margin: 0;
    font-size: var(--font-base);
    color: var(--color-text-muted);
  }

  .section-note {
    flex: none;
    max-width: 38ch;
    align-self: flex-end;
    margin: 0;
    font-size: var(--font-sm);
    color: var(--color-text-muted);
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

  .sparkline-support-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 14px 16px;
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-card-lg);
    background: rgba(255, 255, 255, 0.54);
    font-size: 0.82rem;
    color: var(--color-text-muted);
  }

  .sparkline-support-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
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
    gap: 6px;
    color: var(--color-text-muted);
    font-size: 0.84rem;
    font-weight: 700;
  }

  .line-swatch {
    display: inline-block;
    width: 28px;
    border-top: 3px solid var(--color-text);
    border-radius: var(--radius-pill);
    flex-shrink: 0;
    opacity: 0.9;
  }

  .line-swatch--dashed {
    border-top-style: dashed;
    opacity: 0.42;
  }

  .sparkline-basis-note,
  .pulse-selection-note {
    margin: 0;
    font-size: 0.82rem;
  }

  .clear-run-btn {
    margin-left: auto;
    font-size: var(--font-sm);
    font-weight: 700;
    padding: 6px 10px;
    border-radius: var(--radius-pill);
    border: 1px solid rgba(31, 42, 44, 0.12);
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
