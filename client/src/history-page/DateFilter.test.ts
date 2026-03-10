import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import DateFilter from './DateFilter.svelte';

// ── Shared fixtures ───────────────────────────────────────────────────────────

const DATES = ['2026-01-15', '2026-01-08', '2026-01-01']; // most-recent first
const ROW_COUNTS: Record<string, number> = {
  '2026-01-15': 3,
  '2026-01-08': 3,
  '2026-01-01': 3,
};
const TABLE_ID = 'history-table';

function renderDateFilter(onchangeFn = vi.fn()) {
  return render(DateFilter, {
    dates: DATES,
    rowCounts: ROW_COUNTS,
    tableId: TABLE_ID,
    onchange: onchangeFn,
  });
}

async function openPicker(container: HTMLElement): Promise<void> {
  const btn = container.querySelector<HTMLButtonElement>(
    `button[data-action='toggle-date-picker']`,
  )!;
  await fireEvent.click(btn);
}

// ── Rendering ─────────────────────────────────────────────────────────────────

test('renders one checkbox per date after opening picker', async () => {
  const { container } = renderDateFilter();
  await openPicker(container);

  const checkboxes = container.querySelectorAll<HTMLInputElement>(
    `input[data-date-value][data-table-id='${TABLE_ID}']`,
  );
  expect(checkboxes).toHaveLength(3);
});

test('all date checkboxes are checked by default', async () => {
  const { container } = renderDateFilter();
  await openPicker(container);

  const checkboxes = container.querySelectorAll<HTMLInputElement>(
    `input[data-date-value][data-table-id='${TABLE_ID}']`,
  );
  checkboxes.forEach((cb) => expect(cb.checked).toBe(true));
});

test('allDates checkbox is checked when all dates are selected', () => {
  const { container } = renderDateFilter();
  const allDates = container.querySelector<HTMLInputElement>(`#allDates-${TABLE_ID}`)!;
  expect(allDates.checked).toBe(true);
});

test('allDates checkbox is unchecked when a date is deselected', async () => {
  const { container } = renderDateFilter();
  await openPicker(container);

  const firstCheckbox = container.querySelector<HTMLInputElement>(
    `input[data-date-value='2026-01-15'][data-table-id='${TABLE_ID}']`,
  )!;
  await fireEvent.click(firstCheckbox);

  const allDates = container.querySelector<HTMLInputElement>(`#allDates-${TABLE_ID}`)!;
  expect(allDates.checked).toBe(false);
});

// ── Deselect a date ───────────────────────────────────────────────────────────

test('unchecking a date calls onchange without that date', async () => {
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  const checkbox = container.querySelector<HTMLInputElement>(
    `input[data-date-value='2026-01-15'][data-table-id='${TABLE_ID}']`,
  )!;
  await fireEvent.click(checkbox);

  expect(onchange).toHaveBeenCalledWith(['2026-01-08', '2026-01-01']);
});

// ── Quick-select ──────────────────────────────────────────────────────────────

test('Last Run button calls onchange with the single most recent date', async () => {
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  const btn = container.querySelector<HTMLButtonElement>(
    `button[data-action='select-last-n'][data-n='1']`,
  )!;
  await fireEvent.click(btn);

  expect(onchange).toHaveBeenCalledWith(['2026-01-15']);
});

test('Last 2 Runs button calls onchange with the 2 most recent dates', async () => {
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  const btn = container.querySelector<HTMLButtonElement>(
    `button[data-action='select-last-n'][data-n='2']`,
  )!;
  await fireEvent.click(btn);

  expect(onchange).toHaveBeenCalledWith(['2026-01-15', '2026-01-08']);
});

test('Show All button calls onchange with all dates', async () => {
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  // First narrow to Last 1 Run
  const lastBtn = container.querySelector<HTMLButtonElement>(
    `button[data-action='select-last-n'][data-n='1']`,
  )!;
  await fireEvent.click(lastBtn);

  // Then Show All
  const showAllBtn = container.querySelector<HTMLButtonElement>(
    `button[data-action='show-all-dates']`,
  )!;
  await fireEvent.click(showAllBtn);

  const lastCall = onchange.mock.calls.at(-1)![0] as string[];
  expect(lastCall).toEqual(DATES);
});

test('allDates checkbox is rechecked after Show All', async () => {
  const { container } = renderDateFilter();
  await openPicker(container);

  // Narrow to Last 1 Run
  const lastBtn = container.querySelector<HTMLButtonElement>(
    `button[data-action='select-last-n'][data-n='1']`,
  )!;
  await fireEvent.click(lastBtn);

  // allDates should now be unchecked
  const allDates = container.querySelector<HTMLInputElement>(`#allDates-${TABLE_ID}`)!;
  expect(allDates.checked).toBe(false);

  // Show All
  const showAllBtn = container.querySelector<HTMLButtonElement>(
    `button[data-action='show-all-dates']`,
  )!;
  await fireEvent.click(showAllBtn);

  expect(allDates.checked).toBe(true);
});

// ── allDates checkbox uncheck branch ─────────────────────────────────────────

test('unchecking allDates when already unchecked triggers onchange with no dates removed', async () => {
  // This covers the false branch of handleAllDatesChange (checked = false path)
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  const allDates = container.querySelector<HTMLInputElement>(`#allDates-${TABLE_ID}`)!;
  // Uncheck allDates — checked=false branch; selectedDates is not reset, only notifyParent fires
  await fireEvent.change(allDates, { target: { checked: false } });

  // onchange should have been called (notifyParent fires even when checked=false)
  expect(onchange).toHaveBeenCalled();
});

