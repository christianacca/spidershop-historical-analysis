/**
 * Browser-backed CSS token smoke tests.
 *
 * These tests confirm the Phase 5 visual-contract foundation:
 *
 *   1. templates/common.css is loaded and CSS custom properties are accessible
 *      via getComputedStyle() on the document root.                  (step 32)
 *
 *   2. hexToRgb() converts token hex values to the exact format that
 *      getComputedStyle() returns for rendered elements.             (step 31)
 *
 *   3. CSS custom-property inheritance works end-to-end: an element styled
 *      with `var(--token-name)` computes to the same color as reading the
 *      token directly from the root.                                 (step 32)
 *
 *   4. tokenRgb() provides a correct one-call helper for visual assertions.
 *                                                                    (step 31)
 *
 * These tests do NOT assert specific hex values — that is the role of the
 * Phase 3 token snapshot in design-tokens.test.ts.  Instead they verify
 * that the browser plumbing (loading, inheritance, conversion) is working.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { hexToRgb, tokenRgb, tokenHex } from './token-colors';

// ── Helper: create/cleanup a test element ─────────────────────────────────────

let el: HTMLDivElement;

beforeEach(() => {
  el = document.createElement('div');
  document.body.appendChild(el);
});

afterEach(() => {
  document.body.removeChild(el);
});

// ── Suite 1: CSS custom properties are loaded ─────────────────────────────────

describe('CSS token loading — templates/common.css is available', () => {
  it('--color-accent custom property is defined on the document root', () => {
    const value = tokenHex('--color-accent');
    expect(value).not.toBe('');
    // Should be a hex colour declared in :root
    expect(value).toMatch(/^#[0-9a-f]{3,6}$/i);
  });

  it('--color-primary custom property is defined on the document root', () => {
    const value = tokenHex('--color-primary');
    expect(value).not.toBe('');
    expect(value).toMatch(/^#[0-9a-f]{3,6}$/i);
  });

  it('--color-signal-hot custom property is defined on the document root', () => {
    const value = tokenHex('--color-signal-hot');
    expect(value).not.toBe('');
    expect(value).toMatch(/^#[0-9a-f]{3,6}$/i);
  });
});

// ── Suite 2: hexToRgb conversion ───────────────────────────────────────────────

describe('hexToRgb — converts hex to getComputedStyle format', () => {
  it('converts a full 6-char hex to rgb()', () => {
    expect(hexToRgb('#3498db')).toBe('rgb(52, 152, 219)');
  });

  it('converts a 3-char shorthand hex to rgb()', () => {
    expect(hexToRgb('#abc')).toBe('rgb(170, 187, 204)');
  });

  it('handles uppercase hex correctly', () => {
    expect(hexToRgb('#2C3E50')).toBe('rgb(44, 62, 80)');
  });
});

// ── Suite 3: CSS custom-property inheritance ───────────────────────────────────

describe('CSS custom-property inheritance — var() resolves in the browser', () => {
  it('background-color: var(--color-accent) resolves to hexToRgb of the token value', () => {
    const tokenValue = tokenHex('--color-accent');
    expect(tokenValue).not.toBe(''); // guard: token must be loaded

    el.style.backgroundColor = 'var(--color-accent)';
    const computed = window.getComputedStyle(el).backgroundColor;
    expect(computed).toBe(hexToRgb(tokenValue));
  });

  it('color: var(--color-primary) resolves to hexToRgb of the token value', () => {
    const tokenValue = tokenHex('--color-primary');
    expect(tokenValue).not.toBe('');

    el.style.color = 'var(--color-primary)';
    const computed = window.getComputedStyle(el).color;
    expect(computed).toBe(hexToRgb(tokenValue));
  });
});

// ── Suite 4: tokenRgb helper ───────────────────────────────────────────────────

describe('tokenRgb — one-call helper for visual assertions', () => {
  it('tokenRgb() returns the rgb() form of a hex colour token', () => {
    const result = tokenRgb('--color-accent');
    expect(result).toBeDefined();
    expect(result).toMatch(/^rgb\(\d+, \d+, \d+\)$/);
  });

  it('tokenRgb() matches getComputedStyle for an element using the token', () => {
    el.style.backgroundColor = 'var(--color-accent)';
    const computed = window.getComputedStyle(el).backgroundColor;
    expect(computed).toBe(tokenRgb('--color-accent'));
  });

  it('tokenRgb() returns undefined for non-colour tokens', () => {
    // Spacing tokens are not hex values; tokenRgb should return undefined
    const result = tokenRgb('--spacing-md');
    expect(result).toBeUndefined();
  });
});
