import { render, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import GenusSelector from './GenusSelector.svelte';

const AVAILABLE_GENERA = ['Avicularia', 'Brachypelma', 'Caribena', 'Chromatopelma', 'Grammostola'];
const MOST_OBSERVED = ['Avicularia', 'Caribena'];

function defaultProps(overrides: Partial<{
  availableGenera: string[];
  selectedGenera: string[];
  isAllSelected: boolean;
  mostObservedGenera: string[];
  onSelectionChange: (genera: string[], isAll: boolean) => void;
  initialExpanded: boolean;
}> = {}) {
  return {
    availableGenera: AVAILABLE_GENERA,
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: MOST_OBSERVED,
    onSelectionChange: vi.fn(),
    ...overrides,
  };
}

describe('GenusSelector — all-mode (State 1: collapsed)', () => {
  it('shows "All genera • N available" count label', () => {
    const { container } = render(GenusSelector, defaultProps());
    const label = container.querySelector('.scope-label');
    expect(label?.textContent?.trim()).toBe(`All genera • ${AVAILABLE_GENERA.length} available`);
  });

  it('shows the collapsed note when all-mode and not expanded', () => {
    const { container } = render(GenusSelector, defaultProps());
    const note = container.querySelector('.collapsed-note');
    expect(note).not.toBeNull();
    expect(note?.textContent).toContain('All genera are in scope');
  });

  it('renders no chips in all-mode', () => {
    const { container } = render(GenusSelector, defaultProps());
    expect(container.querySelectorAll('.chip')).toHaveLength(0);
  });

  it('"All" quick-pick button has active class when isAllSelected is true (when expanded)', () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const allBtn = [...container.querySelectorAll('button.quick-pick')]
      .find(b => b.textContent?.trim() === 'All');
    expect(allBtn).not.toBeNull();
    expect(allBtn?.classList.contains('active')).toBe(true);
  });
});

describe('GenusSelector — narrow mode (selected genera)', () => {
  it('shows "N of M genera selected" count label in narrow mode', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena'],
    }));
    const label = container.querySelector('.scope-label');
    expect(label?.textContent?.trim()).toBe(`2 of ${AVAILABLE_GENERA.length} genera selected`);
  });

  it('renders chips for each selected genus in narrow mode', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena'],
    }));
    const chips = container.querySelectorAll('.chip.selected');
    expect(chips).toHaveLength(2);
  });

  it('hides the collapsed note in narrow mode', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    }));
    expect(container.querySelector('.collapsed-note')).toBeNull();
  });

  it('each chip has a dismiss button with aria-label "Remove {genus}"', () => {
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    }));
    const dismiss = container.querySelector('button.dismiss');
    expect(dismiss?.getAttribute('aria-label')).toBe('Remove Avicularia');
  });
});

describe('GenusSelector — toggle button', () => {
  it('toggle button has aria-expanded="false" on mount', () => {
    const { container } = render(GenusSelector, defaultProps());
    const toggle = container.querySelector('button.selector-toggle');
    expect(toggle?.getAttribute('aria-expanded')).toBe('false');
  });

  it('toggle button text is "Show genus selector" on mount', () => {
    const { container } = render(GenusSelector, defaultProps());
    const toggle = container.querySelector('button.selector-toggle');
    expect(toggle?.textContent?.trim()).toContain('Show genus selector');
  });

  it('clicking toggle sets expanded=true; aria-expanded updates', async () => {
    const { container } = render(GenusSelector, defaultProps());
    const toggle = container.querySelector('button.selector-toggle') as HTMLElement;
    await fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    expect(toggle.textContent?.trim()).toContain('Hide genus selector');
  });

  it('clicking toggle twice collapses again', async () => {
    const { container } = render(GenusSelector, defaultProps());
    const toggle = container.querySelector('button.selector-toggle') as HTMLElement;
    await fireEvent.click(toggle);
    await fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
  });

  it('expanded content is hidden on mount', () => {
    const { container } = render(GenusSelector, defaultProps());
    expect(container.querySelector('.expanded-preview')).toBeNull();
  });

  it('expanded content is visible after toggle click', async () => {
    const { container } = render(GenusSelector, defaultProps());
    const toggle = container.querySelector('button.selector-toggle') as HTMLElement;
    await fireEvent.click(toggle);
    expect(container.querySelector('.expanded-preview')).not.toBeNull();
  });

  it('initialExpanded=true shows expanded content immediately', () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    expect(container.querySelector('.expanded-preview')).not.toBeNull();
  });
});

