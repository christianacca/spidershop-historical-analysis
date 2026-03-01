/**
 * Latest Snapshot Page
 *
 * Wires all event handlers for the snapshot-table page:
 * sorting, search, advanced filters, price/wishlist sliders.
 */

import { sortTable } from '../shared/sort.js';
import { filterRows, toggleAdvancedFilters } from '../shared/filter.js';
import { RangeSlider } from '../shared/range-slider.js';

// Page-local slider singletons
let priceSlider: RangeSlider | null = null;
let wishlistSlider: RangeSlider | null = null;

function filterByPrice(tableId: string): void {
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
  filterRows(tableId, priceSlider, wishlistSlider);
}

function filterByWishlist(tableId: string): void {
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
  filterRows(tableId, priceSlider, wishlistSlider);
}

function initOriginalRowIndexes(): void {
  document.querySelectorAll('table[id] tbody').forEach(tbody => {
    Array.from(tbody.querySelectorAll('tr')).forEach((row, index) => {
      row.setAttribute('data-original-index', String(index));
    });
  });
}

function initTableSorting(): void {
  document.querySelectorAll<HTMLElement>('th[data-sortable="true"]').forEach(header => {
    header.addEventListener('click', () => {
      const columnIndex = parseInt(header.dataset.columnIndex ?? '0', 10);
      const tableId = header.dataset.tableId ?? '';
      sortTable(columnIndex, tableId);
    });
  });
}

function initSearchFiltering(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-action="search"]').forEach(input => {
    input.addEventListener('input', () => {
      const tableId = input.dataset.tableId ?? '';
      filterRows(tableId, priceSlider, wishlistSlider);
    });
  });
}

function initAdvancedFiltersToggle(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="toggle-filters"]').forEach(button => {
    button.addEventListener('click', () => {
      const contentId = button.dataset.contentId ?? '';
      toggleAdvancedFilters(contentId, button);
    });
  });
}

function initPriceSliders(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="price"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      filterByPrice(tableId);
    });
  });
}

function initWishlistSliders(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="wishlist"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      filterByWishlist(tableId);
    });
  });
}

function init(): void {
  initOriginalRowIndexes();
  initTableSorting();
  initSearchFiltering();
  initAdvancedFiltersToggle();
  initPriceSliders();
  initWishlistSliders();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
