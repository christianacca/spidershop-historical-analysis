import { writable } from 'svelte/store';
import { render, fireEvent } from '@testing-library/svelte';
import SwUpdateToast from './SwUpdateToast.svelte';

const mockUpdateServiceWorker = vi.fn();
const mockNeedRefresh = writable(false);

function renderToast() {
  return render(SwUpdateToast, {
    needRefresh: mockNeedRefresh,
    updateServiceWorker: mockUpdateServiceWorker,
  });
}

beforeEach(() => {
  mockNeedRefresh.set(false);
  mockUpdateServiceWorker.mockClear();
});

describe('SwUpdateToast', () => {
  it('is not rendered when needRefresh is false', () => {
    const { queryByRole } = renderToast();
    expect(queryByRole('status')).toBeNull();
  });

  it('renders the update message when needRefresh is true', async () => {
    const { getByRole } = renderToast();
    mockNeedRefresh.set(true);
    await Promise.resolve();
    expect(getByRole('status')).toHaveTextContent('New spider listings available.');
  });

  it('calls updateServiceWorker when "Refresh now" is clicked', async () => {
    const { getByText } = renderToast();
    mockNeedRefresh.set(true);
    await Promise.resolve();
    await fireEvent.click(getByText('Refresh now'));
    expect(mockUpdateServiceWorker).toHaveBeenCalled();
  });

  it('dismisses the toast when Dismiss (✕) is clicked', async () => {
    const { getByLabelText, queryByRole } = renderToast();
    mockNeedRefresh.set(true);
    await Promise.resolve();
    await fireEvent.click(getByLabelText('Dismiss'));
    expect(queryByRole('status')).toBeNull();
  });

  describe('countdown auto-refresh', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('shows "Refreshing in 30s…" when toast first appears', async () => {
      const { container } = renderToast();
      mockNeedRefresh.set(true);
      await Promise.resolve();
      expect(container).toHaveTextContent('Refreshing in 30s');
    });

    it('decrements the countdown every second', async () => {
      const { container } = renderToast();
      mockNeedRefresh.set(true);
      await Promise.resolve();

      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      expect(container).toHaveTextContent('Refreshing in 29s');

      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      expect(container).toHaveTextContent('Refreshing in 28s');
    });

    it('calls updateServiceWorker automatically after 30 seconds', async () => {
      renderToast();
      mockNeedRefresh.set(true);
      await Promise.resolve();

      vi.advanceTimersByTime(30_000);
      await Promise.resolve();

      expect(mockUpdateServiceWorker).toHaveBeenCalledOnce();
    });

    it('dismiss cancels the auto-refresh', async () => {
      const { getByLabelText } = renderToast();
      mockNeedRefresh.set(true);
      await Promise.resolve();

      await fireEvent.click(getByLabelText('Dismiss'));
      vi.advanceTimersByTime(30_000);
      await Promise.resolve();

      expect(mockUpdateServiceWorker).not.toHaveBeenCalled();
    });
  });
});
