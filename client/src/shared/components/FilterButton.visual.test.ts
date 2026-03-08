/**
 * FilterButton — browser-backed visual contracts. (Phase 6, step 35)
 *
 * Verifies that the button's computed background and border colours resolve
 * from the correct CSS design tokens in both active and inactive states.
 *
 * These assertions require a real browser: happy-dom cannot resolve
 * CSS custom properties via getComputedStyle().
 */
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/svelte';
import { tokenRgb } from '../../test-utils/token-colors';
import FilterButton from './FilterButton.svelte';

// ── Inactive state ────────────────────────────────────────────────────────────

describe('FilterButton — inactive state', () => {
  it('background uses --color-surface token', () => {
    const { container } = render(FilterButton, {
      label: 'All', value: 'all', active: false, onclick: vi.fn(),
    });
    const btn = container.querySelector('button') as HTMLElement;
    expect(window.getComputedStyle(btn).backgroundColor).toBe(tokenRgb('--color-surface'));
  });

  it('border uses --color-border-light token', () => {
    const { container } = render(FilterButton, {
      label: 'All', value: 'all', active: false, onclick: vi.fn(),
    });
    const btn = container.querySelector('button') as HTMLElement;
    expect(window.getComputedStyle(btn).borderTopColor).toBe(tokenRgb('--color-border-light'));
  });
});

// ── Active state (.is-active) ─────────────────────────────────────────────────

describe('FilterButton — active state (.is-active)', () => {
  it('background uses --color-accent token', () => {
    const { container } = render(FilterButton, {
      label: 'Hot 🔥', value: '🔥', active: true, onclick: vi.fn(),
    });
    const btn = container.querySelector('button') as HTMLElement;
    expect(window.getComputedStyle(btn).backgroundColor).toBe(tokenRgb('--color-accent'));
  });

  it('border uses --color-accent token', () => {
    const { container } = render(FilterButton, {
      label: 'Hot 🔥', value: '🔥', active: true, onclick: vi.fn(),
    });
    const btn = container.querySelector('button') as HTMLElement;
    expect(window.getComputedStyle(btn).borderTopColor).toBe(tokenRgb('--color-accent'));
  });

  it('text color is white (#fff) — hardcoded for contrast on accent background', () => {
    const { container } = render(FilterButton, {
      label: 'Hot 🔥', value: '🔥', active: true, onclick: vi.fn(),
    });
    const btn = container.querySelector('button') as HTMLElement;
    expect(window.getComputedStyle(btn).color).toBe('rgb(255, 255, 255)');
  });
});

// ── State semantics ───────────────────────────────────────────────────────────

describe('FilterButton — state semantics', () => {
  it('active and inactive backgrounds are visually distinct', () => {
    const activeBg = tokenRgb('--color-accent');
    const inactiveBg = tokenRgb('--color-surface');
    expect(activeBg).toBeDefined();
    expect(inactiveBg).toBeDefined();
    expect(activeBg).not.toBe(inactiveBg);
  });
});
