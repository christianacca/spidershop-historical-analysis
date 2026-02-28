/**
 * Shared Utilities
 * 
 * Reusable DOM helpers, components, and utilities used across
 * table-interactions.js and other modules.
 */

import { CSS } from './constants.js';

interface RangeSliderConfig {
  minId: string;
  maxId: string;
  displayId: string;
  parse: (value: string) => number;
  format: (min: number, max: number) => string;
}

/**
 * Get element by ID with warning if not found
 */
export function getElement(id: string): HTMLElement | null {
  const el = document.getElementById(id);
  if (!el) console.warn(`Element not found: ${id}`);
  return el;
}

/**
 * Set active state on a button within a group
 */
export function setActiveButton(button: HTMLElement): void {
  const buttons = button.parentElement!.querySelectorAll(`.${CSS.FILTER_BTN}`);
  buttons.forEach(btn => btn.classList.remove(CSS.ACTIVE));
  button.classList.add(CSS.ACTIVE);
}

/**
 * Toggle row visibility using CSS class
 */
export function toggleRowVisibility(row: HTMLElement, shouldShow: boolean): void {
  row.classList.toggle(CSS.HIDDEN, !shouldShow);
}

/**
 * Range Slider Component
 * Manages min/max slider constraints and display updates
 */
export class RangeSlider {
  private minSlider: HTMLElement | null;
  private maxSlider: HTMLElement | null;
  private display: HTMLElement | null;
  private parse: (value: string) => number;
  private format: (min: number, max: number) => string;

  constructor(config: RangeSliderConfig) {
    this.minSlider = getElement(config.minId);
    this.maxSlider = getElement(config.maxId);
    this.display = getElement(config.displayId);
    this.parse = config.parse;
    this.format = config.format;
  }

  /**
   * Enforce min <= max constraint when sliders change
   */
  enforceConstraints(event?: Event): void {
    if (!this.minSlider || !this.maxSlider) return;

    const minInput = this.minSlider as HTMLInputElement;
    const maxInput = this.maxSlider as HTMLInputElement;

    let min = this.parse(minInput.value);
    let max = this.parse(maxInput.value);

    if (min > max) {
      if (event?.target === this.minSlider) {
        min = max;
        minInput.value = String(max);
      } else {
        max = min;
        maxInput.value = String(min);
      }
    }

    this.updateDisplay(min, max);
  }

  /**
   * Get current slider values
   */
  getValues(): [number, number] {
    if (!this.minSlider || !this.maxSlider) return [0, Infinity];
    return [
      this.parse((this.minSlider as HTMLInputElement).value),
      this.parse((this.maxSlider as HTMLInputElement).value)
    ];
  }

  /**
   * Update display text with formatted values
   */
  updateDisplay(min: number, max: number): void {
    if (this.display) {
      this.display.textContent = this.format(min, max);
    }
  }
}

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
