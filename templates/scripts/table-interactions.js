/**
 * Table Interactions Module
 * 
 * Provides sorting, filtering, and other interactive features for tables.
 * Refactored to use shared utilities and eliminate duplication.
 */

import { CSS, CONFIG, CHART } from './constants.js';
import { getElement, toggleRowVisibility, RangeSlider } from './utils.js';

// Singleton slider instances
let priceSlider = null;
let wishlistSlider = null;

/**
 * Sort table by column index
 * @param {number} columnIndex - Column to sort by (0-based)
 * @param {string} tableId - ID of the table element
 */
export function sortTable(columnIndex, tableId) {
  const table = getElement(tableId);
  if (!table) return;
  
  const tbody = table.querySelector('tbody');
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
    const cellText = rows[i].cells[columnIndex].textContent.trim();
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
    const aText = a.cells[columnIndex].textContent.trim();
    const bText = b.cells[columnIndex].textContent.trim();
    
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
 * @param {string} tableId - ID of the table element
 */
export function filterByPrice(tableId) {
  if (!priceSlider) {
    priceSlider = new RangeSlider({
      minId: 'priceMin',
      maxId: 'priceMax',
      displayId: 'priceDisplay',
      parse: parseFloat,
      format: (min, max) => `Showing: £${Math.round(min)} - £${Math.round(max)}`
    });
  }
  
  priceSlider.enforceConstraints(event);
  filterRows(tableId);
}

/**
 * Filter table rows by wishlist count range
 * Uses lazy initialization for RangeSlider instance
 * @param {string} tableId - ID of the table element
 */
export function filterByWishlist(tableId) {
  if (!wishlistSlider) {
    wishlistSlider = new RangeSlider({
      minId: 'wishlistMin',
      maxId: 'wishlistMax',
      displayId: 'wishlistDisplay',
      parse: parseInt,
      format: (min, max) => `Showing: ${min} - ${max}`
    });
  }
  
  wishlistSlider.enforceConstraints(event);
  filterRows(tableId);
}

/**
 * Apply all active filters to table rows
 * Combines search, price, and wishlist filters
 * @param {string} tableId - ID of the table element
 */
export function filterRows(tableId) {
  const table = getElement(tableId);
  if (!table) return;
  
  const rows = table.querySelectorAll('tbody tr');
  const searchTerm = getElement(`search-${tableId}`)?.value.toLowerCase() ?? '';
  const [priceMin, priceMax] = priceSlider?.getValues() ?? [0, Infinity];
  const [wishlistMin, wishlistMax] = wishlistSlider?.getValues() ?? [0, Infinity];

  // Determine active date selection
  const allDatesEl = document.getElementById(`allDates-${tableId}`);
  const allDatesChecked = allDatesEl?.checked ?? true;
  const selectedDates = allDatesChecked
    ? []
    : Array.from(document.querySelectorAll(`[data-date-value]:checked`))
        .map(cb => cb.dataset.dateValue);
  
  rows.forEach(row => {
    const matchesSearch = !searchTerm || row.textContent.toLowerCase().includes(searchTerm);
    const price = parseFloat(row.getAttribute('data-price')?.replace('\u00a3', '').trim()) || 0;
    const matchesPrice = price >= priceMin && price <= priceMax;
    const wishlist = parseInt(row.getAttribute('data-wishlist')?.trim()) || 0;
    const matchesWishlist = wishlist >= wishlistMin && wishlist <= wishlistMax;
    const date = row.getAttribute('data-date') ?? '';
    const matchesDate = allDatesChecked || selectedDates.length === 0 || selectedDates.includes(date);
    
    toggleRowVisibility(row, matchesSearch && matchesPrice && matchesWishlist && matchesDate);
  });
  
  updateFilterBadge(tableId);
  updateVisibleCount(tableId);
}

/**
 * Toggle advanced filters panel visibility
 * @param {string} contentId - ID of the filters content panel
 * @param {HTMLElement} toggleButton - Button that triggered the toggle
 */
export function toggleAdvancedFilters(contentId, toggleButton) {
  const content = getElement(contentId);
  if (!content) return;
  
  const isExpanded = content.classList.contains(CSS.SHOW);
  
  content.classList.toggle(CSS.SHOW, !isExpanded);
  toggleButton.classList.toggle(CSS.EXPANDED, !isExpanded);
}

/**
 * Update filter badge count
 * Shows badge with count when filters are active
 * @param {string} tableId - ID of the table element
 */
function updateFilterBadge(tableId) {
  const badge = getElement(`filterBadge-${tableId}`);
  if (!badge) return; // Badge might not exist on all pages
  
  let activeFilters = 0;
  
  // Check search filter
  const searchBox = getElement(`search-${tableId}`);
  if (searchBox?.value.trim()) {
    activeFilters++;
  }
  
  // Check price range sliders
  const priceMinSlider = getElement('priceMin');
  const priceMaxSlider = getElement('priceMax');
  if (priceMinSlider && priceMaxSlider) {
    const dataMin = parseFloat(priceMinSlider.getAttribute('min'));
    const dataMax = parseFloat(priceMaxSlider.getAttribute('max'));
    const currentMin = parseFloat(priceMinSlider.value);
    const currentMax = parseFloat(priceMaxSlider.value);
    if (currentMin > dataMin || currentMax < dataMax) {
      activeFilters++;
    }
  }
  
  // Check wishlist range sliders
  const wishlistMinSlider = getElement('wishlistMin');
  const wishlistMaxSlider = getElement('wishlistMax');
  if (wishlistMinSlider && wishlistMaxSlider) {
    const dataMin = parseInt(wishlistMinSlider.getAttribute('min'));
    const dataMax = parseInt(wishlistMaxSlider.getAttribute('max'));
    const currentMin = parseInt(wishlistMinSlider.value);
    const currentMax = parseInt(wishlistMaxSlider.value);
    if (currentMin > dataMin || currentMax < dataMax) {
      activeFilters++;
    }
  }
  
  // Update badge display
  if (activeFilters > 0) {
    badge.textContent = activeFilters;
    badge.classList.remove(CSS.HIDDEN);
  } else {
    badge.classList.add(CSS.HIDDEN);
  }
}

/**
 * Update visible count display for a table
 * Counts rows that are not hidden and updates the stats strip
 * @param {string} tableId - ID of the table element
 */
function updateVisibleCount(tableId) {
  const countElement = getElement(`visible-count-${tableId}`);
  if (!countElement) return; // Stats strip might not exist on all pages
  
  const table = getElement(tableId);
  if (!table) return;
  
  const rows = table.querySelectorAll('tbody tr');
  const visibleCount = Array.from(rows).filter(
    row => !row.classList.contains(CSS.HIDDEN)
  ).length;
  
  countElement.textContent = visibleCount;
}

/**
 * Update the date filter summary info box
 * @param {string} tableId - ID of the table element
 */
export function updateDateSummary(tableId) {
  const summaryEl = document.getElementById(`summary-info-${tableId}`);
  if (!summaryEl) return;

  const allDateCheckboxes = Array.from(
    document.querySelectorAll(`[data-date-value][data-table-id="${tableId}"]`)
  );
  const totalRuns = allDateCheckboxes.length;
  const allDatesEl = document.getElementById(`allDates-${tableId}`);

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
      const match = countSpan.textContent.match(/\d+/);
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
