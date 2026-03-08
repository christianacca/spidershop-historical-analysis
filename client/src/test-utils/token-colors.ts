/**
 * Token-aware helpers for browser-backed visual contract tests.
 *
 * These utilities work entirely within the browser context — no Node.js
 * APIs are used. The design-token values are read from the live document
 * root (populated by browser-setup.ts from templates/common.css).
 *
 * Typical usage in a *.visual.test.ts file:
 *
 *   import { hexToRgb, tokenRgb } from '../test-utils/token-colors';
 *
 *   it('active filter button uses accent colour', () => {
 *     const btn = container.querySelector('.filter-btn.is-active')!;
 *     expect(window.getComputedStyle(btn).backgroundColor)
 *       .toBe(tokenRgb('--color-accent'));
 *   });
 */

/**
 * Convert a hex colour string to the rgb() format returned by getComputedStyle.
 * Supports 3-char shorthand (#abc) and full 6-char (#aabbcc).
 *
 *   hexToRgb('#3498db')  →  'rgb(52, 152, 219)'
 *   hexToRgb('#abc')     →  'rgb(170, 187, 204)'
 */
export function hexToRgb(hex: string): string {
  const h = hex.startsWith('#') ? hex.slice(1) : hex;
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Return the rgb() representation of a CSS design token by reading its current
 * value from the document root (i.e. the :root custom properties loaded by
 * browser-setup.ts).
 *
 * Returns undefined if the property does not exist or its value is not a hex
 * colour (e.g. a spacing token or a non-colour keyword).
 *
 *   tokenRgb('--color-accent')          →  'rgb(52, 152, 219)'
 *   tokenRgb('--color-signal-hot')      →  'rgb(231, 76, 60)'
 *   tokenRgb('--spacing-md')            →  undefined  (not a hex colour)
 */
export function tokenRgb(name: string): string | undefined {
  const style = window.getComputedStyle(document.documentElement);
  const value = style.getPropertyValue(name).trim();
  return value.startsWith('#') ? hexToRgb(value) : undefined;
}

/**
 * Return the raw hex value of a CSS design token as declared in the :root block.
 * Useful when you need to assert an element's border or outline colour in a
 * form other than rgb(), or when you want to call hexToRgb() yourself.
 *
 *   tokenHex('--color-accent')  →  '#3498db'
 *   tokenHex('--spacing-md')    →  '1rem'   (non-hex, returned as-is)
 */
export function tokenHex(name: string): string {
  const style = window.getComputedStyle(document.documentElement);
  return style.getPropertyValue(name).trim();
}
