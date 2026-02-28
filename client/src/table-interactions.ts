/**
 * Table Interactions Module
 * 
 * Provides sorting, filtering, and other interactive features for tables.
 * Refactored to use shared utilities and eliminate duplication.
 */

import { CSS, CONFIG, CHART } from './constants.js';
import { getElement, toggleRowVisibility, RangeSlider } from './utils.js';

// Singleton slider instances
let priceSlider: RangeSlider | null = null;
let wishlistSlider: RangeSlider | null = null;

/**
 * Sort table by column index
 */
export function sortTable(columnIndex: number, tableId: string): void {
  const table = getElement(tableId);
  if (!table) return;

  const tbody = table.querySelector('tbody');
  if (!tbody) return;
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const headers = table.querySelectorAll('th');

  // Bounds check
  if (columnIndex < 0 || columnIndex >= headers.length) {
    console.warn(`Invalid column index: ${columnIndex}`);
    return;
  }

  // Determine if column is numeric by sampling first few rows
  let isNumeric = true;
  for (let i = 0; i < Math.min(CONFIG.NUMERIC_DETECTION_SAMPLE_SIZE, rows.length); i++) {
    const cellText = rows[i].cells[columnIndex].textContent?.trim() ?? '';
    if (cellText && isNaN(parseFloat(cellText.replace(/[^0-9.-]/g, '')))) {
      isNumeric = false;
      break;
    }
  }

  // Get current sort direction and toggle
  const header = headers[columnIndex];
  const currentDirection = header.getAttribute('data-sort-direction') ?? 'asc';
  const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

  // Clear all sort indicators
  headers.forEach(th => th.removeAttribute('data-sort-direction'));

  // Set new sort direction
  header.setAttribute('data-sort-direction', newDirection);

  // Sort rows
  rows.sort((a, b) => {
    const aText = a.cells[columnIndex].textContent?.trim() ?? '';
    const bText = b.cells[columnIndex].textContent?.trim() ?? '';

    if (isNumeric) {
      const aValue = parseFloat(aText.replace(/[^0-9.-]/g, '')) || 0;
      const bValue = parseFloat(bText.replace(/[^0-9.-]/g, '')) || 0;
      return newDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }

    const aLower = aText.toLowerCase();
    const bLower = bText.toLowerCase();
    return newDirection === 'asc' ? aLower.localeCompare(bLower) : bLower.localeCompare(aLower);
  });

  // Reappend sorted rows
  rows.forEach(row => tbody.appendChild(row));
}

/**
 * Filter table rows by price range
 * Uses lazy initialization for RangeSlider instance
 */
export function filterByPrice(tableId: string): void {
  if (!priceSlider) {
    priceSlider = new RangeSlider({
      minId: 'priceMin',
      maxId: 'priceMax',
      displayId: 'priceDisplay',
      parse: parseFloat,
      format: (min, max) => `Showing: £${Math.round(min)} - £${Math.round(max)}`
    });
  }

  priceSlider.enforceConstraints(window.event);
  filterRows(tableId);
}

/**
 * Filter table rows by wishlist count range
 * Uses lazy initialization for RangeSlider instance
 */
export function filterByWishlist(tableId: string): void {
  if (!wishlistSlider) {
    wishlistSlider = new RangeSlider({
      minId: 'wishlistMin',
      maxId: 'wishlistMax',
      displayId: 'wishlistDisplay',
      parse: parseInt,
      format: (min, max) => `Showing: ${min} - ${max}`
    });
  }

  wishlistSlider.enforceConstraints(window.event);
  filterRows(tableId);
}

/**
 * Apply all active filters to table rows
 * Combines search, price, and wishlist filters
 */