describe('GenusSelector — suggestion row interactions', () => {
  it('clicking an unselected suggestion calls onSelectionChange with genus added, isAll=false', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true, onSelectionChange }));
    const rows = container.querySelectorAll('button.suggestion-row');
    const avicularia = [...rows].find(r => r.textContent?.includes('Avicularia')) as HTMLElement;
    await fireEvent.click(avicularia);
    expect(onSelectionChange).toHaveBeenCalledWith(['Avicularia'], false);
  });

  it('clicking a selected suggestion removes it from selection', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({
      initialExpanded: true,
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena'],
      onSelectionChange,
    }));
    const rows = container.querySelectorAll('button.suggestion-row');
    const caribena = [...rows].find(r => r.textContent?.includes('Caribena')) as HTMLElement;
    await fireEvent.click(caribena);
    expect(onSelectionChange).toHaveBeenCalledWith(['Avicularia'], false);
  });

  it('removing the last selected genus reverts to all-mode (onSelectionChange([], true))', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({
      initialExpanded: true,
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
      onSelectionChange,
    }));
    const rows = container.querySelectorAll('button.suggestion-row');
    const avicularia = [...rows].find(r => r.textContent?.includes('Avicularia')) as HTMLElement;
    await fireEvent.click(avicularia);
    expect(onSelectionChange).toHaveBeenCalledWith([], true);
  });

  it('suggestion row shows "Selected" badge for selected genera', () => {
    const { container } = render(GenusSelector, defaultProps({
      initialExpanded: true,
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
    }));
    const rows = container.querySelectorAll('button.suggestion-row');
    const aviculariaRow = [...rows].find(r => r.textContent?.includes('Avicularia'));
    const badge = aviculariaRow?.querySelector('.suggestion-status');
    expect(badge?.textContent?.trim()).toBe('Selected');
    expect(badge?.classList.contains('selected')).toBe(true);
  });

  it('suggestion row shows "Available" badge for unselected genera', () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const rows = container.querySelectorAll('button.suggestion-row');
    const row = rows[0];
    const badge = row?.querySelector('.suggestion-status');
    expect(badge?.textContent?.trim()).toBe('Available');
    expect(badge?.classList.contains('selected')).toBe(false);
  });
});

describe('GenusSelector — chip dismiss', () => {
  it('dismiss button click removes genus from selection', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia', 'Caribena'],
      onSelectionChange,
    }));
    const dismissBtns = container.querySelectorAll('button.dismiss');
    await fireEvent.click(dismissBtns[0] as HTMLElement);
    expect(onSelectionChange).toHaveBeenCalledWith(['Caribena'], false);
  });

  it('dismissing the last chip calls onSelectionChange([], true)', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({
      isAllSelected: false,
      selectedGenera: ['Avicularia'],
      onSelectionChange,
    }));
    const dismiss = container.querySelector('button.dismiss') as HTMLElement;
    await fireEvent.click(dismiss);
    expect(onSelectionChange).toHaveBeenCalledWith([], true);
  });
});

