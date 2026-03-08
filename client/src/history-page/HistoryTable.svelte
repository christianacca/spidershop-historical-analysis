<script lang="ts">
  import SparklineBar from '../shared/components/SparklineBar.svelte';
  import type { SparklineDto } from '../shared/types.js';
  import { escapeCsvRow } from '../shared/csv-utils.js';
  import { computeRange, buildCsv, triggerDownload, applySearchFilter } from '../shared/table-utils.js';
  import { collectAllDates } from './history-utils.js';
  import { SortState } from '../shared/sort-state.svelte.js';
  import type { ColumnConfig } from '../shared/components/SortableTable.svelte';
  import DateFilter from './DateFilter.svelte';
  import RangeSlider from '../shared/components/RangeSlider.svelte';
  import FiltersPanel from '../shared/components/FiltersPanel.svelte';
  import SearchInput from '../shared/components/SearchInput.svelte';
  import TableStats from '../shared/components/TableStats.svelte';
  import ToggleButton from '../shared/components/ToggleButton.svelte';

  // ── Types ───────────────────────────────────────────────────────────────────

  interface Props {
    tableId: string;
    rows: Record<string, unknown>[];
    columns: ColumnConfig[];
    /** Display-header name of the date column (e.g. 'Scrape Date'). */
    dateColumn?: string;
    /** Display-header name of the price column. */
    priceColumn?: string;
    /** Display-header name of the wishlist column. */
    wishlistColumn?: string;
  }

  let { tableId, rows, columns, dateColumn, priceColumn, wishlistColumn }: Props = $props();

  // ── One-time range computation ─────────────────────────────────────────────

  const priceRange = computeRange(rows, priceColumn, 'float');
  const wishlistRange = computeRange(rows, wishlistColumn, 'int');

  // ── Data (raw — rows never change after mount) ─────────────────────────────
  const allRows = $state.raw(rows);

  // ── Derived: unique dates and row counts (from the date column) ────────────
  const allDates = $derived.by(() => collectAllDates(allRows, dateColumn));

  const rowCountsPerDate = $derived.by(() => {
    if (!dateColumn) return {} as Record<string, number>;
    const counts: Record<string, number> = {};
    for (const row of allRows) {
      const d = String(row[dateColumn] ?? '');
      if (d) counts[d] = (counts[d] ?? 0) + 1;
    }
    return counts;
  });

  // ── UI state ────────────────────────────────────────────────────────────────
  // selectedDates is initialised synchronously from the static rows data so
  // visibleRows never filters against an empty set on first render.
  let selectedDates = $state(new Set(collectAllDates(rows, dateColumn)));
  let searchText = $state('');
  let showAdvanced = $state(false);
  const sort = new SortState();
  let sliderPriceMin = $state(priceRange.min);
  let sliderPriceMax = $state(priceRange.max);
  let sliderWishlistMin = $state(wishlistRange.min);
  let sliderWishlistMax = $state(wishlistRange.max);

  // ── Derived: filtered + sorted rows ───────────────────────────────────────
  const visibleRows = $derived.by(() => {
    let result: Record<string, unknown>[] = allRows;

    // 1. Date filter
    if (dateColumn && selectedDates.size > 0 && selectedDates.size < allDates.length) {
      result = result.filter((r) => selectedDates.has(String(r[dateColumn] ?? '')));
    }

    // 2. Search (all columns)
    if (searchText.trim()) {
      result = applySearchFilter(result, columns, searchText);
    }

    // 3. Price range
    if (priceColumn) {
      result = result.filter((r) => {
        const v = parseFloat(String(r[priceColumn] ?? '0'));
        return !isNaN(v) && v >= sliderPriceMin && v <= sliderPriceMax;
      });
    }

    // 4. Wishlist range
    if (wishlistColumn) {
      result = result.filter((r) => {
        const v = parseInt(String(r[wishlistColumn] ?? '0'), 10);
        return !isNaN(v) && v >= sliderWishlistMin && v <= sliderWishlistMax;
      });
    }

    // 5. Sort
    result = sort.apply(result);

    return result;
  });

  // ── Derived: counts ────────────────────────────────────────────────────────
  const visibleCount = $derived(visibleRows.length);
  const totalRows = $derived(allRows.length);

  // ── Derived: active filter count (for badge) ──────────────────────────────
  const activeFilterCount = $derived.by(() => {
    let count = 0;
    if (searchText.trim()) count++;
    if (dateColumn && selectedDates.size > 0 && selectedDates.size < allDates.length) count++;
    if (priceColumn && (sliderPriceMin > priceRange.min || sliderPriceMax < priceRange.max))
      count++;
    if (
      wishlistColumn &&
      (sliderWishlistMin > wishlistRange.min || sliderWishlistMax < wishlistRange.max)
    )
      count++;
    return count;
  });

  // ── Derived: summary strip ─────────────────────────────────────────────────
  const summaryText = $derived.by(() => {
    if (!dateColumn || allDates.length === 0) return '';
    const activeDates =
      selectedDates.size === allDates.length
        ? allDates
        : allDates.filter((d) => selectedDates.has(d));
    const numRuns = activeDates.length;
    const rowCount = activeDates.reduce((s, d) => s + (rowCountsPerDate[d] ?? 0), 0);
    const maxDate = activeDates[0] ?? '';
    const minDate = activeDates[activeDates.length - 1] ?? '';
    return `Viewing ${rowCount} rows across ${numRuns} scrape runs (${minDate} - ${maxDate})`;
  });

  // ── Handlers ───────────────────────────────────────────────────────────────
  function handleDateChange(selected: string[]): void {
    selectedDates = new Set(selected);
  }

  function handlePriceChange(detail: { min: number; max: number }): void {
    sliderPriceMin = detail.min;
    sliderPriceMax = detail.max;
  }

  function handleWishlistChange(detail: { min: number; max: number }): void {
    sliderWishlistMin = detail.min;
    sliderWishlistMax = detail.max;
  }

  // ── CSV download ───────────────────────────────────────────────────────────
  function downloadCsv(): void {
    triggerDownload(
      buildCsv(columns, visibleRows, escapeCsvRow),
      'spidershop_spiderlings_history_filtered.csv',
    );
  }

  const formatPrice = (v: number): string => `£${v}`;
