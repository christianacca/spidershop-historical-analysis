import { describe, it, expect } from 'vitest';
import { unicodeToSvg } from './sparklines.js';

describe('unicodeToSvg', () => {
  it('returns empty string unchanged', () => {
    expect(unicodeToSvg('')).toBe('');
  });

  it('returns "-" unchanged', () => {
    expect(unicodeToSvg('-')).toBe('-');
  });

  it('returns unrecognised character string unchanged', () => {
    expect(unicodeToSvg('hello world')).toBe('hello world');
  });

  it('single "█" returns an SVG string', () => {
    const result = unicodeToSvg('█');
    expect(result).toContain('<svg');
    expect(result).toContain('</svg>');
  });

  it('"▁▂▃▄▅▆▇█" SVG contains 8 bar elements', () => {
    const result = unicodeToSvg('▁▂▃▄▅▆▇█');
    expect(result).toContain('<svg');
    // Count <rect elements — one per bar
    const rectCount = (result.match(/<rect/g) ?? []).length;
    expect(rectCount).toBe(8);
  });

  it('tallest bar (█) is taller than shortest bar (▁)', () => {
    const svgMin = unicodeToSvg('▁');
    const svgMax = unicodeToSvg('█');

    // Extract height attribute from the single <rect> element in each SVG
    const heightOf = (svg: string): number => {
      const match = svg.match(/<rect[^>]+height="([^"]+)"/);
      return match ? parseFloat(match[1]) : 0;
    };

    expect(heightOf(svgMax)).toBeGreaterThan(heightOf(svgMin));
  });
});
