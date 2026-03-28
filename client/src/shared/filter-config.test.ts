import { describe, expect, it } from 'vitest';

import { createFilterConfig } from './filter-config.js';

describe('createFilterConfig', () => {
  it('applies the shared sortable table filter defaults', () => {
    expect(createFilterConfig()).toEqual({
      priceColumn: 'Price',
      wishlistColumn: 'Wishlist',
      showSearch: true,
      statsLabel: 'species',
    });
  });

  it('allows page-specific overrides on top of the shared defaults', () => {
    expect(
      createFilterConfig({
        signalFilter: { column: 'Signal', top10: true },
        stockPatternFilter: { column: 'Stock Pattern' },
        driversKey: 'Drivers',
      }),
    ).toEqual({
      signalFilter: { column: 'Signal', top10: true },
      stockPatternFilter: { column: 'Stock Pattern' },
      priceColumn: 'Price',
      wishlistColumn: 'Wishlist',
      showSearch: true,
      statsLabel: 'species',
      driversKey: 'Drivers',
    });
  });

  it('supports alternate source columns for pages that use raw CSV headings', () => {
    expect(
      createFilterConfig({
        priceColumn: 'Price (GBP)',
        wishlistColumn: 'Wishlist Count',
      }),
    ).toEqual({
      priceColumn: 'Price (GBP)',
      wishlistColumn: 'Wishlist Count',
      showSearch: true,
      statsLabel: 'species',
    });
  });
});