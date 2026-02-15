/**
 * Table Initialization and Event Handler Setup
 * 
 * This module initializes all event handlers for table interactions,
 * replacing inline event handlers (onclick, onkeyup, oninput) with
 * modern addEventListener patterns.
 * 
 * Depends on: table-interactions.js (must be loaded first)
 */

import {
  sortTable,
  filterRows,
  toggleAdvancedFilters,
  filterByPrice,
  filterByWishlist
} from './table-interactions.js';
import { filterByAttribute } from './utils.js';

/**
 * Initialize table header sorting
 * Replaces: onclick="sortTable(i, table_id)"
 */
function initTableSorting() {
    document.querySelectorAll('th[data-sortable="true"]').forEach(header => {
      header.addEventListener('click', function() {
        const columnIndex = parseInt(this.dataset.columnIndex, 10);
        const tableId = this.dataset.tableId;
        sortTable(columnIndex, tableId);
      });
    });
  }

/**
 * Initialize search input filtering
 * Replaces: onkeyup="filterTable(this, table_id)"
 */
function initSearchFiltering() {
    document.querySelectorAll('input[data-action="search"]').forEach(input => {
      input.addEventListener('keyup', function() {
        const tableId = this.dataset.tableId;
        filterRows(tableId);
      });
    });
  }

/**
 * Initialize signal/risk filter buttons
 * Replaces: onclick="filterBySignal(signal, table_id, this)"
 */
function initSignalFilters() {
    document.querySelectorAll('button[data-action="filter-signal"]').forEach(button => {
      button.addEventListener('click', function() {
        const signal = this.dataset.signal;
        const tableId = this.dataset.tableId;
        filterByAttribute('data-signal', signal, tableId, this);
      });
    });
  }

/**
 * Initialize stock pattern filter buttons (breeder-specific)
 * Replaces: onclick="filterByStockPattern(pattern, table_id, this)"
 */
function initStockPatternFilters() {
    document.querySelectorAll('button[data-action="filter-stock-pattern"]').forEach(button => {
      button.addEventListener('click', function() {
        const pattern = this.dataset.stockPattern;
        const tableId = this.dataset.tableId;
        filterByAttribute('data-stock-pattern', pattern, tableId, this);
      });
    });
  }

/**
 * Initialize advanced filters toggle button
 * Replaces: onclick="toggleAdvancedFilters(content_id, this)"
 */
function initAdvancedFiltersToggle() {
    document.querySelectorAll('button[data-action="toggle-filters"]').forEach(button => {
      button.addEventListener('click', function() {
        const contentId = this.dataset.contentId;
        toggleAdvancedFilters(contentId, this);
      });
    });
  }

/**
 * Initialize price range sliders
 * Replaces: oninput="filterByPrice(table_id)"
 */
function initPriceSliders() {
    document.querySelectorAll('input[data-filter="price"]').forEach(slider => {
      slider.addEventListener('input', function() {
        const tableId = this.dataset.tableId;
        filterByPrice(tableId);
      });
    });
  }

/**
 * Initialize wishlist range sliders
 * Replaces: oninput="filterByWishlist(table_id)"
 */
function initWishlistSliders() {
    document.querySelectorAll('input[data-filter="wishlist"]').forEach(slider => {
      slider.addEventListener('input', function() {
        const tableId = this.dataset.tableId;
        filterByWishlist(tableId);
      });
    });
  }

/**
 * Initialize all table interactions
 */
function init() {
  initTableSorting();
  initSearchFiltering();
  initSignalFilters();
  initStockPatternFilters();
  initAdvancedFiltersToggle();
  initPriceSliders();
  initWishlistSliders();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
