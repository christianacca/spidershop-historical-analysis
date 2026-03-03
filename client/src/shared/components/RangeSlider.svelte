<script lang="ts">
  const uid = $props.id();

  interface Props {
    min: number;
    max: number;
    label: string;
    onchange: (detail: { min: number; max: number }) => void;
    /** Override the auto-generated id for the min range input. */
    minInputId?: string;
    /** Override the auto-generated id for the max range input. */
    maxInputId?: string;
    /** Add an id to the display span (e.g. for E2E targeting). */
    displayId?: string;
    /** Format an individual value for the display span (default: String). */
    formatValue?: (v: number) => string;
  }

  let { min, max, label, onchange, minInputId, maxInputId, displayId, formatValue }: Props = $props();

  const resolvedMinId = $derived(minInputId ?? `${uid}-min`);
  const resolvedMaxId = $derived(maxInputId ?? `${uid}-max`);
  const fmt = $derived(formatValue ?? String);

  let currentMin = $state(min);
  let currentMax = $state(max);

  function handleMinInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const newMin = Number(input.value);
    if (newMin > currentMax) {
      currentMax = newMin;
    }
    currentMin = newMin;
    onchange({ min: currentMin, max: currentMax });
  }

  function handleMaxInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const newMax = Number(input.value);
    if (newMax < currentMin) {
      currentMin = newMax;
    }
    currentMax = newMax;
    onchange({ min: currentMin, max: currentMax });
  }
</script>

<div class="range-slider">
  <strong class="label">{label}</strong>
  <div class="slider-container">
    <div class="dual-range-slider">
      <input
        id={resolvedMinId}
        type="range"
        class="slider slider-min"
        min={min}
        max={max}
        value={currentMin}
        oninput={handleMinInput}
      />
      <input
        id={resolvedMaxId}
        type="range"
        class="slider slider-max"
        min={min}
        max={max}
        value={currentMax}
        oninput={handleMaxInput}
      />
    </div>
    <div class="slider-values">
      <span>{fmt(currentMin)}</span>
      <span>{fmt(currentMax)}</span>
    </div>
    <div class="slider-current">Showing: <span id={displayId}>{fmt(currentMin)} – {fmt(currentMax)}</span></div>
  </div>
</div>

<style>
  .range-slider {
    padding: 5px 0;
    width: 100%;
  }

  .label {
    display: block;
    font-size: var(--font-base);
    color: var(--color-primary);
    margin-bottom: 4px;
  }

  .slider-container {
    padding: 10px 0;
  }

  .dual-range-slider {
    position: relative;
    width: 100%;
    height: 20px;
    margin: 10px 0;
  }

  .slider {
    -webkit-appearance: none;
    position: absolute;
    width: 100%;
    height: 20px;
    top: 0;
    left: 0;
    background: transparent;
    outline: none;
    pointer-events: none;
    margin: 0;
    padding: 0;
  }

  /* Track: only visible on min slider (bottom layer) */
  .slider-min::-webkit-slider-runnable-track {
    height: 8px;
    background: #d3d3d3;
    border-radius: 5px;
    margin-top: 6px;
  }

  .slider-min::-moz-range-track {
    height: 8px;
    background: #d3d3d3;
    border-radius: 5px;
  }

  /* Max slider track is transparent — only its thumb shows */
  .slider-max::-webkit-slider-runnable-track {
    height: 8px;
    background: transparent;
    border-radius: 5px;
    margin-top: 6px;
  }

  .slider-max::-moz-range-track {
    height: 8px;
    background: transparent;
    border-radius: 5px;
  }

  /* Thumbs: pointer-events enabled so they are draggable */
  .slider::-webkit-slider-thumb {
    pointer-events: auto;
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--color-accent);
    cursor: pointer;
    margin-top: -6px;
  }

  .slider::-moz-range-thumb {
    pointer-events: auto;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--color-accent);
    cursor: pointer;
    border: none;
  }

  /* Both handles use the same accent colour (visual consistency) */
  .slider-min::-webkit-slider-thumb {
    background: var(--color-accent);
  }

  .slider-min::-moz-range-thumb {
    background: var(--color-accent);
  }

  .slider-values {
    display: flex;
    justify-content: space-between;
    margin-top: 5px;
    color: var(--color-text-muted);
    font-size: var(--font-sm);
  }

  .slider-current {
    margin-top: 8px;
    color: var(--color-primary);
    font-weight: 600;
  }
</style>
