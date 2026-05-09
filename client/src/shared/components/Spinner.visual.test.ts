/**
 * Spinner — browser-backed visual contracts.
 *
 * Verifies that the spinner's computed styles are correct in a real browser.
 * happy-dom cannot resolve CSS custom properties or animation names reliably.
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import Spinner from './Spinner.svelte';

describe('Spinner — visual contracts', () => {
  it('is circular (border-radius: 50%)', async () => {
    const { container } = render(Spinner);
    await Promise.resolve();
    const el = container.querySelector('.spinner') as HTMLElement;
    expect(window.getComputedStyle(el).borderRadius).toBe('50%');
  });

  it('has a spin animation applied', async () => {
    const { container } = render(Spinner);
    await Promise.resolve();
    const el = container.querySelector('.spinner') as HTMLElement;
    const style = window.getComputedStyle(el);
    expect(style.animationName).not.toBe('none');
    expect(style.animationDuration).not.toBe('0s');
  });

  it('respects the size prop — computed width and height match the provided value', async () => {
    const { container } = render(Spinner, { size: '32px' });
    await Promise.resolve();
    const el = container.querySelector('.spinner') as HTMLElement;
    const style = window.getComputedStyle(el);
    expect(style.width).toBe('32px');
    expect(style.height).toBe('32px');
  });
});
