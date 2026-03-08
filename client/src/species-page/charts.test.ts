import { describe, it, expect, beforeEach } from 'vitest';
import { renderLineChart, renderStockStrip, renderCharts } from './charts';

const BASE_LINE_CONFIG = {
  containerId: 'price-chart',
  series: [10, 20, 30] as (number | null)[],
  stroke: '#3498db',
  yMin: 0,
  yMax: 50,
  yLabelTop: '50',
  yLabelMid: '25',
  yLabelLow: '12',
  yLabelBottom: '0',
};

describe('renderLineChart', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('does not throw when container is missing', () => {
    expect(() => renderLineChart(BASE_LINE_CONFIG)).not.toThrow();
  });

  it('sets "No data available" when series is empty', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({ ...BASE_LINE_CONFIG, series: [] });
    expect(document.getElementById('price-chart')!.innerHTML).toBe('<p>No data available</p>');
  });

  it('renders an SVG element for valid series data', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart(BASE_LINE_CONFIG);
    expect(document.querySelector('#price-chart svg')).not.toBeNull();
  });

  it('renders one circle per non-null data point', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({ ...BASE_LINE_CONFIG, series: [10, null, 30] });
    expect(document.querySelectorAll('#price-chart circle')).toHaveLength(2);
  });

  it('uses formatValue in circle title tooltips', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({
      ...BASE_LINE_CONFIG,
      series: [12.5],
      formatValue: (v) => `£${v.toFixed(2)}`,
    });
    const title = document.querySelector('#price-chart circle title');
    expect(title?.textContent).toContain('£12.50');
  });

  it('defaults to String(v) when formatValue is omitted', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({ ...BASE_LINE_CONFIG, series: [42] });
    const title = document.querySelector('#price-chart circle title');
    expect(title?.textContent).toContain('42');
  });

  it('includes y-axis labels in the SVG', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart(BASE_LINE_CONFIG);
    const svg = document.querySelector('#price-chart svg')!;
    expect(svg.innerHTML).toContain('50'); // yLabelTop
    expect(svg.innerHTML).toContain('0');  // yLabelBottom
  });

  it('does not render a polyline for a single-point series', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({ ...BASE_LINE_CONFIG, series: [25] });
    expect(document.querySelectorAll('#price-chart polyline')).toHaveLength(0);
  });

  it('splits null gaps into separate polyline segments', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart({ ...BASE_LINE_CONFIG, series: [10, 20, null, 30, 40] });
    expect(document.querySelectorAll('#price-chart polyline')).toHaveLength(2);
  });

  it('applies the stroke colour to polylines', () => {
    document.body.innerHTML = '<div id="price-chart"></div>';
    renderLineChart(BASE_LINE_CONFIG);
    const polyline = document.querySelector('#price-chart polyline');
    expect(polyline?.getAttribute('stroke')).toBe('#3498db');
  });
});

describe('renderStockStrip', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('does not throw when container is missing', () => {
    expect(() =>
      renderStockStrip({ runs: [{ observed: true, price: '10', wishlist: '5' }] })
    ).not.toThrow();
  });

  it('renders one rect per run plus a background rect', () => {
    document.body.innerHTML = '<div id="stock-strip"></div>';
    renderStockStrip({
      runs: [
        { observed: true, price: '10', wishlist: '5' },
        { observed: false, price: '0', wishlist: '3' },
        { observed: true, price: '12', wishlist: '7' },
      ],
    });
    // 1 background rect + 3 data rects
    expect(document.querySelectorAll('#stock-strip rect')).toHaveLength(4);
  });

  it('fills observed runs green and gaps light grey', () => {
    document.body.innerHTML = '<div id="stock-strip"></div>';
    renderStockStrip({
      runs: [
        { observed: true, price: '10', wishlist: '5' },
        { observed: false, price: '0', wishlist: '3' },
      ],
    });
    const rects = [...document.querySelectorAll('#stock-strip rect')].slice(1); // skip background
    expect(rects[0].getAttribute('fill')).toBe('#dcfce7');
    expect(rects[1].getAttribute('fill')).toBe('#f1f5f9');
  });

  it('includes run number and observation status in tooltips', () => {
    document.body.innerHTML = '<div id="stock-strip"></div>';
    renderStockStrip({
      runs: [
        { observed: true, price: '10', wishlist: '5' },
        { observed: false, price: '0', wishlist: '3' },
      ],
    });
    const titles = document.querySelectorAll('#stock-strip title');
    expect(titles[0].textContent).toContain('Run 1');
    expect(titles[0].textContent).toContain('observed');
    expect(titles[1].textContent).toContain('Run 2');
    expect(titles[1].textContent).toContain('not observed');
  });
});

describe('renderCharts', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    delete window.speciesChartData;
  });

  it('does not throw when speciesChartData is not set', () => {
    expect(() => renderCharts()).not.toThrow();
  });

  it('does not throw when runs array is empty', () => {
    window.speciesChartData = { runs: [] };
    expect(() => renderCharts()).not.toThrow();
  });

  it('renders all three charts when data is present', () => {
    document.body.innerHTML = `
      <div id="price-chart"></div>
      <div id="wishlist-chart"></div>
      <div id="stock-strip"></div>
    `;
    window.speciesChartData = {
      runs: [
        { observed: true, price: '12.50', wishlist: '10' },
        { observed: false, price: '0', wishlist: '0' },
        { observed: true, price: '15.00', wishlist: '12' },
      ],
    };
    renderCharts();
    expect(document.querySelector('#price-chart svg')).not.toBeNull();
    expect(document.querySelector('#wishlist-chart svg')).not.toBeNull();
    expect(document.querySelector('#stock-strip svg')).not.toBeNull();
  });

  it('plots only observed runs as price data points', () => {
    document.body.innerHTML = `
      <div id="price-chart"></div>
      <div id="wishlist-chart"></div>
      <div id="stock-strip"></div>
    `;
    window.speciesChartData = {
      runs: [
        { observed: true, price: '12.50', wishlist: '10' },
        { observed: false, price: '0', wishlist: '0' },
      ],
    };
    renderCharts();
    // 1 observed run → 1 circle in price chart
    expect(document.querySelectorAll('#price-chart circle')).toHaveLength(1);
  });
});