export function filterRows(tableId: string): void {
  const table = getElement(tableId);
  if (!table) return;

  const rows = table.querySelectorAll('tbody tr');
  const searchTerm = (getElement(`search-${tableId}`) as HTMLInputElement | null)?.value.toLowerCase() ?? '';
  const [priceMin, priceMax] = priceSlider?.getValues() ?? [0, Infinity];
  const [wishlistMin, wishlistMax] = wishlistSlider?.getValues() ?? [0, Infinity];

  // Determine active date selection
  const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;
  const allDatesChecked = allDatesEl?.checked ?? true;
  const selectedDates = allDatesChecked
    ? []
    : Array.from(document.querySelectorAll<HTMLInputElement>(`[data-date-value]:checked`))
        .map(cb => cb.dataset.dateValue);

  rows.forEach(row => {
    const matchesSearch = !searchTerm || row.textContent?.toLowerCase().includes(searchTerm) === true;
    const price = parseFloat(row.getAttribute('data-price')?.replace('\u00a3', '').trim() ?? '') || 0;
    const matchesPrice = price >= priceMin && price <= priceMax;
    const wishlist = parseInt(row.getAttribute('data-wishlist')?.trim() ?? '') || 0;
    const matchesWishlist = wishlist >= wishlistMin && wishlist <= wishlistMax;
    const date = row.getAttribute('data-date') ?? '';
    const matchesDate = allDatesChecked || selectedDates.length === 0 || selectedDates.includes(date);

    toggleRowVisibility(row as HTMLElement, matchesSearch && matchesPrice && matchesWishlist && matchesDate);
  });

  updateFilterBadge(tableId);
  updateVisibleCount(tableId);
}

/**
 * Toggle advanced filters panel visibility
 */
export function toggleAdvancedFilters(contentId: string, toggleButton: HTMLElement): void {
  const content = getElement(contentId);
  if (!content) return;

  const isExpanded = content.classList.contains(CSS.SHOW);

  content.classList.toggle(CSS.SHOW, !isExpanded);
  toggleButton.classList.toggle(CSS.EXPANDED, !isExpanded);
}

/**
 * Update filter badge count
 * Shows badge with count when filters are active
 */
function updateFilterBadge(tableId: string): void {
  const badge = getElement(`filterBadge-${tableId}`);
  if (!badge) return; // Badge might not exist on all pages

  let activeFilters = 0;

  // Check search filter
  const searchBox = getElement(`search-${tableId}`) as HTMLInputElement | null;
  if (searchBox?.value.trim()) {
    activeFilters++;
  }

  // Check price range sliders
  const priceMinSlider = getElement('priceMin') as HTMLInputElement | null;
  const priceMaxSlider = getElement('priceMax') as HTMLInputElement | null;
  if (priceMinSlider && priceMaxSlider) {
    const dataMin = parseFloat(priceMinSlider.getAttribute('min') ?? '');
    const dataMax = parseFloat(priceMaxSlider.getAttribute('max') ?? '');
    const currentMin = parseFloat(priceMinSlider.value);
    const currentMax = parseFloat(priceMaxSlider.value);
    if (currentMin > dataMin || currentMax < dataMax) {
      activeFilters++;
    }
  }

  // Check wishlist range sliders
  const wishlistMinSlider = getElement('wishlistMin') as HTMLInputElement | null;
  const wishlistMaxSlider = getElement('wishlistMax') as HTMLInputElement | null;
  if (wishlistMinSlider && wishlistMaxSlider) {
    const dataMin = parseInt(wishlistMinSlider.getAttribute('min') ?? '');
    const dataMax = parseInt(wishlistMaxSlider.getAttribute('max') ?? '');
    const currentMin = parseInt(wishlistMinSlider.value);
    const currentMax = parseInt(wishlistMaxSlider.value);
    if (currentMin > dataMin || currentMax < dataMax) {
      activeFilters++;
    }
  }

  // Update badge display
  if (activeFilters > 0) {
    badge.textContent = String(activeFilters);
    badge.classList.remove(CSS.HIDDEN);
  } else {
    badge.classList.add(CSS.HIDDEN);
  }
}

/**
 * Update visible count display for a table
 * Counts rows that are not hidden and updates the stats strip
 */
function updateVisibleCount(tableId: string): void {
  const countElement = getElement(`visible-count-${tableId}`);
  if (!countElement) return; // Stats strip might not exist on all pages

  const table = getElement(tableId);
  if (!table) return;

  const rows = table.querySelectorAll('tbody tr');
  const visibleCount = Array.from(rows).filter(
    row => !row.classList.contains(CSS.HIDDEN)
  ).length;

  countElement.textContent = String(visibleCount);
}

