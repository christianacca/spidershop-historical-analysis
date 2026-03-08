/**
 * TableStats — browser-backed visual contracts. (Phase 6, step 39)
 *
 * Verifies that the info-strip background and text colour resolve from the
 * correct CSS design tokens.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import { vi } from 'vitest';
import { tokenRgb } from '../../test-utils/token-colors';
import TableStats from './TableStats.svelte';

describe('TableStats — info strip chrome', () => {
  it('background uses --color-info-bg token', () => {
    const { container } = render(TableStats, {
      tableId: 'test', visibleCount: 5, totalRows: 10, onDownload: vi.fn(),
    });
    const strip = container.querySelector('.table-stats') as HTMLElement;
    expect(window.getComputedStyle(strip).backgroundColor).toBe(tokenRgb('--color-info-bg'));
  });

  it('text color uses --color-text token', () => {
    const { container } = render(TableStats, {
      tableId: 'test', visibleCount: 5, totalRows: 10, onDownload: vi.fn(),
    });
    const strip = container.querySelector('.table-stats') as HTMLElement;
    expect(window.getComputedStyle(strip).color).toBe(tokenRgb('--color-text'));
  });
});
