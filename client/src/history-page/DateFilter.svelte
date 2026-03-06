<script lang="ts">
  import ToggleButton from '../shared/components/ToggleButton.svelte';

  // ── Types ───────────────────────────────────────────────────────────────────

  interface Props {
    /** Unique dates in display order (most-recent first). */
    dates: string[];
    /** Number of rows per date key. */
    rowCounts: Record<string, number>;
    /** Matches the parent table's ID for data-table-id attributes. */
    tableId: string;
    /** Fires whenever the selection changes; receives all currently selected dates. */
    onchange: (selected: string[]) => void;
  }

  let { dates, rowCounts, tableId, onchange }: Props = $props();

  // ── State ────────────────────────────────────────────────────────────────────
  let selectedDates = $state<Set<string>>(new Set(dates));
  let showPicker = $state(false);

  // ── Derived ──────────────────────────────────────────────────────────────────
  const allSelected = $derived(selectedDates.size === dates.length);

  const totalSelectedRows = $derived(
    [...selectedDates].reduce((sum, d) => sum + (rowCounts[d] ?? 0), 0),
  );

  // ── Handlers ─────────────────────────────────────────────────────────────────
  function notifyParent(): void {
    // emit in the same order dates appear in the dates prop
    onchange(dates.filter((d) => selectedDates.has(d)));
  }

  function handleAllDatesChange(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      selectedDates = new Set(dates);
    }
    notifyParent();
  }

  function handleDateCheckbox(date: string): void {
    const next = new Set(selectedDates);
    if (next.has(date)) {
      next.delete(date);
    } else {
      next.add(date);
    }
    selectedDates = next;
    notifyParent();
  }

  function selectLast(n: number): void {
    selectedDates = new Set(dates.slice(0, n));
    notifyParent();
  }

  function showAll(): void {
    selectedDates = new Set(dates);
    notifyParent();
  }
</script>

<!-- ── All-dates checkbox ────────────────────────────────────────────────── -->
<div class="date-all-row">
  <label class="date-all-label">
    <input
      type="checkbox"
      id="allDates-{tableId}"
      checked={allSelected}
      onchange={handleAllDatesChange}
    />
    <strong>All Dates ({totalSelectedRows} rows)</strong>
  </label>
</div>

<!-- ── Expand / collapse picker ─────────────────────────────────────────── -->
<ToggleButton
  expanded={showPicker}
  onToggle={() => (showPicker = !showPicker)}
  class="advanced-filters-toggle date-expand-btn"
  data-action="toggle-date-picker"
  data-content-id="date-picker-{tableId}"
  data-table-id={tableId}
>
  {#snippet children(expanded)}
    {expanded ? 'Hide individual dates' : 'Show individual dates'}
  {/snippet}
</ToggleButton>

<!-- ── Individual date picker ───────────────────────────────────────────── -->
{#if showPicker}
  <div id="date-picker-{tableId}" class="date-picker-content show">
    <div class="date-grid">
      {#each dates as date}
        <label class="date-row">
          <input
            type="checkbox"
            class="date-checkbox"
            data-date-value={date}
            data-table-id={tableId}
            checked={selectedDates.has(date)}
            onchange={() => handleDateCheckbox(date)}
          />
          <span class="date-label">{date}</span>
          <span class="date-count">({rowCounts[date] ?? 0} rows)</span>
        </label>
      {/each}
    </div>
    <div class="quick-select-bar">
      <button
        class="btn btn--secondary"
        data-action="select-last-n"
        data-n="1"
        data-table-id={tableId}
        onclick={() => selectLast(1)}
      >Last Run</button>
      <button
        class="btn btn--secondary"
        data-action="select-last-n"
        data-n="2"
        data-table-id={tableId}
        onclick={() => selectLast(2)}
      >Last 2 Runs</button>
      <button
        class="btn btn--secondary"
        data-action="select-last-n"
        data-n="4"
        data-table-id={tableId}
        onclick={() => selectLast(4)}
      >Last 4 Runs</button>
      <button
        class="btn btn--secondary"
        data-action="select-last-n"
        data-n="8"
        data-table-id={tableId}
        onclick={() => selectLast(8)}
      >Last 8 Runs</button>
      <button
        class="btn btn--secondary"
        data-action="show-all-dates"
        data-table-id={tableId}
        onclick={showAll}
      >Show All</button>
    </div>
  </div>
{/if}

<style>
  .date-all-row {
    margin-bottom: 8px;
  }

  .date-all-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }

  .date-expand-btn {
    margin-bottom: 4px;
  }

  .date-picker-content {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--color-date-filter);
  }

  .date-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 0;
  }

  .date-row {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-md);
    padding: 6px 10px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: border-color 0.2s;
  }

  .date-row:hover {
    border-color: var(--color-accent);
  }

  .date-count {
    color: var(--color-text-muted);
    font-size: 0.85rem;
  }

  .quick-select-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    border-top: 2px solid var(--color-date-filter);
    padding-top: 12px;
    margin-top: 12px;
  }
</style>
