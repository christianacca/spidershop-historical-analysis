import type { SortableTablePageConfig } from './page-init.js';
import { registerPageInit, registerSortableTablePage } from './page-init.js';
import { saveScrollPosition } from './scroll-restoration.js';

interface BootstrapSortableTablePageOptions {
  beforeTableInit?: () => void;
}

export function bootstrapSortableTablePage(
  config: SortableTablePageConfig,
  options: BootstrapSortableTablePageOptions = {},
): void {
  // Save scroll position when the user leaves this listing page so that
  // view-transition backward navigation can restore it on return.
  window.addEventListener('pagehide', () => {
    saveScrollPosition(window.location.href, window.scrollY);
  });

  if (options.beforeTableInit) {
    registerPageInit(options.beforeTableInit);
  }

  registerSortableTablePage(config);
}