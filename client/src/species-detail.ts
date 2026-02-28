/**
 * Species Detail Page Interactions
 * 
 * Handles:
 * - Tab switching between Breeder and Dealer views
 * - URL parameter initialization and updates
 * - Back button highlighting sync
 * - Price and wishlist trend chart rendering
 * - Stock observation timeline strip
 * 
 * Data dependency: Expects window.speciesChartData to be set by Jinja template
 */

import { CHART } from './constants.js';
import { getElement } from './utils.js';

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

/**
 * Initialize tab switching behavior
 */
function initTabSwitching(): void {
  document.querySelectorAll('[role="tab"]').forEach(tab => {
    tab.addEventListener('click', (e) => {
      const view = (e.target as HTMLElement).dataset.view;

      // Update tabs
      document.querySelectorAll('[role="tab"]').forEach(t => {
        t.setAttribute('aria-selected', 'false');
      });
      (e.target as HTMLElement).setAttribute('aria-selected', 'true');

      // Update panels
      document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
        (panel as HTMLElement).style.display = 'none';
      });
      document.getElementById(`panel-${view}`)!.style.display = 'block';

      // Update hint text
      const hint = document.getElementById('view-hint');
      if (hint) {
        hint.textContent = view === 'breeder'
          ? 'Breeder view: focuses on opportunity signals and scarcity.'
          : 'Dealer view: focuses on supply risk, reliability, and restock speed.';
      }

      // Highlight the correct origin button
      const backBreeder = document.getElementById('back-breeder');
      const backDealer = document.getElementById('back-dealer');
      if (backBreeder && backDealer) {
        backBreeder.classList.toggle('origin-btn', view === 'breeder');
        backDealer.classList.toggle('origin-btn', view === 'dealer');
      }

      // Update URL
      const url = new URL(window.location.href);
      url.searchParams.set('view', view ?? '');
      window.history.pushState({}, '', url);
    });
  });
}

/**
 * Initialize view from URL parameter on page load
 */
function initViewFromURL(): void {
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view');
  if (viewParam && (viewParam === 'breeder' || viewParam === 'dealer')) {
    const tab = document.querySelector(`[data-view="${viewParam}"]`);
    if (tab) (tab as HTMLElement).click();
  }
}

/**
 * Calculate chart layout dimensions
 */
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

/**
 * Map data points to SVG coordinates
 */
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

/**
 * Build polyline segments from points, splitting on gaps
 */
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

/**
 * Create circle SVG elements with tooltips
 */
function createCircleElements(points: (Point | null)[], formatValue: (v: number) => string): string {
  return points
    .filter((p): p is Point => p !== null)
    .map(([x, y, value, run]) => {
      const title = `Run ${run} — ${formatValue(value)}`;
      return `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${CHART.CIRCLE_RADIUS}"><title>${title}</title></circle>`;
    })
    .join('');
}

/**
 * Create polyline SVG elements for continuous segments
 */
function createPolylines(segments: [number, number][][], stroke: string): string {
  return segments
    .map(seg => {
      const pts = seg.map(p => `${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ');
      return `<polyline fill="none" stroke="${stroke}" stroke-width="${CHART.STROKE_WIDTH}" points="${pts}" />`;
    })
    .join('');
}

/**
 * Render a line chart with gap support for missing data
 */
function renderLineChart({ containerId, series, stroke, yMin, yMax, yLabelTop, yLabelMid, yLabelLow, yLabelBottom, formatValue }: LineChartConfig): void {
  const container = getElement(containerId);
  if (!container || !series.length) {
    if (container) container.innerHTML = '<p>No data available</p>';
    return;
  }

  try {
    const layout = calculateLayout();
    const fmt = formatValue ?? ((v: number) => String(v));

    // Transform data to coordinates
    const points = mapPointsToCoordinates(series, yMin, yMax, layout);

    // Build continuous segments
    const segments = buildPolylineSegments(points);

    // Create SVG elements
    const polylines = createPolylines(segments, stroke);
    const circles = createCircleElements(points, fmt);

    // Assemble final SVG
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

/**
 * Render stock observation timeline strip
 * Shows observed (green) vs not-observed (gray) runs
 */
function renderStockStrip(chartData: SpeciesChartData): void {
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

/**
 * Render all charts using data from window.speciesChartData
 */
function renderCharts(): void {
  // Check if chart data is available
  if (!window.speciesChartData || !window.speciesChartData.runs || window.speciesChartData.runs.length === 0) {
    return;
  }

  const chartData = window.speciesChartData;

  // Extract price and wishlist arrays from chart_data
  const prices = chartData.runs.map(({ observed, price }) =>
    observed ? parseFloat(price) : null
  );
  const wishlists = chartData.runs.map(({ observed, wishlist }) =>
    observed ? parseInt(wishlist) : null
  );

  // Calculate min/max for price chart
  const validPrices = prices.filter((p): p is number => p !== null);
  const priceMin = validPrices.length ? Math.floor(Math.min(...validPrices) / CHART.PRICE_ROUNDING) * CHART.PRICE_ROUNDING : 0;
  const priceMax = validPrices.length ? Math.ceil(Math.max(...validPrices) / CHART.PRICE_ROUNDING) * CHART.PRICE_ROUNDING + CHART.PRICE_ROUNDING : 50;
  const priceMid = Math.round((priceMin + priceMax) / 2);

  // Calculate min/max for wishlist chart
  const validWishlists = wishlists.filter((w): w is number => w !== null);
  const wishlistMin = validWishlists.length ? Math.floor(Math.min(...validWishlists) / CHART.WISHLIST_ROUNDING) * CHART.WISHLIST_ROUNDING : 0;
  const wishlistMax = validWishlists.length ? Math.ceil(Math.max(...validWishlists) / CHART.WISHLIST_ROUNDING) * CHART.WISHLIST_ROUNDING + CHART.WISHLIST_ROUNDING : 100;
  const wishlistMid = Math.round((wishlistMin + wishlistMax) / 2);

  // Render price chart
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

  // Render wishlist chart
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

  // Render stock strip
  renderStockStrip(chartData);
}

/**
 * Initialize all species detail page functionality
 */
function init(): void {
  initTabSwitching();
  initViewFromURL();
  renderCharts();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
