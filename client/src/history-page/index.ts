/**
 * Historical Data Page
 *
 * Wires all event handlers for the history-table page:
 * sorting, search, advanced filters, price/wishlist sliders,
 * date picker, filtered CSV download, and date summary.
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

/**
 * Initialize date picker filter (history page only).
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
      if (allDatesEl.checked) {
        document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
          .forEach(cb => { cb.checked = false; });
      }
      filterRows(tableId, priceSlider, wishlistSlider);
      updateDateSummary(tableId);
    });
  });

  // Wire individual date checkboxes
  document.querySelectorAll<HTMLInputElement>('input[data-date-value]').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      const tableId = checkbox.dataset.tableId ?? '';
      const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;
      if (allDatesEl) allDatesEl.checked = false;
      filterRows(tableId, priceSlider, wishlistSlider);
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
      filterRows(tableId, priceSlider, wishlistSlider);
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
      filterRows(tableId, priceSlider, wishlistSlider);
      updateDateSummary(tableId);
    });
  });
}

/**
 * Initialize filtered CSV download button (history page only).
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
 * Download the currently visible (filtered) rows of a table as a CSV file.
 */
function downloadFilteredCsv(tableId: string): void {
  const table = document.getElementById(tableId);
  if (!table) return;

  const headers = Array.from(table.querySelectorAll('thead th'))
    .map(th => (th as HTMLElement).dataset.csvName ?? th.textContent?.replace('\u21c5', '').trim() ?? '');

  const CSS_HIDDEN = 'hidden';
  const visibleRows = Array.from(table.querySelectorAll(`tbody tr:not(.${CSS_HIDDEN})`));

  const csvLines = [_escapeCsvRow(headers)];
  visibleRows.forEach(row => {
    const values = Array.from(row.querySelectorAll('td')).map(td => {
      if (td.hasAttribute('data-raw')) {
        return td.getAttribute('data-raw') ?? '';
      }
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
 * Update the date filter summary info box.
 */
function updateDateSummary(tableId: string): void {
  const summaryEl = document.getElementById(`summary-info-${tableId}`) as HTMLElement | null;
  if (!summaryEl) return;

  const allDateCheckboxes = Array.from(
    document.querySelectorAll<HTMLInputElement>(`[data-date-value][data-table-id="${tableId}"]`)
  );
  const totalRuns = allDateCheckboxes.length;
  const allDatesEl = document.getElementById(`allDates-${tableId}`) as HTMLInputElement | null;

  if (allDatesEl?.checked) {
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

  let totalRows = 0;
  selectedCheckboxes.forEach(cb => {
    const countSpan = cb.closest('.date-row')?.querySelector('.date-count');
    if (countSpan) {
      const match = countSpan.textContent?.match(/\d+/);
      if (match) totalRows += parseInt(match[0], 10);
    }
  });

  const selectedDates = selectedCheckboxes.map(cb => cb.dataset.dateValue);
  const maxDate = selectedDates[0];
  const minDate = selectedDates[selectedDates.length - 1];

  summaryEl.textContent =
    `Viewing ${totalRows} rows across ${numSelected} scrape runs (${minDate} - ${maxDate})`;
}

function init(): void {
  initOriginalRowIndexes();
  initTableSorting();
  initSearchFiltering();
  initAdvancedFiltersToggle();
  initPriceSliders();
  initWishlistSliders();
  initDateFilter();
  initDownloadButton();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
