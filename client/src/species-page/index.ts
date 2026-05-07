/**
 * Species Detail Page
 *
 * Tab switching, URL parameter sync, and chart initialisation.
 */

import { renderCharts } from './charts.js';

type View = 'breeder' | 'dealer';

const VIEW_LABELS: Record<View, string> = {
  breeder: 'Breeder',
  dealer: 'Dealer',
};

const VIEW_HINTS: Record<View, string> = {
  breeder: 'Breeder view: focuses on opportunity signals and scarcity.',
  dealer: 'Dealer view: focuses on supply risk, reliability, and restock speed.',
};

function updateNavigationContext(view: View): void {
  const backBreeder = document.getElementById('back-breeder');
  const backDealer = document.getElementById('back-dealer');
  if (backBreeder && backDealer) {
    backBreeder.classList.toggle('origin-btn', view === 'breeder');
    backDealer.classList.toggle('origin-btn', view === 'dealer');
  }

  const breadcrumbLink = document.querySelector('.breadcrumbs a') as HTMLAnchorElement | null;
  if (breadcrumbLink) {
    breadcrumbLink.textContent = VIEW_LABELS[view];
    breadcrumbLink.href = breadcrumbLink.href.replace(/(?:breeder|dealer)\.html/, `${view}.html`);
  }
}

function initTabSwitching(): void {
  document.querySelectorAll('[role="tab"]').forEach(tab => {
    tab.addEventListener('click', (e) => {
      const view = (e.target as HTMLElement).dataset.view as View | undefined;
      if (!view) return;

      document.querySelectorAll('[role="tab"]').forEach(t => {
        t.setAttribute('aria-selected', 'false');
      });
      (e.target as HTMLElement).setAttribute('aria-selected', 'true');

      document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
        (panel as HTMLElement).style.display = 'none';
      });
      document.getElementById(`panel-${view}`)!.style.display = 'block';

      const hint = document.getElementById('view-hint');
      if (hint) {
        hint.textContent = VIEW_HINTS[view];
      }

      updateNavigationContext(view);

      const url = new URL(window.location.href);
      url.searchParams.set('view', view);
      window.history.pushState({}, '', url);
    });
  });
}

function initViewFromURL(): void {
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view');
  if (viewParam && (viewParam === 'breeder' || viewParam === 'dealer')) {
    const tab = document.querySelector(`[data-view="${viewParam}"]`);
    if (tab) (tab as HTMLElement).click();
  }
}

function init(): void {
  initTabSwitching();
  initViewFromURL();
  renderCharts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
