import { writable } from 'svelte/store';
import { Workbox } from 'workbox-window';

export interface UseRegisterSWResult {
  needRefresh: ReturnType<typeof writable<boolean>>;
  updateServiceWorker: () => Promise<void>;
}

/**
 * Register a service worker via Workbox and return reactive state.
 *
 * Unlike `useRegisterSW` from `virtual:pwa-register/svelte`, this function
 * takes an explicit `swUrl` so the path is computed at runtime rather than
 * baked in at build time. This is critical for GitHub Pages deployment, where
 * the site lives at a subpath (`/spidershop-historical-analysis/`) and a
 * hardcoded `/sw.js` would 404.
 *
 * Callers should derive `swUrl` from `import.meta.url`, for example:
 *   `new URL('./sw.js', import.meta.url).href`
 * This resolves correctly in every hosting context without any build-time
 * configuration.
 */
export function useRegisterSW(swUrl: string): UseRegisterSWResult {
  const needRefresh = writable(false);
  const wb = new Workbox(swUrl, { type: 'classic' });

  // Reload is unconditional: the 'controlling' listener in showSkipWaitingPrompt
  // always reloads when the new SW takes control. No parameter is needed.
  const updateServiceWorker = async () => {
    wb.messageSkipWaiting();
  };

  const showSkipWaitingPrompt = () => {
    wb.addEventListener('controlling', (event) => {
      if (event.isUpdate) window.location.reload();
    });
    needRefresh.set(true);
  };

  // Primary update path: a new SW is installed and waiting for this tab to close.
  wb.addEventListener('waiting', showSkipWaitingPrompt);

  // Secondary path: another tab (or a direct browser action) triggered the update
  // externally, skipping the normal 'waiting' state for this registration.
  wb.addEventListener('installed', (event) => {
    if (typeof event.isUpdate === 'undefined' && event.isExternal) {
      showSkipWaitingPrompt();
    }
  });

  wb.register({ immediate: true });

  return { needRefresh, updateServiceWorker };
}
