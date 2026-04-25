/**
 * MarketHealthRawData fixture for market-health-engine.ts unit tests (Phase 11).
 *
 * Reference date: 2026-04-13T06:10:00 (most recent scrape_datetime)
 *
 * Four runs spanning Q1 and Q2 2026:
 *   Run 0 — 2026-01-05T06:10:00  (Q1)
 *   Run 1 — 2026-01-12T06:10:00  (Q1; within current-quarter prior: Jan 1–13)
 *   Run 2 — 2026-04-06T06:10:00  (Q2)
 *   Run 3 — 2026-04-13T06:10:00  (Q2; the referenceDate)
 *
 * Five species with deliberate variety:
 *
 *   A. Avicularia avicularia     — present in all runs (stable)
 *   B. Brachypelma hamorii       — runs 0,1 only (OOS flip 1→2, dropped listing)
 *   C. Caribena versicolor       — run 0, absent run 1, back runs 2-3 (OOS flip + restock)
 *   D. Dolichothele diamantinensis — multi-variant: 2 rows per run (same pageUrl url-d,
 *                                    sizeVariants "1.0" and "2.0") — exercises max-variant
 *                                    dedup in wishlist and price metrics
 *   E. Ephebopus murinus         — size transition: size "2.0" at run 0, absent run 1,
 *                                    size "2.5" at runs 2-3 (same pageUrl url-e) — must
 *                                    NOT be counted as a new listing, OOS flip, or restock
 *
 * Hand-calculated medians (for tests):
 *
 *   Run 0 (5 species):
 *     wl by species: A=10, B=20, C=30, D=max(5,5)=5, E=15 → sorted [5,10,15,20,30] → median=15
 *     price by species: A=20, B=40, C=30, D=max(10,20)=20, E=25 → sorted [20,20,25,30,40] → median=25
 *
 *   Run 1 (3 species: A, B, D):
 *     wl: A=12, B=22, D=max(6,6)=6 → sorted [6,12,22] → median=12
 *     price: A=22, B=42, D=max(10,20)=20 → sorted [20,22,42] → median=22
 *
 *   Run 2 (4 species: A, C, D, E):
 *     wl: A=14, C=32, D=max(7,7)=7, E=16 → sorted [7,14,16,32] → median=(14+16)/2=15
 *     price: A=24, C=32, D=max(10,20)=20, E=26 → sorted [20,24,26,32] → median=(24+26)/2=25
 *
 *   Run 3 (4 species: A, C, D, E) [referenceDate]:
 *     wl: A=16, C=34, D=max(8,8)=8, E=18 → sorted [8,16,18,34] → median=(16+18)/2=17
 *     price: A=26, C=34, D=max(10,20)=20, E=28 → sorted [20,26,28,34] → median=(26+28)/2=27
 *
 * All-time events (4 runs, verified by hand):
 *   new_listings=0, dropped_listings=1, restocks=1, oos_flips=2
 *
 * Current-quarter (Q2 2026, runs 2-3): all counts=0 (species set stable across those 2 runs)
 * Last-quarter (Q1 2026, runs 0-1): observed=5, stock=60%, wl=12, price=22
 */

import type { MarketHealthRawData } from '../types.js';

