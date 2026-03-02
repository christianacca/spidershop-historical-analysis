/**
 * Latest Snapshot Page
 *
 * Wires all event handlers for the snapshot-table page:
 * sorting, search, advanced filters, price/wishlist sliders.
 */

import { filterRows } from '../shared/filter.js';
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

function filterByPrice(tableId: string): void {
  if (!priceSlider) {
    priceSlider = RangeSlider.createPriceSlider();
  }
  priceSlider.enforceConstraints(window.event);
  filterRows(tableId, priceSlider, wishlistSlider);
}

function filterByWishlist(tableId: string): void {
  if (!wishlistSlider) {
    wishlistSlider = RangeSlider.createWishlistSlider();
  }
  wishlistSlider.enforceConstraints(window.event);
  filterRows(tableId, priceSlider, wishlistSlider);
}

function init(): void {
  initOriginalRowIndexes();
  initTableSorting();
  initSearchFiltering(priceSlider, wishlistSlider);
  initAdvancedFiltersToggle();
  initPriceSliders(filterByPrice);
  initWishlistSliders(filterByWishlist);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
