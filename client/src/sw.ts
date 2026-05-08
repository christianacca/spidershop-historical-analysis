/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import type { PrecacheEntry } from 'workbox-precaching';
import { shouldEvictOnActivate } from './sw-activate.js';

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
// The unhashed top-level CSS files (common.css, analysis.css, etc.) are also
// included via additionalManifestEntries in vite.config.ts — they behave
// identically to hashed bundles: cache-first, atomically swapped on SW update.
precacheAndRoute(self.__WB_MANIFEST);

// Pre-fetch all main HTML pages into the html-pages cache during SW install.
// Workbox waits for ALL event.waitUntil promises before transitioning to waiting,
// so the toast can only fire after this completes. By the time the user sees
// "New data has been deployed", fresh HTML is already in the cache — clicking
// Refresh is guaranteed to serve the latest market data with no race condition.
// Failures are swallowed so a single unreachable page never aborts the install;
// the SWR route will populate the cache on first navigation as a fallback.
self.addEventListener('install', (event) => {
  const scope = self.registration.scope;
  const mainPages = [
    `${scope}index.html`,
    `${scope}breeder.html`,
    `${scope}dealer.html`,
    `${scope}snapshot.html`,
    `${scope}history.html`,
    `${scope}history-insights.html`,
  ];
  event.waitUntil(
    caches.open('html-pages').then(cache =>
      Promise.all(
        mainPages.map(url =>
          fetch(new Request(url, { cache: 'reload', credentials: 'same-origin' }))
            .then(resp => { if (resp.ok) return cache.put(url, resp); })
            .catch(() => {}),
        ),
      ),
    ),
  );
});

// On every SW activation, evict all non-main-page entries from the html-pages cache.
// Species detail pages (and any other previously-cached pages) are served via the SWR
// NavigationRoute and are only lazily populated — they are NOT pre-fetched during install.
// Without this eviction, after a deploy the old species HTML (with potentially outdated
// inline scripts, including the view-transition pagereveal handler) would be served on
// the first post-update visit, silently breaking view transitions and scroll restoration.
// The six main pages are safe: the install handler already pre-fetched them with
// fresh content before this activate handler runs (Workbox guarantees install completes
// before activate).  Species pages will be fetched fresh on first navigation after
// the SW update — one small network hit, but always correct HTML.
self.addEventListener('activate', (event) => {
  const scope = self.registration.scope;
  event.waitUntil(
    caches.open('html-pages').then(cache =>
      cache.keys().then(keys =>
        Promise.all(
          keys
            .filter(req => shouldEvictOnActivate(req.url, scope))
            .map(req => cache.delete(req)),
        ),
      ),
    ).then(() => self.clients.claim()),
  );
});

// HTML pages: StaleWhileRevalidate — serve from cache immediately, refresh in background.
// The install handler above ensures fresh HTML is already in the cache before the toast
// fires, eliminating the race condition where a user clicks Refresh before the SWR
// background fetch has completed.
// ExpirationPlugin bounds cache growth: 160+ species pages + 6 main pages.
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

