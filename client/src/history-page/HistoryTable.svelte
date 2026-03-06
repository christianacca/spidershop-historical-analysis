<script lang="ts">
  import { unicodeToSvg } from '../shared/sparklines.js';
  import { escapeCsvRow } from '../shared/csv-utils.js';
  import { computeRange, sortRows, buildCsv, triggerDownload } from '../shared/table-utils.js';
  import type { ColumnConfig } from '../shared/components/SortableTable.svelte';
  import DateFilter from './DateFilter.svelte';
  import RangeSlider from '../shared/components/RangeSlider.svelte';
  import FiltersPanel from '../shared/components/FiltersPanel.svelte';
  import SearchInput from '../shared/components/SearchInput.svelte';

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

  // ── Helper: collect unique dates from rows (oldest-to-newest reversed) ─────

  function collectAllDates(
    sourceRows: Record<string, unknown>[],
    dateCol: string | undefined,
  ): string[] {
    if (!dateCol) return [];
    const seen = new Set<string>();
    const ordered: string[] = [];
    for (let i = sourceRows.length - 1; i >= 0; i--) {
      const d = String(sourceRows[i][dateCol] ?? '');
      if (d && !seen.has(d)) {
        seen.add(d);
        ordered.push(d);
      }
    }
    return ordered;
  }

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
  let sortKey = $state<string | null>(null);
  let sortDir = $state<'asc' | 'desc'>('asc');
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
      const q = searchText.trim().toLowerCase();
      result = result.filter((r) =>
        columns.some((col) => String(r[col.key] ?? '').toLowerCase().includes(q)),
      );
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
    if (sortKey !== null) {
      result = sortRows(result, sortKey, sortDir);
    }

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

  function handleSort(key: string): void {
    if (sortKey === key) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortKey = key;
      sortDir = 'asc';
    }
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
<button
  class="btn btn--filters"
  data-action="toggle-filters"
  data-content-id="advanced-filters-{tableId}"
  onclick={() => (showAdvanced = !showAdvanced)}
>
  <span class="arrow">▶</span>
  <span>More Filters</span>
  <span
    class={{ 'filter-badge': true, hidden: activeFilterCount === 0 }}
    id="filterBadge-{tableId}"
  >
    {activeFilterCount}
  </span>
</button>

<!-- ── Advanced filters panel ───────────────────────────────────────────── -->
{#if showAdvanced}
  <div id="advanced-filters-{tableId}" class="advanced-filters">
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
  </div>
{/if}

<!-- ── Table stats ───────────────────────────────────────────────────────── -->
<div class="table-stats">
  <span>
    <strong>Showing:</strong>
    <span id="visible-count-{tableId}">{visibleCount}</span> of {totalRows} rows
  </span>
  <a
    href="#download"
    download
    class="btn btn--download"
    data-action="download-filtered-csv"
    data-table-id={tableId}
    onclick={(e) => { e.preventDefault(); downloadCsv(); }}
  >⬇️ Download Filtered CSV</a>
</div>

<!-- ── Table ─────────────────────────────────────────────────────────────── -->
<div class="table-scroll">
  <table id={tableId} class="data-table">
    <thead>
      <tr>
        {#each columns as col}
          <th
            class="sortable-header"
            data-sort-direction={sortKey === col.key ? sortDir : 'none'}
            onclick={() => handleSort(col.key)}
          >
            {col.label}
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
                {@html unicodeToSvg(String(row[col.key] ?? ''))}
              {:else if col.type === 'page-url'}
                {@const href = String(row[col.key] ?? '')}
                {#if href}<a href={href}>{href}</a>{:else}–{/if}
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
  }

  .date-filter-label {
    font-size: 1rem;
    margin-bottom: 8px;
  }

  .advanced-filters {
    margin-top: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
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

  .filter-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--color-accent);
    color: #fff;
    border-radius: 50%;
    width: 1.2em;
    height: 1.2em;
    font-size: 0.75em;
    font-weight: 700;
  }

  .filter-badge.hidden {
    display: none;
  }

  .table-stats {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    font-size: var(--font-sm);
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
    background: var(--color-info-bg);
    padding: var(--spacing-md);
    border-radius: var(--radius-sm);
  }

  .table-scroll {
    overflow-x: auto;
  }

  .sortable-header {
    cursor: pointer;
    user-select: none;
  }
</style>
