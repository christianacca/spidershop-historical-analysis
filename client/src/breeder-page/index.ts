import { BREEDER_PAGE_CONFIG } from './config.js';
import { wireMethodologyTabs, wireOpenDetailsLinks } from '../shared/dom-utils.js';
import { bootstrapSortableTablePage } from '../shared/page-entry.js';

bootstrapSortableTablePage(BREEDER_PAGE_CONFIG, {
  beforeTableInit: () => {
    wireOpenDetailsLinks();
    wireMethodologyTabs();
  },
});
