/**
 * Static guardrail tests for the design-token system.
 *
 * Step 18 — Token snapshot:
 *   Asserts that every --custom-property in templates/common.css matches the
 *   recorded snapshot. A readable diff appears whenever a token is added,
 *   removed, or its value changes.
 *
 * Steps 19–21 — Svelte CSS compliance:
 *   Each Svelte component in client/src/ gets a dedicated test case. The test
 *   scans the component's <style> block for hardcoded hex colours that
 *   duplicate a known design-token value. Violations produce a prescriptive
 *   message: "<file> uses hardcoded #xxx; use var(--token-name)".
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { relative } from 'path';
import {
  parseTokens,
  findSvelteFiles,
  extractStyleBlock,
  normalizeHex,
  CLIENT_SRC_DIR,
} from './design-tokens';

// ── Step 18: Token map snapshot ───────────────────────────────────────────────

describe('design tokens — templates/common.css', () => {
  it('token map matches snapshot', () => {
    const tokens = parseTokens();
    // Snapshot is sorted alphabetically for stable diffs.
    // When a token changes the diff names the exact property and old/new value.
    expect(tokens).toMatchSnapshot();
  });
});

// ── Steps 19–21: Svelte CSS compliance ───────────────────────────────────────

/**
 * Hardcoded colour values that are explicitly permitted in Svelte style blocks
 * even if they happen to equal a design-token value.
 *
 * - #fff / #ffffff / white: white text on coloured backgrounds is a
 *   conventional contrast pattern. The semantic fix (--color-text-inverse)
 *   is deferred; using var(--color-surface) as text colour would be wrong.
 * - transparent / none: structural CSS — not semantic colour choices.
 * - inherit / currentColor: cascade / relative colour references.
 */
const ALLOWLIST = new Set([
  '#fff',
  '#ffffff',
  'white',
  'transparent',
  'none',
  'inherit',
  'currentcolor',
]);

describe('Svelte CSS compliance — no hardcoded token-equivalent colours', () => {
  // Build an inverted map once: normalised hex value → token name(s).
  const tokens = parseTokens();
  const valueToTokens = new Map<string, string[]>();
  for (const [name, value] of Object.entries(tokens)) {
    if (/^#[0-9a-fA-F]{3,6}$/.test(value)) {
      const normalized = normalizeHex(value);
      const existing = valueToTokens.get(normalized) ?? [];
      existing.push(name);
      valueToTokens.set(normalized, existing);
    }
  }

  const svelteFiles = findSvelteFiles();

  // One test case per .svelte file — failure message names the exact file
  // and lists each violation with the suggested token replacement.
  it.each(
    svelteFiles.map(
      (f) => [relative(CLIENT_SRC_DIR, f), f] as [string, string],
    ),
  )('%s — no hardcoded token-equivalent colours', (_label, filePath) => {
    const source = readFileSync(filePath, 'utf-8');
    const styleContent = extractStyleBlock(source);
    const violations: string[] = [];

    const hexRe = /#[0-9a-fA-F]{3,6}(?![0-9a-fA-F])/g;
    let m: RegExpExecArray | null;
    while ((m = hexRe.exec(styleContent)) !== null) {
      const raw = m[0];
      const normalized = normalizeHex(raw);
      if (ALLOWLIST.has(raw.toLowerCase()) || ALLOWLIST.has(normalized)) continue;
      const matchedTokens = valueToTokens.get(normalized);
      if (matchedTokens) {
        const suggestion = matchedTokens.map((t) => `var(${t})`).join(' or ');
        violations.push(
          `${_label} uses hardcoded ${raw}; use ${suggestion}`,
        );
      }
    }

    if (violations.length > 0) {
      throw new Error(violations.join('\n'));
    }
  });
});
