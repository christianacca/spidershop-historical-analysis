import { describe, expect, test } from 'vitest';
import { collectAllDates } from './history-utils.js';

describe('collectAllDates', () => {
  test('returns empty array when dateColumn is undefined', () => {
    const rows = [{ date: '2026-01-15' }];
    expect(collectAllDates(rows, undefined)).toEqual([]);
  });

  test('returns empty array when rows is empty', () => {
    expect(collectAllDates([], 'date')).toEqual([]);
  });

  test('single date: returns that date in a one-element array', () => {
    const rows = [{ date: '2026-01-15' }, { date: '2026-01-15' }];
    expect(collectAllDates(rows, 'date')).toEqual(['2026-01-15']);
  });

  test('returns dates in ascending order (oldest first)', () => {
    const rows = [
      { date: '2026-01-22' },
      { date: '2026-01-15' },
      { date: '2026-01-08' },
    ];
    expect(collectAllDates(rows, 'date')).toEqual([
      '2026-01-08',
      '2026-01-15',
      '2026-01-22',
    ]);
  });

  test('deduplicates: each date appears once even if multiple rows share it', () => {
    const rows = [
      { date: '2026-01-15' },
      { date: '2026-01-15' },
      { date: '2026-01-08' },
      { date: '2026-01-08' },
    ];
    expect(collectAllDates(rows, 'date')).toEqual(['2026-01-08', '2026-01-15']);
  });

  test('skips rows where the date value is an empty string', () => {
    const rows = [{ date: '' }, { date: '2026-01-15' }];
    expect(collectAllDates(rows, 'date')).toEqual(['2026-01-15']);
  });

  test('skips rows where the date key is missing (undefined coerces to empty string)', () => {
    const rows = [{ other: 'x' }, { date: '2026-01-15' }];
    expect(collectAllDates(rows, 'date')).toEqual(['2026-01-15']);
  });

  test('uses the provided dateColumn key, not a hardcoded one', () => {
    const rows = [
      { scraped_at: '2026-02-01' },
      { scraped_at: '2026-01-15' },
    ];
    expect(collectAllDates(rows, 'scraped_at')).toEqual([
      '2026-01-15',
      '2026-02-01',
    ]);
  });
});
