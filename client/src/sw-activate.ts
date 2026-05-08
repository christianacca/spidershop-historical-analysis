/**
 * Activate-time cache eviction logic for the Service Worker.
 *
 * Extracted as a pure module so the eviction predicate can be unit-tested
 * independently of the Workbox/ServiceWorkerGlobalScope environment.
 */

/** The canonical set of HTML pages that are safe to keep after a SW update.
 *
 * These six pages are pre-fetched during the install handler, so they are
 * already fresh when activate runs.  Everything else (species detail pages, etc.)
 * is lazily cached via StaleWhileRevalidate and must be evicted on every
 * SW update so stale inline scripts in old HTML don't break view transitions.
 */
export function buildMainPageSet(scope: string): Set<string> {
  return new Set([
    `${scope}index.html`,
    `${scope}breeder.html`,
    `${scope}dealer.html`,
    `${scope}snapshot.html`,
    `${scope}history.html`,
    `${scope}history-insights.html`,
  ]);
}

/**
 * Returns `true` when the cached entry at `url` should be evicted during SW activation.
 *
 * All html-pages cache entries that are NOT one of the six main pages are evicted.
 * This ensures stale species-page HTML (which can contain an outdated inline
 * pagereveal script from a previous deploy) is never served after a SW update.
 */
export function shouldEvictOnActivate(url: string, scope: string): boolean {
  return !buildMainPageSet(scope).has(url);
}
