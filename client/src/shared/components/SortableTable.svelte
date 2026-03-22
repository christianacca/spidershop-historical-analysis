<script lang="ts">
  import SparklineBar from './SparklineBar.svelte';
  import type { SparklineDto } from '../types.js';
  import { escapeCsvRow } from '../csv-utils.js';
  import { computeRange, buildCsv, triggerDownload, applySearchFilter } from '../table-utils.js';
  import { SortState } from '../sort-state.svelte.js';
  import FilterButton from './FilterButton.svelte';
  import SearchInput from './SearchInput.svelte';
  import ToggleButton from './ToggleButton.svelte';
  import RangeSlider from './RangeSlider.svelte';
  import FiltersPanel from './FiltersPanel.svelte';
  import TableStats from './TableStats.svelte';
  import InfoTooltip from './InfoTooltip.svelte';
  import FilterSection from './FilterSection.svelte';

  // ── Types ───────────────────────────────────────────────────────────────────

  export interface ColumnConfig {
    key: string;
    label?: string;
    type?: 'sparkline' | 'species-link' | 'page-url';
    linkViewParam?: string;
    /** Row key to use as the visible link text for page-url columns (defaults to the raw URL). */
    linkLabelKey?: string;
    /** Raw CSV column header used when building a downloadable CSV (defaults to `key`). */
    csvHeader?: string;
    /** Key in the row object that holds the raw (unformatted) value for CSV export. */
    rawValueKey?: string;
    /** When true the column is included in row data but has no <th> or <td> rendered. */
    hidden?: boolean;
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
    /** Row key whose value is shown as a tooltip ℹ️ icon in the signal column cell. */
    driversKey?: string;
  }

  interface Props {
    tableId: string;
    rows: Record<string, unknown>[];
    columns: ColumnConfig[];
    filterConfig?: FilterConfig;
    /** When true, renders the More Filters toggle with the primary (blue) button style. */
    primaryToggle?: boolean;
  }

  let { tableId, rows, columns, filterConfig = {}, primaryToggle = false }: Props = $props();

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
  const sort = new SortState();

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

    // 1. Signal filter
    const afterSignal: Record<string, unknown>[] = signalCol && activeSignal !== 'all'
      ? allRows.filter((r) => String(r[signalCol] ?? '') === activeSignal)
      : allRows;

    // 2. Top-10: pins a subset from the signal-filtered list, then allows the
    //    remaining filters to narrow further (e.g. search within top-10).
    const top10Pinned = top10Limit !== null ? new Set(afterSignal.slice(0, top10Limit)) : null;
    const afterTop10 = top10Pinned !== null ? allRows.filter((r) => top10Pinned.has(r)) : afterSignal;

    // 3. Stock pattern filter
    const afterStockPattern = stockPatternCol && activeStockPattern !== 'all'
      ? afterTop10.filter((r) => normalizeStockPattern(r[stockPatternCol]) === activeStockPattern)
      : afterTop10;

    // 4. Search (all columns)
    const afterSearch = searchText.trim()
      ? applySearchFilter(afterStockPattern, columns, searchText)
      : afterStockPattern;

    // 5. Price range — NaN (non-numeric cell, e.g. empty) passes through unchanged.
    const afterPriceRange = priceCol
      ? afterSearch.filter((r) => {
          const v = parseFloat(String(r[priceCol] ?? '').replace(/^[^0-9.]*/, ''));
          return isNaN(v) || (v >= sliderPriceMin && v <= sliderPriceMax);
        })
      : afterSearch;

    // 6. Wishlist range — NaN (emoji values, empty cells) passes through unchanged.
    const afterWishlist = wishlistCol
      ? afterPriceRange.filter((r) => {
          const v = parseInt(String(r[wishlistCol] ?? '').replace(/^[^0-9.]*/, ''), 10);
          return isNaN(v) || (v >= sliderWishlistMin && v <= sliderWishlistMax);
        })
      : afterPriceRange;

    // 7. Sort
    const sorted = sort.apply(afterWishlist);

    return sorted;
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
    triggerDownload(buildCsv(columns.filter(col => !col.hidden), visibleRows, escapeCsvRow), `${tableId}_filtered.csv`);
  }

  // ── Derived: per-signal row counts (from all rows, not filtered) ──────────
  const signalCounts = $derived.by(() => {
    if (!filterConfig.signalFilter) return { all: 0, hot: 0, watch: 0, avoid: 0 };
    const key = filterConfig.signalFilter.column;
    return {
      all: allRows.length,
      hot: allRows.filter(r => String(r[key] ?? '').includes('🔥')).length,
      watch: allRows.filter(r => String(r[key] ?? '').includes('⚠️')).length,
      avoid: allRows.filter(r => String(r[key] ?? '').includes('❌')).length,
    };
  });

  // ── Derived: signal filter buttons with row counts in labels ─────────────
  const signalButtons = $derived([
    { value: 'all', label: `Show All (${signalCounts.all})`, count: signalCounts.all },
    { value: '🔥', label: `🔥 Hot (${signalCounts.hot})`, count: signalCounts.hot },
    { value: '⚠️', label: `⚠️ Watch (${signalCounts.watch})`, count: signalCounts.watch },
    { value: '❌', label: `❌ Avoid (${signalCounts.avoid})`, count: signalCounts.avoid },
  ]);

  // ── Derived: per-stock-pattern row counts (from all rows, not filtered) ───
  const stockPatternCounts = $derived.by(() => {
    if (!filterConfig.stockPatternFilter) return {} as Record<string, number>;
    const key = filterConfig.stockPatternFilter.column;
    const counts: Record<string, number> = { all: allRows.length };
    for (const row of allRows) {
      const val = normalizeStockPattern(row[key]);
      counts[val] = (counts[val] ?? 0) + 1;
    }
    return counts;
  });

  // ── Derived: stock pattern buttons with row counts in labels ─────────────
  const stockPatternButtons = $derived([
    { value: 'all',              label: `Show All (${stockPatternCounts.all ?? 0})` },
    { value: 'Sustained',        label: `Sustained (${stockPatternCounts['Sustained'] ?? 0})` },
    { value: 'Emerging',         label: `Emerging (${stockPatternCounts['Emerging'] ?? 0})` },
    { value: 'Cyclical',         label: `Cyclical (${stockPatternCounts['Cyclical'] ?? 0})` },
    { value: 'Always',           label: `Always (${stockPatternCounts['Always'] ?? 0})` },
    { value: 'Newly Observed',   label: `Newly Observed (${stockPatternCounts['Newly Observed'] ?? 0})` },
  ]);

  // ── Derived: whether there is any collapsible content to show ────────────
  const hasAdvancedContent = $derived(
    !!filterConfig.stockPatternFilter ||
    filterConfig.showSearch === true ||
    !!filterConfig.priceColumn ||
    !!filterConfig.wishlistColumn,
  );

  const formatPrice = (v: number): string => `£${v}`;

  const slugify = (s: string): string =>
    s.toLowerCase().replace(/[^a-z0-9\s.]/g, '').replace(/\s+/g, '-');

  const normalizeStockPattern = (value: unknown): string => {
    const pattern = String(value ?? '');
    return pattern === 'Always Available' ? 'Always' : pattern;
  };
