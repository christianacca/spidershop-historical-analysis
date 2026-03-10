import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import SearchInput from './SearchInput.svelte';

test('renders an input with the placeholder prop as its placeholder attribute', () => {
  const { getByRole } = render(SearchInput, {
    placeholder: 'Search species…',
    tableId: 'breeder-table',
    oninput: vi.fn(),
  });

  const input = getByRole('textbox');
  expect(input).toHaveAttribute('placeholder', 'Search species…');
});

test('input has id="search-{tableId}" for external selector compatibility', () => {
  const { getByRole } = render(SearchInput, {
    placeholder: 'Search…',
    tableId: 'breeder-table',
    oninput: vi.fn(),
  });

  expect(getByRole('textbox')).toHaveAttribute('id', 'search-breeder-table');
});

test('triggers oninput callback with current value on native input event', async () => {
  const oninput = vi.fn();
  const { getByRole } = render(SearchInput, {
    placeholder: 'Search…',
    tableId: 'breeder-table',
    oninput,
  });

  const input = getByRole('textbox');
  await fireEvent.input(input, { target: { value: 'foo' } });

  expect(oninput).toHaveBeenCalledWith('foo');
});
