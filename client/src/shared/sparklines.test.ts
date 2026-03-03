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

  // ── G3: Trend-based colours ──────────────────────────────────────────────

  it('rising sparkline (▁▄▇) uses green fill (#22c55e)', () => {
    const result = unicodeToSvg('▁▄▇');
    expect(result).toContain('fill="#22c55e"');
    expect(result).not.toContain('fill="currentColor"');
  });

  it('falling sparkline (▇▄▁) uses red fill (#ef4444)', () => {
    const result = unicodeToSvg('▇▄▁');
    expect(result).toContain('fill="#ef4444"');
    expect(result).not.toContain('fill="currentColor"');
  });

  it('stable sparkline (▄▄▄) uses blue fill (#3b82f6)', () => {
    const result = unicodeToSvg('▄▄▄');
    expect(result).toContain('fill="#3b82f6"');
    expect(result).not.toContain('fill="currentColor"');
  });

  it('single bar sparkline uses blue fill (stable)', () => {
    const result = unicodeToSvg('▄');
    expect(result).toContain('fill="#3b82f6"');
  });

  it('all bars share the same fill colour (trend is overall, not per-bar)', () => {
    const result = unicodeToSvg('▁▄▇');
    const fills = [...result.matchAll(/fill="([^"]+)"/g)].map((m) => m[1]);
    const uniqueFills = new Set(fills);
    expect(uniqueFills.size).toBe(1);
  });
});
