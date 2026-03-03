<script lang="ts">
  import { unicodeToSvg } from '../sparklines.js';
  import { escapeCsvRow } from '../csv-utils.js';
  import { computeRange, sortRows, buildCsv, triggerDownload } from '../table-utils.js';
  import FilterButton from './FilterButton.svelte';
  import SearchInput from './SearchInput.svelte';
  import RangeSlider from './RangeSlider.svelte';

  // ── Types ───────────────────────────────────────────────────────────────────

  export interface ColumnConfig {
    key: string;
    label: string;
    type?: 'sparkline' | 'species-link' | 'page-url';
    linkViewParam?: string;
    /** Raw CSV column header used when building a downloadable CSV (defaults to `key`). */
    csvHeader?: string;
    /** Key in the row object that holds the raw (unformatted) value for CSV export. */
    rawValueKey?: string;
  }

  export interface SignalFilterConfig {
    column: string;
    label?: string;
    top10?: boolean;
  }

  export interface StockPatternFilterConfig {
    column: string;
  }

  export interface FilterConfig {
    signalFilter?: SignalFilterConfig;
    stockPatternFilter?: StockPatternFilterConfig;
    priceColumn?: string;
    wishlistColumn?: string;
    showSearch?: boolean;
    statsLabel?: string;
  }

  interface Props {
    tableId: string;
    rows: Record<string, unknown>[];
    columns: ColumnConfig[];
    filterConfig?: FilterConfig;
  }

  let { tableId, rows, columns, filterConfig = {} }: Props = $props();

  // ── One-time range computation (data is static after mount) ────────────────

  const priceRange = computeRange(rows, filterConfig.priceColumn, 'float');
  const wishlistRange = computeRange(rows, filterConfig.wishlistColumn, 'int');

  // ── Data (raw — rows never change after mount) ─────────────────────────────
  const allRows = $state.raw(rows);

  // ── UI state ────────────────────────────────────────────────────────────────
  let activeSignal = $state('all');
  let top10Limit = $state<number | null>(null);
  let activeStockPattern = $state('all');
  let searchText = $state('');
  let showAdvanced = $state(false);
  let sortKey = $state<string | null>(null);
  let sortDir = $state<'asc' | 'desc'>('asc');

  // ── Slider state (initialised from static data ranges) ────────────────────
  let sliderPriceMin = $state(priceRange.min);
  let sliderPriceMax = $state(priceRange.max);
  let sliderWishlistMin = $state(wishlistRange.min);
  let sliderWishlistMax = $state(wishlistRange.max);

  // ── Derived: filtered + sorted rows ───────────────────────────────────────
  const visibleRows = $derived.by(() => {
    const signalCol = filterConfig.signalFilter?.column;
    const stockPatternCol = filterConfig.stockPatternFilter?.column;
    const priceCol = filterConfig.priceColumn;
    const wishlistCol = filterConfig.wishlistColumn;

    let result: Record<string, unknown>[] = allRows;

    // 1. Signal filter
    if (signalCol && activeSignal !== 'all') {
      result = result.filter((r) => String(r[signalCol] ?? '') === activeSignal);
    }

    // 2. Top-10: pins a subset from the signal-filtered list, then allows the
    //    remaining filters to narrow further (e.g. search within top-10).
    if (top10Limit !== null) {
      const pinned = new Set(result.slice(0, top10Limit));
      result = allRows.filter((r) => pinned.has(r));
    }

    // 3. Stock pattern filter
    if (stockPatternCol && activeStockPattern !== 'all') {
      result = result.filter(
        (r) => String(r[stockPatternCol] ?? '') === activeStockPattern,
      );
    }

    // 4. Search (all columns)
    if (searchText.trim()) {
      const q = searchText.trim().toLowerCase();
      result = result.filter((r) =>
        columns.some((col) => String(r[col.key] ?? '').toLowerCase().includes(q)),
      );
    }

    // 5. Price range
    if (priceCol) {
      result = result.filter((r) => {
        const v = parseFloat(String(r[priceCol] ?? '0'));
        return !isNaN(v) && v >= sliderPriceMin && v <= sliderPriceMax;
      });
    }

    // 6. Wishlist range
    if (wishlistCol) {
      result = result.filter((r) => {
        const v = parseInt(String(r[wishlistCol] ?? '0'), 10);
        return !isNaN(v) && v >= sliderWishlistMin && v <= sliderWishlistMax;
      });
    }

    // 7. Sort
    if (sortKey !== null) {
      result = sortRows(result, sortKey, sortDir);
    }

    return result;
  });

  // ── Derived: counts ────────────────────────────────────────────────────────
  const totalRows = $derived(allRows.length);
  const visibleCount = $derived(visibleRows.length);
  const statsLabel = $derived(filterConfig.statsLabel ?? 'species');

  // ── Derived: active filter count (for badge) ──────────────────────────────
  const activeFilterCount = $derived.by(() => {
    let count = 0;
    if (activeSignal !== 'all') count++;
    if (top10Limit !== null) count++;
    if (activeStockPattern !== 'all') count++;
    if (searchText.trim()) count++;
    if (filterConfig.priceColumn && (sliderPriceMin > priceRange.min || sliderPriceMax < priceRange.max)) count++;
    if (filterConfig.wishlistColumn && (sliderWishlistMin > wishlistRange.min || sliderWishlistMax < wishlistRange.max)) count++;
    return count;
  });

  // ── Handlers ───────────────────────────────────────────────────────────────
  function handleSignalFilter(signal: string, limit: number | null): void {
    activeSignal = signal;
    top10Limit = limit;
  }

  function handleStockPatternFilter(pattern: string): void {
    activeStockPattern = pattern;
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

  function resetAllFilters(): void {
    activeSignal = 'all';
    top10Limit = null;
    activeStockPattern = 'all';
    searchText = '';
    sliderPriceMin = priceRange.min;
    sliderPriceMax = priceRange.max;
    sliderWishlistMin = wishlistRange.min;
    sliderWishlistMax = wishlistRange.max;
  }

  // ── CSV download ───────────────────────────────────────────────────────────
  function downloadCsv(): void {
    triggerDownload(buildCsv(columns, visibleRows, escapeCsvRow), `${tableId}_filtered.csv`);
  }

  // ── Static button configs ──────────────────────────────────────────────────
  const SIGNAL_BUTTONS: { value: string; label: string }[] = [
    { value: 'all', label: 'Show All' },
    { value: '🔥', label: '🔥 Hot' },
    { value: '⚠️', label: '⚠️ Watch' },
    { value: '❌', label: '❌ Avoid' },
  ];

  const STOCK_PATTERN_BUTTONS: { value: string; label: string }[] = [
    { value: 'all', label: 'Show All' },
    { value: 'Sustained', label: 'Sustained' },
    { value: 'Emerging', label: 'Emerging' },
    { value: 'Cyclical', label: 'Cyclical' },
    { value: 'Always Available', label: 'Always Available' },
  ];

  const formatPrice = (v: number): string => `£${v}`;

  const slugify = (s: string): string => s.toLowerCase().replace(/\s+/g, '-');
</script>

<!-- ── Signal filter row ─────────────────────────────────────────────────── -->
{#if filterConfig.signalFilter}
  <div class="signal-filter-row">
    <span class="filter-label">Signal:</span>
    <div class="filter-buttons-container">
      {#each SIGNAL_BUTTONS as btn}
        <FilterButton
          label={btn.label}
          value={btn.value}
          active={activeSignal === btn.value && top10Limit === null}
          onclick={() => handleSignalFilter(btn.value, null)}
          data-action="filter-signal"
          data-signal={btn.value}
        />
      {/each}
      {#if filterConfig.signalFilter.top10}
        <FilterButton
          label="Top 10"
          value="top10"
          active={top10Limit === 10}
          onclick={() => handleSignalFilter('all', top10Limit === 10 ? null : 10)}
          data-action="filter-signal"
          data-signal="top10"
          data-limit="10"
        />
      {/if}
    </div>
  </div>
{/if}

<!-- ── Stock pattern filter row ─────────────────────────────────────────── -->
{#if filterConfig.stockPatternFilter}
  <div class="signal-filter-row">
    <span class="filter-label">Stock Pattern:</span>
    <div class="filter-buttons-container">
      {#each STOCK_PATTERN_BUTTONS as btn}
        <FilterButton
          label={btn.label}
          value={btn.value}
          active={activeStockPattern === btn.value}
          onclick={() => handleStockPatternFilter(btn.value)}
          data-action="filter-stock-pattern"
          data-stock-pattern={btn.value}
        />
      {/each}
    </div>
  </div>
{/if}

<!-- ── Search + advanced-filters toggle ─────────────────────────────────── -->
<div class="controls-row">
  {#if filterConfig.showSearch !== false}
    <SearchInput
      {tableId}
      placeholder="Search {statsLabel}…"
      oninput={(v) => (searchText = v)}
    />
  {/if}
  {#if filterConfig.priceColumn || filterConfig.wishlistColumn}
    <button
      class={{ btn: true, 'advanced-filters-toggle': true, 'is-expanded': showAdvanced }}
      onclick={() => (showAdvanced = !showAdvanced)}
    >
      Advanced Filters
      <span
        class={{ 'filter-badge': true, hidden: activeFilterCount === 0 }}
        id="filterBadge-{tableId}"
      >
        {activeFilterCount}
      </span>
    </button>
  {/if}
</div>

<!-- ── Advanced filters panel ───────────────────────────────────────────── -->
{#if showAdvanced}
  <div class="advanced-filters-content">
    {#if filterConfig.priceColumn}
      <RangeSlider
        label="Price (£)"
        min={priceRange.min}
        max={priceRange.max}
        onchange={handlePriceChange}
        minInputId="priceMin"
        maxInputId="priceMax"
        displayId="priceDisplay"
        formatValue={formatPrice}
      />
    {/if}
    {#if filterConfig.wishlistColumn}
      <RangeSlider
        label="Wishlist Count"
        min={wishlistRange.min}
        max={wishlistRange.max}
        onchange={handleWishlistChange}
        minInputId="wishlistMin"
        maxInputId="wishlistMax"
        displayId="wishlistDisplay"
      />
    {/if}
  </div>
{/if}

<!-- ── Table stats ───────────────────────────────────────────────────────── -->
<div class="table-stats">
  <span>
    <strong>Showing:</strong>
    <span id="visible-count-{tableId}">{visibleCount}</span> of {totalRows} {statsLabel}
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
        <tr>
          {#each columns as col}
            <td>
              {#if col.type === 'sparkline'}
                {@html unicodeToSvg(String(row[col.key] ?? ''))}
              {:else if col.type === 'species-link'}
                {@const slug = slugify(String(row[col.key] ?? ''))}
                {@const viewSuffix = col.linkViewParam ? `?view=${col.linkViewParam}` : ''}
                {#if slug}<a href="species/{slug}.html{viewSuffix}">{row[col.key] ?? ''}</a>{:else}{row[col.key] ?? ''}{/if}
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

<p class="table-row-count"><strong>Total rows:</strong> {totalRows}</p>

<style>
  .signal-filter-row {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .filter-label {
    color: var(--color-primary-light);
    margin-right: 10px;
    white-space: nowrap;
  }

  .filter-buttons-container {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
  }

  .controls-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-sm);
  }

  .advanced-filters-toggle {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
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

  .advanced-filters-content {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
    padding: var(--spacing-md) 0;
    border-top: 1px solid var(--color-border-light);
    border-bottom: 1px solid var(--color-border-light);
    margin-bottom: var(--spacing-sm);
  }

  .table-stats {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    font-size: var(--font-sm);
    color: var(--color-text-muted);
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

  .table-row-count {
    margin-top: 15px;
    color: var(--color-text-muted);
    font-size: var(--font-sm);
  }
</style>
