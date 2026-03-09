import { describe, it, expect } from 'vitest';
import { assertPayload } from './payload-validation';

describe('assertPayload', () => {
  it('throws descriptive Error in dev mode when rows is not an array', () => {
    expect(() => assertPayload('breeder-table', 'not-an-array', true)).toThrowError(
      /breeder-tableData.*not an array/i
    );
  });

  it('throws descriptive Error in dev mode when rows is an empty array', () => {
    expect(() => assertPayload('breeder-table', [], true)).toThrowError(
      /breeder-tableData.*empty array/i
    );
  });

  it('is a no-op (no throw) in production mode', () => {
    // Neither non-array nor empty array should throw when isDev=false
    expect(() => assertPayload('breeder-table', 'not-an-array', false)).not.toThrow();
    expect(() => assertPayload('breeder-table', [], false)).not.toThrow();
  });

  it('passes through a valid non-empty array without throwing', () => {
    const rows = [{ Species: 'Brachypelma hamorii', Signal: '🔥' }];
    expect(() => assertPayload('breeder-table', rows, true)).not.toThrow();
  });

  it('default isDev param is true in Vitest — throws without explicit isDev argument', () => {
    // Confirms import.meta.env.DEV is true in the Vitest environment, so
    // entry-point calls of assertPayload(tableId, rows) behave as dev mode.
    expect(() => assertPayload('breeder-table', 'not-an-array')).toThrowError(
      /breeder-tableData.*not an array/i
    );
  });
});