</script>

<!-- ── Summary info strip ────────────────────────────────────────────────── -->
{#if dateColumn && summaryText}
  <div id="summary-info-{tableId}" class="summary-info">
    {summaryText}
  </div>
{/if}

<!-- ── Date filter section ───────────────────────────────────────────────── -->
{#if allDates.length > 0}
  <div class="date-filter-section">
    <div class="date-filter-label"><strong>📅 Filter by Scrape Date:</strong></div>
    <DateFilter
      dates={allDates}
      rowCounts={rowCountsPerDate}
      {tableId}
      onchange={handleDateChange}
    />
  </div>
{/if}

<!-- ── More Filters toggle ───────────────────────────────────────────────── -->
<div class="controls-row">
  <ToggleButton
    expanded={showAdvanced}
    onToggle={() => (showAdvanced = !showAdvanced)}
    badge={activeFilterCount}
    badgeId="filterBadge-{tableId}"
    class="advanced-filters-toggle"
    variant="primary"
  >
    {#snippet children()}More Filters{/snippet}
  </ToggleButton>
</div>

<!-- ── Advanced filters panel ───────────────────────────────────────────── -->
{#if showAdvanced}
  <FiltersPanel>
      <div class="search-filter-row">
        <strong class="filter-label">🔍 Search:</strong>
        <SearchInput
          {tableId} 
          placeholder="Type to filter species, dates, etc."
          oninput={(v) => (searchText = v)}
        />
      </div>
      {#if priceColumn}
        <RangeSlider
          label="💷 Price Range:"
          min={priceRange.min}
          max={priceRange.max}
          onchange={handlePriceChange}
          minInputId="priceMin"
          maxInputId="priceMax"
          displayId="priceDisplay"
          formatValue={formatPrice}
        />
      {/if}
      {#if wishlistColumn}
        <RangeSlider
          label="💚 Wishlist Count:"
          min={wishlistRange.min}
          max={wishlistRange.max}
          onchange={handleWishlistChange}
          minInputId="wishlistMin"
          maxInputId="wishlistMax"
          displayId="wishlistDisplay"
        />
      {/if}
  </FiltersPanel>
{/if}

<!-- ── Table stats ───────────────────────────────────────────────────────── -->
<TableStats
  {tableId}
  {visibleCount}
  {totalRows}
  onDownload={downloadCsv}
/>

<!-- ── Table ─────────────────────────────────────────────────────────────── -->
<div class="table-scroll">
  <table id={tableId} class="data-table">
    <thead>
      <tr>
        {#each columns as col}
          <th
            class="sortable-header"
            data-sort-direction={sort.key === col.key ? sort.dir : 'none'}
            onclick={() => sort.toggle(col.key)}
          >
            {col.label}
            <span class="sort-indicator">{sort.key === col.key ? (sort.dir === 'asc' ? '↑' : '↓') : '⇅'}</span>
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each visibleRows as row}
        <tr
          data-price={priceColumn ? String(row[priceColumn] ?? '') : undefined}
          data-wishlist={wishlistColumn ? String(row[wishlistColumn] ?? '') : undefined}
        >
          {#each columns as col}
            <td>
              {#if col.type === 'sparkline'}
                <SparklineBar dto={row[col.key] as SparklineDto | string} />
              {:else if col.type === 'page-url'}
                {@const href = String(row[col.key] ?? '')}
                {@const label = col.linkLabelKey ? String(row[col.linkLabelKey] ?? href) : href}
                {#if href}<a href={href}>{label}</a>{:else}–{/if}
              {:else}
                {row[col.key] ?? ''}
              {/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .controls-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-sm);
  }

  .summary-info {
    background: var(--color-surface-light);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 0.95em;
    color: var(--color-primary);
  }

  .date-filter-section {
    background: var(--color-date-filter-bg);
    border: 2px solid var(--color-date-filter);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    margin-bottom: 15px;
    /* Pass amber theme to ToggleButton inside DateFilter via CSS variable cascade */
    --toggle-btn-bg: var(--color-date-filter);
    --toggle-btn-color: #856404;
    --toggle-btn-hover-bg: var(--color-date-filter-hover);
    --toggle-btn-border: none;  --toggle-btn-hover-border: none;    --toggle-btn-padding: 6px 14px;
    --toggle-btn-radius: var(--radius-sm);
    --toggle-btn-font-size: 0.9rem;
  }

  .date-filter-label {
    font-size: 1rem;
    margin-bottom: 8px;
  }

  .search-filter-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
    width: 100%;
  }

  .filter-label {
    color: var(--color-primary-light);
    white-space: nowrap;
  }

  .table-scroll {
    overflow-x: auto;
  }

  .sortable-header {
    cursor: pointer;
    user-select: none;
  }
</style>
