import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import FilterButton from './FilterButton.svelte';

test('renders a button with the correct label text', () => {
  const { getByRole } = render(FilterButton, {
    label: 'Hot 🔥',
    value: '🔥',
    active: false,
    onclick: vi.fn(),
  });

  expect(getByRole('button')).toHaveTextContent('Hot 🔥');
});

test('active: true — button has .is-active class', () => {
  const { getByRole } = render(FilterButton, {
    label: 'Hot',
    value: '🔥',
    active: true,
    onclick: vi.fn(),
  });

  expect(getByRole('button')).toHaveClass('is-active');
});

test('active: false — .is-active class is absent', () => {
  const { getByRole } = render(FilterButton, {
    label: 'Hot',
    value: '🔥',
    active: false,
    onclick: vi.fn(),
  });

  expect(getByRole('button')).not.toHaveClass('is-active');
});

test('clicking the button triggers the onclick callback', async () => {
  const onclick = vi.fn();
  const { getByRole } = render(FilterButton, {
    label: 'Hot',
    value: '🔥',
    active: false,
    onclick,
  });

  await fireEvent.click(getByRole('button'));

  expect(onclick).toHaveBeenCalled();
});
