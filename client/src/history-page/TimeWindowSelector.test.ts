import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import TimeWindowSelector from './TimeWindowSelector.svelte';
import type { WindowId } from './types.js';

const ALL_WINDOWS: { id: WindowId; label: string }[] = [
  { id: 'this-month',      label: 'This month' },
  { id: 'last-month',      label: 'Last month' },
  { id: 'current-quarter', label: 'Current quarter' },
  { id: 'last-quarter',    label: 'Last quarter' },
  { id: 'this-year',       label: 'This year' },
  { id: 'last-year',       label: 'Last year' },
  { id: 'all-time',        label: 'All time' },
];

function defaultProps(overrides: Partial<{
  windowId: WindowId;
  basisNote: string;
  onWindowChange: (id: WindowId) => void;
}> = {}) {
  return {
    windowId: 'current-quarter' as WindowId,
    basisNote: 'Comparison basis: last full quarter vs prior full quarter.',
    onWindowChange: vi.fn(),
    ...overrides,
  };
}

describe('TimeWindowSelector — button labels', () => {
  it('renders all 7 window buttons with correct labels', () => {
    const { container } = render(TimeWindowSelector, defaultProps());
    const buttons = container.querySelectorAll('button.window');
    expect(buttons).toHaveLength(7);
    const labels = [...buttons].map(b => b.textContent?.trim());
    expect(labels).toEqual([
      'This month',
      'Last month',
      'Current quarter',
      'Last quarter',
      'This year',
      'Last year',
      'All time',
    ]);
  });
});

describe('TimeWindowSelector — aria-pressed', () => {
  it('active button has aria-pressed="true"; all others have aria-pressed="false"', () => {
    const { container } = render(TimeWindowSelector, defaultProps({ windowId: 'last-quarter' }));
    const buttons = container.querySelectorAll('button.window');
    buttons.forEach(btn => {
      const isActive = btn.textContent?.trim() === 'Last quarter';
      expect(btn.getAttribute('aria-pressed')).toBe(isActive ? 'true' : 'false');
    });
  });
});

describe('TimeWindowSelector — onWindowChange callback', () => {
  it('clicking the already-active button still fires onWindowChange', async () => {
    const onWindowChange = vi.fn();
    const { getByText } = render(TimeWindowSelector, defaultProps({
      windowId: 'current-quarter',
      onWindowChange,
    }));
    await fireEvent.click(getByText('Current quarter'));
    expect(onWindowChange).toHaveBeenCalledOnce();
    expect(onWindowChange).toHaveBeenCalledWith('current-quarter');
  });

  it.each(ALL_WINDOWS)('clicking $label fires onWindowChange with $id', async ({ id, label }) => {
    const onWindowChange = vi.fn();
    const { getByText } = render(TimeWindowSelector, defaultProps({ onWindowChange }));
    await fireEvent.click(getByText(label));
    expect(onWindowChange).toHaveBeenCalledWith(id);
  });
});

describe('TimeWindowSelector — basisNote', () => {
  it('renders basisNote as text content in .micro-note', () => {
    const note = 'Comparison basis: last full month vs prior full month.';
    const { container } = render(TimeWindowSelector, defaultProps({ basisNote: note }));
    const microNote = container.querySelector('.micro-note');
    expect(microNote?.textContent?.trim()).toBe(note);
  });
});
