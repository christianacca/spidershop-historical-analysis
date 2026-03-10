/**
 * Design-token utilities for static guardrail tests.
 *
 * Exported functions are used by design-tokens.test.ts to verify that:
 *   1. The token set in templates/common.css has not drifted unexpectedly.
 *   2. Svelte component style blocks do not use hardcoded values that
 *      duplicate a known design token.
 */
import { readFileSync, readdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve, join, extname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '../../..');

export const TOKEN_CSS_PATH = resolve(PROJECT_ROOT, 'templates/common.css');
export const CLIENT_SRC_DIR = resolve(PROJECT_ROOT, 'client/src');

/**
 * Parse every --custom-property declaration from the :root block in a CSS file.
 * Returns an alphabetically-sorted record for stable snapshot diffs.
 */
export function parseTokens(cssPath = TOKEN_CSS_PATH): Record<string, string> {
  const css = readFileSync(cssPath, 'utf-8');
  const rootMatch = css.match(/:root\s*\{([\s\S]*?)\}/);
  if (!rootMatch) return {};

  const tokens: Record<string, string> = {};
  // Match --name: value; lines, capturing value up to the first semicolon.
  const tokenRe = /(--[\w-]+)\s*:\s*([^;]+);/g;
  let m: RegExpExecArray | null;
  while ((m = tokenRe.exec(rootMatch[1])) !== null) {
    tokens[m[1]] = m[2].trim();
  }
  // Sort by key so snapshots produce a stable, readable diff.
  return Object.fromEntries(Object.entries(tokens).sort(([a], [b]) => a.localeCompare(b)));
}

/**
 * Recursively collect all .svelte files under a directory.
 */
export function findSvelteFiles(dir = CLIENT_SRC_DIR): string[] {
  const results: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findSvelteFiles(full));
    } else if (extname(entry.name) === '.svelte') {
      results.push(full);
    }
  }
  return results;
}

/**
 * Extract the concatenated text of every <style> block in a Svelte source
 * string, with CSS block comments stripped to avoid false positives.
 */
export function extractStyleBlock(source: string): string {
  const styleRe = /<style[^>]*>([\s\S]*?)<\/style>/g;
  const parts: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = styleRe.exec(source)) !== null) {
    parts.push(m[1].replace(/\/\*[\s\S]*?\*\//g, ''));
  }
  return parts.join('\n');
}

/**
 * Normalise a hex colour to lowercase 6-char form.
 *   #ABC  →  #aabbcc
 *   #AABBCC  →  #aabbcc
 */
export function normalizeHex(hex: string): string {
  const h = hex.toLowerCase();
  return h.length === 4
    ? '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3]
    : h;
}
