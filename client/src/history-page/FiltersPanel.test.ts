import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import FiltersPanel from './FiltersPanel.svelte';

const AVAILABLE_GENERA = ['Avicularia', 'Brachypelma', 'Caribena', 'Grammostola'];
const MOST_OBSERVED = ['Avicularia', 'Caribena'];

function defaultProps(overrides: Partial<{
  availableGenera: string[];
  selectedGenera: string[];
  isAllSelected: boolean;
  mostObservedGenera: string[];
  windowId: import('./types.js').WindowId;
  basisNote: string;
  windowLabel: string;
  scopeLabel: string;
  onSelectionChange: (genera: string[], isAll: boolean) => void;
  onWindowChange: (id: import('./types.js').WindowId) => void;
}> = {}) {
  return {
    availableGenera: AVAILABLE_GENERA,
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: MOST_OBSERVED,
    windowId: 'current-quarter' as import('./types.js').WindowId,
    basisNote: 'Quarter in progress.',
    windowLabel: 'Current quarter',
    scopeLabel: '',
    onSelectionChange: vi.fn(),
    onWindowChange: vi.fn(),
    ...overrides,
  };
}

describe('FiltersPanel — panel heading', () => {
  it('renders <h2> with text "Global filters"', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const heading = container.querySelector('h2');
    expect(heading?.textContent?.trim()).toBe('Global filters');
  });
});

describe('FiltersPanel — child components present', () => {
  it('renders GenusSelector (.selector-shell)', () => {
    const { container } = render(FiltersPanel, defaultProps());
    expect(container.querySelector('.selector-shell')).not.toBeNull();
  });

  it('renders TimeWindowSelector (.window-row)', () => {
    const { container } = render(FiltersPanel, defaultProps());
    expect(container.querySelector('.window-row')).not.toBeNull();
  });
});

describe('FiltersPanel — global scope label text', () => {
  it('all-mode: shows "Current market scope: all genera • Current quarter"', () => {
    const { container } = render(FiltersPanel, defaultProps({
      isAllSelected: true,
      windowLabel: 'Current quarter',
      scopeLabel: '',
    }));
    const label = container.querySelector('.scope-label');
    expect(label?.textContent?.trim()).toBe('Current market scope: all genera • Current quarter');
  });

  it('narrow 1-genus: shows "Current market scope: Avicularia • Last month"', () => {
    const { container } = render(FiltersPanel, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
      windowLabel: 'Last month',
      scopeLabel: 'Avicularia',
    }));
    const label = container.querySelector('.scope-label');
    expect(label?.textContent?.trim()).toBe('Current market scope: Avicularia • Last month');
  });

  it('narrow 4-genera: shows "Current market scope: your 4 selected genera • This year"', () => {
    const genera = ['Avicularia', 'Caribena', 'Grammostola', 'Brachypelma'];
    const { container } = render(FiltersPanel, defaultProps({
      isAllSelected: false,
      selectedGenera: genera,
      windowLabel: 'This year',
      scopeLabel: 'your 4 selected genera',
    }));
    const label = container.querySelector('.scope-label');
    expect(label?.textContent?.trim()).toBe(
      'Current market scope: your 4 selected genera • This year'
    );
  });
});

describe('FiltersPanel — collapse toggle', () => {
  it('panel starts expanded by default — GenusSelector and TimeWindowSelector visible', () => {
    const { container } = render(FiltersPanel, defaultProps());
    expect(container.querySelector('.selector-shell')).not.toBeNull();
    expect(container.querySelector('.window-row')).not.toBeNull();
  });

  it('toggle button has is-expanded class when expanded', () => {
    const { container } = render(FiltersPanel, defaultProps());
    const btn = container.querySelector('.panel-header button');
    expect(btn).toHaveClass('is-expanded');
  });

  it('clicking toggle hides GenusSelector and TimeWindowSelector', async () => {
    const { container } = render(FiltersPanel, defaultProps());
    const btn = container.querySelector('.panel-header button') as HTMLButtonElement;
    await fireEvent.click(btn);
    expect(container.querySelector('.selector-shell')).toBeNull();
    expect(container.querySelector('.window-row')).toBeNull();
  });

  it('toggle button does not have is-expanded class when collapsed', async () => {
    const { container } = render(FiltersPanel, defaultProps());
    const btn = container.querySelector('.panel-header button') as HTMLButtonElement;
    await fireEvent.click(btn);
    expect(btn).not.toHaveClass('is-expanded');
  });

  it('scope label is always visible regardless of panel state', async () => {
    const { container } = render(FiltersPanel, defaultProps());
    const btn = container.querySelector('.panel-header button') as HTMLButtonElement;
    await fireEvent.click(btn);
    const label = container.querySelector('.scope-label');
    expect(label).not.toBeNull();
    expect(label?.textContent?.trim()).toBe('Current market scope: all genera • Current quarter');
  });

  it('clicking toggle again re-expands the panel', async () => {
    const { container } = render(FiltersPanel, defaultProps());
    const btn = container.querySelector('.panel-header button') as HTMLButtonElement;
    await fireEvent.click(btn);
    await fireEvent.click(btn);
    expect(container.querySelector('.selector-shell')).not.toBeNull();
    expect(container.querySelector('.window-row')).not.toBeNull();
  });
});
