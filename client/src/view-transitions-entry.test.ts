import { describe, expect, it } from 'vitest';
import { isSpeciesPage, handlePageReveal } from './view-transitions-entry.js';

describe('isSpeciesPage', () => {
  it.each([
    ['species page at subpath',            '/subpath/species/brachypelma-hamorii.html', true],
    ['species page at root',               '/species/foo.html',                         true],
    ['species page with query param',      '/species/foo.html?view=breeder',            true],
    ['breeder listing page',               '/breeder.html',                             false],
    ['dealer listing page',               '/dealer.html',                              false],
    ['homepage',                           '/index.html',                               false],
    ['history page',                       '/history.html',                             false],
    ['species only in filename, not path', '/not-a-species.html',                       false],
  ])('%s', (_label, url, expected) => {
    expect(isSpeciesPage(url)).toBe(expected);
  });
});

// ---------------------------------------------------------------------------
// handlePageReveal — pagereveal handler logic
// ---------------------------------------------------------------------------

describe('handlePageReveal', () => {
  /** Creates a minimal ViewTransition mock that records which types were added. */
  function makeVt(): { vt: ViewTransition; added: Set<string> } {
    const added = new Set<string>();
    const vt = {
      types: {
        add: (t: string) => { added.add(t); },
        delete: (t: string) => { added.delete(t); },
        has: (t: string) => added.has(t),
      },
    } as unknown as ViewTransition;
    return { vt, added };
  }

  function makeEvent(viewTransition: ViewTransition | null): Event {
    return { viewTransition } as unknown as Event;
  }

  function makeActivation(fromUrl: string | null, entryUrl: string): NavigationActivation {
    return {
      from: fromUrl ? { url: fromUrl } : null,
      entry: { url: entryUrl },
    } as NavigationActivation;
  }

  it('does nothing when viewTransition is null (no VT support)', () => {
    const { added } = makeVt();
    handlePageReveal(makeEvent(null), makeActivation('/breeder.html', '/species/foo.html'));
    expect(added.size).toBe(0);
  });

  it('does nothing when activation is undefined (no Navigation API)', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), undefined);
    expect(added.size).toBe(0);
  });

  it('does nothing when activation.from is null (direct / typed navigation)', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), makeActivation(null, '/species/foo.html'));
    expect(added.size).toBe(0);
  });

  it('adds "forward" when navigating from a listing page to a species page', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), makeActivation('/breeder.html', '/species/aphonopelma-seemanni.html'));
    expect(added.has('forward')).toBe(true);
    expect(added.has('backward')).toBe(false);
  });

  it('adds "backward" when navigating from a species page to a listing page', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), makeActivation('/species/aphonopelma-seemanni.html', '/breeder.html'));
    expect(added.has('backward')).toBe(true);
    expect(added.has('forward')).toBe(false);
  });

  it('adds no type for species-to-species navigation', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), makeActivation('/species/foo.html', '/species/bar.html'));
    expect(added.size).toBe(0);
  });

  it('adds no type for non-species-to-non-species navigation', () => {
    const { vt, added } = makeVt();
    handlePageReveal(makeEvent(vt), makeActivation('/breeder.html', '/dealer.html'));
    expect(added.size).toBe(0);
  });
});
