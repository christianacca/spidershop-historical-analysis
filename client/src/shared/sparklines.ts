/**
 * Sparkline rendering — Unicode block chars → inline SVG bar charts.
 *
 * The Python side stores sparklines as 8-level Unicode block characters
 * (▁▂▃▄▅▆▇█). This module converts those strings to proportional SVG
 * bar charts for client-side rendering, avoiding the need to ship large
 * pre-rendered SVG strings in the page's JSON payload.
 */

/** Maps each sparkline block character to its relative height level (1–8). */
const SPARKLINE_LEVELS: Record<string, number> = {
  '▁': 1,
  '▂': 2,
  '▃': 3,
  '▄': 4,
  '▅': 5,
  '▆': 6,
  '▇': 7,
  '█': 8,
};

const MAX_LEVEL = 8;
const BAR_WIDTH = 4;
const BAR_GAP = 1;
const SVG_HEIGHT = 20;
const SVG_PADDING_TOP = 2;  // small gap at top so full-height bars don't clip

/**
 * Derive a trend-based fill colour from bar height levels.
 *
 * Mirrors the colour logic in `src/website/sparkline_conversion.py`:
 * - Rising  (last > first + 1): green  (#22c55e)
 * - Falling (last < first - 1): red    (#ef4444)
 * - Stable / single bar:        blue   (#3b82f6)
 */
function sparklineFillColor(levels: number[]): string {
  if (levels.length < 2) return '#3b82f6';
  const first = levels[0];
  const last = levels[levels.length - 1];
  if (last > first + 1) return '#22c55e';
  if (last < first - 1) return '#ef4444';
  return '#3b82f6';
}

/**
 * Convert a Unicode sparkline string to an inline SVG bar chart.
 *
 * Returns the input unchanged when:
 * - The string is empty or `"-"`
 * - None of the characters are recognised sparkline block characters
 *
 * @param sparkline - Unicode sparkline string (e.g. `"▁▂▃▄▅▆▇█"`)
 * @returns SVG markup string, or the original string if not a sparkline
 */
export function unicodeToSvg(sparkline: string): string {
  if (!sparkline || sparkline === '-') {
    return sparkline;
  }

  const levels = [...sparkline].map(ch => SPARKLINE_LEVELS[ch] ?? null);
  const validLevels = levels.filter((l): l is number => l !== null);

  if (validLevels.length === 0) {
    // No recognised sparkline characters — return unchanged
    return sparkline;
  }

  const totalWidth = validLevels.length * (BAR_WIDTH + BAR_GAP) - BAR_GAP;
  const usableHeight = SVG_HEIGHT - SVG_PADDING_TOP;
  const color = sparklineFillColor(validLevels);

  const rects = validLevels
    .map((level, i) => {
      const x = i * (BAR_WIDTH + BAR_GAP);
      const barHeight = Math.round((level / MAX_LEVEL) * usableHeight);
      const y = SVG_HEIGHT - barHeight;
      return `<rect x="${x}" y="${y}" width="${BAR_WIDTH}" height="${barHeight}" fill="${color}"/>`;
    })
    .join('');

  return (
    `<svg xmlns="http://www.w3.org/2000/svg" ` +
    `width="${totalWidth}" height="${SVG_HEIGHT}" ` +
    `viewBox="0 0 ${totalWidth} ${SVG_HEIGHT}" ` +
    `aria-hidden="true" class="sparkline">` +
    rects +
    `</svg>`
  );
}
