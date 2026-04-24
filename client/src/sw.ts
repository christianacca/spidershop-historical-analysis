/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import type { PrecacheEntry } from 'workbox-precaching';

declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<PrecacheEntry | string> };

// Must be called BEFORE precacheAndRoute to remove stale entries from prior builds.
cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);
