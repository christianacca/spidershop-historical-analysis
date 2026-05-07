/**
 * Scroll position save/restore for cross-document view transitions.
 *
 * Problem: when a user navigates listing → species → back, the listing page
 * is loaded fresh and starts at scrollY = 0, losing their position.
 *
 * Two-phase restoration strategy:
 *
 * Phase 1 — `beginScrollRestoration` (called from the inline pagereveal handler
 * in base.html, which fires before DOMContentLoaded and before the VT animation
 * starts). Scrolls immediately so the listing page is already at the correct
 * position when the species page slides off.
 *
 * Phase 2 — `completeScrollRestoration` (called from page-init.ts after the
 * Svelte table is mounted). Corrects the position when the skeleton at pagereveal
 * time was shorter than the fully-inflated table, causing phase 1 to clamp.
 *
 * `saveScrollPosition` is called from page-entry.ts on the `pagehide` event so
 * the position is always persisted before the user leaves the listing page.
 */

export const SCROLL_KEY_PREFIX = 'vt-scroll:';

/**
 * Saves the current scroll position for a listing page URL to sessionStorage.
 * Called from the listing page `pagehide` handler so the position is persisted
 * before the user navigates away.
 */
export function saveScrollPosition(url: string, scrollY: number): void {
  try {
    sessionStorage.setItem(`${SCROLL_KEY_PREFIX}${url}`, String(Math.round(scrollY)));
  } catch {
    // Ignore QuotaExceededError or SecurityError (e.g. private browsing restrictions)
  }
}

/**
 * Phase 1 restoration — call this as early as possible (pagereveal / before
 * DOMContentLoaded) when a backward view transition is detected.
 *
 * Reads and removes the saved scroll Y from sessionStorage, stores it in
 * `window.__vtScrollRestoreY` for phase 2, and scrolls immediately.
 *
 * Returns true when a saved position was found and applied; false otherwise.
 */
export function beginScrollRestoration(url: string): boolean {
  try {
    const key = `${SCROLL_KEY_PREFIX}${url}`;
    const saved = sessionStorage.getItem(key);
    if (saved === null) return false;

    sessionStorage.removeItem(key);
    const y = parseInt(saved, 10);

    // Stash for phase 2 (in case the skeleton is shorter than the full content)
    (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY = y;
    window.scrollTo({ top: y, behavior: 'instant' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Phase 2 restoration — call this after the Svelte table is mounted (i.e. once
 * the page is fully inflated). If phase 1 was clamped because the page skeleton
 * was shorter than the final content, this corrects the scroll position.
 *
 * No-op when phase 1 was not called or already completed.
 */
export function completeScrollRestoration(): void {
  const w = window as { __vtScrollRestoreY?: number };
  const y = w.__vtScrollRestoreY;
  if (y === undefined) return;

  delete w.__vtScrollRestoreY;
  window.scrollTo({ top: y, behavior: 'instant' });
}
