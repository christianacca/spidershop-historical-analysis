/**
 * Table Filtering
 *
 * Generic attribute-based filtering, row filtering, and filter UI helpers.
 * Note: filterByPrice and filterByWishlist are page-specific (they depend on
 * module-level RangeSlider singletons) and live in each page-slice index.ts.
 */

import { CSS } from './constants.js';
import { getElement, setActiveButton, toggleRowVisibility } from './dom-utils.js';
import { type RangeSlider } from './range-slider.js';

/**
 * Generic attribute-based row filtering
 */
export function filterByAttribute(
  attributeName: string,
  filterValue: string,
  tableId: string,
  button: HTMLElement,
  limit: number | null = null
): void {
  const table = getElement(tableId);
  if (!table) return;

  const rows = table.querySelectorAll('tbody tr');

  setActiveButton(button);

  // When a limit is set, determine which rows to show by their original CSV
  // index (data-original-index), not their current DOM position.  This ensures
  // the same N entries are always selected regardless of the active sort order.
  let allowedOriginalIndexes: Set<string | null> | null = null;
  if (limit !== null) {
    const matchingRows = Array.from(rows).filter(
      row => filterValue === 'all' || row.getAttribute(attributeName) === filterValue
    );
    matchingRows.sort(
      (a, b) => parseInt(a.getAttribute('data-original-index') ?? '0', 10)
             - parseInt(b.getAttribute('data-original-index') ?? '0', 10)
    );
    allowedOriginalIndexes = new Set(
      matchingRows.slice(0, limit).map(row => row.getAttribute('data-original-index'))
    );
  }

  rows.forEach(row => {
    const attrValue = row.getAttribute(attributeName);
    const matches = filterValue === 'all' || attrValue === filterValue;
    let shouldShow: boolean;
    if (allowedOriginalIndexes !== null) {
      shouldShow = matches && allowedOriginalIndexes.has(row.getAttribute('data-original-index'));
    } else {
      shouldShow = matches;
    }
    toggleRowVisibility(row as HTMLElement, shouldShow);
  });

  // Update visible count (signal/stock filters don't update badge)
  const countElement = getElement(`visible-count-${tableId}`);
  if (countElement) {
    const visibleCount = Array.from(rows).filter(
      row => !row.classList.contains(CSS.HIDDEN)
    ).length;
    countElement.textContent = String(visibleCount);
  }
}

/**
 * Apply all active filters to table rows.
 * Combines search, price, and wishlist filters.
 * Accepts optional slider instances so callers can pass their page-local singletons.
 */
export function filterRows(
  tableId: string,
  priceSlider: RangeSlider | null = null,
  wishlistSlider: RangeSlider | null = null
): void {
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
 * Update filter badge count.
 * Shows badge with count when filters are active.
 */
export function updateFilterBadge(tableId: string): void {
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
 * Update visible count display for a table.
 * Counts rows that are not hidden and updates the stats strip.
 */
export function updateVisibleCount(tableId: string): void {
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
