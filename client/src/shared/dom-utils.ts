/**
 * DOM Utilities
 *
 * Reusable DOM helpers used across page slices.
 */

/**
 * Get element by ID with warning if not found
 */
export function getElement(id: string): HTMLElement | null {
  const el = document.getElementById(id);
  if (!el) console.warn(`Element not found: ${id}`);
  return el;
}

/**
 * Wire click listeners on `<a data-action="open-details">` elements so that
 * clicking them opens the `<details>` element referenced by `data-target`.
 */
export function wireOpenDetailsLinks(): void {
  document.querySelectorAll<HTMLAnchorElement>('a[data-action="open-details"]').forEach((link) => {
    link.addEventListener('click', () => {
      const targetId = link.dataset.target;
      if (targetId) {
        const target = document.getElementById(targetId) as HTMLDetailsElement | null;
        if (target) target.open = true;
      }
    });
  });
}
