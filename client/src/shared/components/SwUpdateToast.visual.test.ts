/**
 * SwUpdateToast — browser-backed visual contracts.
 *
 * Verifies that the toast's computed styles resolve from CSS design tokens,
 * that an entrance animation is applied, and that mobile layout is correct.
 *
 * These assertions require a real browser: happy-dom cannot resolve
 * CSS custom properties via getComputedStyle().
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
import { writable } from 'svelte/store';
import { render } from '@testing-library/svelte';
import { tokenRgb, tokenHex } from '../../test-utils/token-colors';
import SwUpdateToast from './SwUpdateToast.svelte';

const mockUpdateServiceWorker = vi.fn();
const mockNeedRefresh = writable(false);

function renderToast() {
  return render(SwUpdateToast, {
    needRefresh: mockNeedRefresh,
    updateServiceWorker: mockUpdateServiceWorker,
  });
}

// Ensure each test starts with the toast hidden regardless of declaration order.
beforeEach(() => {
  mockNeedRefresh.set(false);
});

describe('SwUpdateToast — visible state', () => {
  it('background uses --color-accent token', async () => {
    mockNeedRefresh.set(true);
    const { container } = renderToast();
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    expect(window.getComputedStyle(toast).backgroundColor).toBe(tokenRgb('--color-accent'));
  });

  it('has position: fixed', async () => {
    mockNeedRefresh.set(true);
    const { container } = renderToast();
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    expect(window.getComputedStyle(toast).position).toBe('fixed');
  });

  it('has a slide-up entrance animation', async () => {
    mockNeedRefresh.set(true);
    const { container } = renderToast();
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    const style = window.getComputedStyle(toast);
    expect(style.animationName).not.toBe('none');
    expect(style.animationDuration).not.toBe('0s');
  });
});

describe('SwUpdateToast — mobile layout (≤480px viewport)', () => {
  const DESKTOP_WIDTH = 1280;
  const DESKTOP_HEIGHT = 900;
  const MOBILE_WIDTH = 390;
  const MOBILE_HEIGHT = 844;

  afterEach(async () => {
    await page.viewport(DESKTOP_WIDTH, DESKTOP_HEIGHT);
    mockNeedRefresh.set(false);
  });

  it('left edge is pinned to --spacing-lg on mobile', async () => {
    await page.viewport(MOBILE_WIDTH, MOBILE_HEIGHT);
    mockNeedRefresh.set(true);
    const { container } = renderToast();
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    const expectedLeft = tokenHex('--spacing-lg'); // '20px'
    expect(window.getComputedStyle(toast).left).toBe(expectedLeft);
  });

  it('buttons have a minimum 44px touch target height on mobile', async () => {
    await page.viewport(MOBILE_WIDTH, MOBILE_HEIGHT);
    mockNeedRefresh.set(true);
    const { container } = renderToast();
    await Promise.resolve();
    const buttons = container.querySelectorAll('.sw-update-toast button') as NodeListOf<HTMLElement>;
    for (const btn of buttons) {
      const height = parseFloat(window.getComputedStyle(btn).height);
      expect(height).toBeGreaterThanOrEqual(44);
    }
  });
});
