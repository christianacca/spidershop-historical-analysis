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
  <span class="label">{label}</span>
  <span class="display" id={displayId}>{fmt(currentMin)} – {fmt(currentMax)}</span>
  <div class="track">
    <label for={resolvedMinId}>Min</label>
    <input
      id={resolvedMinId}
      type="range"
      class="thumb"
      min={min}
      max={max}
      value={currentMin}
      oninput={handleMinInput}
    />
    <label for={resolvedMaxId}>Max</label>
    <input
      id={resolvedMaxId}
      type="range"
      class="thumb"
      min={min}
      max={max}
      value={currentMax}
      oninput={handleMaxInput}
    />
  </div>
</div>

<style>
  .range-slider {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .label {
    font-size: var(--font-sm);
    color: var(--color-text-muted);
    font-weight: 600;
  }

  .display {
    font-size: var(--font-sm);
    color: var(--color-text);
  }

  .track {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .thumb {
    flex: 1;
    accent-color: var(--color-primary);
    cursor: pointer;
  }

  label {
    font-size: var(--font-sm);
    color: var(--color-text-dim);
  }
</style>
