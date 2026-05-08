# WP-Arch — Filter Architecture: Implementation Plan

**Work package:** WP-Arch  
**Spec:** `docs/ux/history-page/wp-arch-filter-architecture-spec.md`  
**Date:** 8 May 2026  
**Status:** Ready to execute

---

## Overview

This plan delivers the global filter panel for the History Insights page in 6 phases. No
phase may begin until the previous phase's GATE block is output. The plan is written for
direct execution by an agent — every task is a concrete action, every acceptance criterion is
observable.

**Test commands (all phases):**

| Command | Use |
|---|---|
| `make test-client-fast` | Fast Vitest run; use during active iteration |
| `make test-client` | Vitest + coverage; required at Phase 4 gate |
| `make test-visual` | Browser-backed visual contracts; required at Phases 1, 2, 3, 4 |
| `make storybook` | Storybook dev server on `http://localhost:6006` |
| `make preview` | Generate site + serve at `http://localhost:8000` |
| `make test-e2e` | Full E2E suite; required at Phase 5 gate |

**Feed-forward log:** Maintained as a dated note at the end of this file. Add an entry after
each phase, even if there are no new findings.

---

## Code Smell Checklist (run at every H2 step)

- [ ] No hardcoded colour literals except where spec explicitly permits (`rgba(255,255,255,0.72)` etc.)
- [ ] All new `var(--token)` references exist in `templates/common.css`
- [ ] No business logic inside Svelte `<script>` blocks — computation stays in the engine
- [ ] Props are typed with a named `interface Props`; `$props()` is destructured immediately
- [ ] `$derived` used for computed values; no manual `$effect` for derived state
- [ ] Callback props named `on*`; not dispatched events (Svelte 5 pattern)
- [ ] All interactive elements have sufficient accessible labels
- [ ] No naked `button`, `input`, `label` selectors in new CSS (only scoped class selectors)
- [ ] Test files do not import `@testing-library/jest-dom` (it is globally imported in `test-setup.ts`)
- [ ] `fireEvent.*` calls in tests are `await`-ed

---

## Phase 0 — Pre-implementation Audit

> **No product code is written in this phase.** This phase records the ground truth against
> which all implementation and divergence tracking will be measured.

### Tasks

- [ ] **P0-1** Open the mock at `docs/ux/history-page/history-kpi-concepts-mockup.html` in a
  browser. Use Chrome DevTools to capture the computed styles for each element listed in the
  Mock Parity Audit table below. Record any values that differ from the spec §7 table.

- [ ] **P0-2** Audit every `var(--token)` planned for new components against the `templates/common.css`
  `:root` block. Confirm that the following tokens exist (or are planned for Phase 1):

  | Token | Status |
  |---|---|
  | `--color-border-warm` | ✓ exists (`#d7cfc0`) |
  | `--color-text` | ✓ exists (`#1f2a2c`) |
  | `--color-text-label` | ✓ exists (`#5d6a6d`) |
  | `--color-market-health` | ✓ exists (`#1f7a6b`) |
  | `--color-surface` | ✓ exists (`#fffaf2`) |
  | `--shadow-popover` | ✓ exists |
  | `--color-breeder-focus` | ❌ MISSING — to be added in Phase 1 |

  If any additional token is found to be missing, document it and add it in Phase 1.

- [ ] **P0-3** Audit global CSS collision risk. Check `templates/common.css` for naked element
  selectors that would affect elements inside the Svelte islands:

  | Selector | Risk | Mitigation |
  |---|---|---|
  | `h2 { color: var(--color-primary); margin-bottom: 20px; }` | `<h2>Global filters</h2>` inside `FiltersPanel.svelte` will inherit `margin-bottom: 20px` | Svelte-scoped `.panel-heading { margin: 0 0 4px; }` override required |
  | `.content > h2 { border-bottom: 2px solid var(--color-accent); }` | Direct-child selector — does NOT reach Svelte islands; no collision | None required |
  | `button` rules | No naked `button` selector in `common.css` | None required |
  | `input` rules | No naked `input` selector in `common.css` | None required |
  | `label` rules | No naked `label` selector in `common.css` | None required |
  | `details`/`summary` rules | No global rules in `common.css` | None required |

  Re-verify these findings by searching `common.css` at implementation time.

- [ ] **P0-4** Initialize the divergence log at the bottom of this file. Add one entry per
  by-design deviation listed in spec §12.

- [ ] **P0-5** Confirm the Storybook command: `make storybook` (runs `cd client && npm run storybook`,
  serves at `http://localhost:6006`). No code written — just confirm command works.

### Mock Parity Audit (P0-1 capture target)

Record computed values from the live mock for these elements. Compare against spec §7. Mark
as `match`, `differs`, or `not applicable` (if element is absent in current state).

