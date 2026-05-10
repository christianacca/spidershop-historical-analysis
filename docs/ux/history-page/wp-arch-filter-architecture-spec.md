# WP-Arch — Filter Architecture: Functional / UX Handoff Spec

**Work package:** WP-Arch  
**Page:** History Insights (`history-insights.html`)  
**Date:** 8 May 2026  
**Status:** Ready for implementation  
**Blocks:** WP2 (Breeder Opportunity KPIs)

---

## §1 Purpose and Scope

WP-Arch delivers the global filter panel for the History Insights page. The filter panel owns
two interactive controls — the **genus multi-select** and the **time window selector** — that
apply to every section on the page. When the user changes either control, the client-side
engine is called reactively, the derived `MarketHealthPayload` is updated, and the
`MarketHealthSection` re-renders with the new data.

WP-Arch also performs the structural pivot from the current single-component mount (index.ts →
`MarketHealthSection`) to a single root-component architecture (`HistoryInsightsRoot.svelte`)
that will host WP2, WP3, and WP4 sections once those work packages are delivered.

**In scope:**

1. Global genus multi-select panel — collapsible shell, search input, suggestion list, selected-genus chip display, quick-pick group buttons (All, Most observed, Arboreal, Terrestrial, Fossorial, Clear all).
2. Time window selector panel — 7 pill buttons (`this-month` through `all-time`) plus the dynamic `windowBasisNote` text displayed below.
3. Global scope label — reflects current genus scope and active window label.
4. Reactive wiring — on any genus or window change, call `buildMarketHealthPayload(rawData, windowId, { selectedGenera, isAllSelected })` and propagate the updated `MarketHealthPayload` to `MarketHealthSection`.
5. Root component restructure — introduce `HistoryInsightsRoot.svelte` to own `selectedGenera`, `isAllSelected`, and `windowId` reactive state, distributing them downstream. This is the structural unblocking step required by WP2.
6. Updated `index.ts` mount logic and updated `templates/history_insights_page.html` mount point.
7. Storybook stories for `GenusSelector` and `TimeWindowSelector` components.

---

## §2 Explicit Out of Scope

- Breeder Opportunity KPIs (WP2), Comparison Controls (WP2), Bias Control KPIs (WP3), Filtered Data Preview (WP4).
- Replacing `history.html` with `history-insights.html` as the canonical deployed page.
- Python-side generator changes of any kind.
- Species-level filtering — genus-level only.
- The `.comparison-panel` and `#breeder-section` elements — those belong to WP2.
- The "Most observed" preset content itself (defined by rawData-derived genus frequency; the preset UI control is in scope but its content computation belongs to the root component).

---

## §3 Page Layout

### Hero section structure

The filters panel is the right panel inside a two-column hero grid:

```
.hero {
  display: grid;
  grid-template-columns: 1.35fr 0.9fr;
  gap: 24px;
  margin-bottom: 24px;
}

.hero-panel   ←  left  (static intro copy; not prototype scaffolding)
.filters-panel  ←  right (this work package)
```

