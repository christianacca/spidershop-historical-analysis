import { render, fireEvent } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import { vi } from 'vitest';
import ToggleButton from './ToggleButton.svelte';

// ── Snippet helpers ──────────────────────────────────────────────────────────

/** Snippet that renders fixed text regardless of expanded state. */
const staticChildren = createRawSnippet<[boolean]>(() => ({
  render: () => '<span>More Filters</span>',
}));

/** Snippet that varies text based on the expanded parameter. */
const dynamicChildren = createRawSnippet<[boolean]>((getExpanded) => ({
  render: () => `<span>${getExpanded() ? 'Hide' : 'Show'}</span>`,
}));

// ── Arrow ────────────────────────────────────────────────────────────────────

test('renders the arrow span with class toggle-btn__arrow', () => {
  const { container } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    children: staticChildren,
  });

  expect(container.querySelector('.toggle-btn__arrow')).toBeTruthy();
});

test('button does not have is-expanded class when expanded=false', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    children: staticChildren,
  });

  expect(getByRole('button')).not.toHaveClass('is-expanded');
});

test('button has is-expanded class when expanded=true', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: true,
    onToggle: vi.fn(),
    children: staticChildren,
  });

  expect(getByRole('button')).toHaveClass('is-expanded');
});

// ── Click handler ────────────────────────────────────────────────────────────

test('onToggle is called when button is clicked', async () => {
  const onToggle = vi.fn();
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle,
    children: staticChildren,
  });

  await fireEvent.click(getByRole('button'));

  expect(onToggle).toHaveBeenCalled();
});

// ── Children snippet ─────────────────────────────────────────────────────────

test('children snippet receives false when expanded=false', () => {
  const { getByText } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    children: dynamicChildren,
  });

  expect(getByText('Show')).toBeTruthy();
});

test('children snippet receives true when expanded=true', () => {
  const { getByText } = render(ToggleButton, {
    expanded: true,
    onToggle: vi.fn(),
    children: dynamicChildren,
  });

  expect(getByText('Hide')).toBeTruthy();
});

// ── Badge ────────────────────────────────────────────────────────────────────

test('badge is rendered and visible when badge > 0', () => {
  const { container } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    badge: 3,
    children: staticChildren,
  });

  const badge = container.querySelector('.toggle-btn__badge');
  expect(badge).toBeTruthy();
  expect(badge).not.toHaveClass('hidden');
  expect(badge).toHaveTextContent('3');
});

test('badge has hidden class when badge === 0', () => {
  const { container } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    badge: 0,
    children: staticChildren,
  });

  expect(container.querySelector('.toggle-btn__badge')).toHaveClass('hidden');
});

test('badge is absent from DOM when badge prop is omitted', () => {
  const { container } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    children: staticChildren,
  });

  expect(container.querySelector('.toggle-btn__badge')).toBeNull();
});

test('badgeId is forwarded to the badge element id', () => {
  const { container } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    badge: 2,
    badgeId: 'filterBadge-test',
    children: staticChildren,
  });

  expect(container.querySelector('#filterBadge-test')).toBeTruthy();
});

// ── Variant ──────────────────────────────────────────────────────────────────

test('variant=primary — button has toggle-btn--primary class', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    variant: 'primary',
    children: staticChildren,
  });

  expect(getByRole('button')).toHaveClass('toggle-btn--primary');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--muted');
});

test('variant=muted — button has toggle-btn--muted class', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    variant: 'muted',
    children: staticChildren,
  });

  expect(getByRole('button')).toHaveClass('toggle-btn--muted');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--primary');
});

test('variant=pill — button has toggle-btn--pill class', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    variant: 'pill',
    children: staticChildren,
  });

  expect(getByRole('button')).toHaveClass('toggle-btn--pill');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--primary');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--muted');
});

test('default variant — button has none of the variant modifier classes', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    children: staticChildren,
  });

  expect(getByRole('button')).not.toHaveClass('toggle-btn--primary');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--muted');
  expect(getByRole('button')).not.toHaveClass('toggle-btn--pill');
});

// ── Extra class / attribute forwarding ──────────────────────────────────────

test('extra class names from class prop appear on the button', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    class: 'advanced-filters-toggle',
    children: staticChildren,
  });

  expect(getByRole('button')).toHaveClass('advanced-filters-toggle');
});

test('data-* attributes forwarded via rest appear on the button', () => {
  const { getByRole } = render(ToggleButton, {
    expanded: false,
    onToggle: vi.fn(),
    'data-action': 'toggle-date-picker',
    'data-table-id': 'history-table',
    children: staticChildren,
  });

  const btn = getByRole('button');
  expect(btn).toHaveAttribute('data-action', 'toggle-date-picker');
  expect(btn).toHaveAttribute('data-table-id', 'history-table');
});
