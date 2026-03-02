/**
 * DOM Utilities
 *
 * Reusable DOM helpers used across page slices.
 */

/**
 * Get element by ID with warning if not found
 */
export function getElement(id: string): HTMLElement | null {
  const el = document.getElementById(id);
  if (!el) console.warn(`Element not found: ${id}`);
  return el;
}
