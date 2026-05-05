/**
 * Cross-document View Transitions — direction detection.
 *
 * The actual `pagereveal` event listener lives as an inline classic script in
 * `templates/base.html`.  <script type="module"> is deferred past
 * DOMContentLoaded, but `pagereveal` fires BEFORE DOMContentLoaded, so a
 * module script would always miss it.
 *
 * This module exports `isSpeciesPage` and `handlePageReveal` as pure functions
 * so they can be unit-tested in isolation.  The runtime behaviour is driven
 * entirely by the inline script in base.html.
 *
 * Graceful degradation:
 * - `pagereveal` is silently ignored by browsers without VT Level 2 support.
 * - `window.navigation` is Chrome 102+; optional-chaining guards Safari/Firefox
 *   so they receive the default cross-fade rather than throwing.
 *
 * The `@view-transition { navigation: auto }` CSS opt-in lives in `common.css`.
 */

/** Returns true when `url` is a species detail page. Exported for unit testing.
 *  Accepts null/undefined so callers can pass NavigationHistoryEntry.url directly
 *  (typed as string | null in the DOM lib — null for cross-origin opaque entries). */
export function isSpeciesPage(url: string | null | undefined): boolean {
  return !!url && /\/species\//.test(url);
}

/**
 * Core direction-detection logic for cross-document view transitions.
 * Exported for unit testing; the inline script in base.html calls equivalent
 * logic at runtime (classic script fires before DOMContentLoaded / pagereveal).
 *
 * @param event      - The `pagereveal` Event (cast to PageRevealEvent internally)
 * @param activation - The Navigation API activation, or undefined if not supported
 */
export function handlePageReveal(
  event: Event,
  activation: NavigationActivation | null | undefined,
): void {
  const vtEvent = event as PageRevealEvent;
  if (!vtEvent.viewTransition) return;
  if (!activation?.from) return;

  const fromSpecies = isSpeciesPage(activation.from.url);
  const toSpecies = isSpeciesPage(activation.entry.url);

  const vt = vtEvent.viewTransition;
  if (!fromSpecies && toSpecies) {
    vt.types.add('forward');
  } else if (fromSpecies && !toSpecies) {
    vt.types.add('backward');
  }
}
