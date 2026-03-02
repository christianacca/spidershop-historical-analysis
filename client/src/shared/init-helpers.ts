/**
 * Common Initialization Helpers
 *
 * Reusable init functions shared across page slices.
 */

import { sortTable } from './sort.js';
import { filterRows, toggleAdvancedFilters } from './filter.js';
import { type RangeSlider } from './range-slider.js';

/**
 * Initialize data-original-index attributes for all table rows
 */
export function initOriginalRowIndexes(): void {
  document.querySelectorAll('table[id] tbody').forEach(tbody => {
    Array.from(tbody.querySelectorAll('tr')).forEach((row, index) => {
      row.setAttribute('data-original-index', String(index));
    });
  });
}

/**
 * Initialize table header sorting handlers
 */
export function initTableSorting(): void {
  document.querySelectorAll<HTMLElement>('th[data-sortable="true"]').forEach(header => {
    header.addEventListener('click', () => {
      const columnIndex = parseInt(header.dataset.columnIndex ?? '0', 10);
      const tableId = header.dataset.tableId ?? '';
      sortTable(columnIndex, tableId);
    });
  });
}

/**
 * Initialize search input handlers
 */
export function initSearchFiltering(
  priceSlider: RangeSlider | null,
  wishlistSlider: RangeSlider | null
): void {
  document.querySelectorAll<HTMLInputElement>('input[data-action="search"]').forEach(input => {
    input.addEventListener('input', () => {
      const tableId = input.dataset.tableId ?? '';
      filterRows(tableId, priceSlider, wishlistSlider);
    });
  });
}

/**
 * Initialize advanced filter toggle buttons
 */
export function initAdvancedFiltersToggle(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="toggle-filters"]').forEach(button => {
    button.addEventListener('click', () => {
      const contentId = button.dataset.contentId ?? '';
      toggleAdvancedFilters(contentId, button);
    });
  });
}

/**
 * Initialize price slider handlers
 */
export function initPriceSliders(onInput: (tableId: string) => void): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="price"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      onInput(tableId);
    });
  });
}

/**
 * Initialize wishlist slider handlers
 */
export function initWishlistSliders(onInput: (tableId: string) => void): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="wishlist"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      onInput(tableId);
    });
  });
}
