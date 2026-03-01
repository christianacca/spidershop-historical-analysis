/**
 * Species Detail Page — Chart Rendering
 *
 * Price and wishlist trend charts, and the stock observation timeline strip.
 * Data source: window.speciesChartData set by the Jinja2 template.
 */

import { CHART } from '../shared/constants.js';
import { getElement } from '../shared/dom-utils.js';

type Point = [number, number, number, number]; // [x, y, value, run]

interface ChartLayout {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
}

interface LineChartConfig {
  containerId: string;
  series: (number | null)[];
  stroke: string;
  yMin: number;
  yMax: number;
  yLabelTop: string;
  yLabelMid: string;
  yLabelLow: string;
  yLabelBottom: string;
  formatValue?: (value: number) => string;
}

function calculateLayout(): ChartLayout {
  return {
    width: CHART.WIDTH,
    height: CHART.HEIGHT,
    left: CHART.MARGINS.left,
    right: CHART.MARGINS.right,
    top: CHART.MARGINS.top,
    bottom: CHART.MARGINS.bottom
  };
}

function mapPointsToCoordinates(
  series: (number | null)[],
  yMin: number,
  yMax: number,
  layout: ChartLayout
): (Point | null)[] {
  const n = series.length;
  const dx = n > 1 ? (layout.right - layout.left) / (n - 1) : 0;

  return series.map((v, i) => {
    const x = layout.left + i * dx;
    if (v == null) return null;

    const t = (v - yMin) / (yMax - yMin);
    const y = layout.bottom - t * (layout.bottom - layout.top);
    return [x, Math.max(layout.top, Math.min(layout.bottom, y)), v, i + 1] as Point;
  });
}

function buildPolylineSegments(points: (Point | null)[]): [number, number][][] {
  const segments: [number, number][][] = [];
  let current: [number, number][] = [];

  for (const p of points) {
    if (!p) {
      if (current.length >= 2) segments.push(current);
      current = [];
      continue;
    }
    current.push([p[0], p[1]]);
  }

  if (current.length >= 2) segments.push(current);
  return segments;
}

function createCircleElements(points: (Point | null)[], formatValue: (v: number) => string): string {
  return points
    .filter((p): p is Point => p !== null)
    .map(([x, y, value, run]) => {
      const title = `Run ${run} — ${formatValue(value)}`;
      return `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${CHART.CIRCLE_RADIUS}"><title>${title}</title></circle>`;
    })
    .join('');
}