| Element | Property | Spec §7 value | Computed (mock) | Result |
|---|---|---|---|---|
| `.filters-panel` | `display` | `grid` | `grid` | match |
| `.filters-panel` | `gap` | `18px` | `18px` | match |
| `.filters-panel` | `padding` | `24px` | `24px` | match |
| `.filters-panel` | `border-radius` | `20px` (mock) / `18px` (implementation) | `20px` | by-design (deviation #7) |
| `.selector-shell` | `border-radius` | `18px` | `18px` | match |
| `.selector-shell` | `background` | `rgba(255,255,255,0.72)` | `rgba(255, 255, 255, 0.72)` | match |
| `.chip.selected` | `background` | `rgba(204,107,73,0.14)` | `rgba(204, 107, 73, 0.14)` (CSS source; no element in default all-mode state) | match |
| `.window.active` | `background-color` | resolves to `rgb(31,42,44)` | `rgb(31, 42, 44)` | match |
| `.quick-pick` | `border-style` | `dashed` | `dashed` (non-active quick-pick confirmed) | match |
| `.scope-label` | `background` | `rgba(31,122,107,0.12)` | `rgba(31, 122, 107, 0.12)` | match |
| `.scope-label` | `color` | resolves to `rgb(31,122,107)` | `rgb(31, 122, 107)` | match |
| `.scope-label` | `display` | `inline-flex` | CSS source: `inline-flex`; `getComputedStyle` returned `flex` (browser computed-value artifact for span in flex container) | match — use `inline-flex` in implementation |

### Acceptance criteria

- All computed styles captured in the table above
- Token audit complete; no unexpected missing tokens
- Collision audit findings documented
- Divergence log initialized with all by-design deviations from spec §12

### Housekeeping

```
[x] H1 - All Phase 0 tasks checked off
[x] H2 - Reflection scan against code smell checklist (N/A — no code written)
[x] H3 - Feed-forward log entry added (dated)
[x] H4 - No commit in Phase 0 (audit only)
[x] GATE - Output Phase 0 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 0 COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    N/A (no code written)
║  Commit:   N/A
║  Stories:  N/A
║  Blockers: none — all tokens confirmed; one display: inline-flex computed-value artifact noted (no action needed)
╚══════════════════════════════════════════════════════════════╝
```

---

## Phase 1 — Foundation

> Adds the missing CSS token, restructures the mount point, and creates
> `HistoryInsightsRoot.svelte`. After this phase the page loads identically to the current
> WP1 state — `MarketHealthSection` still renders with the default window and all-mode genus.

### Tasks

- [ ] **P1-1** Add `--color-breeder-focus: #cc6b49;` to the `:root` block of
  `templates/common.css`. Place it immediately after `--color-market-health` in the Brand /
  Accent section. Add a comment: `/* warm orange — selected genus chip, breeder-focus emphasis */`

- [ ] **P1-2** Update `templates/history_insights_page.html`:
  - Change `<div id="market-health-root"></div>` to `<div id="history-insights-root"></div>`
  - No other changes to this file

- [ ] **P1-3** Create `client/src/history-page/HistoryInsightsRoot.svelte`.

  **Minimum viable content for Phase 1 (filters not yet wired):**
  ```svelte
  <script lang="ts">
    import MarketHealthSection from './MarketHealthSection.svelte';
    import type { MarketHealthRawData, MarketHealthPayload, WindowId } from './types.js';
    import { buildMarketHealthPayload } from './market-health-engine.js';

    interface Props {
      rawData: MarketHealthRawData;
    }

    let { rawData }: Props = $props();

    let selectedGenera: string[] = $state([]);
    let isAllSelected: boolean = $state(true);
    let windowId: WindowId = $state('current-quarter');

    const payload: MarketHealthPayload = $derived(
      buildMarketHealthPayload(rawData, windowId, { selectedGenera, isAllSelected })
    );
  </script>

  <MarketHealthSection {payload} />
  ```

  This is intentionally minimal. The hero/filter UI is added in Phases 2–4.

- [ ] **P1-4** Update `client/src/history-page/index.ts`:
  - Import `HistoryInsightsRoot` instead of `MarketHealthSection`
  - Remove the `buildMarketHealthPayloadAllWindows` call and `allPayloads` variable
  - Change mount target from `#market-health-root` to `#history-insights-root`
  - Pass `rawData` as a prop to `HistoryInsightsRoot`

  Expected result:
  ```typescript
  import { mount } from 'svelte';
  import { HISTORY_PAGE_CONFIG } from './config.js';
  import { bootstrapSortableTablePage } from '../shared/page-entry.js';
  import HistoryInsightsRoot from './HistoryInsightsRoot.svelte';
  import type { MarketHealthRawData } from './types.js';

  bootstrapSortableTablePage(HISTORY_PAGE_CONFIG);

  const historyInsightsRoot = document.getElementById('history-insights-root');
  if (historyInsightsRoot) {
    const rawData = (window as unknown as Record<string, unknown>)
      .marketHealthRawData as MarketHealthRawData | undefined;

    if (rawData && rawData.records.length > 0) {
      mount(HistoryInsightsRoot, {
        target: historyInsightsRoot,
        props: { rawData },
      });
    }
  }
  ```

- [ ] **P1-5** Write `client/src/history-page/HistoryInsightsRoot.test.ts`.

  Tests to cover:
  - Renders `MarketHealthSection` when `rawData` has records
  - Initial window defaults to `current-quarter` (verify `payload.windowId === 'current-quarter'`)
  - Initial mode is all-mode (`payload.isAllSelected === true`)
  - `payload` is reactive: changing `windowId` state produces a new payload with the new `windowId`

  Use `@testing-library/svelte` `render()`. Expose `windowId` as a prop for testability or
  test via the derived payload output.

- [ ] **P1-6** Write a visual contract test at
  `client/src/history-page/HistoryInsightsRoot.visual.test.ts`:
  - Verify `--color-breeder-focus` CSS custom property resolves to `rgb(204, 107, 73)` in the
    browser (use `getComputedStyle(document.documentElement).getPropertyValue('--color-breeder-focus').trim()`).

- [ ] **P1-7** Run `make test-client-fast` — confirm all tests pass (green).

- [ ] **P1-8** Run `make test-visual` — confirm the new visual contract passes.

- [ ] **P1-9** Run `make preview`. Navigate to `http://localhost:8000/history-insights.html`.
  Confirm the Market Health section renders identically to the pre-WP-Arch state.

### Acceptance criteria

- `http://localhost:8000/history-insights.html` loads; `MarketHealthSection` renders
- `--color-breeder-focus` token exists in `common.css` and resolves correctly in the browser
- All existing tests remain green (`make test-client-fast`)
- New visual contract passes (`make test-visual`)

### Housekeeping

```
[ ] H1 - All Phase 1 tasks checked off
[ ] H2 - Reflection scan: token exists in :root; no naked-button/input collisions introduced; props typed correctly
[ ] H3 - Feed-forward log entry added (dated)
[ ] H4 - Commit: "WP-Arch Phase 1: add --color-breeder-focus token, HistoryInsightsRoot foundation"
          Verify: git log --oneline -1
[ ] GATE - Output Phase 1 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 1 COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-client-fast]
║  Visual:   [paste final line of: make test-visual]
║  Commit:   [paste: git log --oneline -1]
║  Stories:  N/A
║  Blockers: none / [deferred item]
╚══════════════════════════════════════════════════════════════╝
```

---

## Phase 2 — TimeWindowSelector

> Creates the time window pill selector and wires it into `HistoryInsightsRoot`. After this
> phase the user can switch windows and see `MarketHealthSection` re-render.

### Tasks

- [ ] **P2-1** Create `client/src/history-page/TimeWindowSelector.svelte`.

  **Props interface:**
  ```typescript
  interface Props {
    windowId: WindowId;
    basisNote: string;
    onWindowChange: (id: WindowId) => void;
  }
  ```

  **Renders:**
  - A `<div class="window-row">` containing 7 `<button class="window">` elements
  - Button order: `this-month`, `last-month`, `current-quarter`, `last-quarter`, `this-year`, `last-year`, `all-time`
  - Button labels: "This month", "Last month", "Current quarter", "Last quarter", "This year", "Last year", "All time"
  - Active button: `class={{ window: true, active: windowId === id }}` and `aria-pressed={windowId === id}`
  - Below the row: `<p class="micro-note">{basisNote}</p>`

  **Svelte-scoped styles** (Layer 3): `.window`, `.window.active` per spec §7 visual contract.
  Use `var(--color-border-warm)` for the default border, `var(--color-text)` for the active
  background.

  The `.window-row` container must have `display: flex; gap: 8px; flex-wrap: wrap;` as a
  **base style** (not inside any `@media` block). `flex-wrap: wrap` is sourced from mock CSS
  and ensures 7 pills wrap gracefully at all viewport widths — including mobile portrait —
  without requiring any breakpoint rule.

- [ ] **P2-2** Write `client/src/history-page/TimeWindowSelector.test.ts`.

  Tests to cover:
  - All 7 buttons render with correct labels
  - Active button has `aria-pressed="true"`; all others have `aria-pressed="false"`
  - Clicking a non-active button fires `onWindowChange` with the correct `WindowId`
  - Clicking the already-active button still fires `onWindowChange`
  - `basisNote` is rendered as text content in the `.micro-note`

- [ ] **P2-3** Write `client/src/history-page/TimeWindowSelector.visual.test.ts`.

  Visual contracts to assert (via `evaluate_script` in browser-backed tests):
  - Active button `backgroundColor` resolves to `rgb(31, 42, 44)` (= `var(--color-text)`)
  - Active button `color` resolves to `rgb(255, 255, 255)`
  - Default button `borderStyle` is `solid` and `backgroundColor` is `rgb(255, 255, 255)`
  - At mobile viewport (390 × 844): `getComputedStyle(windowRow).flexWrap` is `"wrap"` and
    at least one pill has a `offsetTop` greater than the first pill (confirming multi-row
    wrapping when all 7 pills don't fit in ~358 px)

- [ ] **P2-4** Write `client/src/history-page/TimeWindowSelector.stories.ts`.

  Named exports (each passes a `windowId` and appropriate `basisNote`):
  1. `ThisMonthActive` — `windowId: 'this-month'`; dynamic in-progress basis note
  2. `LastMonthActive` — `windowId: 'last-month'`; `"Comparison basis: last full month vs prior full month."`
  3. `CurrentQuarterActive` — `windowId: 'current-quarter'`; dynamic in-progress basis note
  4. `LastQuarterActive` — `windowId: 'last-quarter'`; static basis note
  5. `ThisYearActive` — `windowId: 'this-year'`; dynamic in-progress basis note
  6. `LastYearActive` — `windowId: 'last-year'`; static basis note
  7. `AllTimeActive` — `windowId: 'all-time'`; `"Comparison basis: structural context only, with no prior-period delta."`
  8. `Interactive` — all args configurable via Storybook controls; `onWindowChange: fn()`

  Follow the WP1 story pattern: `satisfies Story`, typed `args`, no wrapping function.

- [ ] **P2-5** Wire `TimeWindowSelector` into `HistoryInsightsRoot.svelte`:
  - Import and render `TimeWindowSelector` inside the root (temporarily, before `FiltersPanel` is built)
  - Pass `windowId`, `basisNote` (`payload.windowBasisNote`), and `onWindowChange` callback
  - `onWindowChange` handler: `(id) => { windowId = id; }`

- [ ] **P2-6** Run `make test-client-fast` — confirm green.

- [ ] **P2-7** Run `make test-visual` — confirm all visual contracts pass.

- [ ] **P2-8** Open `make storybook`. Navigate to `history-page/TimeWindowSelector`. Verify all
  8 stories render correctly. Verify:
  - Active button is visually dark (dark background, white text)
  - Default buttons are white with warm border
  - Basis note renders below the button row
  - Toggle between stories to confirm window switching works visually

- [ ] **P2-9** Run `make preview`. Navigate to `http://localhost:8000/history-insights.html`.
  Click each window button. Confirm:
  - Basis note text updates
  - `MarketHealthSection` heading updates (e.g. switching to `all-time` changes the heading)

### Acceptance criteria

- All 7 window buttons render; clicking any updates `MarketHealthSection`
- Basis note updates on every window change
- All 8 Storybook stories visible and correct
- `make test-client-fast` green; `make test-visual` green

### Housekeeping

```
[ ] H1 - All Phase 2 tasks checked off
[ ] H2 - Reflection scan: aria-pressed on all 7 buttons; no business logic in component; basisNote from payload not hardcoded
[ ] H3 - Feed-forward log entry (dated)
[ ] H4 - Commit: "WP-Arch Phase 2: TimeWindowSelector component and stories"
          Verify: git log --oneline -1
[ ] GATE - Output Phase 2 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 2 COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-client-fast]
║  Visual:   [paste final line of: make test-visual]
║  Commit:   [paste: git log --oneline -1]
║  Stories:  ThisMonthActive ✓ LastMonthActive ✓ CurrentQuarterActive ✓ LastQuarterActive ✓ ThisYearActive ✓ LastYearActive ✓ AllTimeActive ✓ Interactive ✓
║  Blockers: none / [deferred item]
╚══════════════════════════════════════════════════════════════╝
```

---

## Phase 3 — GenusSelector

> Creates the genus multi-select component. After this phase the user can select genera and
> see `MarketHealthSection` re-render with the filtered payload.

### Spec-vs-mock review gate (mandatory before writing code)

Before writing any Phase 3 code, confirm:

- [ ] The spec §6 DOM structure decision (Svelte `$state` boolean, not `<details>`) is still the
  correct approach relative to the mock's behaviour.
- [ ] The `onSelectionChange` callback signature `(genera: string[], isAll: boolean) => void` is
  compatible with how `HistoryInsightsRoot` will consume it.
- [ ] The suggestion list filtering approach (case-insensitive substring match, no cap) is
  acceptable for a dataset of ~70 genera.

### Tasks

- [ ] **P3-1** Define the lifestyle preset config constant. Place it in
  `client/src/history-page/GenusSelector.svelte` as a module-level `const` (not exported):

  ```typescript
  const LIFESTYLE_PRESETS = {
    arboreal: ['Avicularia', 'Caribena', 'Psalmopoeus', 'Poecilotheria', 'Tapinauchenius', 'Ybyrapora', 'Iridopelma'],
    terrestrial: ['Grammostola', 'Aphonopelma', 'Brachypelma', 'Tliltocatl', 'Nhandu', 'Chromatopelma', 'Euathlus'],
    fossorial: ['Chilobrachys', 'Cyriopagopus', 'Haplocosmia', 'Pelinobius', 'Ceratogyrus', 'Idiothele'],
  } as const;
  ```

  These lists are filtered at runtime against `availableGenera` so phantom genera (not in the
  real dataset) are silently excluded.

- [ ] **P3-2** Create `client/src/history-page/GenusSelector.svelte`.

  **Props interface:**
  ```typescript
  interface Props {
    availableGenera: string[];
    selectedGenera: string[];
    isAllSelected: boolean;
    onSelectionChange: (genera: string[], isAll: boolean) => void;
  }
  ```

  **Internal state:**
  ```typescript
  let expanded: boolean = $state(false);
  let search: string = $state('');
  ```

  **Derived values:**
  ```typescript
  const availableCount = $derived(availableGenera.length);
  const selectedCount = $derived(selectedGenera.length);
  const countLabel = $derived(
    isAllSelected
      ? `All genera • ${availableCount} available`
      : `${selectedCount} of ${availableCount} genera selected`
  );
  const filteredSuggestions = $derived(
    search.trim() === ''
      ? availableGenera
      : availableGenera.filter(g => g.toLowerCase().includes(search.toLowerCase()))
  );
  ```

  **Handler functions (inside `<script>`):**
  - `toggleGenus(genus)` — adds or removes from `selectedGenera`; if removing last genus, calls `selectAll()`
  - `selectAll()` — calls `onSelectionChange([], true)`; sets `expanded = false`
  - `clearAll()` — calls `selectAll()`
  - `applyPreset(key: keyof typeof LIFESTYLE_PRESETS)` — filters preset against `availableGenera`; calls `onSelectionChange(filtered, false)`
  - `applyMostObserved()` — emits a selection of up to 12 genera; the root computes the actual top-12 and passes it back via props. This handler calls `onSelectionChange('__most-observed__' signal)` — **wait**: the root owns rawData; the root must compute the top-12 list and pass it as a prop. See data contract note below.

  **Most-observed implementation note:** `GenusSelector` does not have access to `rawData`
  and should not. Two options:
  
  - **Option A (recommended):** Pass `mostObservedGenera: string[]` as an additional prop from
    `HistoryInsightsRoot` (pre-computed from rawData). The `applyMostObserved()` handler calls
    `onSelectionChange(mostObservedGenera, false)`.
  - **Option B:** Pass an `onMostObservedPick` callback from the root, called by the component.

  Use **Option A**. Add `mostObservedGenera: string[]` to the `GenusSelector` props interface.

  **DOM structure:** Follow spec §6 exactly, including `aria-expanded`, `aria-controls`,
  `role="combobox"`, `role="listbox"`, `role="option"`, and `aria-label` on chip dismiss
  buttons.

- [ ] **P3-3** Add `mostObservedGenera` derivation to `HistoryInsightsRoot.svelte`:

  ```typescript
  const mostObservedGenera = $derived(
    (() => {
      const counts = new Map<string, number>();
      for (const r of rawData.records) {
        const genus = r.scientificName.split(' ')[0];
        counts.set(genus, (counts.get(genus) ?? 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 12)
        .map(([g]) => g);
    })()
  );
  ```

- [ ] **P3-4** Write `client/src/history-page/GenusSelector.test.ts`.

  Tests must cover the full state machine per spec §8.2. Key assertions:

  - All-mode: count label shows "All genera • N available"; collapsed note visible; no chips
  - Toggle button: clicking sets `expanded = true`; `aria-expanded` attribute updates
  - Suggestion row click (unselected genus): `onSelectionChange` called with genus added, `isAll = false`
  - Suggestion row click (selected genus): genus removed; if last → `onSelectionChange([], true)`
  - Chip dismiss: same as above
  - "All" quick-pick: `onSelectionChange([], true)` fired
  - Lifestyle preset: `onSelectionChange` called with filtered preset list
  - "Clear all": equivalent to "All"
  - "Most observed": `onSelectionChange(mostObservedGenera, false)`
  - Search: `filteredSuggestions` updates correctly; empty search restores full list
  - Narrow mode: chip row visible; collapsed note hidden

  Use `vi.fn()` for `onSelectionChange`. `await fireEvent.click(...)` for all interactions.

- [ ] **P3-5** Write `client/src/history-page/GenusSelector.visual.test.ts`.

  Visual contracts:
  - `.chip.selected` `backgroundColor` resolves to `rgba(204, 107, 73, 0.14)` computed
  - `.chip.selected` `borderColor` resolves to the expected rgba value
  - `.scope-label` `backgroundColor` is the teal rgba
  - Toggle button `aria-expanded` attribute is `"false"` on mount; `"true"` after click

- [ ] **P3-6** Write `client/src/history-page/GenusSelector.stories.ts`.

  Named exports:
  1. `AllMode` — `isAllSelected: true`, `selectedGenera: []`, `availableGenera: [68 genera]`
  2. `NarrowOneGenus` — `isAllSelected: false`, `selectedGenera: ['Avicularia']`
  3. `NarrowMultipleGenera` — `isAllSelected: false`, `selectedGenera: ['Avicularia', 'Caribena', 'Psalmopoeus', 'Chromatopelma']`
  4. `ExpandedWithSearch` — same props as AllMode but `initialExpanded` prop set to `true`
  5. `ExpandedWithResults` — `initialExpanded: true`, `availableGenera` with a pre-typed search showing 3 suggestions

  **Note on `initialExpanded`:** To make `expanded` state testable in Storybook, expose it
  as a prop with a default of `false`. This is acceptable for stories — it does not affect
  production use where `expanded` starts at `false`.

- [ ] **P3-7** Wire `GenusSelector` into `HistoryInsightsRoot.svelte`:
  - Import `GenusSelector`
  - Pass `availableGenera`, `selectedGenera`, `isAllSelected`, `mostObservedGenera`
  - `onSelectionChange`: `(genera, isAll) => { selectedGenera = genera; isAllSelected = isAll; }`
  - At this stage, render `GenusSelector` directly in the root (before `FiltersPanel` is built in Phase 4)

- [ ] **P3-8** Run `make test-client-fast` — confirm green.

- [ ] **P3-9** Run `make test-visual` — confirm green.

- [ ] **P3-10** Open `make storybook`. Navigate to `history-page/GenusSelector`. Verify all 5
  stories. Specifically:
  - `AllMode`: no chips visible; "All genera • N available" count label; "All" button visually active
  - `NarrowOneGenus`: one chip with dismiss button; count label shows "1 of N genera selected"
  - `NarrowMultipleGenera`: four chips; chip style is warm-orange tinted
  - `ExpandedWithSearch`: search box and suggestion list visible; quick-pick row visible
  - `ExpandedWithResults`: filtered suggestion list visible; badges show "Available"/"Selected"

- [ ] **P3-11** Run `make preview`. Verify:
  - Clicking a suggestion adds a chip; MarketHealthSection heading changes to genus-specific
  - Dismissing the last chip reverts to all-mode heading
  - Clearing all via "Clear all" reverts to all-mode
  - Arboreal preset selects the expected genera

### Acceptance criteria

- All 5 Storybook stories render correctly with the expected visual treatment
- Full state machine covered by unit tests
- `make test-client-fast` green; `make test-visual` green
- Genus selection drives `MarketHealthSection` re-render on the live preview page

### Housekeeping

```
[ ] H1 - All Phase 3 tasks checked off
[ ] H2 - Reflection scan: dismiss buttons have aria-label; toggle button text is DOM text not ::after; lifestyle presets filtered against availableGenera; mostObservedGenera is a prop, not computed inside component
[ ] H3 - Feed-forward log entry (dated)
[ ] H4 - Commit: "WP-Arch Phase 3: GenusSelector component, state machine, stories"
          Verify: git log --oneline -1
[ ] GATE - Output Phase 3 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 3 COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-client-fast]
║  Visual:   [paste final line of: make test-visual]
║  Commit:   [paste: git log --oneline -1]
║  Stories:  AllMode ✓ NarrowOneGenus ✓ NarrowMultipleGenera ✓ ExpandedWithSearch ✓ ExpandedWithResults ✓
║  Blockers: none / [deferred item]
╚══════════════════════════════════════════════════════════════╝
```

---

## Phase 4 — FiltersPanel + Full Integration

> Wraps both selectors into `FiltersPanel.svelte`, adds the global scope label, adds
> responsive layout, and runs the full test suite with coverage.

### Tasks

- [ ] **P4-1** Create `client/src/history-page/FiltersPanel.svelte`.

  **Props interface:**
  ```typescript
  interface Props {
    availableGenera: string[];
    selectedGenera: string[];
    isAllSelected: boolean;
    mostObservedGenera: string[];
    windowId: WindowId;
    basisNote: string;
    windowLabel: string;
    scopeLabel: string;
    onSelectionChange: (genera: string[], isAll: boolean) => void;
    onWindowChange: (id: WindowId) => void;
  }
  ```

  **Global scope label text derivation** (computed inside `FiltersPanel`):
  ```typescript
  const globalScopeText = $derived(
    isAllSelected
      ? `Current market scope: all genera • ${windowLabel}`
      : `Current market scope: ${scopeLabel} • ${windowLabel}`
  );
  ```

  **DOM structure:**
  ```svelte
  <aside class="filters-panel">
    <div>
      <h2 class="panel-heading">Global filters</h2>
      <p class="filter-note">Both the time window and genus selection apply to every section...</p>
    </div>
    <div class="scope-inline">
      <span class="scope-label">{globalScopeText}</span>
      <p class="filter-note">All KPIs, charts, preview rows, and CSV export reflect this scope.</p>
    </div>
    <div class="filter-group">
      <label>Genus multi-select</label>
      <GenusSelector {availableGenera} {selectedGenera} {isAllSelected} {mostObservedGenera} {onSelectionChange} />
      <p class="micro-note">Search or use shortcut groups such as lifestyle to narrow the genus list quickly.</p>
    </div>
    <div class="filter-group">
      <label>Time window</label>
      <TimeWindowSelector {windowId} {basisNote} {onWindowChange} />
    </div>
  </aside>
  ```

  **Svelte-scoped styles:**
  - `.panel-heading` — override `h2` global `margin-bottom: 20px` with `margin: 0 0 4px;`
  - `.filters-panel` — `display: grid; gap: 18px; padding: 24px; align-content: start;` plus surface/border/shadow per spec §7
  - `.filter-group` — `display: grid; gap: 10px;`
  - `.scope-inline` — `display: grid; gap: 8px;`
  - `label` within `.filter-group` — `color: var(--color-text-label); font-size: 0.86rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;`
  - `.filter-note` — `color: var(--color-text-label); font-size: 0.92rem;`
  - `.micro-note` — `color: var(--color-text-label); font-size: 0.84rem;`

  **`@media (max-width: 480px)` block (spec §11 Breakpoint 3):**

  ```css
  @media (max-width: 480px) {
    .filters-panel {
      background: none;
      border: none;
      border-radius: 0;
      box-shadow: none;
      padding: 0;
    }
    .scope-label {
      white-space: normal;
      border-radius: 12px;
    }
  }
  ```

  Do **not** add `@media (orientation: landscape) and (max-height: 500px)` — spec §11
  Breakpoint 4 explicitly states no CSS rules are required for the filter panel at that
  breakpoint.

- [ ] **P4-2** Write `client/src/history-page/FiltersPanel.test.ts`.

  Tests:
  - All-mode scope label renders as "Current market scope: all genera • Current quarter"
  - Narrow 1-genus scope label: "Current market scope: Avicularia • Last month"
  - Narrow 4-genera scope label: "Current market scope: your 4 selected genera • This year"
  - `GenusSelector` and `TimeWindowSelector` are rendered (check for presence of `.selector-shell` and `.window-row`)
  - Panel heading `<h2>` text is "Global filters"

- [ ] **P4-3** Write `client/src/history-page/FiltersPanel.visual.test.ts`.

  Visual contracts:
  - `.scope-label` computed `backgroundColor` matches `rgba(31, 122, 107, 0.12)` (or its computed rgb equivalent)
  - `.scope-label` computed `color` matches `rgb(31, 122, 107)` (= `--color-market-health`)
  - `.filters-panel` `display` is `grid`
  - `.panel-heading` `marginBottom` is `4px` (not the global 20px)
  - At mobile viewport (390 × 844): `.filters-panel` `backgroundColor` is `rgba(0, 0, 0, 0)` or empty string (card chrome stripped)
  - At mobile viewport (390 × 844): `.scope-label` `borderRadius` is `12px` (not `999px`)
  - At mobile viewport (390 × 844): `.scope-label` `whiteSpace` is `"normal"`

- [ ] **P4-4** Restructure `HistoryInsightsRoot.svelte` to use `FiltersPanel`:
  - Replace the temporary inline `GenusSelector` and `TimeWindowSelector` usage with `FiltersPanel`
  - Add the `.hero` grid layout CSS to `HistoryInsightsRoot.svelte` `<style>`:
    ```css
    .hero {
      display: grid;
      grid-template-columns: 1.35fr 0.9fr;
      gap: 24px;
      margin-bottom: 24px;
    }
    @media (max-width: 1100px) {
      .hero {
        grid-template-columns: 1fr;
      }
    }
    @media (max-width: 760px) {
      :global(.hero-panel),
      :global(.filters-panel) {
        padding: 18px;
      }
    }
    ```
  - Render a minimal hero panel (left column) with static intro copy:
    ```svelte
    <div class="hero-panel">
      <h1 class="hero-heading">Understand market conditions for the genera you care about.</h1>
      <p class="hero-copy">Use the filters to narrow the time window and genus scope. Every section on this page reflects the same selection.</p>
    </div>
    ```
  - Render `FiltersPanel` (right column) with all required props

- [ ] **P4-5** Run `make test-client` (with coverage, not just `test-client-fast`). Confirm:
  - All tests pass
  - Coverage thresholds met (branches 85%, functions 90%, lines 95%, statements 95%)
  - If any threshold is violated, add tests before proceeding

- [ ] **P4-6** Run `make test-visual` — confirm all visual contracts pass.

- [ ] **P4-7** Open `make storybook`. Verify `FiltersPanel` in both all-mode and narrow-mode
  (you may add a `FiltersPanel.stories.ts` if useful, or verify composition via the integrated
  preview). At minimum confirm:
  - Global scope label renders with teal pill styling in all-mode
  - Scope label updates to show genus names in narrow-mode
  - Two filter groups (Genus multi-select, Time window) both render

- [ ] **P4-8** Run `make preview`. Verify the full filters panel layout at
  `http://localhost:8000/history-insights.html`:
  - Two-column hero layout visible at desktop width
  - Filters panel on the right with genus and window selectors
  - Selecting genera changes the scope label and MarketHealthSection heading
  - Changing the window updates the basis note and MarketHealthSection content
  - Collapse to single column at viewport width < 1100px
  - **Mobile portrait (390 × 844):** Use DevTools to emulate 390 px width. Verify:
    - `.filters-panel` card chrome is stripped (no visible border or background card)
    - All 7 window pills wrap across multiple rows (pills do not overflow horizontally)
    - 6 quick-pick buttons wrap across multiple rows
    - Scope label text wraps within its badge (no horizontal overflow; border-radius is not pill-shaped)
  - **Phone landscape (844 × 390):** Use DevTools to emulate 844 × 390. Verify:
    - Single-column layout active (hero grid collapsed at 1100 px)
    - Window pills remain on a single row (7 pills fit at ~800 px inner width)
    - Filter panel card chrome is still visible (chrome is retained at landscape widths)
    - No horizontal overflow anywhere in the filter panel

### Acceptance criteria

- Full filter panel renders with correct layout, styling, and copy
- Scope label updates reactively on genus and window changes
- Responsive layout collapses correctly at 1100px
- `make test-client` passes with coverage thresholds met
- `make test-visual` passes

### Housekeeping

```
[ ] H1 - All Phase 4 tasks checked off
[ ] H2 - Reflection scan: global h2 margin-bottom override confirmed; no Layer 2 CSS bleed into islands; all token references valid; FilterPanel has no state of its own
[ ] H3 - Feed-forward log entry (dated)
[ ] H4 - Commit: "WP-Arch Phase 4: FiltersPanel integration, responsive layout, coverage gate"
          Verify: git log --oneline -1
[ ] GATE - Output Phase 4 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 4 COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-client]
║  Visual:   [paste final line of: make test-visual]
║  Commit:   [paste: git log --oneline -1]
║  Stories:  [FiltersPanel AllMode → verified] [FiltersPanel NarrowMode → verified]
║  Blockers: none / [deferred item]
╚══════════════════════════════════════════════════════════════╝
```

---

## Phase 5 — Live Verification and E2E

> Runs the complete verification harness: live preview inspection, side-by-side mock
> comparison, E2E tests, and divergence log finalization.

### Spec-vs-mock review gate (mandatory before E2E authoring)

Before writing E2E tests, do one final check:

- [ ] Read spec §8 (state machine) and §7 (visual contracts) against the live integrated page
- [ ] Confirm no new visual divergences appeared during Phase 4 integration that were not
  already classified in the divergence log
- [ ] If any new divergence exists: classify it (fixed/by-design/deferred) before writing tests

### Tasks

- [ ] **P5-1** Run `make preview`. Navigate to `http://localhost:8000/history-insights.html`.
  Perform the following manual verification checklist:

  **Layout:**
  - [ ] Two-column hero grid visible at full width
  - [ ] Filters panel is on the right; intro text on the left
  - [ ] Filters panel has correct surface background, warm border, rounded corners

  **All-mode (default state):**
  - [ ] Scope label shows "Current market scope: all genera • Current quarter"
  - [ ] Selector count label shows "All genera • N available"
  - [ ] Collapsed note visible below header
  - [ ] "All" quick-pick button is visually active (dark background) — requires expanding first
  - [ ] MarketHealthSection heading: "Is the wider tarantula market growing, becoming harder to source, or levelling off?"

  **Genus selection (narrow mode):**
  - [ ] Expand the selector; click a genus suggestion
  - [ ] Chip appears with warm-orange tint and `×` dismiss button
  - [ ] Scope label updates to show the genus name
  - [ ] MarketHealthSection heading changes to genus-specific phrasing
  - [ ] Dismiss the chip → reverts to all-mode

  **Time window:**
  - [ ] Click "This month" → basis note updates to dynamic in-progress text
  - [ ] Click "All time" → basis note shows "Comparison basis: structural context only..."
  - [ ] MarketHealthSection re-renders (heading and KPI values update)

  **Responsive:**
  - [ ] Resize to < 1100px → filters panel stacks below hero panel

- [ ] **P5-2** Side-by-side mock comparison. Open the mock in one browser tab, the integrated
  preview in another. Verify visual parity for:
  - All-mode state (scope label, collapsed note, window pills)
  - Narrow-mode state (chips row, count label, window pills)
  - Expanded state (search box, suggestion list, quick-pick row)
  - Any visual differences: classify as `fixed`, `by-design` (already in divergence log), or
    `deferred` (document new entry if found)

- [ ] **P5-3** Write E2E tests in `tests/e2e/test_history_insights_filters.py`.

  **Test 1 — Genus selection triggers MarketHealthSection update:**
  - Navigate to `http://localhost:8000/history-insights.html`
  - Verify initial heading contains "wider tarantula market"
  - Expand the genus selector
  - Click the suggestion row for "Avicularia"
  - Verify a chip for "Avicularia" appears in `.chips`
  - Verify the MarketHealthSection heading contains "Avicularia"

  **Test 2 — Window change updates basis note:**
  - Navigate to `http://localhost:8000/history-insights.html`
  - Note current basis note text
  - Click the "All time" window button
  - Verify the basis note text contains "structural context only"
  - Verify "All time" button has `aria-pressed="true"`

  **Test 3 — All-mode → narrow → clear all:**
  - Navigate to the page
  - Expand the selector
  - Select two genera (e.g. Avicularia and Caribena)
  - Verify scope label shows "your 2 selected genera" or the two genus names
  - Click "Clear all" quick-pick
  - Verify scope label reverts to "all genera"
  - Verify no chips are visible

  **Test 4 — Lifestyle preset (arboreal):**
  - Navigate to the page; expand the selector
  - Click "Arboreal" quick-pick
  - Verify the selector count label shows "N of M genera selected"
  - Verify at least "Avicularia" chip is present (it is always in the arboreal preset)

  Use `make test-e2e-file FILE=tests/e2e/test_history_insights_filters.py` to run the new
  file in isolation before adding to the full suite.

- [ ] **P5-4** Run `make test-e2e` — full E2E suite must pass.

- [ ] **P5-5** Finalize the divergence log at the bottom of this file. Every entry must have a
  classification (`fixed`, `by-design`, or `deferred`). No entry may be left as `pending`.

- [ ] **P5-6** Confirm all CSS token references in new components resolve correctly. Use
  Chrome DevTools MCP `evaluate_script` if any visual discrepancy is visible:

  ```javascript
  // Check --color-breeder-focus resolves
  getComputedStyle(document.documentElement).getPropertyValue('--color-breeder-focus').trim()
  // Expected: " #cc6b49" (with leading space is normal)

  // Check chip.selected background on a selected chip
  const chip = document.querySelector('.chip.selected');
  getComputedStyle(chip).backgroundColor;
  // Expected: rgba(204, 107, 73, 0.14) or equivalent
  ```

### Acceptance criteria

- All manual verification checklist items pass
- Mock vs integrated side-by-side comparison complete; all divergences classified
- E2E tests pass (`make test-e2e`)
- Divergence log finalized with no pending entries
- All CSS tokens verified as resolving correctly in the browser

### Housekeeping

```
[ ] H1 - All Phase 5 tasks checked off
[ ] H2 - Reflection scan: E2E tests use page-object helpers per existing pattern; no hardcoded waits; divergence log fully classified
[ ] H3 - Feed-forward log entry (dated)
[ ] H4 - Commit: "WP-Arch Phase 5: E2E tests, live verification, divergence log finalized"
          Verify: git log --oneline -1
[ ] GATE - Output Phase 5 completion block
```

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 5 COMPLETE — WP-ARCH DONE                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-e2e]
║  Commit:   [paste: git log --oneline -1]
║  Stories:  [all stories verified ✓]
║  Blockers: none / [deferred items for WP2]
╚══════════════════════════════════════════════════════════════╝
```

---

## Files Reference

### New files

| File | Phase |
|---|---|
| `client/src/history-page/HistoryInsightsRoot.svelte` | 1 |
| `client/src/history-page/HistoryInsightsRoot.test.ts` | 1 |
| `client/src/history-page/HistoryInsightsRoot.visual.test.ts` | 1 |
| `client/src/history-page/TimeWindowSelector.svelte` | 2 |
| `client/src/history-page/TimeWindowSelector.test.ts` | 2 |
| `client/src/history-page/TimeWindowSelector.visual.test.ts` | 2 |
| `client/src/history-page/TimeWindowSelector.stories.ts` | 2 |
| `client/src/history-page/GenusSelector.svelte` | 3 |
| `client/src/history-page/GenusSelector.test.ts` | 3 |
| `client/src/history-page/GenusSelector.visual.test.ts` | 3 |
| `client/src/history-page/GenusSelector.stories.ts` | 3 |
| `client/src/history-page/FiltersPanel.svelte` | 4 |
| `client/src/history-page/FiltersPanel.test.ts` | 4 |
| `client/src/history-page/FiltersPanel.visual.test.ts` | 4 |
| `tests/e2e/test_history_insights_filters.py` | 5 |

### Modified files

| File | Change | Phase |
|---|---|---|
| `templates/common.css` | Add `--color-breeder-focus: #cc6b49` to `:root` | 1 |
| `templates/history_insights_page.html` | `#market-health-root` → `#history-insights-root` | 1 |
| `client/src/history-page/index.ts` | Mount `HistoryInsightsRoot` instead of `MarketHealthSection` | 1 |

---

## Divergence Log

*Initialized in Phase 0. Updated as findings occur. Finalized in Phase 5.*

| # | Element | Mock behaviour | Implementation | Classification | Phase |
|---|---|---|---|---|---|
| 1 | Genus selector shell | Native `<details>` hides chips when closed | Svelte `$state` boolean; chips always visible in narrow mode | by-design | P0 |
| 2 | `--color-breeder-focus` token | Mock-local `--accent-2` variable | Repo token `--color-breeder-focus: #cc6b49` added in Phase 1 | by-design | P0 |
| 3 | "Most observed" preset | Hardcoded list of 12 specific genera | Derived from rawData at runtime (top 12 by occurrence) | by-design | P0 |
| 4 | Hero panel copy | "Three ways to assess the market before backing a genus." (prototype scaffolding) | Minimal static intro copy | by-design | P0 |
| 5 | Lifestyle preset lists | Static lists; may include genera not in real dataset | Hardcoded lists filtered at runtime against `availableGenera` | by-design | P0 |
| 6 | Selector toggle text | CSS `::after content: "Show genus selector"` | Actual button text in DOM | by-design | P0 |
| 7 | `.filters-panel` border-radius | `20px` (mock `--radius: 20px` token) | `18px` (WP1 card precedent; no 18px token) | by-design | P0 |

---

## Feed-Forward Log

*Add a dated entry after every phase. Even if nothing changed, write "no new findings".*

| Date | Phase | Notes |
|---|---|---|
| 8 May 2026 | 0 | All 11 computed-style rows captured via Chrome DevTools MCP. All spec §7 values match mock. Only `.filters-panel border-radius` differs (20px mock vs 18px implementation) — by-design deviation #7, already logged. `--color-breeder-focus` confirmed missing from `common.css` — add in Phase 1. Naked `h2 { margin-bottom: 20px }` in common.css confirmed — Phase 1/4 must add `.panel-heading { margin: 0 0 4px }` scoped override in FiltersPanel.svelte. No naked button/input/label/details/summary selectors found. `make storybook` command confirmed (`cd client && npm run storybook`, port 6006). Divergence log pre-populated with all 7 by-design deviations from spec §12 — no additional deviations found. |
| _(add here)_ | 1 | |
| _(add here)_ | 2 | |
| _(add here)_ | 3 | |
| _(add here)_ | 4 | |
| _(add here)_ | 5 | |
