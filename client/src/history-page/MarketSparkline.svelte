<script lang="ts">
  // MarketSparkline — inline SVG sparkline with run-selection.
  // Renders 12 data points per series; supports a prior-period overlay.
  // All colours are passed as the `color` prop (not CSS tokens) because the
  // spec defines per-metric colours (#1f7a6b / #cc6b49 / #a18b35 / #5d6a6d)
  // that do not exist as global CSS custom properties.

  interface Props {
    series: number[];         // up to 12 current-period values (fewer for in-progress windows)
    priorSeries: number[];    // up to 12 prior-period values; [] when showPrior = false
    showPrior: boolean;
    color: string;            // CSS colour string — passed from KpiCard / story args
    formatValue: (v: number) => string;
    selectedRun: number | null;
    onRunSelect: (run: number | null) => void;
  }

  let {
    series,
    priorSeries,
    showPrior,
    color,
    formatValue,
    selectedRun,
    onRunSelect,
  }: Props = $props();

  // --- Layout constants (match mock: viewBox 268×82, padding left/right 14, top 10, bottom 18) ---
  const W = 268;
  const H = 82;
  const TOP_PAD    = 10;
  const BOTTOM_PAD = 18; // space for axis labels
  const LEFT_PAD   = 14;
  const RIGHT_PAD  = 14;
  const CHART_H = H - TOP_PAD - BOTTOM_PAD;
  const CHART_W = W - LEFT_PAD - RIGHT_PAD;
  // N is the x-scale grid size — xAt() always uses this denominator so a truncated
  // series (fewer than 12 runs) appears left-aligned within the full chart width.
  const N = 12;

  // --- Coordinate helpers ---
  function xAt(i: number): number {
    return LEFT_PAD + (i / (N - 1)) * CHART_W;
  }

  // Auto-range: match mock's Math.max(range, 1) approach.
  // Higher values plot HIGHER (lower y) — maxValue maps to TOP_PAD.
  function autoRange(curr: number[], prior: number[], usePrior: boolean): { min: number; max: number } {
    const all = usePrior ? [...curr, ...prior] : [...curr];
    const min = Math.min(...all);
    const max = Math.max(...all);
    return { min, max };
  }

  function range(min: number, max: number): number {
    return Math.max(max - min, 1);
  }

  function yAt(v: number, min: number, max: number): number {
    return TOP_PAD + ((max - v) / range(min, max)) * CHART_H;
  }

  function toPoints(values: number[], min: number, max: number): string {
    return values.map((v, i) => `${xAt(i)},${yAt(v, min, max)}`).join(' ');
  }

  // Reactive derived values
  let autoRangeResult = $derived(autoRange(series, priorSeries, showPrior && priorSeries.length > 0));
  let currentPoints   = $derived(toPoints(series, autoRangeResult.min, autoRangeResult.max));
  let priorPoints     = $derived(priorSeries.length > 0 ? toPoints(priorSeries, autoRangeResult.min, autoRangeResult.max) : '');

  // Baseline y position (bottom of chart area)
  const BASELINE_Y = TOP_PAD + CHART_H;

  // Hit-area width per run slot
  const HIT_W = CHART_W / (N - 1);

  function handleHitClick(index: number) {
    onRunSelect(selectedRun === index ? null : index);
  }

  // Axis labels — computed from actual series length so truncated series shows
  // correct run numbers rather than hardcoded "Run 1 / Run 6 / Run 12".
  interface AxisLabel { index: number; text: string; anchor: string; }
  let axisLabels = $derived((): AxisLabel[] => {
    const n = series.length;
    if (n === 0) return [];
    if (n === 1) return [{ index: 0, text: 'Run 1', anchor: 'start' }];
    if (n === 2) return [
      { index: 0,   text: 'Run 1', anchor: 'start' },
      { index: 1,   text: 'Run 2', anchor: 'end'   },
    ];
    const mid = Math.floor((n - 1) / 2);
    return [
      { index: 0,   text: 'Run 1',        anchor: 'start'  },
      { index: mid, text: `Run ${mid + 1}`, anchor: 'middle' },
      { index: n-1, text: `Run ${n}`,      anchor: 'end'    },
    ];
  });
</script>

<svg
  class="market-sparkline"
  viewBox="0 0 {W} {H}"
  width="100%"
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
      stroke-dasharray="5 4"
    />
    {#each priorSeries as v, i}
      {@const isSelected = selectedRun === i}
      <circle
        class="sparkline-point-prior"
        cx={xAt(i)}
        cy={yAt(v, autoRangeResult.min, autoRangeResult.max)}
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
      cy={yAt(v, autoRangeResult.min, autoRangeResult.max)}
      r={isSelected ? 4.4 : 2.7}
      fill={color}
      stroke="none"
    />
  {/each}

  <!-- Invisible hit areas — one per run slot for easy clicking -->
  {#each series as _v, i}
    <rect
      class="sparkline-hit"
      x={i === 0 ? LEFT_PAD : xAt(i) - HIT_W / 2}
      y={TOP_PAD}
      width={HIT_W}
      height={CHART_H}
      fill="transparent"
      style="cursor: pointer;"
      onclick={() => handleHitClick(i)}
    />
  {/each}

  <!-- Run-axis labels — derived from series length; font-size 10 matches mock CSS .sparkline-run-labels -->
  {#each axisLabels() as lbl}
    <text class="sparkline-run-label" x={xAt(lbl.index)} y={H - 4} text-anchor={lbl.anchor} font-size="10">{lbl.text}</text>
  {/each}
</svg>

<style>
  .market-sparkline {
    display: block;
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