</script>

<!-- ── Signal filter row ─────────────────────────────────────────────────── -->
{#if filterConfig.signalFilter}
  <FilterSection label="🎯 Signal:">
    {#snippet children()}
      {#each signalButtons as btn, i}
        <FilterButton
          label={btn.label}
          value={btn.value}
          active={activeSignal === btn.value && top10Limit === null}
          onclick={() => handleSignalFilter(btn.value, null)}
          data-action="filter-signal"
          data-signal={btn.value}
          data-count={btn.count}
        />
        {#if i === 0 && filterConfig.signalFilter.top10}
          <FilterButton
            label="🔥 Hot (top 10)"
            value="top10"
            active={top10Limit === 10}
            onclick={() => handleSignalFilter('all', top10Limit === 10 ? null : 10)}
            data-action="filter-signal"
            data-signal="top10"
            data-limit="10"
          />
        {/if}
      {/each}
      {#if hasAdvancedContent}
        <ToggleButton
          expanded={showAdvanced}
          onToggle={() => (showAdvanced = !showAdvanced)}
          badge={activeFilterCount}
          badgeId="filterBadge-{tableId}"
          class="advanced-filters-toggle"
          variant={primaryToggle ? 'primary' : 'default'}
        >
          {#snippet children()}More Filters{/snippet}
        </ToggleButton>
      {/if}
    {/snippet}
  </FilterSection>
{/if}

<!-- ── Fallback controls row (for pages without a signal filter) ─────────── -->
{#if !filterConfig.signalFilter && hasAdvancedContent}
  <div class="controls-row">
    <ToggleButton
      expanded={showAdvanced}
      onToggle={() => (showAdvanced = !showAdvanced)}
      badge={activeFilterCount}
      badgeId="filterBadge-{tableId}"
      class="advanced-filters-toggle"
      variant={primaryToggle ? 'primary' : 'default'}
    >
      {#snippet children()}More Filters{/snippet}
    </ToggleButton>
  </div>
{/if}

<!-- ── Advanced filters panel ───────────────────────────────────────────── -->
{#if showAdvanced}
  <FiltersPanel>
    {#if filterConfig.stockPatternFilter}
      <FilterSection label="📊 Stock Pattern:">
        {#snippet children()}
          {#each stockPatternButtons as btn}
            <FilterButton
              label={btn.label}
              value={btn.value}
              active={activeStockPattern === btn.value}
              onclick={() => handleStockPatternFilter(btn.value)}
              data-action="filter-stock-pattern"
              data-stock-pattern={btn.value}
            />
          {/each}
        {/snippet}
      </FilterSection>
    {/if}
    {#if filterConfig.showSearch !== false}
      <div class="search-filter-row">
        <strong class="filter-label">🔍 Search:</strong>
        <SearchInput
          {tableId}
          placeholder="Type to filter {statsLabel}, names, etc."
          oninput={(v) => (searchText = v)}
        />
      </div>
    {/if}
    {#if filterConfig.priceColumn}
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
    {#if filterConfig.wishlistColumn}
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
  {statsLabel}
  onDownload={downloadCsv}
/>

<!-- ── Table ─────────────────────────────────────────────────────────────── -->
<div class="table-scroll">
  <table id={tableId} class="data-table">
    <thead>
      <tr>
        {#each columns as col}
          {#if !col.hidden}
            <th
              class="sortable-header"
              data-sort-direction={sort.key === col.key ? sort.dir : 'none'}
              onclick={() => sort.toggle(col.key)}
            >
              {col.label ?? col.key}
              <span class="sort-indicator">{sort.key === col.key ? (sort.dir === 'asc' ? '↑' : '↓') : '⇅'}</span>
            </th>
          {/if}
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each visibleRows as row}
        <tr>
          {#each columns as col}
            {#if !col.hidden}
              {@const isSignalCol = col.key === (filterConfig.signalFilter?.column ?? '')}
              {@const cellValue = String(row[col.key] ?? '')}
              <td
                class:signal-hot={isSignalCol && cellValue.includes('🔥')}
                class:signal-watch={isSignalCol && cellValue.includes('⚠️')}
                class:signal-avoid={isSignalCol && cellValue.includes('❌')}
              >
                {#if col.type === 'sparkline'}
                  <SparklineBar dto={row[col.key] as SparklineDto | string} />
                {:else if col.type === 'species-link'}
                  {@const slug = slugify(cellValue)}
                  {@const viewSuffix = col.linkViewParam ? `?view=${col.linkViewParam}` : ''}
                  {#if slug}<a href="species/{slug}.html{viewSuffix}">{cellValue}</a>{:else}{cellValue}{/if}
                {:else}
                  {cellValue}<InfoTooltip tip={isSignalCol && filterConfig.driversKey ? String(row[filterConfig.driversKey] ?? '') : ''} />
                {/if}
              </td>
            {/if}
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

  .search-filter-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
    width: 100%;
  }

  .table-scroll {
    overflow-x: auto;
  }

  .sortable-header {
    cursor: pointer;
    user-select: none;
  }
</style>
