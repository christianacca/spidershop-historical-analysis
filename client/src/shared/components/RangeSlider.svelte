<script lang="ts">
  const uid = $props.id();

  interface Props {
    min: number;
    max: number;
    label: string;
    onchange: (detail: { min: number; max: number }) => void;
  }

  let { min, max, label, onchange }: Props = $props();

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
  <span class="display">{currentMin} – {currentMax}</span>
  <div class="track">
    <label for="{uid}-min">Min</label>
    <input
      id="{uid}-min"
      type="range"
      class="thumb"
      min={min}
      max={max}
      value={currentMin}
      oninput={handleMinInput}
    />
    <label for="{uid}-max">Max</label>
    <input
      id="{uid}-max"
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
