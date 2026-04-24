/**
 * Stub for virtual:pwa-register/svelte — used in browser-mode visual tests.
 *
 * vite-plugin-pwa is not loaded in vite.browser.config.ts, so Vite cannot
 * resolve the real virtual module. This stub makes the module resolvable, and
 * vi.mock('virtual:pwa-register/svelte', factory) in individual test files
 * will override it with test-specific behaviour.
 */
import { writable } from 'svelte/store';

export function useRegisterSW() {
  return {
    needRefresh: writable(false),
    updateServiceWorker: () => {},
  };
}