/**
 * Download the currently visible (filtered) rows of a table as a CSV file.
 *
 * Cell values are extracted to match the raw server CSV as closely as possible:
 *  - scrape_datetime cells: original ISO string from the data-raw attribute
 *  - page_url cells: the href of the rendered <a> tag, not its text content
 *  - all other cells: plain textContent
 */
export function downloadFilteredCsv(tableId: string): void {
  const table = getElement(tableId);
  if (!table) return;

  // Prefer data-csv-name (raw column name for download) over display text.
  // Fall back to stripping the sort indicator (⇅) from header text.
  const headers = Array.from(table.querySelectorAll('thead th'))
    .map(th => (th as HTMLElement).dataset.csvName ?? th.textContent?.replace('\u21c5', '').trim() ?? '');

  const visibleRows = Array.from(table.querySelectorAll('tbody tr:not(.' + CSS.HIDDEN + ')'));

  const csvLines = [_escapeCsvRow(headers)];
  visibleRows.forEach(row => {
    const values = Array.from(row.querySelectorAll('td')).map(td => {
      // Raw ISO datetime stored before display-formatting
      if (td.hasAttribute('data-raw')) {
        return td.getAttribute('data-raw') ?? '';
      }
      // page_url: extract href rather than link label text
      const anchor = td.querySelector('a[href]');
      if (anchor) {
        return anchor.getAttribute('href') ?? '';
      }
      return td.textContent?.trim() ?? '';
    });
    csvLines.push(_escapeCsvRow(values));
  });

  const csvContent = csvLines.join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const tempLink = document.createElement('a');
  tempLink.href = url;
  tempLink.download = 'spidershop_spiderlings_history_filtered.csv';
  tempLink.style.display = 'none';
  document.body.appendChild(tempLink);
  tempLink.click();
  document.body.removeChild(tempLink);
  URL.revokeObjectURL(url);
}

/**
 * Escape an array of values as a single CSV row.
 * Cells containing commas, double-quotes, or newlines are wrapped in double-quotes;
 * internal double-quotes are doubled.
 */
function _escapeCsvRow(values: string[]): string {
  return values.map(value => {
    const str = String(value ?? '');
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  }).join(',');
}

/**
 * Update the date filter summary info box
 */
export function updateDateSummary(tableId: string): void {
  const summaryEl = document.getElementById(`summary-info-${tableId}`) as HTMLElement | null;
  if (!summaryEl) return;

  const allDateCheckboxes = Array.from(
    document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
  );
  const totalRuns = allDateCheckboxes.length;
  const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;

  if (allDatesEl?.checked) {
    // All dates selected: read totals from data attributes on the element
    const totalRows = parseInt(summaryEl.dataset.totalRows ?? '0', 10);
    const minDate = summaryEl.dataset.minDate ?? '';
    const maxDate = summaryEl.dataset.maxDate ?? '';
    summaryEl.textContent =
      `Viewing ${totalRows} rows across ${totalRuns} scrape runs (${minDate} - ${maxDate})`;
    return;
  }

  const selectedCheckboxes = allDateCheckboxes.filter(cb => cb.checked);
  const numSelected = selectedCheckboxes.length;

  if (numSelected === 0) {
    summaryEl.textContent = 'Viewing 0 rows across 0 scrape runs';
    return;
  }

  // Sum row counts from each checkbox's sibling .date-count span
  let totalRows = 0;
  selectedCheckboxes.forEach(cb => {
    const countSpan = cb.closest('.date-row')?.querySelector('.date-count');
    if (countSpan) {
      const match = countSpan.textContent?.match(/\d+/);
      if (match) totalRows += parseInt(match[0], 10);
    }
  });

  // Date array is ordered newest-first in the DOM; last = oldest = min, first = newest = max
  const selectedDates = selectedCheckboxes.map(cb => cb.dataset.dateValue);
  const maxDate = selectedDates[0];
  const minDate = selectedDates[selectedDates.length - 1];

  summaryEl.textContent =
    `Viewing ${totalRows} rows across ${numSelected} scrape runs (${minDate} - ${maxDate})`;
}


