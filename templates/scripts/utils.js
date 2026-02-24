/**
 * Shared Utilities
 * 
 * Reusable DOM helpers, components, and utilities used across
 * table-interactions.js and other modules.
 */

import { CSS } from './constants.js';

/**
 * Get element by ID with warning if not found
 * @param {string} id - Element ID
 * @returns {HTMLElement|null}
 */
export function getElement(id) {
  const el = document.getElementById(id);
  if (!el) console.warn(`Element not found: ${id}`);
  return el;
}

/**
 * Set active state on a button within a group
 * @param {HTMLElement} button - Button to activate
 */
export function setActiveButton(button) {
  const buttons = button.parentElement.querySelectorAll(`.${CSS.FILTER_BTN}`);
  buttons.forEach(btn => btn.classList.remove(CSS.ACTIVE));
  button.classList.add(CSS.ACTIVE);
}

/**
 * Toggle row visibility using CSS class
 * @param {HTMLElement} row - Table row element
 * @param {boolean} shouldShow - Whether to show the row
 */
export function toggleRowVisibility(row, shouldShow) {
  row.classList.toggle(CSS.HIDDEN, !shouldShow);
}

/**
 * Range Slider Component
 * Manages min/max slider constraints and display updates
 */
export class RangeSlider {
  /**
   * @param {Object} config - Configuration object
   * @param {string} config.minId - Min slider element ID
   * @param {string} config.maxId - Max slider element ID
   * @param {string} config.displayId - Display element ID
   * @param {Function} config.parse - Parse function (parseFloat or parseInt)
   * @param {Function} config.format - Format function (min, max) => string
   */
  constructor(config) {
    this.minSlider = getElement(config.minId);
    this.maxSlider = getElement(config.maxId);
    this.display = getElement(config.displayId);
    this.parse = config.parse;
    this.format = config.format;
  }
  
  /**
   * Enforce min <= max constraint when sliders change
   * @param {Event} event - Input event from slider
   */
  enforceConstraints(event) {
    if (!this.minSlider || !this.maxSlider) return;
    
    let min = this.parse(this.minSlider.value);
    let max = this.parse(this.maxSlider.value);
    
    if (min > max) {
      if (event?.target === this.minSlider) {
        min = max;
        this.minSlider.value = max;
      } else {
        max = min;
        this.maxSlider.value = min;
      }
    }
    
    this.updateDisplay(min, max);
  }
  
  /**
   * Get current slider values
   * @returns {[number, number]} [min, max] values
   */
  getValues() {
    if (!this.minSlider || !this.maxSlider) return [0, Infinity];
    return [
      this.parse(this.minSlider.value),
      this.parse(this.maxSlider.value)
    ];
  }
  
  /**
   * Update display text with formatted values
   * @param {number} min - Min value
   * @param {number} max - Max value
   */
  updateDisplay(min, max) {
    if (this.display) {
      this.display.textContent = this.format(min, max);
    }
  }
}

/**
 * Generic attribute-based row filtering
 * @param {string} attributeName - Data attribute to filter by (e.g., 'data-signal')
 * @param {string} filterValue - Value to match ('all' shows everything)
 * @param {string} tableId - ID of the table element
 * @param {HTMLElement} button - Button that triggered the filter
 */
export function filterByAttribute(attributeName, filterValue, tableId, button, limit = null) {
  const table = getElement(tableId);
  if (!table) return;
  
  const rows = table.querySelectorAll('tbody tr');
  
  setActiveButton(button);
  
  let matchCount = 0;
  rows.forEach(row => {
    const attrValue = row.getAttribute(attributeName);
    const matches = filterValue === 'all' || attrValue === filterValue;
    const withinLimit = limit === null || matchCount < limit;
    const shouldShow = matches && withinLimit;
    if (matches) matchCount++;
    toggleRowVisibility(row, shouldShow);
  });
  
  // Update visible count (signal/stock filters don't update badge)
  const countElement = getElement(`visible-count-${tableId}`);
  if (countElement) {
    const visibleCount = Array.from(rows).filter(
      row => !row.classList.contains(CSS.HIDDEN)
    ).length;
    countElement.textContent = visibleCount;
  }
}
