import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  SCROLL_KEY_PREFIX,
  saveScrollPosition,
  beginScrollRestoration,
  completeScrollRestoration,
} from './scroll-restoration.js';

describe('saveScrollPosition', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('saves the scroll position under the expected key', () => {
    saveScrollPosition('http://localhost/breeder.html', 350);
    expect(sessionStorage.getItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html`)).toBe('350');
  });

  it('rounds fractional scrollY values', () => {
    saveScrollPosition('http://localhost/dealer.html', 123.7);
    expect(sessionStorage.getItem(`${SCROLL_KEY_PREFIX}http://localhost/dealer.html`)).toBe('124');
  });

  it('preserves full URL including query string in the key', () => {
    saveScrollPosition('http://localhost/breeder.html?view=hot', 200);
    expect(sessionStorage.getItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html?view=hot`)).toBe('200');
  });

  it('overwrites an existing saved position for the same URL', () => {
    saveScrollPosition('http://localhost/breeder.html', 100);
    saveScrollPosition('http://localhost/breeder.html', 400);
    expect(sessionStorage.getItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html`)).toBe('400');
  });
});

describe('beginScrollRestoration', () => {
  let scrollToSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    sessionStorage.clear();
    scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    delete (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY;
  });

  afterEach(() => {
    scrollToSpy.mockRestore();
    delete (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY;
  });

  it('returns false when no position is saved for the URL', () => {
    const result = beginScrollRestoration('http://localhost/breeder.html');
    expect(result).toBe(false);
  });

  it('returns true when a saved position is found', () => {
    sessionStorage.setItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html`, '350');
    const result = beginScrollRestoration('http://localhost/breeder.html');
    expect(result).toBe(true);
  });

  it('calls window.scrollTo with the saved Y position', () => {
    sessionStorage.setItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html`, '450');
    beginScrollRestoration('http://localhost/breeder.html');
    expect(scrollToSpy).toHaveBeenCalledWith({ top: 450, behavior: 'instant' });
  });

  it('removes the sessionStorage key after reading', () => {
    const key = `${SCROLL_KEY_PREFIX}http://localhost/breeder.html`;
    sessionStorage.setItem(key, '350');
    beginScrollRestoration('http://localhost/breeder.html');
    expect(sessionStorage.getItem(key)).toBeNull();
  });

  it('stores the target Y in window.__vtScrollRestoreY for phase 2', () => {
    sessionStorage.setItem(`${SCROLL_KEY_PREFIX}http://localhost/breeder.html`, '600');
    beginScrollRestoration('http://localhost/breeder.html');
    expect((window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY).toBe(600);
  });

  it('does not set window.__vtScrollRestoreY when nothing is saved', () => {
    beginScrollRestoration('http://localhost/breeder.html');
    expect((window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY).toBeUndefined();
  });

  it('does not call window.scrollTo when nothing is saved', () => {
    beginScrollRestoration('http://localhost/breeder.html');
    expect(scrollToSpy).not.toHaveBeenCalled();
  });
});

describe('completeScrollRestoration', () => {
  let scrollToSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    delete (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY;
  });

  afterEach(() => {
    scrollToSpy.mockRestore();
    delete (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY;
  });

  it('is a no-op when window.__vtScrollRestoreY is not set', () => {
    completeScrollRestoration();
    expect(scrollToSpy).not.toHaveBeenCalled();
  });

  it('calls window.scrollTo with the pending Y position', () => {
    (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY = 350;
    completeScrollRestoration();
    expect(scrollToSpy).toHaveBeenCalledWith({ top: 350, behavior: 'instant' });
  });

  it('clears window.__vtScrollRestoreY after applying', () => {
    (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY = 350;
    completeScrollRestoration();
    expect((window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY).toBeUndefined();
  });

  it('is idempotent — second call is a no-op', () => {
    (window as { __vtScrollRestoreY?: number }).__vtScrollRestoreY = 350;
    completeScrollRestoration();
    completeScrollRestoration();
    expect(scrollToSpy).toHaveBeenCalledTimes(1);
  });
});
