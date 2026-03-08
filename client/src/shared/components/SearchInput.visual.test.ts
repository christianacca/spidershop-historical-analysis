/**
 * SearchInput — browser-backed visual contracts. (Phase 6, step 36)
 *
 * Verifies that border colours resolve from CSS design tokens in both the
 * unfocused and focused states.
 *
 * Focus-state assertions require a real browser: happy-dom cannot reliably
 * resolve :focus pseudo-class styles against CSS custom properties.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import { vi } from 'vitest';
import { tokenRgb } from '../../test-utils/token-colors';
import SearchInput from './SearchInput.svelte';

// ── Unfocused state ───────────────────────────────────────────────────────────

describe('SearchInput — unfocused state', () => {
  it('border uses --color-border token', () => {
    const { container } = render(SearchInput, {
      placeholder: 'Search...', tableId: 'test', oninput: vi.fn(),
    });
    const input = container.querySelector('input') as HTMLInputElement;
    expect(window.getComputedStyle(input).borderTopColor).toBe(tokenRgb('--color-border'));
  });

  it('background uses --color-surface token', () => {
    const { container } = render(SearchInput, {
      placeholder: 'Search...', tableId: 'test', oninput: vi.fn(),
    });
    const input = container.querySelector('input') as HTMLInputElement;
    expect(window.getComputedStyle(input).backgroundColor).toBe(tokenRgb('--color-surface'));
  });
});

// ── Focused state ─────────────────────────────────────────────────────────────

describe('SearchInput — focused state', () => {
  it('focused border uses --color-accent token', () => {
    const { container } = render(SearchInput, {
      placeholder: 'Search...', tableId: 'test', oninput: vi.fn(),
    });
    const input = container.querySelector('input') as HTMLInputElement;
    input.focus();
    expect(window.getComputedStyle(input).borderTopColor).toBe(tokenRgb('--color-accent'));
  });

  it('focused border is visually distinct from unfocused border', () => {
    const unfocusedColor = tokenRgb('--color-border');
    const focusedColor = tokenRgb('--color-accent');
    expect(unfocusedColor).toBeDefined();
    expect(focusedColor).toBeDefined();
    expect(focusedColor).not.toBe(unfocusedColor);
  });
});
