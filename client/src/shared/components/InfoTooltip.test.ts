import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import InfoTooltip from './InfoTooltip.svelte';

describe('InfoTooltip', () => {
  it('renders nothing when tip is empty string', () => {
    const { container } = render(InfoTooltip, { tip: '' });
    expect(container.querySelector('.info-icon')).toBeNull();
  });

  it('renders ℹ️ icon when tip is provided', () => {
    const { container } = render(InfoTooltip, { tip: 'Some tooltip text' });
    expect(container.querySelector('.info-icon')).not.toBeNull();
  });

  it('tooltip span contains the tip text', () => {
    const { container } = render(InfoTooltip, { tip: 'Drivers info here' });
    const tooltipSpan = container.querySelector('.tooltip');
    expect(tooltipSpan?.textContent).toBe('Drivers info here');
  });
});
