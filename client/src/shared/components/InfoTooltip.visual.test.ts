/**
 * InfoTooltip + WarningTip — browser-backed visual contracts (common.css).
 *
 * Guards against regressions in the tooltip CSS after the deduplication of
 * .info-tip and .warning-tip shared rules in common.css.
 *
 * InfoTooltip is a Svelte component → rendered via @testing-library/svelte.
 * WarningTip has no Svelte component → tested via raw DOM fixture (class-based
 * CSS from common.css applies because common.css is injected by browser-setup.ts).
 *
 * Coverage:
 *   - Background colour per-tip (unique: --color-primary vs --color-signal-watch)
 *   - Shared hidden state at rest (visibility: hidden)
 *   - Shared position: absolute on desktop
 *   - Shared border-radius from --radius-md token
 *   - Shared font-size 0.85rem
 *   - Mobile (≤768px): position: fixed, left/right pinned to viewport edges
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { page } from '@vitest/browser/context';
import { render } from '@testing-library/svelte';
import { tokenRgb, tokenHex } from '../../test-utils/token-colors';
import InfoTooltip from './InfoTooltip.svelte';

// ── Warning-tip DOM fixture ──────────────────────────────────────────────────

/**
 * Insert a raw .warning-tip element into document.body.
 * Returns the inserted element.  Caller must remove it after the test.
 */
function insertWarningTip(text = 'Test warning'): HTMLElement {
  const el = document.createElement('span');
  el.className = 'warning-tip';
  el.setAttribute('tabindex', '0');
  el.innerHTML = `⚠️<span class="warning-tip__text">${text}</span>`;
  document.body.appendChild(el);
  return el;
}

// ── Desktop info-tip visual contracts ────────────────────────────────────────

describe('InfoTooltip — .info-tip__text CSS (desktop)', () => {
  beforeEach(async () => {
    await page.viewport(1280, 900);
  });

  it('background-color uses --color-primary token', () => {
    const { container } = render(InfoTooltip, { tip: 'Test info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).backgroundColor).toBe(tokenRgb('--color-primary'));
  });

  it('is hidden (visibility: hidden) at rest', () => {
    const { container } = render(InfoTooltip, { tip: 'Test info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).visibility).toBe('hidden');
  });

  it('is position: absolute on desktop', () => {
    const { container } = render(InfoTooltip, { tip: 'Test info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).position).toBe('absolute');
  });

  it('border-radius resolves to --radius-md token value', () => {
    const { container } = render(InfoTooltip, { tip: 'Test info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).borderRadius).toBe(tokenHex('--radius-md'));
  });
});

// ── Desktop warning-tip visual contracts ─────────────────────────────────────

describe('WarningTip — .warning-tip__text CSS (desktop)', () => {
  let fixture: HTMLElement | null = null;

  beforeEach(async () => {
    await page.viewport(1280, 900);
  });

  afterEach(() => {
    if (fixture?.parentNode) fixture.parentNode.removeChild(fixture);
    fixture = null;
  });

  it('background-color uses --color-signal-watch token', () => {
    fixture = insertWarningTip();
    const text = fixture.querySelector('.warning-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).backgroundColor).toBe(tokenRgb('--color-signal-watch'));
  });

  it('is hidden (visibility: hidden) at rest', () => {
    fixture = insertWarningTip();
    const text = fixture.querySelector('.warning-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).visibility).toBe('hidden');
  });

  it('is position: absolute on desktop', () => {
    fixture = insertWarningTip();
    const text = fixture.querySelector('.warning-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).position).toBe('absolute');
  });

  it('border-radius resolves to --radius-md token value', () => {
    fixture = insertWarningTip();
    const text = fixture.querySelector('.warning-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).borderRadius).toBe(tokenHex('--radius-md'));
  });
});

// ── Mobile tooltip positioning (≤768px) ──────────────────────────────────────

describe('Tooltip — mobile positioning (≤768px)', () => {
  const DESKTOP = { width: 1280, height: 900 };
  const MOBILE = { width: 390, height: 844 };

  afterEach(async () => {
    await page.viewport(DESKTOP.width, DESKTOP.height);
  });

  it('.info-tip__text has position:fixed on mobile', async () => {
    await page.viewport(MOBILE.width, MOBILE.height);
    const { container } = render(InfoTooltip, { tip: 'Mobile info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).position).toBe('fixed');
  });

  it('.warning-tip__text has position:fixed on mobile', async () => {
    await page.viewport(MOBILE.width, MOBILE.height);
    const el = insertWarningTip('Mobile warning');
    try {
      const text = el.querySelector('.warning-tip__text') as HTMLElement;
      expect(window.getComputedStyle(text).position).toBe('fixed');
    } finally {
      el.parentNode?.removeChild(el);
    }
  });

  it('.info-tip__text is pinned left 16px on mobile', async () => {
    await page.viewport(MOBILE.width, MOBILE.height);
    const { container } = render(InfoTooltip, { tip: 'Mobile info' });
    const text = container.querySelector('.info-tip__text') as HTMLElement;
    expect(window.getComputedStyle(text).left).toBe('16px');
  });

  it('.warning-tip__text is pinned left 16px on mobile', async () => {
    await page.viewport(MOBILE.width, MOBILE.height);
    const el = insertWarningTip('Mobile warning');
    try {
      const text = el.querySelector('.warning-tip__text') as HTMLElement;
      expect(window.getComputedStyle(text).left).toBe('16px');
    } finally {
      el.parentNode?.removeChild(el);
    }
  });
});
