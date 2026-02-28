/**
 * DOM Utilities
 *
 * Reusable DOM helpers used across page slices.
 */

import { CSS } from './constants.js';

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