describe('GenusSelector — quick-pick buttons', () => {
  it('"All" quick-pick calls onSelectionChange([], true)', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true, onSelectionChange }));
    const allBtn = [...container.querySelectorAll('button.quick-pick')]
      .find(b => b.textContent?.trim() === 'All') as HTMLElement;
    await fireEvent.click(allBtn);
    expect(onSelectionChange).toHaveBeenCalledWith([], true);
  });

  it('"Clear all" is equivalent to "All" — calls onSelectionChange([], true)', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true, onSelectionChange }));
    const clearBtn = container.querySelector('button.quick-pick-action') as HTMLElement;
    await fireEvent.click(clearBtn);
    expect(onSelectionChange).toHaveBeenCalledWith([], true);
  });

  it('"Most observed" quick-pick calls onSelectionChange(mostObservedGenera, false)', async () => {
    const onSelectionChange = vi.fn();
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true, onSelectionChange }));
    const mostObservedBtn = [...container.querySelectorAll('button.quick-pick')]
      .find(b => b.textContent?.trim() === 'Most observed') as HTMLElement;
    await fireEvent.click(mostObservedBtn);
    expect(onSelectionChange).toHaveBeenCalledWith(MOST_OBSERVED, false);
  });

  it('Arboreal preset filters against availableGenera and calls onSelectionChange', async () => {
    const onSelectionChange = vi.fn();
    // availableGenera only includes 'Avicularia' and 'Caribena' from the arboreal preset
    const { container } = render(GenusSelector, defaultProps({
      initialExpanded: true,
      availableGenera: ['Avicularia', 'Caribena', 'Grammostola'],
      onSelectionChange,
    }));
    const arborealBtn = [...container.querySelectorAll('button.quick-pick')]
      .find(b => b.textContent?.trim() === 'Arboreal') as HTMLElement;
    await fireEvent.click(arborealBtn);
    // Avicularia and Caribena are in the arboreal preset and in availableGenera
    expect(onSelectionChange).toHaveBeenCalledWith(
      expect.arrayContaining(['Avicularia', 'Caribena']),
      false
    );
    const callArgs = onSelectionChange.mock.calls[0][0] as string[];
    // Grammostola is not in arboreal preset
    expect(callArgs).not.toContain('Grammostola');
  });

  it('Fossorial preset only includes genera present in availableGenera', async () => {
    const onSelectionChange = vi.fn();
    // Only Chilobrachys is in availableGenera from the fossorial preset
    const { container } = render(GenusSelector, defaultProps({
      initialExpanded: true,
      availableGenera: ['Chilobrachys', 'Avicularia'],
      onSelectionChange,
    }));
    const fossorialBtn = [...container.querySelectorAll('button.quick-pick')]
      .find(b => b.textContent?.trim() === 'Fossorial') as HTMLElement;
    await fireEvent.click(fossorialBtn);
    expect(onSelectionChange).toHaveBeenCalledWith(['Chilobrachys'], false);
  });
});

describe('GenusSelector — search filtering', () => {
  it('shows all genera when search is empty', () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const rows = container.querySelectorAll('button.suggestion-row');
    expect(rows).toHaveLength(AVAILABLE_GENERA.length);
  });

  it('filters suggestion list by case-insensitive substring match', async () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const input = container.querySelector('input.search-input') as HTMLInputElement;
    await fireEvent.input(input, { target: { value: 'avi' } });
    const rows = container.querySelectorAll('button.suggestion-row');
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toContain('Avicularia');
  });

  it('shows no results when search matches nothing', async () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const input = container.querySelector('input.search-input') as HTMLInputElement;
    await fireEvent.input(input, { target: { value: 'zzzzz' } });
    const rows = container.querySelectorAll('button.suggestion-row');
    expect(rows).toHaveLength(0);
  });

  it('restores full list when search is cleared', async () => {
    const { container } = render(GenusSelector, defaultProps({ initialExpanded: true }));
    const input = container.querySelector('input.search-input') as HTMLInputElement;
    await fireEvent.input(input, { target: { value: 'avi' } });
    await fireEvent.input(input, { target: { value: '' } });
    const rows = container.querySelectorAll('button.suggestion-row');
    expect(rows).toHaveLength(AVAILABLE_GENERA.length);
  });
});
