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
  filterByWishlist,
  updateDateSummary,
  downloadFilteredCsv
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
 * Replaces: oninput="filterTable(this, table_id)"
 */
function initSearchFiltering() {
    document.querySelectorAll('input[data-action="search"]').forEach(input => {
      input.addEventListener('input', function() {
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
 * Initialize date picker filter (checkbox-based, history page only)
 */
function initDateFilter() {
    // Toggle date picker panel visibility
    document.querySelectorAll('button[data-action="toggle-date-picker"]').forEach(button => {
      button.addEventListener('click', function() {
        const contentId = this.dataset.contentId;
        toggleAdvancedFilters(contentId, this);
      });
    });

    // Wire "All Dates" master checkbox
    document.querySelectorAll('input[id^="allDates-"]').forEach(allDatesEl => {
      const tableId = allDatesEl.id.replace('allDates-', '');
      allDatesEl.addEventListener('change', function() {
        // Uncheck all individual date checkboxes when "All Dates" is checked
        if (this.checked) {
          document.querySelectorAll(`[data-date-value][data-table-id="${tableId}"]`)
            .forEach(cb => { cb.checked = false; });
        }
        filterRows(tableId);
        updateDateSummary(tableId);
      });
    });

    // Wire individual date checkboxes
    document.querySelectorAll('input[data-date-value]').forEach(checkbox => {
      checkbox.addEventListener('change', function() {
        const tableId = this.dataset.tableId;
        // Uncheck "All Dates" when any individual date is toggled
        const allDatesEl = document.getElementById(`allDates-${tableId}`);
        if (allDatesEl) allDatesEl.checked = false;
        filterRows(tableId);
        updateDateSummary(tableId);
      });
    });

    // Wire quick-select: "Last N Runs"
    document.querySelectorAll('button[data-action="select-last-n"]').forEach(button => {
      button.addEventListener('click', function() {
        const tableId = this.dataset.tableId;
        const n = parseInt(this.dataset.n, 10);
        const allDatesEl = document.getElementById(`allDates-${tableId}`);
        if (allDatesEl) allDatesEl.checked = false;
        const dateCheckboxes = Array.from(
          document.querySelectorAll(`[data-date-value][data-table-id="${tableId}"]`)
        );
        dateCheckboxes.forEach((cb, i) => { cb.checked = i < n; });
        filterRows(tableId);
        updateDateSummary(tableId);
      });
    });

    // Wire "Show All" button
    document.querySelectorAll('button[data-action="show-all-dates"]').forEach(button => {
      button.addEventListener('click', function() {
        const tableId = this.dataset.tableId;
        const allDatesEl = document.getElementById(`allDates-${tableId}`);
        if (allDatesEl) allDatesEl.checked = true;
        document.querySelectorAll(`[data-date-value][data-table-id="${tableId}"]`)
          .forEach(cb => { cb.checked = false; });
        filterRows(tableId);
        updateDateSummary(tableId);
      });
    });
  }

/**
 * Initialize filtered CSV download button (history page only).
 * Intercepts the static download anchor and triggers a client-side
 * export of only the currently visible (filtered) rows.
 */
function initDownloadButton() {
  document.querySelectorAll('a[data-action="download-filtered-csv"]').forEach(btn => {
    btn.addEventListener('click', function (event) {
      event.preventDefault();
      downloadFilteredCsv(this.dataset.tableId);
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
  initDateFilter();
  initDownloadButton();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
