<script lang="ts">
  // MarketSparkline — inline SVG sparkline with run-selection.
  // Renders 12 data points per series; supports a prior-period overlay.
  // All colours are passed as the `color` prop (not CSS tokens) because the
  // spec defines per-metric colours (#1f7a6b / #cc6b49 / #a18b35 / #5d6a6d)
  // that do not exist as global CSS custom properties.

  interface Props {
    series: number[];         // 12 current-period values
    priorSeries: number[];    // 12 prior-period values; [] when showPrior = false
    showPrior: boolean;
    color: string;            // CSS colour string — passed from KpiCard / story args
    formatValue: (v: number) => string;
    selectedRun: number | null;
    onRunSelect: (run: number | null) => void;
    runLabels?: [string, string, string]; // default: ["Run 1", "Run 6", "Run 12"]
  }

  let {
    series,
    priorSeries,
    showPrior,
    color,
    formatValue,
    selectedRun,
    onRunSelect,
    runLabels = ['Run 1', 'Run 6', 'Run 12'],
  }: Props = $props();

  // --- Layout constants ---
  const W = 120;
  const H = 56;
  const TOP_PAD    = 6;
  const BOTTOM_PAD = 14; // space for axis labels
  const LEFT_PAD   = 0;
  const RIGHT_PAD  = 0;
  const CHART_H = H - TOP_PAD - BOTTOM_PAD;
  const CHART_W = W - LEFT_PAD - RIGHT_PAD;
  const N = 12;

  // --- Coordinate helpers ---
  function xAt(i: number): number {
    return LEFT_PAD + (i / (N - 1)) * CHART_W;
  }

  function autoRange(curr: number[], prior: number[], usePrior: boolean): { min: number; max: number } {
    const all = usePrior ? [...curr, ...prior] : [...curr];
    const min = Math.min(...all);
    const max = Math.max(...all);
    return { min, max: max === min ? min + 1 : max };
  }

  function yAt(v: number, min: number, max: number): number {
    const t = (v - min) / (max - min);
    return TOP_PAD + CHART_H - t * CHART_H;
  }

  function toPoints(values: number[], min: number, max: number): string {
    return values.map((v, i) => `${xAt(i)},${yAt(v, min, max)}`).join(' ');
  }

  // Reactive derived values
  let range = $derived(autoRange(series, priorSeries, showPrior && priorSeries.length > 0));
  let currentPoints = $derived(toPoints(series, range.min, range.max));
  let priorPoints   = $derived(priorSeries.length > 0 ? toPoints(priorSeries, range.min, range.max) : '');

  // Baseline y position
  const BASELINE_Y = TOP_PAD + CHART_H;

  // Hit-area width per run slot
  const HIT_W = CHART_W / (N - 1);

  function handleHitClick(index: number) {
    onRunSelect(selectedRun === index ? null : index);
  }
</script>

<svg
  class="market-sparkline"
  viewBox="0 0 {W} {H}"
  width={W}
  height={H}
  aria-hidden="true"
>
  <!-- Baseline axis line -->
  <line
    class="sparkline-baseline"
    x1={LEFT_PAD}
    y1={BASELINE_Y}
    x2={W - RIGHT_PAD}
    y2={BASELINE_Y}
    stroke="#d7cfc0"
    stroke-width="1"
  />

  <!-- Prior series (dashed, behind current) -->
  {#if showPrior && priorSeries.length > 0}
    <polyline
      class="sparkline-prior"
      points={priorPoints}
      fill="none"
      stroke={color}
      stroke-width="1.5"
      stroke-dasharray="3 2"
    />
    {#each priorSeries as v, i}
      {@const isSelected = selectedRun === i}
      <circle
        class="sparkline-point-prior"
        cx={xAt(i)}
        cy={yAt(v, range.min, range.max)}
        r={isSelected ? 3.4 : 2.2}
        fill="none"
        stroke={color}
        stroke-width="1"
      />
    {/each}
  {/if}

  <!-- Current series (solid, on top) -->
  <polyline
    class="sparkline-current"
    points={currentPoints}
    fill="none"
    stroke={color}
    stroke-width="2.5"
  />
  {#each series as v, i}
    {@const isSelected = selectedRun === i}
    {@const isSubdued  = selectedRun !== null && !isSelected}
    <circle
      class:is-subdued={isSubdued}
      class="sparkline-point-current"
      cx={xAt(i)}
      cy={yAt(v, range.min, range.max)}
      r={isSelected ? 4.4 : 2.7}
      fill={color}
      stroke="none"
    />
  {/each}

  <!-- Invisible hit areas — one per run slot for easy clicking -->
  {#each series as _v, i}
    <rect
      class="sparkline-hit"
      x={i === 0 ? 0 : xAt(i) - HIT_W / 2}
      y={TOP_PAD}
      width={HIT_W}
      height={CHART_H}
      fill="transparent"
      style="cursor: pointer;"
      onclick={() => handleHitClick(i)}
    />
  {/each}

  <!-- Run-axis labels at indices 0, 5, 11 -->
  <text class="sparkline-run-label" x={xAt(0)}  y={H - 2} text-anchor="start"   font-size="7">{runLabels[0]}</text>
  <text class="sparkline-run-label" x={xAt(5)}  y={H - 2} text-anchor="middle"  font-size="7">{runLabels[1]}</text>
  <text class="sparkline-run-label" x={xAt(11)} y={H - 2} text-anchor="end"     font-size="7">{runLabels[2]}</text>
</svg>

<style>
  .market-sparkline {
    display: block;
    width: 100%;   /* fill the .metric-sparkline container (spec §4.6) */
    height: auto;  /* proportional scaling via viewBox */
    overflow: visible;
  }

  .sparkline-prior {
    opacity: 0.38;
  }

  .sparkline-point-prior {
    opacity: 0.45;
  }

  .is-subdued {
    opacity: 0.16;
  }

  .sparkline-run-label {
    fill: var(--color-text-muted);
    font-family: inherit;
  }

  .sparkline-hit:hover ~ .sparkline-point-current {
    cursor: pointer;
  }
</style>
