import { render } from '@testing-library/svelte';
import Spinner from './Spinner.svelte';

describe('Spinner', () => {
  it('renders with role="status"', () => {
    const { getByRole } = render(Spinner);
    expect(getByRole('status')).toBeInTheDocument();
  });

  it('has default aria-label "Loading"', () => {
    const { getByRole } = render(Spinner);
    expect(getByRole('status')).toHaveAttribute('aria-label', 'Loading');
  });

  it('accepts a custom label', () => {
    const { getByRole } = render(Spinner, { label: 'Saving changes' });
    expect(getByRole('status')).toHaveAttribute('aria-label', 'Saving changes');
  });

  it('applies custom size as a CSS custom property via inline style', () => {
    const { getByRole } = render(Spinner, { size: '2rem' });
    const el = getByRole('status') as HTMLElement;
    expect(el.style.getPropertyValue('--spinner-size')).toBe('2rem');
  });

  it('sets 1em as the default size CSS custom property', () => {
    const { getByRole } = render(Spinner);
    const el = getByRole('status') as HTMLElement;
    expect(el.style.getPropertyValue('--spinner-size')).toBe('1em');
  });
});
