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
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg?.waiting) {
      // Normal path: tell the waiting SW to take control.
      // The 'controlling' listener fires the reload once the new SW becomes active.
      wb.messageSkipWaiting();
    } else {
      // Race path: another tab already activated the new SW.
      // Reload directly since V2 is already serving.
      window.location.reload();
    }
  };

  let needRefreshCalled = false;
  const showSkipWaitingPrompt = () => {
    needRefreshCalled = true;
    // Reload unconditionally: this listener is only added when an update is confirmed
    // (inside showSkipWaitingPrompt), so 'controlling' here always means the new SW
    // just took over after an explicit user action or auto-countdown.
    //
    // The `event.isUpdate` guard was previously used here but is unreliable: when a
    // new tab opens and the waiting SW was already present before this Workbox instance
    // was created, Workbox never sees 'updatefound', so _isUpdate stays undefined and
    // event.isUpdate is falsy — causing the reload to be silently skipped.
    wb.addEventListener('controlling', () => {
      window.location.reload();
    });
    needRefresh.set(true);
  };

  // Primary update path: a new SW is installed and waiting for this tab to close.
  wb.addEventListener('waiting', showSkipWaitingPrompt);

  // Secondary path: another tab (or a direct browser action) triggered the update
  // externally, skipping the normal 'waiting' state for this registration.
  wb.addEventListener('installed', (event) => {
    if (!needRefreshCalled && typeof event.isUpdate === 'undefined' && event.isExternal) {
      showSkipWaitingPrompt();
    }
  });

  wb.register({ immediate: true });

  return { needRefresh, updateServiceWorker };
}