function createPolylines(segments: [number, number][][], stroke: string): string {
  return segments
    .map(seg => {
      const pts = seg.map(p => `${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ');
      return `<polyline fill="none" stroke="${stroke}" stroke-width="${CHART.STROKE_WIDTH}" points="${pts}" />`;
    })
    .join('');
}

export function renderLineChart({
  containerId, series, stroke, yMin, yMax,
  yLabelTop, yLabelMid, yLabelLow, yLabelBottom, formatValue
}: LineChartConfig): void {
  const container = getElement(containerId);
  if (!container || !series.length) {
    if (container) container.innerHTML = '<p>No data available</p>';
    return;
  }

  try {
    const layout = calculateLayout();
    const fmt = formatValue ?? ((v: number) => String(v));

    const points = mapPointsToCoordinates(series, yMin, yMax, layout);
    const segments = buildPolylineSegments(points);
    const polylines = createPolylines(segments, stroke);
    const circles = createCircleElements(points, fmt);

    container.innerHTML = `
      <svg width="100%" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}" role="img">
        <rect x="0" y="0" width="${layout.width}" height="${layout.height}" fill="#fafafa" />
        <g stroke="#e5e7eb" stroke-width="1">
          <line x1="${layout.left}" y1="${layout.top}" x2="${layout.left}" y2="${layout.bottom}" />
          <line x1="${layout.left}" y1="${layout.bottom}" x2="${layout.right}" y2="${layout.bottom}" />
          <line x1="${layout.left}" y1="110" x2="${layout.right}" y2="110" />
          <line x1="${layout.left}" y1="70" x2="${layout.right}" y2="70" />
          <line x1="${layout.left}" y1="30" x2="${layout.right}" y2="30" />
        </g>
        ${polylines}
        <g fill="${stroke}">${circles}</g>
        <g fill="#607080" font-size="12" font-family="inherit">
          <text x="${layout.left}" y="168">old</text>
          <text x="${layout.right}" y="168" text-anchor="end">recent</text>
          <text x="10" y="34">${yLabelTop}</text>
          <text x="10" y="74">${yLabelMid}</text>
          <text x="10" y="114">${yLabelLow}</text>
          <text x="10" y="154">${yLabelBottom}</text>
        </g>
      </svg>
    `;
  } catch (error) {
    console.error('Chart rendering failed:', error);
    container.innerHTML = '<p>Failed to render chart</p>';
  }
}

export function renderStockStrip(chartData: SpeciesChartData): void {
  const container = getElement('stock-strip');
  if (!container) return;

  const width = CHART.WIDTH;
  const height = 34;
  const left = CHART.MARGINS.left;
  const right = CHART.MARGINS.right;

  const observed = chartData.runs.map(r => r.observed);
  const n = observed.length;
  const available = right - left;
  const gap = 4;
  const blockWidth = Math.max(10, Math.floor((available - gap * (n - 1)) / n));
  const extra = available - (blockWidth * n + gap * (n - 1));
  const startX = left + Math.floor(extra / 2);

  let x = startX;
  const rects: string[] = [];
  for (const [i, obs] of observed.entries()) {
    const fill = obs ? '#dcfce7' : '#f1f5f9';
    const stroke = obs ? '#16a34a' : '#94a3b8';
    const label = obs ? 'observed' : 'not observed (gap)';
    const title = `Run ${i + 1} — ${label}`;
    rects.push(`<rect x="${x}" y="9" width="${blockWidth}" height="14" fill="${fill}" stroke="${stroke}"><title>${title}</title></rect>`);
    x += blockWidth + gap;
  }

  container.innerHTML = `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Stock timeline barcode">
      <rect x="0" y="0" width="${width}" height="${height}" fill="#ffffff" />
      <line x1="${left}" y1="28" x2="${right}" y2="28" stroke="#e5e7eb" stroke-width="1" />
      <g>${rects.join('')}</g>
    </svg>
  `;
}

export function renderCharts(): void {
  if (!window.speciesChartData || !window.speciesChartData.runs || window.speciesChartData.runs.length === 0) {
    return;
  }

  const chartData = window.speciesChartData;

  const prices = chartData.runs.map(({ observed, price }) =>
    observed ? parseFloat(price) : null
  );
  const wishlists = chartData.runs.map(({ observed, wishlist }) =>
    observed ? parseInt(wishlist) : null
  );

  const validPrices = prices.filter((p): p is number => p !== null);
  const priceMin = validPrices.length ? Math.floor(Math.min(...validPrices) / CHART.PRICE_ROUNDING) * CHART.PRICE_ROUNDING : 0;
  const priceMax = validPrices.length ? Math.ceil(Math.max(...validPrices) / CHART.PRICE_ROUNDING) * CHART.PRICE_ROUNDING + CHART.PRICE_ROUNDING : 50;
  const priceMid = Math.round((priceMin + priceMax) / 2);

  const validWishlists = wishlists.filter((w): w is number => w !== null);
  const wishlistMin = validWishlists.length ? Math.floor(Math.min(...validWishlists) / CHART.WISHLIST_ROUNDING) * CHART.WISHLIST_ROUNDING : 0;
  const wishlistMax = validWishlists.length ? Math.ceil(Math.max(...validWishlists) / CHART.WISHLIST_ROUNDING) * CHART.WISHLIST_ROUNDING + CHART.WISHLIST_ROUNDING : 100;
  const wishlistMid = Math.round((wishlistMin + wishlistMax) / 2);

  renderLineChart({
    containerId: 'price-chart',
    series: prices,
    stroke: '#3498db',
    formatValue: (v) => `£${Number(v).toFixed(2)}`,
    yMin: priceMin,
    yMax: priceMax,
    yLabelTop: `£${priceMax}`,
    yLabelMid: `£${priceMid}`,
    yLabelLow: `£${Math.round((priceMin + priceMid) / 2)}`,
    yLabelBottom: `£${priceMin}`
  });

  renderLineChart({
    containerId: 'wishlist-chart',
    series: wishlists,
    stroke: '#16a34a',
    formatValue: (v) => `${Number(v)}`,
    yMin: wishlistMin,
    yMax: wishlistMax,
    yLabelTop: `${wishlistMax}`,
    yLabelMid: `${wishlistMid}`,
    yLabelLow: `${Math.round((wishlistMin + wishlistMid) / 2)}`,
    yLabelBottom: `${wishlistMin}`
  });

  renderStockStrip(chartData);
}
