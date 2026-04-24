import { writable } from 'svelte/store';
import { render, fireEvent } from '@testing-library/svelte';
import SwUpdateToast from './SwUpdateToast.svelte';

const mockUpdateServiceWorker = vi.fn();
const mockNeedRefresh = writable(false);

vi.mock('virtual:pwa-register/svelte', () => ({
  useRegisterSW: vi.fn(() => ({
    needRefresh: mockNeedRefresh,
    updateServiceWorker: mockUpdateServiceWorker,
  })),
}));

beforeEach(() => {
  mockNeedRefresh.set(false);
  mockUpdateServiceWorker.mockClear();
});

describe('SwUpdateToast', () => {
  it('is not rendered when needRefresh is false', () => {
    const { queryByRole } = render(SwUpdateToast);
    expect(queryByRole('status')).toBeNull();
  });

  it('renders the update message when needRefresh is true', async () => {
    const { getByRole } = render(SwUpdateToast);
    mockNeedRefresh.set(true);
    // Allow Svelte to flush the reactive update
    await Promise.resolve();
    expect(getByRole('status')).toHaveTextContent('New data has been deployed.');
  });

  it('calls updateServiceWorker(true) when Refresh is clicked', async () => {
    const { getByText } = render(SwUpdateToast);
    mockNeedRefresh.set(true);
    await Promise.resolve();
    await fireEvent.click(getByText('Refresh'));
    expect(mockUpdateServiceWorker).toHaveBeenCalledWith(true);
  });

  it('dismisses the toast when Dismiss (✕) is clicked', async () => {
    const { getByLabelText, queryByRole } = render(SwUpdateToast);
    mockNeedRefresh.set(true);
    await Promise.resolve();
    await fireEvent.click(getByLabelText('Dismiss'));
    expect(queryByRole('status')).toBeNull();
  });
});
