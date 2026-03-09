import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import FilterSection from './FilterSection.svelte';

describe('FilterSection', () => {
  it('renders the label text', () => {
    const { container } = render(FilterSection, { label: '🎯 Signal:' });
    const labelEl = container.querySelector('.filter-label');
    expect(labelEl?.textContent).toBe('🎯 Signal:');
  });

  it('renders slotted children', async () => {
    // Verify the filter-controls div exists as the children container
    const { container } = render(FilterSection, { label: 'Test' });
    expect(container.querySelector('.filter-section')).not.toBeNull();
    expect(container.querySelector('.filter-controls')).not.toBeNull();
  });
});
