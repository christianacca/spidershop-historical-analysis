import type { SortableTablePageConfig } from './page-init.js';
import { registerPageInit, registerSortableTablePage } from './page-init.js';

interface BootstrapSortableTablePageOptions {
  beforeTableInit?: () => void;
}

export function bootstrapSortableTablePage(
  config: SortableTablePageConfig,
  options: BootstrapSortableTablePageOptions = {},
): void {
  if (options.beforeTableInit) {
    registerPageInit(options.beforeTableInit);
  }

  registerSortableTablePage(config);
}