import { describe, it, expect } from 'vitest';
import { escapeCsvRow } from './csv-utils.js';

describe('escapeCsvRow', () => {
  it('returns empty string for an empty array', () => {
    expect(escapeCsvRow([])).toBe('');
  });

  it('returns a plain value unchanged when no special characters present', () => {
    expect(escapeCsvRow(['hello'])).toBe('hello');
  });

  it('joins multiple plain values with commas', () => {
    expect(escapeCsvRow(['a', 'b', 'c'])).toBe('a,b,c');
  });

  it('wraps a value containing a comma in double-quotes', () => {
    expect(escapeCsvRow(['hello, world'])).toBe('"hello, world"');
  });

  it('wraps a value containing a double-quote in double-quotes and escapes the inner quote', () => {
    expect(escapeCsvRow(['say "hi"'])).toBe('"say ""hi"""');
  });

  it('wraps a value containing a newline in double-quotes', () => {
    expect(escapeCsvRow(['line1\nline2'])).toBe('"line1\nline2"');
  });

  it('wraps a value containing a carriage return in double-quotes', () => {
    expect(escapeCsvRow(['line1\rline2'])).toBe('"line1\rline2"');
  });

  it('handles a row combining all edge cases', () => {
    const result = escapeCsvRow(['plain', 'has, comma', 'has "quotes"', 'has\nnewline']);
    expect(result).toBe('plain,"has, comma","has ""quotes""","has\nnewline"');
  });
});
