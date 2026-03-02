<script lang="ts">
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
<button
  class={{ btn: true, 'date-expand-btn': true, 'advanced-filters-toggle': true, expanded: showPicker }}
  data-action="toggle-date-picker"
  data-content-id="date-picker-{tableId}"
  data-table-id={tableId}
  onclick={() => (showPicker = !showPicker)}
>
  <span class="arrow">▶</span>
  {#if showPicker}
    <span>Hide individual dates</span>
  {:else}
    <span>Show individual dates</span>
  {/if}
</button>

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
    background: var(--color-date-filter);
    color: #856404;
    border: none;
    padding: 6px 14px;
    border-radius: var(--radius-sm);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    margin-bottom: 4px;
  }

  .date-expand-btn:hover {
    background: var(--color-date-filter-hover);
  }

  .date-expand-btn .arrow {
    transition: transform 0.2s;
    font-size: 0.8rem;
  }

  .date-expand-btn.expanded .arrow {
    transform: rotate(90deg);
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
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 6px 10px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: border-color 0.2s;
  }

  .date-row:hover {
    border-color: var(--color-accent);
  }

  .date-count {
    color: #888;
    font-size: 0.85rem;
  }

  .quick-select-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    border-top: 1px solid #e8c400;
    padding-top: 12px;
    margin-top: 12px;
  }
</style>
