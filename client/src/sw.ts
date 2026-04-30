/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import type { PrecacheEntry } from 'workbox-precaching';

declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<PrecacheEntry | string> };

// Respond to the SKIP_WAITING message sent by wb.messageSkipWaiting() in register-sw.ts.
// Without this listener the waiting SW never calls self.skipWaiting(), so the Refresh
// button appears but the page never reloads with the new version.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Must be called BEFORE precacheAndRoute to remove stale entries from prior builds.
cleanupOutdatedCaches();

// Cache-first for hashed JS/CSS bundles (auto-managed via precache manifest).
precacheAndRoute(self.__WB_MANIFEST);

// SWR for all HTML navigation requests — covers *.html and /species/<slug>/ paths.
// Never cache-first: pages contain inline window.marketHealthRawData.
// ExpirationPlugin bounds cache growth: the site has 160+ species pages (~12 KB
// each uncompressed) plus 6 main pages (~250 KB each). Without a limit the cache
// grows indefinitely. maxAgeSeconds = 14 days (2× weekly scrape cadence) so a page
// the user visited two weeks ago is evicted rather than served stale forever.
registerRoute(
  new NavigationRoute(
    new StaleWhileRevalidate({
      cacheName: 'html-pages',
      plugins: [
        new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 14 * 24 * 60 * 60 }),
      ],
    }),
  ),
);

// Runtime SWR for unhashed CSS files not covered by the precache manifest:
// common.css, analysis.css, homepage.css, species-detail.css.
// Small fixed set (≤5 files) — maxEntries is a safety net against unexpected growth.
// Do NOT add a route for scripts — hashed JS bundles are handled exclusively by
// precacheAndRoute above; a second route for them would corrupt the cache.
registerRoute(
  ({ request }) => request.destination === 'style',
  new StaleWhileRevalidate({
    cacheName: 'css-runtime',
    plugins: [
      new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 30 * 24 * 60 * 60 }),
    ],
  }),
);

