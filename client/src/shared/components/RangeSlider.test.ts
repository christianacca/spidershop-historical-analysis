import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import RangeSlider from './RangeSlider.svelte';

test('renders two range inputs with min, max, value attributes matching props', () => {
  const { getAllByRole } = render(RangeSlider, {
    min: 0,
    max: 100,
    label: 'Price',
    onchange: vi.fn(),
  });

  const sliders = getAllByRole('slider');
  expect(sliders).toHaveLength(2);

  // min/max are HTML attributes; value is managed as a DOM property by Svelte
  // (not as an HTML attribute), so we check the .value property directly.
  expect(sliders[0]).toHaveAttribute('min', '0');
  expect(sliders[0]).toHaveAttribute('max', '100');
  expect((sliders[0] as HTMLInputElement).value).toBe('0');

  expect(sliders[1]).toHaveAttribute('min', '0');
  expect(sliders[1]).toHaveAttribute('max', '100');
  expect((sliders[1] as HTMLInputElement).value).toBe('100');
});

test('display text shows formatted minProp – maxProp initially', () => {
  const { getByText } = render(RangeSlider, {
    min: 10,
    max: 50,
    label: 'Price',
    onchange: vi.fn(),
  });

  expect(getByText('10 – 50')).toBeTruthy();
});

test('setting min input above current max clamps max up', async () => {
  // Use max=200 so values up to 200 are valid for the HTML input.
  // Reduce currentMax first (to 60), then push min above it (to 80).
  const { getAllByRole } = render(RangeSlider, {
    min: 0,
    max: 200,
    label: 'Price',
    onchange: vi.fn(),
  });

  const sliders = getAllByRole('slider') as HTMLInputElement[];
  const minInput = sliders[0];
  const maxInput = sliders[1];

  // Bring max down to 60 so we can push min past it
  await fireEvent.input(maxInput, { target: { value: '60' } });
  // Push min to 80 — above currentMax (60) but within HTML max (200)
  await fireEvent.input(minInput, { target: { value: '80' } });

  expect(maxInput.value).toBe('80');
});

test('setting max input below current min clamps min down', async () => {
  const { getAllByRole } = render(RangeSlider, {
    min: 0,
    max: 100,
    label: 'Price',
    onchange: vi.fn(),
  });

  const sliders = getAllByRole('slider') as HTMLInputElement[];
  const minInput = sliders[0];
  const maxInput = sliders[1];

  // First, raise the min to 50
  await fireEvent.input(minInput, { target: { value: '50' } });
  // Now drag max below the current min
  await fireEvent.input(maxInput, { target: { value: '20' } });

  expect(minInput.value).toBe('20');
});

test('onchange is called with {min, max} payload after constraint enforcement', async () => {
  const onchange = vi.fn();
  // Use max=200 so we can set min above a pre-lowered max without HTML clamping.
  const { getAllByRole } = render(RangeSlider, {
    min: 0,
    max: 200,
    label: 'Price',
    onchange,
  });

  const sliders = getAllByRole('slider') as HTMLInputElement[];
  const minInput = sliders[0];
  const maxInput = sliders[1];

  // Reduce max to 60, then push min to 80 — max should clamp up to 80
  await fireEvent.input(maxInput, { target: { value: '60' } });
  onchange.mockClear();
  await fireEvent.input(minInput, { target: { value: '80' } });

  expect(onchange).toHaveBeenCalledWith({ min: 80, max: 80 });
});

test('explicit minInputId and maxInputId override auto-generated ids', () => {
  const { container } = render(RangeSlider, {
    min: 0,
    max: 100,
    label: 'Price',
    onchange: vi.fn(),
    minInputId: 'priceMin',
    maxInputId: 'priceMax',
  });

  expect(container.querySelector('#priceMin')).toBeTruthy();
  expect(container.querySelector('#priceMax')).toBeTruthy();
});

test('displayId is applied to the display span', () => {
  const { container } = render(RangeSlider, {
    min: 0,
    max: 100,
    label: 'Price',
    onchange: vi.fn(),
    displayId: 'priceDisplay',
  });

  expect(container.querySelector('#priceDisplay')).toBeTruthy();
});

test('formatValue is applied to display span text', () => {
  const { getByText } = render(RangeSlider, {
    min: 10,
    max: 50,
    label: 'Price',
    onchange: vi.fn(),
    formatValue: (v) => `£${v}`,
  });

  expect(getByText('£10 – £50')).toBeTruthy();
});