The hero panel (left) contains static introductory copy for the page. It is **not** the
"Three ways to assess the market" prototype scaffolding from the mock — that text is mock
context and is explicitly not production UI (see §12, deviation #4).

The filters panel (right) layout:

```
.filters-panel {
  display: grid;
  gap: 18px;
  padding: 24px;
  align-content: start;
}
```

**Internal stacking order (top to bottom):**
1. Panel heading: `<h2>Global filters</h2>` + filter-note paragraph
2. Global scope label (`.scope-inline`)
3. Genus multi-select filter group
4. Time window filter group

### Responsive collapse

At `@media (max-width: 1100px)`:
- The hero `.hero` grid collapses to `grid-template-columns: 1fr`
- The filters panel stacks below the hero panel

At `@media (max-width: 760px)`:
- Padding on `.hero-panel` and `.filters-panel` reduces to `18px`

---

## §4 Copy Contracts

### §4.1 Global scope label (`#global-scope-label`)

The global scope label is a teal pill badge rendered inside `.scope-inline` immediately below
the filters panel heading. It summarises the currently active data scope in one line.

| State | Text |
|---|---|
| All-mode (default) | `Current market scope: all genera • {windowLabel}` |
| Narrow, 1 genus | `Current market scope: {genus} • {windowLabel}` |
| Narrow, 2 genera | `Current market scope: {genusA} and {genusB} • {windowLabel}` |
| Narrow, 3 genera | `Current market scope: {genusA}, {genusB} and {genusC} • {windowLabel}` |
| Narrow, ≥4 genera | `Current market scope: your {N} selected genera • {windowLabel}` |

The text after the bullet `•` is always the `windowLabel` from the current payload
(e.g. "Current quarter", "This month", "All time"). The scope prefix text before `•` is
derived from `payload.scopeLabel` (empty string in all-mode; the engine already builds
the correct `scopeLabel` value).

Below the badge: `<p class="filter-note">All KPIs, charts, preview rows, and CSV export reflect this scope.</p>`

### §4.2 Selector count label (`#selector-count-label`)

Displayed inside the selector header as a `.scope-label` badge.

| State | Text |
|---|---|
| All-mode | `All genera • {availableCount} available` |
| Narrow mode | `{selectedCount} of {availableCount} genera selected` |

`availableCount` is derived from `rawData` — the count of distinct genera appearing in any
run record. It is a static value for the lifetime of the page. `selectedCount` is
`selectedGenera.length`.

### §4.3 Collapsed note (`#collapsed-selector-note`)

Displayed inside the `.collapsed-shell` below the chips row. Visible only when no chips are
present (all-mode) and the selector is collapsed.

| State | Text |
|---|---|
| All-mode, collapsed | `All genera are in scope for Market Health KPIs. Select specific genera to narrow the focus and unlock comparison controls.` |
| Narrow mode | *(not shown — chips are visible instead)* |

When the selector is expanded, this note is hidden regardless of mode.

### §4.4 Window basis note (`#time-window-basis-note`)

Rendered as a `.micro-note` paragraph below the time window pill buttons. The text is sourced
directly from `payload.windowBasisNote` — the engine already computes the correct string for
all seven windows.

| `windowId` | Note type | Example / pattern |
|---|---|---|
| `this-month` | Dynamic (in-progress) | `Month in progress (May 2026) — comparing May 1 – May 8 against the same span last month (Apr 1 – Apr 8).` |
| `last-month` | Static | `Comparison basis: last full month vs prior full month.` |
| `current-quarter` | Dynamic (in-progress) | `Quarter in progress (Q2 2026) — comparing Apr 1 – May 8 against the same span into Q1 (Jan 1 – Feb 7).` |
| `last-quarter` | Static | `Comparison basis: last full quarter vs prior full quarter.` |
| `this-year` | Dynamic (in-progress) | `Year in progress (2026) — comparing Jan 1 – May 8 against the same span in 2025.` |
| `last-year` | Static | `Comparison basis: last full year vs year before.` |
| `all-time` | Static | `Comparison basis: structural context only, with no prior-period delta.` |

**Implementation note:** Do not hardcode these strings in the filter panel. Render
`payload.windowBasisNote` directly. Empty strings are expected for completed windows where the
basis is self-evident from the window label — the engine returns an appropriate string for all
seven windows.

### §4.5 Chip label and dismiss affordance

Each chip in the `.chips` row:
- Label: the genus name (e.g. `Avicularia`)
- Dismiss button: a `×` character rendered as a `<button>` with `class="dismiss"` inside the chip
- `aria-label` on the dismiss button: `Remove {genus}` (e.g. `Remove Avicularia`)
- The outer chip element is a `<span>`, not a button; only the dismiss button is interactive

### §4.6 Quick-pick group labels

The quick-pick row contains five preset buttons and one action button:

| Element | Class | Label | Behaviour |
|---|---|---|---|
| All | `.quick-pick` | `All` | Sets all-mode (isAllSelected=true, selectedGenera=[]) |
| Most observed | `.quick-pick` | `Most observed` | Selects top 12 genera by occurrence count in rawData |
| Arboreal | `.quick-pick` | `Arboreal` | Applies arboreal preset list (filtered against availableGenera) |
| Terrestrial | `.quick-pick` | `Terrestrial` | Applies terrestrial preset list (filtered against availableGenera) |
| Fossorial | `.quick-pick` | `Fossorial` | Applies fossorial preset list (filtered against availableGenera) |
| Clear all | `.quick-pick-action` | `Clear all` | Clears selection → reverts to all-mode |

The `All` button carries the `.active` modifier when `isAllSelected` is true. Preset buttons
(Most observed, Arboreal, Terrestrial, Fossorial) do not carry `.active` in WP-Arch — active
state for presets is deferred to WP2+ as it requires cross-component coordination.

Below the selector shell: `<p class="micro-note">Search or use shortcut groups such as lifestyle to narrow the genus list quickly.</p>`

### §4.7 Suggestion row status badge

Each suggestion row in the list has a status badge:

| State | Class | Text |
|---|---|---|
| Not selected | `.suggestion-status` (no modifier) | `Available` |
| Already selected | `.suggestion-status.selected` | `Selected` |

The badge text reflects whether the genus is currently in `selectedGenera`. Clicking a row
with `Available` adds it; clicking a row with `Selected` removes it (toggle behaviour).

---

## §5 Component Inventory

Four new Svelte components are introduced. No existing shared components are reused for the
filter panel itself (rationale below).

### `HistoryInsightsRoot.svelte`

**Location:** `client/src/history-page/HistoryInsightsRoot.svelte`  
**Role:** Single root component. Owns all global reactive state and orchestrates the page
sections. Reads `rawData` from `window.marketHealthRawData` (injected by Python into the
template). This is the M2 mount strategy — one `mount()` call in `index.ts`.

**Reactive state:**
```typescript
let selectedGenera: string[] = $state([]);
let isAllSelected: boolean = $state(true);
let windowId: WindowId = $state('current-quarter');
```

**Derived values:**
```typescript
let payload = $derived(
  buildMarketHealthPayload(rawData, windowId, { selectedGenera, isAllSelected })
);
let availableGenera = $derived(
  [...new Set(rawData.records.map(r => r.scientificName.split(' ')[0]))].sort()
);
```

**Renders:** `FiltersPanel` + `MarketHealthSection` (and eventually WP2/3/4 sections).

**Why M2 over M1:** WP2, WP3, and WP4 all need the same `selectedGenera`, `windowId`, and
`focusGenus` shared state. A single root component distributes that state cleanly via props
and callback props, without `index.ts` becoming a state coordination layer. M1 (multiple
`mount()` calls) would require passing shared mutable state through `index.ts` as closure
variables — less maintainable as sections grow.

### `FiltersPanel.svelte`

**Location:** `client/src/history-page/FiltersPanel.svelte`  
**Role:** Thin wrapper that renders the panel heading, global scope label, `GenusSelector`,
and `TimeWindowSelector` inside the `.filters-panel` grid layout. Owns no reactive state —
all values are received as props and all mutations are forwarded via callback props.

**Props:**
```typescript
interface Props {
  availableGenera: string[];
  selectedGenera: string[];
  isAllSelected: boolean;
  windowId: WindowId;
  basisNote: string;       // payload.windowBasisNote
  windowLabel: string;     // payload.windowLabel
  scopeLabel: string;      // payload.scopeLabel
  onSelectionChange: (genera: string[], isAll: boolean) => void;
  onWindowChange: (id: WindowId) => void;
}
```

### `GenusSelector.svelte`

**Location:** `client/src/history-page/GenusSelector.svelte`  
**Role:** Renders the genus multi-select UI: collapsible shell, search box, suggestion list,
chips row, quick-pick buttons. Manages its own `expanded` and `search` UI state; emits genus
selection changes via `onSelectionChange`.

**Props:**
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

**Does NOT reuse `client/src/shared/components/SearchInput.svelte`** — that component carries
a `tableId` prop and is wired to the table-filter architecture (it emits values via a
`data-action="search"` attribute consumed by the shared `bootstrapSortableTablePage` function).
The genus search is a simpler standalone `<input>` that updates the internal `search` state.

### `TimeWindowSelector.svelte`

**Location:** `client/src/history-page/TimeWindowSelector.svelte`  
**Role:** Renders 7 window pill buttons and the basis note below them. Owns no state — the
active window is controlled by the parent.

**Props:**
```typescript
interface Props {
  windowId: WindowId;
  basisNote: string;
  onWindowChange: (id: WindowId) => void;
}
```

---

## §6 DOM Structure Decisions

### Genus selector: Svelte `$state` boolean instead of native `<details>`

**Decision:** Use a Svelte `$state` boolean (`expanded`) to control whether the suggestion
area is visible. The toggle is a `<button>` element that flips `expanded`. Do **not** use a
native `<details>` / `<summary>` element.

**Rationale:** The mock uses `<details>`, which hides **all children** (including the chips
row) when closed. The required behaviour (per §3 of the original brief) is:
- **Collapsed** (default): chips visible; search/suggestions/quick-picks hidden
- **Expanded**: all content visible

A native `<details>` collapses all descendant content, making chips invisible when the
selector is collapsed. Svelte's conditional rendering (`{#if expanded}`) applied only to the
`.expanded-preview` block solves this: chips live outside the conditional and are always
rendered when `isAllSelected` is false.

**Resulting DOM structure:**

```svelte
<div class="selector-shell">
  <div class="selector-header">
    <div class="selector-title">
      <span class="scope-label">{countLabel}</span>
      <span class="selector-meta">Selected genera stay visible here...</span>
    </div>
    <button
      class="selector-toggle"
      aria-expanded={expanded}
      aria-controls="genus-expanded-content"
      onclick={() => (expanded = !expanded)}
    >
      <span class="toggle-icon" class:rotated={expanded}>▶</span>
      {expanded ? 'Hide genus selector' : 'Show genus selector'}
    </button>
  </div>

  <!-- Chips: always rendered in narrow mode -->
  {#if !isAllSelected}
    <div class="chips">
      {#each selectedGenera as genus}
        <span class="chip selected">
          {genus}
          <button class="dismiss" aria-label="Remove {genus}" onclick={() => removeGenus(genus)}>×</button>
        </span>
      {/each}
    </div>
  {:else if !expanded}
    <p class="collapsed-note">{collapsedNote}</p>
  {/if}

  <!-- Expanded content: conditional on expanded boolean -->
  {#if expanded}
    <div class="expanded-preview" id="genus-expanded-content">
      <strong>Selector contents</strong>
      <div class="search-shell">
        <div class="search-box">
          <span class="search-icon" aria-hidden="true">🔍</span>
          <input
            class="search-input"
            type="text"
            aria-label="Search genus"
            role="combobox"
            aria-expanded={filteredSuggestions.length > 0}
            aria-controls="genus-suggestion-list"
            bind:value={search}
          />
        </div>
        <div class="suggestion-list" id="genus-suggestion-list" role="listbox">
          {#each filteredSuggestions as genus}
            <button
              class="suggestion-row"
              role="option"
              aria-selected={selectedGenera.includes(genus)}
              onclick={() => toggleGenus(genus)}
            >
              <strong>{genus}</strong>
              <span class="suggestion-status" class:selected={selectedGenera.includes(genus)}>
                {selectedGenera.includes(genus) ? 'Selected' : 'Available'}
              </span>
            </button>
          {/each}
        </div>
      </div>
      <div class="quick-pick-row">
        <button class="quick-pick" class:active={isAllSelected} onclick={selectAll}>All</button>
        <button class="quick-pick" onclick={applyMostObserved}>Most observed</button>
        <button class="quick-pick" onclick={() => applyPreset('arboreal')}>Arboreal</button>
        <button class="quick-pick" onclick={() => applyPreset('terrestrial')}>Terrestrial</button>
        <button class="quick-pick" onclick={() => applyPreset('fossorial')}>Fossorial</button>
        <button class="quick-pick-action" onclick={clearAll}>Clear all</button>
      </div>
    </div>
  {/if}
</div>
```

---

## §7 Visual Contract for Key Elements

All values below are sourced from mock CSS source + repo token mapping. These are the ground
truth for implementation and visual contract tests.

| Element | Property | Value | Source |
|---|---|---|---|
| `.filters-panel` | `display` | `grid` | mock CSS |
| `.filters-panel` | `gap` | `18px` | mock CSS |
| `.filters-panel` | `padding` | `24px` | mock CSS |
| `.filters-panel` | `background` | `rgba(255, 253, 248, 0.92)` | mock CSS |
| `.filters-panel` | `border` | `1px solid rgba(215, 207, 192, 0.95)` | mock CSS |
| `.filters-panel` | `border-radius` | `18px` | implementation choice (mock: 20px; WP1 card precedent: 18px — see §12 deviation #7) |
| `.selector-shell` | `display` | `grid` | mock CSS |
| `.selector-shell` | `gap` | `12px` | mock CSS |
| `.selector-shell` | `padding` | `12px` | mock CSS |
| `.selector-shell` | `border` | `1px solid var(--color-border-warm)` | mock `--line` → repo `--color-border-warm` |
| `.selector-shell` | `border-radius` | `18px` | hardcoded (no token; WP1 precedent) |
| `.selector-shell` | `background` | `rgba(255, 255, 255, 0.72)` | mock CSS |
| `.chip` (unselected/all-mode) | `padding` | `9px 12px` | mock CSS |
| `.chip` (unselected/all-mode) | `border-radius` | `999px` | mock CSS |
| `.chip` (unselected/all-mode) | `border` | `1px solid var(--color-border-warm)` | mock `--line` |
| `.chip` (unselected/all-mode) | `background` | `#fff` | mock CSS |
| `.chip` (unselected/all-mode) | `color` | `var(--color-text)` | mock `--ink` |
| `.chip` (unselected/all-mode) | `font-size` | `0.92rem` | mock CSS |
| `.chip.selected` | `background` | `rgba(204, 107, 73, 0.14)` | mock CSS; token `--color-breeder-focus` at 14% opacity |
| `.chip.selected` | `border-color` | `rgba(204, 107, 73, 0.28)` | mock CSS; token at 28% opacity |
| `.chip.selected` | `font-weight` | `700` | mock CSS |
| `.chips` | `display` | `flex` | mock CSS |
| `.chips` | `gap` | `8px` | mock CSS |
| `.chips` | `flex-wrap` | `wrap` | mock CSS base style — chip row wraps at all viewports; not a breakpoint rule |
| `.window` (default) | `padding` | `9px 12px` | mock CSS |
| `.window` (default) | `border-radius` | `999px` | mock CSS |
| `.window` (default) | `border` | `1px solid var(--color-border-warm)` | mock `--line` |
| `.window` (default) | `background` | `#fff` | mock CSS |
| `.window.active` | `background` | `var(--color-text)` | mock `--ink` → repo `--color-text` |
| `.window.active` | `border-color` | `var(--color-text)` | mock CSS |
| `.window.active` | `color` | `#fff` | mock CSS |
| `.window-row` | `display` | `flex` | mock CSS |
| `.window-row` | `gap` | `8px` | mock CSS |
| `.window-row` | `flex-wrap` | `wrap` | mock CSS base style — pills wrap to the next row at any width where all 7 don't fit; not a breakpoint rule |
| `.quick-pick` (default) | `border-style` | `dashed` | mock CSS |
| `.quick-pick` (default) | `border-color` | `rgba(31, 42, 44, 0.18)` | mock CSS |
| `.quick-pick` (default) | `background` | `rgba(255, 255, 255, 0.78)` | mock CSS |
| `.quick-pick` (default) | `font-size` | `0.86rem` | mock CSS |
| `.quick-pick` (default) | `font-weight` | `700` | mock CSS |
| `.quick-pick.active` | `background` | `var(--color-text)` | mock CSS |
| `.quick-pick.active` | `border-style` | `solid` | mock CSS |
| `.quick-pick-action` (Clear all) | `border` | `1px solid rgba(31, 42, 44, 0.22)` | mock CSS |
| `.quick-pick-action` | `background` | `transparent` | mock CSS |
| `.quick-pick-action` | `color` | `var(--color-text-label)` | mock `--muted` |
| `.quick-pick-action` | `font-weight` | `400` | mock CSS |
| `.quick-pick-row` | `display` | `flex` | mock CSS |
| `.quick-pick-row` | `gap` | `8px` | mock CSS |
| `.quick-pick-row` | `flex-wrap` | `wrap` | mock CSS base style — quick-pick buttons wrap to the next row at narrow viewports; not a breakpoint rule |
| `.scope-label` | `display` | `inline-flex` | mock CSS |
| `.scope-label` | `padding` | `8px 12px` | mock CSS |
| `.scope-label` | `border-radius` | `999px` | mock CSS |
| `.scope-label` | `background` | `rgba(31, 122, 107, 0.12)` | mock CSS |
| `.scope-label` | `color` | `var(--color-market-health)` | mock `--accent` → repo `--color-market-health` |
| `.scope-label` | `font-size` | `0.86rem` | mock CSS |
| `.scope-label` | `font-weight` | `700` | mock CSS |
| `.scope-label` | `white-space` | `nowrap` | mock CSS — overridden to `normal` at `@media (max-width: 480px)` when pill text would overflow (see §11 Breakpoint 3) |
| `.search-box` | `display` | `flex` | mock CSS |
| `.search-box` | `padding` | `12px 14px` | mock CSS |
| `.search-box` | `border-radius` | `16px` | mock CSS |
| `.search-box` | `border` | `1px solid var(--color-border-warm)` | mock `--line` |
| `.search-box` | `background` | `#fff` | mock CSS |
| `.suggestion-list` | `border-radius` | `16px` | mock CSS |
| `.suggestion-list` | `background` | `rgba(255, 255, 255, 0.84)` | mock CSS |
| `.suggestion-row` | `padding` | `8px 10px` | mock CSS |
| `.suggestion-row` | `border-radius` | `12px` | mock CSS |
| `.suggestion-row` | `background` | `rgba(247, 242, 232, 0.7)` | mock CSS |
| `.suggestion-status.selected` | `background` | `rgba(204, 107, 73, 0.14)` | mock CSS |
| `.suggestion-status.selected` | `color` | `var(--color-breeder-focus)` | requires new token |

---

## §8 Interaction and State Machine

### 8.1 Genus selector — full state machine

The genus selector has two orthogonal dimensions of state:

- **Selection mode:** All-mode vs Narrow-mode
- **Panel visibility:** Collapsed vs Expanded

These combine into the following states:

| State | `isAllSelected` | `selectedGenera` | `expanded` | Visible elements |
|---|---|---|---|---|
| **1. All-mode, collapsed** (default) | `true` | `[]` | `false` | Header; collapsed note; "All" quick-pick active |
| **2. All-mode, expanded** | `true` | `[]` | `true` | Header; search box; full suggestion list; quick-pick row; "All" active |
| **3. Narrow, collapsed** | `false` | `[…]` | `false` | Header with count; chips row; no suggestion area |
| **4. Narrow, expanded** | `false` | `[…]` | `true` | Header with count; chips row; search box; suggestion list; quick-pick row |
| **5. Narrow, expanded, search active** | `false` | `[…]` | `true` | Same as 4, with suggestion list filtered to `search` text |

### 8.2 State transitions

| Action | From | To | Effect |
|---|---|---|---|
| Toggle button clicked | 1 | 2 | `expanded = true` |
| Toggle button clicked | 2 | 1 | `expanded = false` |
| Toggle button clicked | 3 | 4 | `expanded = true` |
| Toggle button clicked | 4 | 3 | `expanded = false`; `search = ''` |
| "All" quick-pick | any | 1 | `isAllSelected = true`; `selectedGenera = []`; `expanded = false` |
| Preset quick-pick (arboreal/terrestrial/fossorial) | any | 3 or 4 | `isAllSelected = false`; `selectedGenera = [preset ∩ availableGenera]`; `expanded` unchanged |
| "Most observed" quick-pick | any | 3 or 4 | `isAllSelected = false`; `selectedGenera = [top 12 genera by count]`; `expanded` unchanged |
| "Clear all" | any | 1 | `isAllSelected = true`; `selectedGenera = []`; `expanded = false` |
| Suggestion row clicked (genus not in selection) | 2 or 4 or 5 | 2 or 4 | `isAllSelected = false`; genus appended to `selectedGenera` |
| Suggestion row clicked (genus in selection) | 2 or 4 or 5 | 2 or 4 or 1 | genus removed from `selectedGenera`; if `selectedGenera` becomes `[]` → `isAllSelected = true` |
| Chip dismiss clicked | 3 or 4 | 3 or 4 or 1 | genus removed from `selectedGenera`; if last genus removed → `isAllSelected = true` |
| Search input typed | 2 or 4 | 5 | `search` updated; suggestion list filters to matches |
| Search input cleared | 5 | 2 or 4 | `search = ''`; suggestion list resets |

### 8.3 Suggestion list filtering

The suggestion list shows all `availableGenera` when `search` is empty. When `search` is
non-empty, the list shows genera whose names contain the search string (case-insensitive).
The already-selected genera appear at the top of the filtered list (or with their
`suggestion-status.selected` badge) so the user can see and de-select them easily.

Maximum suggestion list items: no cap in WP-Arch (the real genus list is ~70 items, which
fits without pagination).

### 8.4 WP2 handoff contract (forward-compatibility)

When `selectedGenera` changes, the following must hold for WP2 to function correctly:

- If a genus in `focusGenus` (WP2 state) is removed from `selectedGenera`, WP2 must clear
  `focusGenus` immediately (placeholder state shown).
- If `isAllSelected` becomes `true`, WP2 comparison controls must enter the disabled /
  broad-scope state.

WP-Arch does not implement these effects but must emit `selectedGenera` and `isAllSelected`
cleanly from `HistoryInsightsRoot` so WP2 can observe them as props.

### 8.5 Time window selector behaviour

Clicking a window pill calls `onWindowChange(windowId)`. The root updates `windowId`, which
triggers `$derived` recomputation of `payload`. `MarketHealthSection` receives the new
payload as a prop and re-renders. No animation or transition is required on window switch.

The `payload.windowBasisNote` returned by the engine is rendered directly below the pill row
as `.micro-note` text. It changes on every window switch.

---

## §9 Data Contract

### §9.1 State ownership

```
HistoryInsightsRoot.svelte
  ├── selectedGenera: string[]  ($state)
  ├── isAllSelected: boolean    ($state)
  ├── windowId: WindowId        ($state)
  ├── payload: MarketHealthPayload  ($derived via buildMarketHealthPayload)
  └── availableGenera: string[]     ($derived from rawData)
```

### §9.2 Prop flow

```
HistoryInsightsRoot
  → FiltersPanel
      → GenusSelector   (availableGenera, selectedGenera, isAllSelected, onSelectionChange)
      → TimeWindowSelector (windowId, basisNote, onWindowChange)
  → MarketHealthSection (payload)
```

### §9.3 Engine call

```typescript
// Reactive — recomputes whenever windowId, selectedGenera, or isAllSelected changes
const payload = $derived(
  buildMarketHealthPayload(rawData, windowId, {
    selectedGenera,
    isAllSelected,
  })
);
```

`buildMarketHealthPayload` is a pure function with no side effects. Calling it on every
selection change is safe and fast for the typical dataset size.

### §9.4 `rawData` injection

`rawData` is read once from `window.marketHealthRawData` in `index.ts` and passed to
`HistoryInsightsRoot` as a prop. The component does not re-read `window` directly.

```typescript
// index.ts
const rawData = (window as unknown as Record<string, unknown>)
  .marketHealthRawData as MarketHealthRawData | undefined;

mount(HistoryInsightsRoot, {
  target: historyInsightsRoot,
  props: { rawData },
});
```

### §9.5 `availableGenera` derivation

```typescript
const availableGenera = $derived(
  [...new Set(rawData.records.map(r => r.scientificName.split(' ')[0]))]
    .sort()
);
```

This is computed once in `HistoryInsightsRoot` and passed down to `GenusSelector` as a prop.
The derived value is stable for the lifetime of the page (rawData does not change).

---

## §10 Accessibility Requirements

### Genus selector toggle button

```html
<button
  aria-expanded={expanded}
  aria-controls="genus-expanded-content"
>
  {expanded ? 'Hide genus selector' : 'Show genus selector'}
</button>
```

Button text changes visibly — do **not** use CSS `content` pseudo-property for toggle text
(screen readers do not reliably announce pseudo-content).

### Search input

```html
<input
  type="text"
  aria-label="Search genus"
  role="combobox"
  aria-expanded={filteredSuggestions.length > 0}
  aria-controls="genus-suggestion-list"
/>
```

### Suggestion list

```html
<div id="genus-suggestion-list" role="listbox">
  <button role="option" aria-selected={isSelected}>…</button>
</div>
```

### Chip dismiss buttons

```html
<button class="dismiss" aria-label="Remove {genus}">×</button>
```

The `×` character alone has no accessible label. The `aria-label` must be applied on the
button, not the parent chip span.

### Window pill buttons

```html
<button
  class="window"
  class:active={windowId === id}
  aria-pressed={windowId === id}
  onclick={() => onWindowChange(id)}
>
  {label}
</button>
```

`aria-pressed` is used (not `aria-selected`) because these are toggle-like action buttons,
not members of a listbox.

### Filter group labels

Each filter group uses `<label>` as a visual heading above the control. This is not a
`<label for="...">` association (the control below is a composite widget, not a single input);
it is a visual grouping label. Consider wrapping each filter group in a `<fieldset>` with a
`<legend>` for stronger semantic grouping if desired, but this is not strictly required by
WCAG 2.1 AA for the current layout.

---

## §11 Responsive Behaviour

### Breakpoint 1: `@media (max-width: 1100px)`

The `.hero` grid collapses to a single column:

```css
.hero {
  grid-template-columns: 1fr;
}
```

The filters panel stacks below the hero panel. The filters panel retains its full width
within the single-column layout. The selector shell, chip row, and quick-pick row all wrap
naturally within the narrower container.

### Breakpoint 2: `@media (max-width: 760px)`

Padding on `.hero-panel` and `.filters-panel` reduces from `24px` to `18px`. No other
structural changes.

The `.chips`, `.window-row`, and `.quick-pick-row` containers all have `flex-wrap: wrap` as
**base styles** (sourced directly from mock CSS, not a breakpoint rule). All three rows wrap
naturally at any viewport where their content exceeds the available width. No breakpoint-
specific rules are required for these rows at this breakpoint.

### Breakpoint 3: `@media (max-width: 480px)` — mobile portrait

This breakpoint mirrors the established pattern in `MarketHealthSection.svelte` (Phase 13
of WP1). At `390 × 844 px` (iPhone portrait), `common.css` removes `.container` side padding
and reduces `.content` padding to `var(--spacing-md)` (16 px each side), leaving
approximately 358 px of available inner width for the filter panel.

**`.filters-panel` card chrome — stripped:**

```css
.filters-panel {
  background: none;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
}
```

Consistent with how `MarketHealthSection` strips its card chrome at 480 px. The panel
content sits directly on the page background, reducing visual clutter on small screens.

**`.scope-label` — allow text wrap:**

The mock sets `white-space: nowrap` on `.scope-label`. At 390 px, the longest scope label
text ("Current market scope: your 4 selected genera • Current quarter", ~434 px at 0.86 rem)
exceeds the ~358 px available after panel chrome is stripped. Override at this breakpoint:

```css
.scope-label {
  white-space: normal;
  border-radius: 12px; /* pill (999px) shape breaks visually when text wraps to 2 lines */
}
```

**`.window-row`, `.quick-pick-row`, `.chips` — no additional rules needed:**

All three containers already have `flex-wrap: wrap` as base styles. At 390 px, the 7 window
pills (~90 px each) wrap to approximately 3–4 per row; the 6 quick-pick buttons wrap
similarly. This is the intended wrapping behaviour — no breakpoint-specific rules required.

### Breakpoint 4: `@media (orientation: landscape) and (max-height: 500px)` — phone landscape

This breakpoint is established in `MarketHealthSection.svelte` (KPI grid → 2 columns), but
**does not apply to any filter panel component**.

The `.hero` grid collapses at 1100 px, which covers all common phone landscape widths
(667–926 px). The filter panel is therefore already single-column and full-width in landscape
— no further structural change is needed.

At landscape widths ≥ 667 px, all 7 window pills fit on a single row and all 6 quick-pick
buttons fit on a single row. `flex-wrap: wrap` (base style) ensures no overflow on
unexpectedly narrow devices.

**FiltersPanel card chrome is retained at landscape.** Unlike `@media (max-width: 480px)`,
the landscape filter panel has ample horizontal space; stripping the card chrome would be
visually inconsistent with the rest of the page at that width.

**No additional CSS rules are required for the filter panel at this breakpoint.**

The filter panel occupies a large proportion of the visible viewport at landscape height
(≤ 390 px). The default-collapsed genus selector (spec §6) limits vertical space to the
selector header + collapsed note (~60 px). Users on landscape phones are expected to scroll
past the filter panel to reach the Market Health section.

> The agent must **not** add `@media (orientation: landscape) and (max-height: 500px)` rules
> to `FiltersPanel.svelte`, `GenusSelector.svelte`, or `TimeWindowSelector.svelte`.

---

## §12 By-Design Deviations from Mock

| # | Mock behaviour | Implementation behaviour | Reason |
|---|---|---|---|
| 1 | Chips live inside `<details>`; hidden when selector is closed | Chips live outside the conditional block; always visible when in narrow mode | Chips must remain visible when collapsed so the user can see the current selection at a glance |
| 2 | `--color-breeder-focus` is `--accent-2` in the mock (mock-local token) | `--color-breeder-focus: #cc6b49` added to `templates/common.css` in WP-Arch Phase 1 | WP-Arch is the first consumer of this colour (`.chip.selected`, `.suggestion-status.selected`); adding it in WP-Arch avoids hardcoding rgba literals in WP2 |
| 3 | "Most observed" preset is a hardcoded list of 12 specific genera | "Most observed" is computed from rawData — top 12 genera by total occurrence count across all runs | The real dataset genera may differ from the mock's illustrative list |
| 4 | Hero panel (left) shows "Three ways to assess the market" copy | Hero panel shows minimal static intro copy | The mock's hero copy is explicitly labelled prototype scaffolding; it is not production UI |
| 5 | Lifestyle preset lists (arboreal/terrestrial/fossorial) are static | Lifestyle presets are hardcoded config constants filtered at runtime against `availableGenera` | Some mock genera may not appear in the real dataset; filtering avoids showing phantom genera in the selection |
| 6 | Selector toggle text is rendered via CSS `::after` content | Toggle text is actual button text in the DOM | `content` pseudo-property text is not reliably announced by screen readers |
| 7 | Mock `.filters-panel` border-radius is `20px` (mock `--radius: 20px`) | Implementation uses `18px` | WP1 KPI card border-radius is hardcoded at 18px; consistent rounding within the same panel is more important than matching the mock token. No 18px repo token exists. |

---

## §13 Open Questions — All Resolved

| Question | Resolution |
|---|---|
| Mount strategy: M1 (multiple mount points) vs M2 (single root component)? | **M2 chosen.** `HistoryInsightsRoot.svelte` owns all shared state. WP2/3/4 sections are added as children when those work packages ship. One `mount()` call in `index.ts`. |
| Should `--color-breeder-focus` be added in WP-Arch or WP2? | **WP-Arch adds it.** WP-Arch is the first consumer (`.chip.selected`). Deferring it to WP2 would require inline rgba literals in WP-Arch components. |
| Native `<details>` vs Svelte `$state` for the expandable? | **`$state` chosen.** See §6 for full rationale. |
| Should `SearchInput.svelte` (shared) be reused? | **No.** That component is bound to the table-filter architecture. A standalone `<input>` inside `GenusSelector.svelte` is simpler and correct. |
| What is the default window on mount? | **`current-quarter`** — matches the existing WP1 hardcoded default. |
| Should the hero panel render on `history_insights_page.html`? | **Yes.** The `.hero` grid is rendered by `HistoryInsightsRoot.svelte`. Python renders only a single `<div id="history-insights-root">` mount point inside the `.content` wrapper. |
