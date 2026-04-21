<script lang="ts">
  import MarketSparkline from './MarketSparkline.svelte';
  import type { KpiCardData, SparklineSeries } from './types.js';

  // Sparkline colour per KPI id (spec §3).
  // These are per-metric series colours, not CSS tokens.
  const SPARKLINE_COLOR: Record<KpiCardData['id'], string> = {
    observed: '#1f7a6b',
    stock:    '#cc6b49',
    wishlist: '#a18b35',
    price:    '#5d6a6d',
  };

  // Hardcoded tooltip text per KPI id (spec §7.2 note — never varies by window).
  const TOOLTIP: Record<KpiCardData['id'], string> = {
    observed: 'Count of distinct species seen in-stock at least once during the selected window.',
    stock:    'Of species seen in-stock this period, what % are in-stock at the most recent run?',
    wishlist: 'Median wishlist count across in-stock species at the most recent run.',
    price:    'Median price (GBP) across in-stock species at the most recent run.',
  };

  // Format helper for sparkline readout values.
  function makeFormatter(id: KpiCardData['id']): (v: number) => string {
    if (id === 'stock')    return (v) => `${v}%`;
    if (id === 'price')    return (v) => `GBP ${v}`;
    return (v) => String(v);
  }

  interface Props {
    card: KpiCardData;
    series: SparklineSeries;
    showPrior: boolean;
    selectedRun: number | null;
    onRunSelect: (run: number | null) => void;
    windowScopeLabel?: string;
  }

  let { card, series, showPrior, selectedRun, onRunSelect, windowScopeLabel = 'all time' }: Props = $props();

  // Readout text per spec §4.5.
  const fmt = makeFormatter(card.id);
  const readoutText = $derived((): string => {
    if (selectedRun === null) {
      if (showPrior) {
        return `${card.title} shown as active window vs matched prior-period overlay.`;
      }
      return `${card.title} shown as ${windowScopeLabel} context with no prior-period overlay.`;
    }
    const pointLabel = `Run ${selectedRun + 1}`;
    const currentValue = fmt(series.current[selectedRun]!);
    if (showPrior && series.prior.length > 0) {
      const priorValue = fmt(series.prior[selectedRun]!);
      return `${pointLabel}: ${currentValue} current vs ${priorValue} matched prior period.`;
    }
    return `${pointLabel}: ${currentValue} within ${windowScopeLabel}, with no prior-period overlay.`;
  });
</script>

<article class="kpi-card">
  <div class="metric-title-row">
    <h3 class="kpi-title">{card.title}</h3>
    <details class="metric-info">
      <summary class="metric-info-button" aria-label="What is {card.title}?">?</summary>
      <div class="metric-popover">
        <strong>What this means</strong>
        <p>{TOOLTIP[card.id]}</p>
      </div>
    </details>
  </div>

  <span class="metric-value">{card.value}</span>
  <span class="metric-delta {card.deltaClass}">{card.delta}</span>

  <p class="kpi-copy">{card.copy}</p>

  <div class="metric-sparkline-shell">
    <div class="metric-sparkline">
      <MarketSparkline
        series={series.current}
        priorSeries={series.prior}
        {showPrior}
        color={SPARKLINE_COLOR[card.id]}
        formatValue={makeFormatter(card.id)}
        {selectedRun}
        {onRunSelect}
      />
    </div>
    <p class="sparkline-readout">{readoutText()}</p>
  </div>
</article>

<style>
  .kpi-card {
    background: linear-gradient(rgba(255, 255, 255, 0.96), rgba(247, 242, 232, 0.92)); /* warm gradient — matches mock; gradient required, not a single token */
    border: 1px solid var(--color-border-warm);
    border-radius: 18px; /* mock uses 18px; --radius-card-lg is 16px (used by event tiles), so overridden here */
    padding: var(--spacing-md);
    min-height: 140px;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    box-shadow: var(--shadow-sm); /* lifts card off the warm-white section surface */
  }

  .kpi-title {
    font-size: var(--font-sm);
    font-weight: 700;
    color: var(--color-text-label);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
  }

  .metric-title-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--spacing-sm);
  }

  .metric-info {
    position: relative;
    flex: 0 0 auto;
  }

  .metric-info summary {
    list-style: none;
  }

  .metric-info summary::-webkit-details-marker {
    display: none;
  }

  .metric-info-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: var(--radius-pill);
    border: 1px solid rgba(31, 42, 44, 0.16);
    background: rgba(255, 255, 255, 0.9); /* semi-transparent white; rgba() required — no CSS-native opacity modifier for custom properties without color-mix() */
    color: var(--color-text-label);
    font-size: 0.84rem;
    font-weight: 800;
    cursor: pointer;
    user-select: none;
  }

  .metric-info[open] .metric-info-button {
    border-color: rgba(31, 122, 107, 0.24);
    color: var(--color-market-health);
    background: rgba(31, 122, 107, 0.08);
  }

  .metric-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: min(280px, 70vw);
    padding: 12px;
    border-radius: 14px; /* mock uses 14px; --radius-lg is 8px, overriding */
    border: 1px solid var(--color-border-warm); /* warm sand — matches mock */
    background: rgba(255, 253, 248, 0.98); /* near-pure white — lighter than --color-surface (#fffaf2); matches mock */
    box-shadow: 0 20px 40px rgba(65, 54, 33, 0.08); /* large, warm shadow — matches mock */
    z-index: 10;
    font-size: var(--font-sm);
    line-height: 1.5;
    color: var(--color-text);
  }

  .metric-popover strong {
    display: block;
    margin-bottom: 4px;
    color: var(--color-text-heading);
    font-weight: 700;
  }

  .metric-popover p {
    margin: 0;
  }

  .metric-value {
    font-size: 2rem;
    font-weight: 750;
    letter-spacing: -0.03em;
    color: var(--color-text);
    line-height: 1;
  }

  /* Positive/neutral (default, class "") — teal pill */
  .metric-delta {
    display: inline-flex;
    width: fit-content;
    border-radius: var(--radius-pill);
    background: rgba(31, 122, 107, 0.12); /* tinted --color-market-health; rgba() required: no CSS-native opacity modifier for custom properties without color-mix() */
    color: var(--color-market-health);
    font-size: var(--font-sm);
    font-weight: 700;
    padding: 4px 8px;
  }

  /* Negative — red-amber pill */
  .metric-delta.down {
    background: rgba(178, 76, 61, 0.12); /* tinted; close to but not --color-danger (#e74c3c) */
    color: #b24c3d;
  }

  /* Neutral / all-time — muted pill */
  .metric-delta.flat {
    background: rgba(127, 140, 141, 0.12); /* tinted --color-text-muted */
    color: var(--color-text-muted);
  }

  .kpi-copy {
    font-size: var(--font-sm);
    color: var(--color-text);
    line-height: 1.5;
    margin: 0;
  }

  /* Sparkline shell — separates sparkline area from copy above (spec §4.6) */
  .metric-sparkline-shell {
    display: grid;
    gap: 8px;
    margin-top: 6px;
    padding-top: 10px;
    border-top: 1px dashed rgba(31, 42, 44, 0.12);
  }

  /* Bordered box enclosing the SVG sparkline (spec §4.6) */
  .metric-sparkline {
    border: 1px solid rgba(215, 207, 192, 0.9); /* warm sand — same family as card border */
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.72); /* semi-transparent white inset */
    overflow: hidden;
  }

  /* Readout text below the sparkline box (spec §4.5) */
  .sparkline-readout {
    color: var(--color-text-muted);
    font-size: 0.79rem;
    margin: 0;
  }
</style>

