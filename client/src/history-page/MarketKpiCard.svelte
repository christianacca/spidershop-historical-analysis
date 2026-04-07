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
  }

  let { card, series, showPrior, selectedRun, onRunSelect }: Props = $props();
</script>

<article class="kpi-card">
  <h3 class="kpi-title" title={TOOLTIP[card.id]}>{card.title}</h3>

  <div class="kpi-value-row">
    <span class="metric-value">{card.value}</span>
    <span class="metric-delta {card.deltaClass}">{card.delta}</span>
  </div>

  <p class="kpi-copy">{card.copy}</p>

  <MarketSparkline
    series={series.current}
    priorSeries={series.prior}
    {showPrior}
    color={SPARKLINE_COLOR[card.id]}
    formatValue={makeFormatter(card.id)}
    {selectedRun}
    {onRunSelect}
  />
</article>

<style>
  .kpi-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-card-lg);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .kpi-title {
    font-size: var(--font-sm);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 0;
    cursor: help;
  }

  .kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--color-text-heading);
    line-height: 1;
  }

  /* Positive/neutral (default, class "") — teal pill */
  .metric-delta {
    border-radius: var(--radius-pill);
    background: rgba(31, 122, 107, 0.12); /* tinted --color-market-health; rgba() required: no CSS-native opacity modifier for custom properties without color-mix() */
    color: var(--color-market-health);
    font-size: var(--font-sm);
    font-weight: 600;
    padding: 3px 8px;
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
</style>