test('checking allDates checkbox after narrowing resets selection to all dates', async () => {
  // This covers the true branch of handleAllDatesChange (checked = true path → if(checked) runs)
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  // Narrow with Last 1 Run → allDates becomes unchecked
  const lastBtn = container.querySelector<HTMLButtonElement>(
    `button[data-action='select-last-n'][data-n='1']`,
  )!;
  await fireEvent.click(lastBtn);

  // Click allDates checkbox to recheck it → fires handleAllDatesChange with checked=true
  const allDates = container.querySelector<HTMLInputElement>(`#allDates-${TABLE_ID}`)!;
  await fireEvent.click(allDates);

  const lastCall = onchange.mock.calls.at(-1)![0] as string[];
  expect(lastCall).toEqual(DATES);
});

// ── Re-checking a date (handleDateCheckbox else branch) ───────────────────────

test('re-checking an unchecked date adds it back and calls onchange', async () => {
  const onchange = vi.fn();
  const { container } = renderDateFilter(onchange);
  await openPicker(container);

  // First uncheck 2026-01-15
  const checkbox = container.querySelector<HTMLInputElement>(
    `input[data-date-value='2026-01-15'][data-table-id='${TABLE_ID}']`,
  )!;
  await fireEvent.click(checkbox);
  expect(onchange).toHaveBeenLastCalledWith(['2026-01-08', '2026-01-01']);

  // Now re-check it (covers the else { next.add(date) } branch)
  await fireEvent.click(checkbox);
  const finalCall = onchange.mock.calls.at(-1)![0] as string[];
  expect(finalCall).toContain('2026-01-15');
  expect(finalCall).toHaveLength(3);
});

// ── Missing rowCounts entry (covers rowCounts[d] ?? 0 fallback) ──────────────

test('date missing from rowCounts shows 0 rows count in total-selected label', () => {
  // DATES contains '2026-01-15', '2026-01-08', '2026-01-01'
  // ROW_COUNTS only has '2026-01-15' and '2026-01-08' — '2026-01-01' is missing.
  // This exercises the `rowCounts[d] ?? 0` fallbacks in totalSelectedRows and the template.
  const partialCounts: Record<string, number> = {
    '2026-01-15': 3,
    '2026-01-08': 3,
    // '2026-01-01' intentionally omitted
  };
  const { container } = render(DateFilter, {
    dates: DATES,
    rowCounts: partialCounts,
    tableId: TABLE_ID,
    onchange: vi.fn(),
  });

  // The "All Dates" label should show the total as 6 (3+3+0)
  const label = container.querySelector('.date-all-label') as HTMLElement;
  expect(label.textContent).toContain('6 rows');
});

test('individual date with missing rowCounts shows (0 rows) in the picker', async () => {
  const partialCounts: Record<string, number> = {
    '2026-01-15': 3,
    '2026-01-08': 3,
    // '2026-01-01' intentionally omitted
  };
  const { container } = render(DateFilter, {
    dates: DATES,
    rowCounts: partialCounts,
    tableId: TABLE_ID,
    onchange: vi.fn(),
  });
  await openPicker(container);

  // The date-count span for '2026-01-01' should show "(0 rows)"
  const dateRows = container.querySelectorAll<HTMLElement>('.date-row');
  const missingDateRow = Array.from(dateRows).find((r) =>
    r.textContent?.includes('2026-01-01'),
  );
  expect(missingDateRow?.textContent).toContain('(0 rows)');
});

// ── Unchecked individual checkbox visible in picker ───────────────────────────

test('individual date checkboxes render unchecked when selection is narrowed', async () => {
  // Narrow via Last 1 Run FIRST, then open picker → some checkboxes rendered unchecked
  const { container } = renderDateFilter();

  // Narrow — without opening the picker
  const btn = container.querySelector<HTMLButtonElement>("button[data-action='toggle-date-picker']")!;
  await fireEvent.click(btn); // open
  const lastRunBtn = container.querySelector<HTMLButtonElement>(
    "button[data-action='select-last-n'][data-n='1']",
  )!;
  await fireEvent.click(lastRunBtn);

  // With the picker still open, the 2nd and 3rd date checkboxes should be unchecked
  const checkboxes = container.querySelectorAll<HTMLInputElement>(
    `input[data-date-value][data-table-id='${TABLE_ID}']`,
  );
  const unchecked = Array.from(checkboxes).filter((cb) => !cb.checked);
  expect(unchecked.length).toBe(2);
});

// ── Toggle picker open then closed (covers "Hide individual dates" text) ──────

test('toggling picker twice hides it again', async () => {
  const { container } = renderDateFilter();
  const toggleBtn = container.querySelector<HTMLButtonElement>(
    "button[data-action='toggle-date-picker']",
  )!;

  // Open
  await fireEvent.click(toggleBtn);
  expect(container.querySelector('.date-picker-content')).not.toBeNull();
  // The button text now says "Hide individual dates"
  expect(toggleBtn.textContent).toContain('Hide individual dates');

  // Close
  await fireEvent.click(toggleBtn);
  expect(container.querySelector('.date-picker-content')).toBeNull();
  expect(toggleBtn.textContent).toContain('Show individual dates');
});
