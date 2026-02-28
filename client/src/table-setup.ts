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
function initTableSorting(): void {
  document.querySelectorAll<HTMLElement>('th[data-sortable="true"]').forEach(header => {
    header.addEventListener('click', () => {
      const columnIndex = parseInt(header.dataset.columnIndex ?? '0', 10);
      const tableId = header.dataset.tableId ?? '';
      sortTable(columnIndex, tableId);
    });
  });
}

/**
 * Initialize search input filtering
 * Replaces: oninput="filterTable(this, table_id)"
 */
function initSearchFiltering(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-action="search"]').forEach(input => {
    input.addEventListener('input', () => {
      const tableId = input.dataset.tableId ?? '';
      filterRows(tableId);
    });
  });
}

/**
 * Initialize signal/risk filter buttons
 * Replaces: onclick="filterBySignal(signal, table_id, this)"
 */
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

/**
 * Initialize stock pattern filter buttons (breeder-specific)
 * Replaces: onclick="filterByStockPattern(pattern, table_id, this)"
 */
function initStockPatternFilters(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="filter-stock-pattern"]').forEach(button => {
    button.addEventListener('click', () => {
      const pattern = button.dataset.stockPattern ?? '';
      const tableId = button.dataset.tableId ?? '';
      filterByAttribute('data-stock-pattern', pattern, tableId, button);
    });
  });
}

/**
 * Initialize advanced filters toggle button
 * Replaces: onclick="toggleAdvancedFilters(content_id, this)"
 */
function initAdvancedFiltersToggle(): void {
  document.querySelectorAll<HTMLElement>('button[data-action="toggle-filters"]').forEach(button => {
    button.addEventListener('click', () => {
      const contentId = button.dataset.contentId ?? '';
      toggleAdvancedFilters(contentId, button);
    });
  });
}

/**
 * Initialize price range sliders
 * Replaces: oninput="filterByPrice(table_id)"
 */
function initPriceSliders(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="price"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      filterByPrice(tableId);
    });
  });
}

/**
 * Initialize wishlist range sliders
 * Replaces: oninput="filterByWishlist(table_id)"
 */
function initWishlistSliders(): void {
  document.querySelectorAll<HTMLInputElement>('input[data-filter="wishlist"]').forEach(slider => {
    slider.addEventListener('input', () => {
      const tableId = slider.dataset.tableId ?? '';
      filterByWishlist(tableId);
    });
  });
}

/**
 * Initialize date picker filter (checkbox-based, history page only)
 */
function initDateFilter(): void {
  // Toggle date picker panel visibility
  document.querySelectorAll<HTMLElement>('button[data-action="toggle-date-picker"]').forEach(button => {
    button.addEventListener('click', () => {
      const contentId = button.dataset.contentId ?? '';
      toggleAdvancedFilters(contentId, button);
    });
  });

  // Wire "All Dates" master checkbox
  document.querySelectorAll<HTMLInputElement>('input[id^="allDates-"]').forEach(allDatesEl => {
    const tableId = allDatesEl.id.replace('allDates-', '');
    allDatesEl.addEventListener('change', () => {
      // Uncheck all individual date checkboxes when "All Dates" is checked
      if (allDatesEl.checked) {
        document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
          .forEach(cb => { cb.checked = false; });
      }
      filterRows(tableId);
      updateDateSummary(tableId);
    });
  });

  // Wire individual date checkboxes
  document.querySelectorAll<HTMLInputElement>('input[data-date-value]').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      const tableId = checkbox.dataset.tableId ?? '';
      // Uncheck "All Dates" when any individual date is toggled
      const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;
      if (allDatesEl) allDatesEl.checked = false;
      filterRows(tableId);
      updateDateSummary(tableId);
    });
  });

  // Wire quick-select: "Last N Runs"
  document.querySelectorAll<HTMLElement>('button[data-action="select-last-n"]').forEach(button => {
    button.addEventListener('click', () => {
      const tableId = button.dataset.tableId ?? '';
      const n = parseInt(button.dataset.n ?? '0', 10);
      const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;
      if (allDatesEl) allDatesEl.checked = false;
      const dateCheckboxes = Array.from(
        document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
      );
      dateCheckboxes.forEach((cb, i) => { cb.checked = i < n; });
      filterRows(tableId);
      updateDateSummary(tableId);
    });
  });

  // Wire "Show All" button
  document.querySelectorAll<HTMLElement>('button[data-action="show-all-dates"]').forEach(button => {
    button.addEventListener('click', () => {
      const tableId = button.dataset.tableId ?? '';
      const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;
      if (allDatesEl) allDatesEl.checked = true;
      document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
        .forEach(cb => { cb.checked = false; });
      filterRows(tableId);
      updateDateSummary(tableId);
    });
  });
}

/**
 * Initialize open-details links
 * Opens a <details> element and scrolls to it when the anchor is clicked.
 */
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

/**
 * Initialize filtered CSV download button (history page only).
 * Intercepts the static download anchor and triggers a client-side
 * export of only the currently visible (filtered) rows.
 */
function initDownloadButton(): void {
  document.querySelectorAll<HTMLElement>('a[data-action="download-filtered-csv"]').forEach(btn => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const tableId = btn.dataset.tableId ?? '';
      downloadFilteredCsv(tableId);
    });
  });
}

/**
 * Stamp each table row with its original CSV position so that limit-based
 * filters (e.g. 'Hot top 10') always select the first N rows from source
 * order, regardless of any user-applied sort.
 */
function initOriginalRowIndexes(): void {
  document.querySelectorAll('table[id] tbody').forEach(tbody => {
    Array.from(tbody.querySelectorAll('tr')).forEach((row, index) => {
      row.setAttribute('data-original-index', String(index));
    });
  });
}

/**
 * Initialize all table interactions
 */
function init(): void {
  initOriginalRowIndexes();
  initTableSorting();
  initSearchFiltering();
  initSignalFilters();
  initStockPatternFilters();
  initAdvancedFiltersToggle();
  initPriceSliders();
  initWishlistSliders();
  initDateFilter();
  initDownloadButton();
  initOpenDetailsLinks();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
