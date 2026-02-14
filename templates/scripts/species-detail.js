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

const DEFAULT_RUN_WINDOW = 26;

/**
 * Initialize tab switching behavior
 */
function initTabSwitching() {
  document.querySelectorAll('[role="tab"]').forEach(tab => {
  tab.addEventListener('click', (e) => {
    const view = e.target.dataset.view;
    
    // Update tabs
    document.querySelectorAll('[role="tab"]').forEach(t => {
      t.setAttribute('aria-selected', 'false');
    });
    e.target.setAttribute('aria-selected', 'true');
    
    // Update panels
    document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
      panel.style.display = 'none';
    });
    document.getElementById(`panel-${view}`).style.display = 'block';
    
    // Update hint text
    const hint = document.getElementById('view-hint');
    hint.textContent = view === 'breeder'
      ? 'Breeder view: focuses on opportunity signals and scarcity.'
      : 'Dealer view: focuses on supply risk, reliability, and restock speed.';

    // Highlight the correct origin button
    const backBreeder = document.getElementById('back-breeder');
    const backDealer = document.getElementById('back-dealer');
    if (backBreeder && backDealer) {
      backBreeder.classList.toggle('origin-btn', view === 'breeder');
      backDealer.classList.toggle('origin-btn', view === 'dealer');
    }
    
    // Update URL
    const url = new URL(window.location);
    url.searchParams.set('view', view);
    window.history.pushState({}, '', url);
  });
});
}

/**
 * Initialize view from URL parameter on page load
 */
function initViewFromURL() {
  const urlParams = new URLSearchParams(window.location.search);
const viewParam = urlParams.get('view');
if (viewParam && (viewParam === 'breeder' || viewParam === 'dealer')) {
  const tab = document.querySelector(`[data-view="${viewParam}"]`);
  if (tab) tab.click();
}
}

/**
 * Render a line chart with gap support for missing data
 * 
 * @param {Object} config - Chart configuration
 * @param {string} config.containerId - ID of container element
 * @param {Array} config.series - Array of numeric values (null for gaps)
 * @param {string} config.stroke - SVG stroke color
 * @param {number} config.yMin - Y-axis minimum value
 * @param {number} config.yMax - Y-axis maximum value
 * @param {string} config.yLabelTop - Label for top Y-axis
 * @param {string} config.yLabelMid - Label for middle Y-axis
 * @param {string} config.yLabelLow - Label for lower-mid Y-axis
 * @param {string} config.yLabelBottom - Label for bottom Y-axis
 * @param {Function} config.formatValue - Function to format values for tooltips
 */
function renderLineChart({ containerId, series, stroke, yMin, yMax, yLabelTop, yLabelMid, yLabelLow, yLabelBottom, formatValue }) {
  const container = document.getElementById(containerId);
const width = 640;
const height = 180;
const left = 40;
const right = 620;
const top = 20;
const bottom = 150;

const n = series.length;
const dx = n > 1 ? (right - left) / (n - 1) : 0;

const fmt = formatValue || ((v) => String(v));

const points = [];
const circles = [];
for (let i = 0; i < n; i++) {
  const x = left + i * dx;
  const v = series[i];
  if (v == null) {
    points.push(null);
    continue;
  }
  const t = (v - yMin) / (yMax - yMin);
  const y = bottom - t * (bottom - top);
  points.push([x, Math.max(top, Math.min(bottom, y))]);
}

// Build polyline with gaps
const segments = [];
let current = [];
for (const p of points) {
  if (!p) {
    if (current.length >= 2) segments.push(current);
    current = [];
    continue;
  }
  current.push(p);
}
if (current.length >= 2) segments.push(current);

for (let i = 0; i < points.length; i++) {
  const p = points[i];
  if (!p) continue;
  const v = series[i];
  const title = `Run ${i + 1} — ${fmt(v)}`;
  circles.push(`<circle cx="${p[0].toFixed(2)}" cy="${p[1].toFixed(2)}" r="3.6"><title>${title}</title></circle>`);
}

const poly = segments.map(seg => {
  const pts = seg.map(p => `${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ');
  return `<polyline fill="none" stroke="${stroke}" stroke-width="3" points="${pts}" />`;
}).join('');

container.innerHTML = `
  <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" role="img">
    <rect x="0" y="0" width="${width}" height="${height}" fill="#fafafa" />
    <g stroke="#e5e7eb" stroke-width="1">
      <line x1="${left}" y1="${top}" x2="${left}" y2="${bottom}" />
      <line x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}" />
      <line x1="${left}" y1="110" x2="${right}" y2="110" />
      <line x1="${left}" y1="70" x2="${right}" y2="70" />
      <line x1="${left}" y1="30" x2="${right}" y2="30" />
    </g>
    ${poly}
    <g fill="${stroke}">${circles.join('')}</g>
    <g fill="#607080" font-size="12" font-family="inherit">
      <text x="${left}" y="168">old</text>
      <text x="${right}" y="168" text-anchor="end">recent</text>
      <text x="10" y="34">${yLabelTop}</text>
      <text x="10" y="74">${yLabelMid}</text>
      <text x="10" y="114">${yLabelLow}</text>
      <text x="10" y="154">${yLabelBottom}</text>
    </g>
  </svg>
`;
}

/**
 * Render stock observation timeline strip
 * Shows observed (green) vs not-observed (gray) runs
 */
function renderStockStrip(chartData) {
  const container = document.getElementById('stock-strip');
const width = 640;
const height = 34;
const left = 40;
const right = 620;

const observed = chartData.runs.map(r => r.observed);
const n = observed.length;
const available = right - left;
const gap = 4;
const blockWidth = Math.max(10, Math.floor((available - gap * (n - 1)) / n));
const extra = available - (blockWidth * n + gap * (n - 1));
const startX = left + Math.floor(extra / 2);

let x = startX;
const rects = [];
for (let i = 0; i < n; i++) {
  const obs = observed[i];
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
function renderCharts() {
// Check if chart data is available
if (!window.speciesChartData || !window.speciesChartData.runs || window.speciesChartData.runs.length === 0) {
  return;
}

const chartData = window.speciesChartData;

// Extract price and wishlist arrays from chart_data
const prices = chartData.runs.map(r => r.observed ? parseFloat(r.price) : null);
const wishlists = chartData.runs.map(r => r.observed ? parseInt(r.wishlist) : null);

// Calculate min/max for price chart
const validPrices = prices.filter(p => p !== null);
const priceMin = validPrices.length ? Math.floor(Math.min(...validPrices) / 5) * 5 : 0;
const priceMax = validPrices.length ? Math.ceil(Math.max(...validPrices) / 5) * 5 + 5 : 50;
const priceMid = Math.round((priceMin + priceMax) / 2);

// Calculate min/max for wishlist chart
const validWishlists = wishlists.filter(w => w !== null);
const wishlistMin = validWishlists.length ? Math.floor(Math.min(...validWishlists) / 10) * 10 : 0;
const wishlistMax = validWishlists.length ? Math.ceil(Math.max(...validWishlists) / 10) * 10 + 10 : 100;
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
function init() {
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
