import { render } from '@testing-library/svelte';
import SparklineBar from './SparklineBar.svelte';
import type { SparklineDto, SparklineBarData } from '../types.js';

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeBar(overrides: Partial<SparklineBarData> = {}): SparklineBarData {
  return {
    bar_height: 14,
    fill: '#22c55e',
    opacity: 0.85,
    tooltip: '£15.00',
    ...overrides,
  };
}

function makeDto(overrides: Partial<SparklineDto> = {}): SparklineDto {
  return {
    bars: [makeBar(), makeBar({ bar_height: 20, opacity: 1.0 })],
    svg_width: 20,
    svg_height: 20,
    title: 'Price History',
    ...overrides,
  };
}

// ── SVG structure ─────────────────────────────────────────────────────────────

test('renders <svg> with width, height, viewBox from DTO', () => {
  const dto = makeDto({ svg_width: 30, svg_height: 20 });
  const { container } = render(SparklineBar, { dto });

  const svg = container.querySelector('svg');
  expect(svg).not.toBeNull();
  expect(svg).toHaveAttribute('width', '30');
  expect(svg).toHaveAttribute('height', '20');
  expect(svg).toHaveAttribute('viewBox', '0 0 30 20');
});

test('renders outer <title> inside <svg> with dto.title value', () => {
  const dto = makeDto({ title: 'Wishlist History' });
  const { container } = render(SparklineBar, { dto });

  const svg = container.querySelector('svg');
  expect(svg).not.toBeNull();
  // The outer title is a direct child of <svg>
  const titles = svg!.querySelectorAll(':scope > title');
  expect(titles).toHaveLength(1);
  expect(titles[0].textContent).toBe('Wishlist History');
});

test('renders correct number of <rect> elements — null gap bars excluded', () => {
  const dto = makeDto({
    bars: [makeBar(), null, makeBar()],
    svg_width: 30,
  });
  const { container } = render(SparklineBar, { dto });

  const rects = container.querySelectorAll('rect');
  expect(rects).toHaveLength(2);
});

test('each <rect> has fill attribute matching bar.fill', () => {
  const dto = makeDto({
    bars: [makeBar({ fill: '#ef4444' }), makeBar({ fill: '#3b82f6' })],
    svg_width: 20,
  });
  const { container } = render(SparklineBar, { dto });

  const rects = container.querySelectorAll('rect');
  expect(rects[0]).toHaveAttribute('fill', '#ef4444');
  expect(rects[1]).toHaveAttribute('fill', '#3b82f6');
});

test('each <rect> has opacity attribute matching bar.opacity', () => {
  const dto = makeDto({
    bars: [makeBar({ opacity: 0.7 }), makeBar({ opacity: 1.0 })],
    svg_width: 20,
  });
  const { container } = render(SparklineBar, { dto });

  const rects = container.querySelectorAll('rect');
  expect(rects[0]).toHaveAttribute('opacity', '0.7');
  expect(rects[1]).toHaveAttribute('opacity', '1');
});

test('each <rect> has a child <title> with bar.tooltip string', () => {
  const dto = makeDto({
    bars: [makeBar({ tooltip: '£10.00' }), makeBar({ tooltip: '£20.00' })],
    svg_width: 20,
  });
  const { container } = render(SparklineBar, { dto });

  const rects = container.querySelectorAll('rect');
  expect(rects[0].querySelector('title')?.textContent).toBe('£10.00');
  expect(rects[1].querySelector('title')?.textContent).toBe('£20.00');
});

// ── Gap x-positioning ─────────────────────────────────────────────────────────

test('null gap at index 1 — second rect has x="20", not x="10"', () => {
  // bars: [bar(i=0), null(i=1), bar(i=2)] → x values are 0, -, 20
  const dto = makeDto({
    bars: [makeBar(), null, makeBar()],
    svg_width: 30,
  });
  const { container } = render(SparklineBar, { dto });

  const rects = container.querySelectorAll('rect');
  expect(rects[0]).toHaveAttribute('x', '0');
  expect(rects[1]).toHaveAttribute('x', '20');
});

// ── Single bar ────────────────────────────────────────────────────────────────

test('single-bar DTO — rect has height="20" and y="0"', () => {
  const dto: SparklineDto = {
    bars: [makeBar({ bar_height: 20 })],
    svg_width: 10,
    svg_height: 20,
    title: 'Stock History',
  };
  const { container } = render(SparklineBar, { dto });

  const rect = container.querySelector('rect');
  expect(rect).not.toBeNull();
  expect(rect).toHaveAttribute('height', '20');
  expect(rect).toHaveAttribute('y', '0');
});

// ── String fallback ───────────────────────────────────────────────────────────

test('dto is string "-" — no <svg> rendered, string "-" present in DOM', () => {
  const { container } = render(SparklineBar, { dto: '-' });

  expect(container.querySelector('svg')).toBeNull();
  expect(container.textContent).toContain('-');
});

test('dto is unicode string "▁▂▃" — no <svg> rendered, string present in DOM', () => {
  const { container } = render(SparklineBar, { dto: '▁▂▃' });

  expect(container.querySelector('svg')).toBeNull();
  expect(container.textContent).toContain('▁▂▃');
});
