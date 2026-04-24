/**
 * SwUpdateToast — browser-backed visual contracts.
 *
 * Verifies that the toast's computed styles resolve from CSS design tokens
 * and that position/visibility behave correctly.
 *
 * These assertions require a real browser: happy-dom cannot resolve
 * CSS custom properties via getComputedStyle().
 */
import { describe, it, expect, vi } from 'vitest';
import { writable } from 'svelte/store';
import { render } from '@testing-library/svelte';
import { tokenRgb } from '../../test-utils/token-colors';
import SwUpdateToast from './SwUpdateToast.svelte';

const mockUpdateServiceWorker = vi.fn();
const mockNeedRefresh = writable(false);

vi.mock('virtual:pwa-register/svelte', () => ({
  useRegisterSW: vi.fn(() => ({
    needRefresh: mockNeedRefresh,
    updateServiceWorker: mockUpdateServiceWorker,
  })),
}));

describe('SwUpdateToast — hidden state', () => {
  it('is not rendered in the DOM when needRefresh is false', () => {
    const { container } = render(SwUpdateToast);
    expect(container.querySelector('.sw-update-toast')).toBeNull();
  });
});

describe('SwUpdateToast — visible state', () => {
  it('background uses --color-primary token', async () => {
    mockNeedRefresh.set(true);
    const { container } = render(SwUpdateToast);
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    expect(window.getComputedStyle(toast).backgroundColor).toBe(tokenRgb('--color-primary'));
  });

  it('has position: fixed', async () => {
    mockNeedRefresh.set(true);
    const { container } = render(SwUpdateToast);
    await Promise.resolve();
    const toast = container.querySelector('.sw-update-toast') as HTMLElement;
    expect(window.getComputedStyle(toast).position).toBe('fixed');
  });
});
