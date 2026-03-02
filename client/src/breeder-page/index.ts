/**
 * Breeder Opportunities Page
 *
 * Wires all event handlers for the breeder-table page:
 * sorting, search, signal/stock-pattern filters, advanced filters,
 * price/wishlist sliders, and open-details links.
 */

import { filterByAttribute, filterRows } from '../shared/filter.js';
import { RangeSlider } from '../shared/range-slider.js';
import {
  initOriginalRowIndexes,
  initTableSorting,
  initSearchFiltering,
  initAdvancedFiltersToggle,
  initPriceSliders,
  initWishlistSliders
} from '../shared/init-helpers.js';

// Page-local slider singletons
let priceSlider: RangeSlider | null = null;
let wishlistSlider: RangeSlider | null = null;

/**
 * Filter table rows by price range.
 * Lazy-initialises the RangeSlider singleton on first call.
 */
function filterByPrice(tableId: string): void {
  if (!priceSlider) {
    priceSlider = RangeSlider.createPriceSlider();
  }
  priceSlider.enforceConstraints(window.event);
  filterRows(tableId, priceSlider, wishlistSlider);
}

/**
 * Filter table rows by wishlist count range.
 * Lazy-initialises the RangeSlider singleton on first call.
 */
function filterByWishlist(tableId: string): void {
  if (!wishlistSlider) {
    wishlistSlider = RangeSlider.createWishlistSlider();
  }
  wishlistSlider.enforceConstraints(window.event);
  filterRows(tableId, priceSlider, wishlistSlider);
}



function initSignalFilters(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="filter-signal"]').forEach(button => {
    button.addEventListener('click', () => {
      const signal = button.dataset.signal ?? '';
      const tableId = button.dataset.tableId ?? '';
      const limit = button.dataset.limit ? parseInt(button.dataset.limit, 10) : null;
      filterByAttribute('data-signal', signal, tableId, button, limit);
    });
  });
}

function initStockPatternFilters(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="filter-stock-pattern"]').forEach(button => {
    button.addEventListener('click', () => {
      const pattern = button.dataset.stockPattern ?? '';
      const tableId = button.dataset.tableId ?? '';
      filterByAttribute('data-stock-pattern', pattern, tableId, button);
    });
  });
}



function initOpenDetailsLinks(): void {
  document.querySelectorAll<HTMLElement>('a[data-action="open-details"]').forEach(link => {
    link.addEventListener('click', () => {
      const targetId = link.dataset.target ?? '';
      const target = document.getElementById(targetId);
      if (target && target.tagName === 'DETAILS') {
        (target as HTMLDetailsElement).open = true;
      }
    });
  });
}

function init(): void {
  initOriginalRowIndexes();
  initTableSorting();
  initSearchFiltering(priceSlider, wishlistSlider);
  initSignalFilters();
  initStockPatternFilters();
  initAdvancedFiltersToggle();
  initPriceSliders(filterByPrice);
  initWishlistSliders(filterByWishlist);
  initOpenDetailsLinks();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
