/**
 * TimeWindowSelector — browser-backed visual contracts (P2-3).
 *
 * Verifies computed styles for window pill buttons:
 * - Active pill: dark background (var(--color-text)), white text
 * - Default pill: white background, solid warm border
 * - flex-wrap at mobile viewport
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
import { render } from '@testing-library/svelte';
import TimeWindowSelector from './TimeWindowSelector.svelte';
import { tokenRgb } from '../test-utils/token-colors';
import type { WindowId } from './types.js';

function defaultProps(overrides: Partial<{
  windowId: WindowId;
  basisNote: string;
  onWindowChange: (id: WindowId) => void;
}> = {}) {
  return {
    windowId: 'current-quarter' as WindowId,
    basisNote: 'Comparison basis: last full quarter vs prior full quarter.',
    onWindowChange: vi.fn(),
    ...overrides,
  };
}

describe('TimeWindowSelector — active pill styles', () => {
  it('active button backgroundColor resolves to var(--color-text) = rgb(31, 42, 44)', () => {
    const { container } = render(TimeWindowSelector, defaultProps({ windowId: 'current-quarter' }));
    const activeBtn = [...container.querySelectorAll('button.window')]
      .find(b => b.classList.contains('active')) as HTMLElement;
    expect(activeBtn).not.toBeNull();
    const bg = window.getComputedStyle(activeBtn).backgroundColor;
    expect(bg).toBe(tokenRgb('--color-text'));
  });

  it('active button color resolves to rgb(255, 255, 255)', () => {
    const { container } = render(TimeWindowSelector, defaultProps({ windowId: 'this-month' }));
    const activeBtn = [...container.querySelectorAll('button.window')]
      .find(b => b.classList.contains('active')) as HTMLElement;
    expect(activeBtn).not.toBeNull();
    const color = window.getComputedStyle(activeBtn).color;
    expect(color).toBe('rgb(255, 255, 255)');
  });
});

describe('TimeWindowSelector — default pill styles', () => {
  it('non-active button borderStyle is solid', () => {
    const { container } = render(TimeWindowSelector, defaultProps({ windowId: 'this-month' }));
    const defaultBtn = [...container.querySelectorAll('button.window')]
      .find(b => !b.classList.contains('active')) as HTMLElement;
    expect(defaultBtn).not.toBeNull();
    const borderStyle = window.getComputedStyle(defaultBtn).borderTopStyle;
    expect(borderStyle).toBe('solid');
  });

  it('non-active button backgroundColor is rgb(255, 255, 255)', () => {
    const { container } = render(TimeWindowSelector, defaultProps({ windowId: 'this-month' }));
    const defaultBtn = [...container.querySelectorAll('button.window')]
      .find(b => !b.classList.contains('active')) as HTMLElement;
    expect(defaultBtn).not.toBeNull();
    const bg = window.getComputedStyle(defaultBtn).backgroundColor;
    expect(bg).toBe('rgb(255, 255, 255)');
  });
});

describe('TimeWindowSelector — flex-wrap at mobile viewport', () => {
  afterEach(async () => {
    await page.viewport(1280, 720);
  });

  it('window-row has flex-wrap: wrap at mobile viewport (390 × 844)', async () => {
    await page.viewport(390, 844);
    const { container } = render(TimeWindowSelector, defaultProps());
    const windowRow = container.querySelector('.window-row') as HTMLElement;
    expect(windowRow).not.toBeNull();
    const flexWrap = window.getComputedStyle(windowRow).flexWrap;
    expect(flexWrap).toBe('wrap');
  });

  it('at least one pill wraps to a new row at mobile viewport (390 × 844)', async () => {
    await page.viewport(390, 844);
    const { container } = render(TimeWindowSelector, defaultProps());
    const buttons = [...container.querySelectorAll('button.window')] as HTMLElement[];
    expect(buttons.length).toBe(7);
    const firstTop = buttons[0].offsetTop;
    const wraps = buttons.some(b => b.offsetTop > firstTop);
    expect(wraps).toBe(true);
  });
});
