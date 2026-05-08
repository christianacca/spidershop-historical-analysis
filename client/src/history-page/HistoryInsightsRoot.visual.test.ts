/**
 * HistoryInsightsRoot — browser-backed visual contracts.
 *
 * P1-6: Verify --color-breeder-focus CSS custom property resolves to the correct
 * computed colour value in a real Chromium instance.
 */
import { describe, it, expect } from 'vitest';
import { tokenRgb } from '../test-utils/token-colors';

describe('HistoryInsightsRoot — P1-6 --color-breeder-focus token', () => {
  it('--color-breeder-focus resolves to rgb(204, 107, 73)', () => {
    // #cc6b49 → rgb(204, 107, 73)
    expect(tokenRgb('--color-breeder-focus')).toBe('rgb(204, 107, 73)');
  });
});
