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
    if (link.dataset.detailsWired === 'true') return;

    link.addEventListener('click', () => {
      const targetId = link.dataset.target;
      if (targetId) {
        const target = document.getElementById(targetId) as HTMLDetailsElement | null;
        if (target) target.open = true;
      }
    });

    link.dataset.detailsWired = 'true';
  });
}

export function wireMethodologyTabs(): void {
  document.querySelectorAll<HTMLElement>('#methodology-section').forEach((section) => {
    const tabs = Array.from(
      section.querySelectorAll<HTMLButtonElement>('[data-methodology-tab]'),
    );
    const panels = Array.from(
      section.querySelectorAll<HTMLElement>('[data-methodology-panel]'),
    );

    if (tabs.length === 0 || panels.length === 0) return;

    const setActiveTab = (activeId: string): void => {
      tabs.forEach((tab) => {
        const isActive = tab.dataset.methodologyTab === activeId;
        tab.classList.toggle('is-active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        tab.tabIndex = isActive ? 0 : -1;
      });

      panels.forEach((panel) => {
        const isActive = panel.dataset.methodologyPanel === activeId;
        panel.classList.toggle('is-active', isActive);
        panel.hidden = !isActive;
      });
    };

    tabs.forEach((tab) => {
      if (tab.dataset.methodologyWired === 'true') return;

      tab.addEventListener('click', () => {
        const targetId = tab.dataset.methodologyTab;
        if (targetId) setActiveTab(targetId);
      });

      tab.dataset.methodologyWired = 'true';
    });

    const initiallyActive = tabs.find((tab) => tab.classList.contains('is-active'));
    setActiveTab(initiallyActive?.dataset.methodologyTab ?? tabs[0].dataset.methodologyTab ?? '');
  });
}
