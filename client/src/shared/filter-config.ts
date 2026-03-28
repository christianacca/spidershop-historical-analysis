import type { FilterConfig } from './components/SortableTable.svelte';

const DEFAULT_FILTER_CONFIG = {
  priceColumn: 'Price',
  wishlistColumn: 'Wishlist',
  showSearch: true,
  statsLabel: 'species',
} satisfies Required<
  Pick<FilterConfig, 'priceColumn' | 'wishlistColumn' | 'showSearch' | 'statsLabel'>
>;

export function createFilterConfig(overrides: Partial<FilterConfig> = {}): FilterConfig {
  return {
    ...DEFAULT_FILTER_CONFIG,
    ...overrides,
  };
}