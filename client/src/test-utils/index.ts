/**
 * Shared Vitest test helpers for client-side component tests.
 *
 * Import from this module to avoid duplicating URL mocks, download helpers,
 * and panel-expansion helpers across test files.
 */
import { beforeAll, beforeEach, afterAll, vi } from 'vitest';
import { fireEvent } from '@testing-library/svelte';

// ── URL / Blob mock ───────────────────────────────────────────────────────────

/**
 * Install URL.createObjectURL / revokeObjectURL stubs for the enclosing test
 * scope (file root or a `describe` block).  Clears createObjectURL call
 * history before each test so assertions stay isolated.
 *
 * Usage — call once at the top of a test file or describe block:
 *   setupBlobUrlMock();
 */
export function setupBlobUrlMock(): void {
  beforeAll(() => {
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:mock-url'),
      revokeObjectURL: vi.fn(),
    });
  });
  beforeEach(() => {
    (URL.createObjectURL as ReturnType<typeof vi.fn>).mockClear();
  });
  afterAll(() => vi.unstubAllGlobals());
}

// ── CSV download helper ───────────────────────────────────────────────────────

/**
 * Click the CSV download link and return the Blob passed to
 * URL.createObjectURL.  Requires setupBlobUrlMock() in the same scope.
 */
export async function clickDownloadAndGetBlob(container: HTMLElement): Promise<Blob> {
  const link = container.querySelector<HTMLAnchorElement>(
    "a[data-action='download-filtered-csv']",
  )!;
  await fireEvent.click(link);
  return (URL.createObjectURL as ReturnType<typeof vi.fn>).mock.calls[0][0] as Blob;
}

// ── Panel helpers ─────────────────────────────────────────────────────────────

/**
 * Open the "More Filters" advanced-filters panel.
 * Uses `:not(.date-expand-btn)` to target the correct toggle in components
 * (like HistoryTable) that also have a date-specific expand button.
 */
export async function openAdvancedFilters(container: HTMLElement): Promise<void> {
  const btn = container.querySelector<HTMLButtonElement>(
    '.advanced-filters-toggle:not(.date-expand-btn)',
  )!;
  await fireEvent.click(btn);
}

/**
 * Open the date-picker section in HistoryTable.
 */
export async function openDatePicker(container: HTMLElement): Promise<void> {
  const btn = container.querySelector<HTMLButtonElement>(
    "button[data-action='toggle-date-picker']",
  )!;
  await fireEvent.click(btn);
}