export const rawMarketHealthData: MarketHealthRawData = {
  referenceDate: '2026-04-13T06:10:00',
  records: [
    // ── Run 0 — 2026-01-05T06:10:00 ──────────────────────────────────────────

    // A: Avicularia avicularia
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Avicularia avicularia', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 10, priceGbp: 20 },
    // B: Brachypelma hamorii
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Brachypelma hamorii', sizeVariant: '3.0', pageUrl: 'url-b', wishlistCount: 20, priceGbp: 40 },
    // C: Caribena versicolor
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Caribena versicolor', sizeVariant: '1.5', pageUrl: 'url-c', wishlistCount: 30, priceGbp: 30 },
    // D: Dolichothele diamantinensis — variant 1 (size 1.0)
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '1.0', pageUrl: 'url-d', wishlistCount: 5, priceGbp: 10 },
    // D: Dolichothele diamantinensis — variant 2 (size 2.0, same pageUrl)
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '2.0', pageUrl: 'url-d', wishlistCount: 5, priceGbp: 20 },
    // E: Ephebopus murinus — size 2.0
    { scrapeDatetime: '2026-01-05T06:10:00', scientificName: 'Ephebopus murinus', sizeVariant: '2.0', pageUrl: 'url-e', wishlistCount: 15, priceGbp: 25 },

    // ── Run 1 — 2026-01-12T06:10:00 ──────────────────────────────────────────
    // C (Caribena) and E (Ephebopus) are absent → OOS flips from run 0→1

    // A: Avicularia avicularia
    { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Avicularia avicularia', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 12, priceGbp: 22 },
    // B: Brachypelma hamorii
    { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Brachypelma hamorii', sizeVariant: '3.0', pageUrl: 'url-b', wishlistCount: 22, priceGbp: 42 },
    // D: Dolichothele — variant 1
    { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '1.0', pageUrl: 'url-d', wishlistCount: 6, priceGbp: 10 },
    // D: Dolichothele — variant 2
    { scrapeDatetime: '2026-01-12T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '2.0', pageUrl: 'url-d', wishlistCount: 6, priceGbp: 20 },

    // ── Run 2 — 2026-04-06T06:10:00 ──────────────────────────────────────────
    // B (Brachypelma) drops out permanently after run 1
    // C (Caribena) restocks (not a size transition — same URL, same sizeVariant)
    // E (Ephebopus) reappears with a DIFFERENT sizeVariant but SAME pageUrl url-e
    //   → this is a size transition from run 0 → run 2 (gap=2 ≤ 3) → NOT a restock

    // A: Avicularia avicularia
    { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Avicularia avicularia', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 14, priceGbp: 24 },
    // C: Caribena versicolor — restock
    { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Caribena versicolor', sizeVariant: '1.5', pageUrl: 'url-c', wishlistCount: 32, priceGbp: 32 },
    // D: Dolichothele — variant 1
    { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '1.0', pageUrl: 'url-d', wishlistCount: 7, priceGbp: 10 },
    // D: Dolichothele — variant 2
    { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '2.0', pageUrl: 'url-d', wishlistCount: 7, priceGbp: 20 },
    // E: Ephebopus murinus — size transition (2.0 → 2.5, same pageUrl url-e)
    { scrapeDatetime: '2026-04-06T06:10:00', scientificName: 'Ephebopus murinus', sizeVariant: '2.5', pageUrl: 'url-e', wishlistCount: 16, priceGbp: 26 },

    // ── Run 3 — 2026-04-13T06:10:00 (referenceDate) ──────────────────────────

    // A: Avicularia avicularia
    { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Avicularia avicularia', sizeVariant: '2.0', pageUrl: 'url-a', wishlistCount: 16, priceGbp: 26 },
    // C: Caribena versicolor
    { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Caribena versicolor', sizeVariant: '1.5', pageUrl: 'url-c', wishlistCount: 34, priceGbp: 34 },
    // D: Dolichothele — variant 1
    { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '1.0', pageUrl: 'url-d', wishlistCount: 8, priceGbp: 10 },
    // D: Dolichothele — variant 2
    { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Dolichothele diamantinensis', sizeVariant: '2.0', pageUrl: 'url-d', wishlistCount: 8, priceGbp: 20 },
    // E: Ephebopus murinus — size 2.5 (same as run 2)
    { scrapeDatetime: '2026-04-13T06:10:00', scientificName: 'Ephebopus murinus', sizeVariant: '2.5', pageUrl: 'url-e', wishlistCount: 18, priceGbp: 28 },
  ],
};
