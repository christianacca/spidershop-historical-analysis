/**
 * Unit tests for the SW activate-time cache eviction logic.
 *
 * The logic lives in sw-activate.ts so it can be tested outside a
 * ServiceWorkerGlobalScope.  sw.ts wires the pure predicate into the real
 * Cache API during the activate event.
 *
 * Mutation targets exercised here:
 * - Remove a page from buildMainPageSet → that page is now evicted (main-page
 *   retention tests fail).
 * - Replace `!mainPages.has(url)` with `mainPages.has(url)` → all tests invert:
 *   main pages are evicted, species pages are kept.
 * - Change the scope interpolation from `${scope}breeder.html` to `breeder.html`
 *   (drop the scope prefix) → scoped-URL tests fail.
 * - Rename `history-insights.html` to `history-insights-page.html` → the
 *   history-insights retention test fails.
 */

import { describe, expect, it } from 'vitest';
import { buildMainPageSet, shouldEvictOnActivate } from './sw-activate.js';

const SCOPE = 'https://example.github.io/spidershop/';

// ─────────────────────────────────────────────────────────────────────────────
// buildMainPageSet
// ─────────────────────────────────────────────────────────────────────────────

describe('buildMainPageSet', () => {
  it('contains exactly six main HTML pages', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.size).toBe(6);
  });

  it('contains index.html at the scope root', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}index.html`)).toBe(true);
  });

  it('contains breeder.html', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}breeder.html`)).toBe(true);
  });

  it('contains dealer.html', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}dealer.html`)).toBe(true);
  });

  it('contains snapshot.html', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}snapshot.html`)).toBe(true);
  });

  it('contains history.html', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}history.html`)).toBe(true);
  });

  it('contains history-insights.html', () => {
    // This page is often forgotten because it is not in the primary nav.
    // If it is evicted on activation the user gets a full network fetch,
    // breaking the "fresh HTML before toast" guarantee.
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}history-insights.html`)).toBe(true);
  });

  it('does NOT contain species pages', () => {
    const pages = buildMainPageSet(SCOPE);
    expect(pages.has(`${SCOPE}species/aphonopelma-seemanni.html`)).toBe(false);
  });

  it('prefixes every entry with the scope', () => {
    const scopeA = 'https://a.example.com/app/';
    const scopeB = 'https://b.example.com/';
    const pagesA = buildMainPageSet(scopeA);
    const pagesB = buildMainPageSet(scopeB);
    // All entries use the correct scope prefix, not each other's
    for (const url of pagesA) {
      expect(url.startsWith(scopeA)).toBe(true);
      expect(pagesB.has(url)).toBe(false);
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// shouldEvictOnActivate — main pages: KEEP (returns false)
// ─────────────────────────────────────────────────────────────────────────────

describe('shouldEvictOnActivate — main pages are NOT evicted', () => {
  const mainPages = [
    'index.html',
    'breeder.html',
    'dealer.html',
    'snapshot.html',
    'history.html',
    'history-insights.html',
  ];

  it.each(mainPages)('%s is retained (returns false)', (page) => {
    const result = shouldEvictOnActivate(`${SCOPE}${page}`, SCOPE);
    expect(result).toBe(false);
  });

  it('retains main pages with query strings unchanged (exact URL match)', () => {
    // Cache keys are exact request URLs — a query string makes it a different entry
    // so it would be evicted.  This confirms the Set comparison is exact.
    const withQuery = shouldEvictOnActivate(`${SCOPE}breeder.html?v=1`, SCOPE);
    expect(withQuery).toBe(true); // query string → NOT a main page → evicted
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// shouldEvictOnActivate — non-main pages: EVICT (returns true)
// ─────────────────────────────────────────────────────────────────────────────

describe('shouldEvictOnActivate — non-main pages ARE evicted', () => {
  it('evicts a species detail page', () => {
    const result = shouldEvictOnActivate(
      `${SCOPE}species/aphonopelma-seemanni.html`,
      SCOPE,
    );
    expect(result).toBe(true);
  });

  it('evicts a species page at any slug', () => {
    const slugs = [
      'brachypelma-hamorii',
      'tliltocatl-albopilosus',
      'chromatopelma-cyaneopubescens',
    ];
    for (const slug of slugs) {
      expect(shouldEvictOnActivate(`${SCOPE}species/${slug}.html`, SCOPE)).toBe(true);
    }
  });

  it('evicts an unknown top-level HTML page not in the main set', () => {
    // Defensively evicts anything that was cached but is not a known main page.
    const result = shouldEvictOnActivate(`${SCOPE}unknown-page.html`, SCOPE);
    expect(result).toBe(true);
  });

  it('evicts a page whose URL uses a different scope', () => {
    // A cached entry from a prior scope (e.g. after a path change) must be evicted.
    const staleUrl = 'https://old.example.com/spidershop/breeder.html';
    const result = shouldEvictOnActivate(staleUrl, SCOPE);
    expect(result).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Eviction result: correct subset of a mixed cache
// ─────────────────────────────────────────────────────────────────────────────

describe('eviction filter over a realistic html-pages cache snapshot', () => {
  const cachedUrls = [
    `${SCOPE}index.html`,
    `${SCOPE}breeder.html`,
    `${SCOPE}dealer.html`,
    `${SCOPE}snapshot.html`,
    `${SCOPE}history.html`,
    `${SCOPE}history-insights.html`,
    `${SCOPE}species/aphonopelma-seemanni.html`,
    `${SCOPE}species/brachypelma-hamorii.html`,
    `${SCOPE}species/grammostola-pulchripes.html`,
  ];

  const toEvict = cachedUrls.filter(url => shouldEvictOnActivate(url, SCOPE));
  const toKeep = cachedUrls.filter(url => !shouldEvictOnActivate(url, SCOPE));

  it('evicts exactly the three species pages', () => {
    expect(toEvict).toHaveLength(3);
    expect(toEvict).toContain(`${SCOPE}species/aphonopelma-seemanni.html`);
    expect(toEvict).toContain(`${SCOPE}species/brachypelma-hamorii.html`);
    expect(toEvict).toContain(`${SCOPE}species/grammostola-pulchripes.html`);
  });

  it('keeps exactly the six main pages', () => {
    expect(toKeep).toHaveLength(6);
  });

  it('keeps every main page by name', () => {
    const keptNames = toKeep.map(url => url.replace(SCOPE, ''));
    expect(keptNames).toEqual(
      expect.arrayContaining([
        'index.html',
        'breeder.html',
        'dealer.html',
        'snapshot.html',
        'history.html',
        'history-insights.html',
      ]),
    );
  });

  it('never evicts a main page', () => {
    const evictedNames = toEvict.map(url => url.replace(SCOPE, ''));
    for (const name of evictedNames) {
      expect(name).toMatch(/^species\//);
    }
  });
});
