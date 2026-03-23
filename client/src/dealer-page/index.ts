import { DEALER_PAGE_CONFIG } from './config.js';
import { wireMethodologyTabs, wireOpenDetailsLinks } from '../shared/dom-utils.js';
import { registerPageInit, registerSortableTablePage } from '../shared/page-init.js';

registerPageInit(() => {
	wireOpenDetailsLinks();
	wireMethodologyTabs();
});
registerSortableTablePage(DEALER_PAGE_CONFIG);
