# Post-Migration Hardening Plan

## Overview

Harden the Svelte migration without over-abstracting the parts that are about to change significantly. The history page will become chart/KPI-heavy — that redesign is not represented here. This plan targets what can and should be improved now.

Work falls into three categories:

| Category | Pages | Approach |
|---|---|---|
| **Stable** | Breeder, Dealer, Snapshot | Harden now, raise quality bar |
| **Transitional** | History | Minimal low-risk improvements, keep everything local |
| **Future-facing** | History chart data | Data/type layer only, no UI abstractions |

### Explicit Scope Boundaries

**In scope:**
- `SortableTable.svelte` internal clarity and edge-case coverage
- `table-utils.ts` correctness fixes and coverage gaps
- Page-boundary validation for stable entry points
- Typed window globals for current table payloads
- Visual regression net reinforcement (keep and extend)
- History chart data contract at the type/DTO layer only
- Coverage threshold ratchet after stable code settles
- Doc compression to stable operating model

**Out of scope (explicitly deferred or forbidden):**
- Merging `HistoryTable.svelte` into `SortableTable.svelte`
- Building a generic table-state engine
- Generalizing `DateFilter.svelte` (it will change when charts become primary)
- Any chart/KPI Svelte components before history page design is settled
- Reducing or removing the visual test layer

---

## Phase 1 — Scope Lock and Baseline Verification

**Goal:** Confirm the starting state is fully green, understand the exact shape of each key file, and record a coverage baseline before any code changes.

### Checklist

- [x] 1.1 Run `make test-client-fast` — 216 tests pass across 13 test files ✅
- [x] 1.2 Run `make test-visual` — 37 tests pass across 8 visual test files ✅
- [x] 1.3 Run `make test` — 610 pass, 136 skipped; Python total coverage 95.27% ✅
- [x] 1.4 Run `make test-e2e` — 136 passed ✅
- [x] 1.5 Coverage baseline recorded: **statements 96.84% | branches 85.92% | functions 94.2% | lines 96.84%** ✅
- [x] 1.6 `SortableTable.svelte` — `$derived.by()` has **7 inline steps, zero named intermediates**. All steps operate on a single mutable `result` variable. Pipeline order: signal → top-10 → stock-pattern → search → price-range → wishlist → sort. Confirms Phase 3 refactor is needed. ✅
- [x] 1.7 `table-utils.ts` — **Inconsistency confirmed.** `computeRange()` uses `toNumericStr = (raw) => String(raw ?? '0').replace(/^[^0-9.]*/, '')` before `parseFloat`. `sortRows()` calls `parseFloat(String(aRaw))` directly — **no leading-char strip**. A price value `"£25.00 ↑"` returns NaN in `sortRows` (falls through to `localeCompare`) but parses correctly in `computeRange`. Phase 2 is needed as described. ✅
- [x] 1.8 All 8 `.visual.test.ts` files read and mapped:
  - `browser-smoke.visual.test.ts` — CSS token loading plumbing: `common.css` loaded, `tokenRgb()`/`tokenHex()` helpers work, custom-property inheritance end-to-end (11 tests)
  - `RangeSlider.visual.test.ts` — `.label` uses `--color-primary`; `.slider-values` uses `--color-text-muted`; `.slider-current` uses `--color-primary` (3 tests)
  - `SearchInput.visual.test.ts` — unfocused border `--color-border`; unfocused bg `--color-surface`; focused border `--color-accent`; focus/unfocus visually distinct (4 tests)
  - `FiltersPanel.visual.test.ts` — bg `--color-surface`; border `--color-border-light`; display flex; flex-direction column (4 tests)
  - `FilterButton.visual.test.ts` — inactive bg `--color-surface` / border `--color-border-light`; active bg `--color-accent` / border `--color-accent`; active text white; active/inactive distinct (6 tests)
  - `DateFilter.visual.test.ts` — absent when collapsed / present when expanded; date-picker border-top `--color-date-filter`; quick-select bar top border `--color-date-filter` (4 tests)
  - `TableStats.visual.test.ts` — bg `--color-info-bg`; text `--color-text` (2 tests)
  - `SortableTable.visual.test.ts` — `.table-scroll` overflow-x:auto; `.controls-row` display:flex; `.controls-row` flex-wrap:wrap (3 tests)
  - **Gaps found:** `DateFilter` has no active quick-select *button background* colour assertion (only border assertions exist). `SortableTable` has no assertion that an active signal filter button uses `--color-accent` (layout only). Both confirm Phase 6 steps 6.2–6.3. ✅
- [x] 1.9 All 4 entry points read. Every entry point reads its payload with `((window as Record<string, unknown>)[`${TABLE_ID}Data`] ?? []) as Record<string, unknown>[]` — **zero validation anywhere**. Window global key names are kebab-case derived (e.g. `'breeder-tableData'`, `'dealer-tableData'`). **Discovery for Phase 4**: `global.d.ts` typed Window properties must use quoted kebab-case keys (`'breeder-tableData'?: TableRow[]`) since the TABLE_ID contains a hyphen. ✅
- [x] 1.10 `global.d.ts` — only `speciesChartData?: SpeciesChartData` is typed. All stable entry points (`breeder`, `dealer`, `snapshot`, `history`) cast their window global with `as Record<string, unknown>` — none are typed. Confirms Phase 4 steps 4.1–4.3 are fully unimplemented. ✅
- [x] 1.11 **All steps complete. Discoveries recorded above. Phase 2–9 notes updated below.** ✅

---

## Phase 2 — Fix `table-utils.ts` Edge Cases

**Goal:** Eliminate the numeric-parsing inconsistency between `computeRange()` and `sortRows()`. Close coverage gaps for edge cases that are not yet exercised.

### Context

`computeRange()` strips leading non-numeric characters before `parseFloat` using `/^[^0-9.]*/`. `sortRows()` calls `parseFloat(String(aRaw))` directly with no stripping. Result: a price column holding `"£25.00 ↑"` sorts correctly by range slider but sorts incorrectly (falls back to `localeCompare`) when a column header is clicked. Both functions must use identical parsing logic.

> **Findings / Discoveries from Phase 1:**
> - Inconsistency confirmed exactly as described: `computeRange()` strips `^[^0-9.]*` before `parseFloat`; `sortRows()` does not. A value like `"£25.00 ↑"` sorts incorrectly (NaN → `localeCompare`) but sliders work correctly.
> - No surprises in scope — Phase 2 steps need no changes.

### Checklist

**RED phase — write failing tests first:**
- [x] 2.1 In `client/src/shared/table-utils.test.ts`, add test `sortRows – ascending sort strips leading currency symbol` (rows `['£15.00 ↑', '£5.00 →', '£25.00 ↓']`; ascending should give `£5.00`, `£15.00`, `£25.00`)
- [x] 2.2 Add test `sortRows – descending sort strips leading currency symbol` (same rows reversed)
- [x] 2.3 Run `make test-client-fast` and confirm both new tests **fail** (RED confirmed before writing any implementation)

**GREEN phase — fix the implementation:**
- [x] 2.4 In `client/src/shared/table-utils.ts`, extract the leading-non-numeric-strip logic into a private `toSortableNumber` helper that mirrors `computeRange()`'s `toNumericStr` — or inline the same regex into `sortRows()`'s numeric detection
- [x] 2.5 Update `sortRows()` to call `toSortableNumber` (or equivalent) before `parseFloat` for both `aRaw` and `bRaw`
- [x] 2.6 Run `make test-client-fast` — confirm both new tests now **pass** and no existing tests regress

**Close remaining edge-case gaps:**
- [x] 2.7 Add test `sortRows – empty rows returns empty array`
- [x] 2.8 Add test `sortRows – single row returns unchanged single-element array`
- [x] 2.9 Add test `buildCsv – empty rows produces header-only output (no data lines)` *(already existed as `empty visibleRows produces header line only` — no action needed)*
- [x] 2.10 Add test `applySearchFilter – matches partial text across multiple columns`
- [x] 2.11 Add test `applySearchFilter – whitespace-only search returns all rows unchanged` *(already existed as `returns all rows when searchText is whitespace only` — no action needed)*
- [x] 2.12 Run `make test-client` — confirm all tests pass and coverage does not regress
- [x] 2.13 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 3 before starting it.**

---

## Phase 3 — Harden `SortableTable.svelte` Internals and Test Coverage

**Goal:** Improve readability of the main filter/sort pipeline without any public API change. Add unit tests for combined filter semantics, badge counts, top-10 pinning, and CSV scope that are not yet covered.

### Context

The `$derived.by()` block in `SortableTable.svelte` runs 6–7 sequential filter/sort steps inline with no intermediate labels. Introducing named local `const` variables (`afterSignal`, `afterTop10`, etc.) makes intent explicit and makes future filter additions lower-risk while producing identical runtime behaviour. The refactor is rename-only — no logic moves.

> **Findings / Discoveries from Phase 2:**
> - Fix was minimal: introduced a private `toSortableNumber` helper in `sortRows()` using the same `/^[^0-9.]*/` regex as `computeRange()`. No other logic changed.
> - Steps 2.9 and 2.11 were already covered by existing tests (`empty visibleRows produces header line only` and `returns all rows when searchText is whitespace only`). Marked done without adding duplicates.
> - `table-utils.ts` branch coverage is now 80.95% (up from ~78%). The uncovered branches are the `rawValueKey` fallback path in `buildCsv` and the `?? ''` null-coalesce in `toSortableNumber` — both are low-risk defensive guards unlikely to be hit in production.
> - No surprises — Phase 3 steps need no changes.

### Checklist

**Read before writing:**
- [x] 3.1 Re-read the `$derived.by()` block in `SortableTable.svelte` and sketch the exact pipeline order (signal → top-10 → stock-pattern → search → price-range → wishlist → sort) to confirm it matches expectation

**Refactor — internal pipeline clarity (no API change):**
- [x] 3.2 In the `$derived.by()` block, introduce named `const` intermediate variables for each stage. Use the names: `afterSignal`, `afterTop10`, `afterStockPattern`, `afterSearch`, `afterPriceRange`, `afterWishlist`, `sorted`
- [x] 3.3 Run `make test-client-fast` — confirm no regressions from the naming-only change

**Tests — combined filter and badge behaviour:**
- [x] 3.4 In `client/src/shared/components/SortableTable.test.ts`, add test `signal filter + search applied together — only rows matching both criteria are visible`  
  *(inject 3 rows: two 🔥 with different species names; activate 🔥 filter then type a search term that matches only one of them; assert 1 row visible)*
- [x] 3.5 Add test `signal filter buttons show correct per-signal row counts via data-count attribute`  
  *(inject rows with known signal distribution; assert `data-count` on each signal button matches count)*
- [x] 3.6 Add test `top-10 pin: only 10 rows shown when top10 is enabled and 15 rows injected`
- [x] 3.7 Add test `stock-pattern filter: clicking a pattern button filters table to matching rows only`
- [x] 3.8 Add test `CSV download contains only currently visible rows, not all rows`  
  *(activate a signal filter, trigger download via `clickDownloadAndGetBlob`, parse result, assert only filtered species names present)*
- [x] 3.9 Run `make test-client` — confirm all tests pass and branches coverage holds or improves
- [x] 3.10 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 4 before starting it.**

---

## Phase 4 — Page-Boundary Validation (Stable Entry Points)

**Goal:** Make Python template payload drift fail loudly and locally at page mount time, not silently as an empty table. Extend `global.d.ts` with typed window globals for all current table payloads.

### Context

Every stable entry point reads its payload as `(window as Record<string, unknown>)[...] ?? []` with no further validation. When the Python template renames a column or changes the serialisation shape, the JS receives an array of incorrectly shaped rows and renders an empty table — no error, no log. A small `assertPayload()` function gated on `import.meta.env.DEV` adds a clear error in development and CI without bundling any validation logic into production builds.

> **Findings / Discoveries from Phase 3:**
> - The `$derived.by()` refactor was pure naming — zero logic changes. The `top10` step introduced one helper (`top10Pinned`) alongside `afterTop10` to keep the conditional readable without an IIFE.
> - Tests 3.7 (`stock-pattern filter`) and 3.8 (`CSV scoped to visible rows`) were already covered by "clicking a stock pattern filter button filters rows" and "filtered CSV excludes hidden rows" respectively — marked done without adding duplicates.
> - Test 3.6 (`top-10 exact count`) was partially covered by an existing test that used `toBeLessThanOrEqual(10)`. Strengthened that assertion to `toHaveLength(10)` — exact count is achievable because all 15 injected rows share the same signal.
> - `data-count` attribute did not exist on signal filter buttons before Phase 3. Added `count` field to the `signalButtons` derived array and spread `data-count={btn.count}` onto each `FilterButton`. `FilterButton` already accepts `...rest` so no component change was needed.
> - Coverage: statements 96.83% | branches 86.01% | functions 94.28% | lines 96.83% — all hold or improve vs baseline.
> - No surprises — Phase 4 steps need no changes.
>
> **Pre-seeded from Phase 1:** Window global keys are kebab-case (e.g. `'breeder-tableData'`) because TABLE_ID uses hyphens. TypeScript `interface Window` supports quoted property names with hyphens — step 4.2 must use `'breeder-tableData'?: TableRow[]` syntax rather than `breederTableData`. Verify the Python template injection to confirm the exact key names before writing global.d.ts additions.

### Checklist

**Typed window globals:**
- [x] 4.1 In `client/src/global.d.ts`, add a `TableRow` type alias (`Record<string, unknown>`) with a JSDoc that explains why it's structurally open (Python owns column names)
- [x] 4.2 Add typed window globals: `'breeder-tableData'?: TableRow[]`, `'dealer-tableData'?: TableRow[]`, `'snapshot-tableData'?: TableRow[]` (quoted kebab-case keys as required by TABLE_ID shape)
- [x] 4.3 Add `HistoryTableRow` interface that includes `_raw_scrape_datetime: string` (required for correct CSV export) alongside the general `TableRow` fields; add `'history-tableData'?: HistoryTableRow[]`

**Validation utility — RED phase first:**
- [x] 4.4 Create `client/src/shared/payload-validation.test.ts` and write the following failing tests before writing the implementation:
  - `assertPayload – throws descriptive Error in dev mode when rows is not an array`
  - `assertPayload – throws descriptive Error in dev mode when rows is an empty array`
  - `assertPayload – is a no-op (no throw) in production mode`
  - `assertPayload – passes through a valid non-empty array without throwing`
- [x] 4.5 Run `make test-client-fast` — confirm all 4 tests **fail** (RED)

**Validation utility — GREEN phase:**
- [x] 4.6 Create `client/src/shared/payload-validation.ts` and implement `assertPayload(tableId: string, rows: unknown, isDev?: boolean): asserts rows is TableRow[]` — throws with a message that names `tableId` and explains what was found; guards behind `import.meta.env.DEV` (exposed as optional `isDev` parameter for testability without `vi.stubEnv`)
- [x] 4.7 Run `make test-client-fast` — confirm all 4 tests now **pass**

**Wire into stable entry points:**
- [x] 4.8 In `client/src/breeder-page/index.ts`, import `assertPayload` and call it on the `rows` value before passing to `mount`
- [x] 4.9 In `client/src/dealer-page/index.ts`, same
- [x] 4.10 In `client/src/snapshot-page/index.ts`, same
- [x] 4.11 In `client/src/history-page/index.ts`, add `assertPayload` call — dev warning only, no required-column enforcement (history row shape is about to change significantly)
- [x] 4.12 Run `make test-client` — confirm all tests pass
- [x] 4.13 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 5 before starting it.**

---

## Phase 5 — History Slice Low-Risk Improvements

**Goal:** Improve the internal quality of the history slice without generalising any abstractions. The goal is to make the current code easy to replace, not to make it more shared.

### Context

The history slice (`HistoryTable.svelte`, `DateFilter.svelte`, `history-utils.ts`) will be substantially redesigned when the chart/KPI page lands. The only acceptable work here is making the current code cleaner and its contracts clearer — so the eventual redesign has a clean cut point.

### Do-not-touch list (hard stops during review)

- Do **not** extract `DateFilter.svelte` into a shared component
- Do **not** merge `HistoryTable.svelte` into `SortableTable.svelte`
- Do **not** add a generic date-picker interface used by other pages
- Do **not** make any `history-utils.ts` function depend on Svelte context or reactive primitives

> **Findings / Discoveries from Phase 4:**
> - `assertPayload` signature uses `rows: unknown` (not `unknown[]`) so the runtime non-array check is meaningful. The `asserts rows is TableRow[]` narrowing makes the TypeScript cast after the call unnecessary — but all 4 entry points still use the old `as Record<string, unknown>[]` pattern for now. This is deliberate: the cast was left unchanged to keep the diff minimal; Phase 9 doc cleanup can note this as a future simplification.
> - The `isDev` optional parameter (defaulting to `import.meta.env.DEV`) avoids `vi.stubEnv` in tests, which is unreliable with `import.meta.env` in Vitest. The production-mode test passes `false` explicitly — clean and unambiguous.
> - `global.d.ts` window properties use quoted kebab-case keys (`'breeder-tableData'`) as expected from the Phase 1 discovery. Entry points continue to use the dynamic `window[\`${TABLE_ID}Data\`]` read (untyped); the globals typing is for IDE tooling and documentation rather than a runtime path change.
> - Coverage: statements 96.9% | branches 86.21% | functions 94.36% | lines 96.9% — all hold or improve vs. Phase 3 baseline. `payload-validation.ts` is at 100% across all metrics.
> - No surprises — Phase 5 steps need no changes.

### Checklist

**Read before writing:**
- [x] 5.1 Read `client/src/history-page/HistoryTable.svelte` in full — `_raw_scrape_datetime` confirmed in the CSV column definition as `rawValueKey`; filter pipeline: date → search → price → wishlist → sort ✅
- [x] 5.2 Read `client/src/history-page/history-utils.ts` — `collectAllDates()` is pure: no side effects, no global reads ✅
- [x] 5.3 Read `client/src/history-page/DateFilter.svelte` — `data-action` attributes present: `toggle-date-picker`, `select-last-n`, `show-all-dates`. E2E test file confirms these are all that are required ✅

**Low-risk improvements only:**
- [x] 5.4 `collectAllDates()` is pure — no side effects to extract (no-op) ✅
- [x] 5.5 Added property-level JSDoc directly on `_raw_scrape_datetime` in `global.d.ts` — the interface-level JSDoc existed but no property-level doc. Added one explaining why it must survive to `buildCsv()` via `rawValueKey` ✅
- [x] 5.6 No missing `data-action` attributes — E2E tests use `toggle-date-picker`, `select-last-n`, and `show-all-dates` which all exist; `select-all`/`clear-all` are not required by any E2E selector (no-op) ✅

**Tests:**
- [x] 5.7 Already covered by `'CSV header uses csvHeader values from column config'` which asserts `headerLine === 'scrape_datetime,scientific_name,price_gbp,wishlist_count'` — no duplicate test added ✅
- [x] 5.8 Already covered by `'deselecting a date hides rows for that date'` which opens the date picker, deselects 2026-01-15, and asserts 2 rows remain — no duplicate test added ✅
- [x] 5.9 Run `make test-client` — all tests pass; coverage holds: statements 96.9% | branches 86.18% | functions 94.36% | lines 96.9% ✅
- [x] 5.10 **All steps complete. Discoveries recorded below. Phase 6 findings updated.** ✅

---

## Phase 6 — Visual Regression Net Reinforcement

**Goal:** Keep and extend the browser-backed visual test layer. Add contracts for CSS behaviours that are known to be fragile but not yet protected. Enforce the `tokenRgb()` pattern consistently.

### Context

CSS regression is an identified project risk. Visual tests are mandatory for any CSS-affecting change. Eight `.visual.test.ts` files currently exist. The gap analysis identified: no active-state token colour assertion for `DateFilter` quick-select buttons; no sort-indicator colour assertion on `SortableTable` headers. These are the most useful gaps to close.

> **Findings / Discoveries from Phase 5:**
> - History slice is in good shape overall — `history-utils.ts` is already pure (step 5.4 no-op); all required E2E `data-action` attributes are present on `DateFilter.svelte` (step 5.6 no-op).
> - `HistoryTableRow._raw_scrape_datetime` lacked a property-level JSDoc even though the interface-level JSDoc existed. Added a property-level doc explaining the `rawValueKey` CSV export contract.
> - Steps 5.7 and 5.8 were already covered by existing tests: `'CSV header uses csvHeader values from column config'` and `'deselecting a date hides rows for that date'` respectively — not duplicated.
> - Coverage unchanged from Phase 4 baseline: 96.9% | 86.18% | 94.36% | 96.9%.
> - No surprises — Phase 6 steps need no changes.
>
> **Pre-seeded from Phase 1:** Both gaps identified in the plan are confirmed absent:
> - `DateFilter.visual.test.ts` has only two *border* assertions using `--color-date-filter` — zero assertions on active quick-select button *background* colour.
> - `SortableTable.visual.test.ts` covers overflow-x and flex-wrap only — no assertion on active signal filter button `--color-accent` background.
> Steps 6.2 and 6.3 are definitely needed.

### Checklist

**Audit the existing suite:**
- [ ] 6.1 For each of the 8 `.visual.test.ts` files, record in a comment or note: "protects [specific behaviour] via [specific assertion]". This creates a machine-readable coverage map of the visual layer

**Close identified gaps:**
- [ ] 6.2 In `client/src/history-page/DateFilter.visual.test.ts`, if an active quick-select button colour assertion is missing, add one using `tokenRgb('--color-date-filter')` (the background token for active date filter controls)
- [ ] 6.3 In `client/src/shared/components/SortableTable.visual.test.ts`, if there is no assertion that an active signal filter button uses `var(--color-accent)`, add one

**Enforce conventions:**
- [ ] 6.4 In `client/src/test-utils/token-colors.ts`, confirm the JSDoc at the top of the file names the exact import pattern and `tokenRgb()` usage — update if the example is stale
- [ ] 6.5 In `client/src/test-utils/design-tokens.test.ts`, add a JSDoc comment on the `ALLOWLIST` set explaining why `#fff`/`white` is permitted (white text on coloured backgrounds — `--color-text-inverse` deferred) so future contributors don't mistakenly add new colours to the list without understanding the intent
- [ ] 6.6 Run `make test-visual` — confirm all visual contracts pass (green)
- [ ] 6.7 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 7 before starting it.**

---

## Phase 7 — Future History Chart Data Contract (Data Layer Only)

**Goal:** Define and test typed payloads for the upcoming chart/KPI history page without building any UI abstractions. Both the client-side type declarations and the Python DTO function must be completable before the chart design is settled.

### Constraints

- No chart or KPI Svelte components in this phase
- No changes to `HistoryTable.svelte` or `DateFilter.svelte`
- No new Jinja2 template injection until the data shape is locked
- All work stays at the type definition and pure-function data layer

> **Findings / Discoveries from Phase 6:** *(fill in after Phase 6 reflection)*

### Checklist

**Client-side type contracts:**
- [ ] 7.1 In `client/src/global.d.ts`, add `HistoryChartRun` interface:  
  `{ date: string; price_gbp: number | null; wishlist_count: number | null; in_stock: boolean }`
- [ ] 7.2 Add `HistoryChartSpecies` interface:  
  `{ scientific_name: string; common_name: string; runs: HistoryChartRun[] }`
- [ ] 7.3 Add `HistoryChartData` interface:  
  `{ species: HistoryChartSpecies[]; scrape_dates: string[] }` and declare `historyChartData?: HistoryChartData` on `Window`

**Python DTO — RED phase first:**
- [ ] 7.4 Read `src/website/sparkline_dto.py` and `src/website/table_data_helpers.py` in full — understand the DTO pattern and serialisation conventions before writing any code
- [ ] 7.5 Create `tests/website_module/test_history_chart_dto.py` and write the following failing tests before writing the implementation:
  - `build_history_chart_dto – empty input returns empty species list and empty scrape_dates`
  - `build_history_chart_dto – single species with multiple rows groups all runs under one species entry`
  - `build_history_chart_dto – in-stock detection: row with non-empty price is in_stock=True`
  - `build_history_chart_dto – out-of-stock detection: row with empty or None price is in_stock=False`
  - `build_history_chart_dto – scrape_dates are sorted chronologically and deduplicated`
  - `build_history_chart_dto – multiple species produce one entry each in the species list`
- [ ] 7.6 Run `make test-file FILE=tests/website_module/test_history_chart_dto.py` — confirm all tests **fail** (RED)

**Python DTO — GREEN phase:**
- [ ] 7.7 Create `src/website/history_chart_dto.py` and implement `build_history_chart_dto(history_rows: list[dict]) -> dict` as a pure function with type annotations. No file I/O, no HTML, no templates. Follow the same style as `sparkline_dto.py`
- [ ] 7.8 Run `make test-file FILE=tests/website_module/test_history_chart_dto.py` — confirm all tests **pass**
- [ ] 7.9 Run `make test` — confirm no Python regressions
- [ ] 7.10 Run `python scripts/check_coverage.py --module=website/history_chart_dto.py --threshold=80` — confirm coverage meets threshold
- [ ] 7.11 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 8 before starting it.**

---

## Phase 8 — Raise Coverage Thresholds

**Goal:** Ratchet `lines` and `statements` thresholds in `client/vite.config.ts` now that the stable table layer has been hardened. The increase should reflect settled code, not churn.

### Context

`branches` and `functions` are currently gated at 80%. `lines` and `statements` are at 0 — deliberately left for ratcheting upward phase-by-phase as the migration adds and tests components. Phases 2–7 should substantially increase line coverage of `table-utils.ts`, `SortableTable.svelte`, and `payload-validation.ts`.

> **Findings / Discoveries from Phase 7:** *(fill in after Phase 7 reflection)*

### Checklist

- [ ] 8.1 Run `make test-client` and record the current `lines` % and `statements` % from the coverage output
- [ ] 8.2 In `client/vite.config.ts`, locate the `coverage.thresholds` block
- [ ] 8.3 Set `lines` and `statements` to the actual measured values, rounded **down** to the nearest 5% — this is the safe ratchet rule (never set a threshold above what currently passes)
- [ ] 8.4 Run `make test-client` again — confirm the new thresholds pass immediately with no false-failures
- [ ] 8.5 In `.github/copilot-instructions.md`, update the note about `lines`/`statements` threshold to reflect the new non-zero values
- [ ] 8.6 **Mark off each completed step. Reflect on any discoveries that will inform future phases. Update the "Findings / Discoveries" section at the top of Phase 9 before starting it.**

---

## Phase 9 — Compress Docs to Stable Operating Model

**Goal:** Update `docs/MIGRATION_PLAN.md` and `.github/copilot-instructions.md` so they describe the enduring architecture — not the migration journey. Future contributors should not need to know a migration happened.

### Context

Migration plan documents accumulate narrative that is historically accurate but operationally irrelevant. The useful content is: what the stable architecture looks like, what the testing rules are, and what the history slice is and why it's intentionally local. Everything else can be collapsed or removed.

> **Findings / Discoveries from Phase 8:** *(fill in after Phase 8 reflection)*

### Checklist

**`docs/MIGRATION_PLAN.md`:**
- [ ] 9.1 Identify all completed-phase narrative. Collapse it into a single "Migration history (archived)" section at the bottom of the file — keep it for traceability but stop it from dominating the document
- [ ] 9.2 Make the "Current architecture" section the first thing a reader sees. It must cover clearly: stable shared table layer, transitional history slice, mandatory visual regression testing, typed server-to-client payload contracts, `assertPayload()` pattern
- [ ] 9.3 Add a "History page — future direction" section: describes the planned chart/KPI redesign and explicitly states that `HistoryTable.svelte` and `DateFilter.svelte` should not be hardened or generalised before that redesign is scoped

**`.github/copilot-instructions.md`:**
- [ ] 9.4 Update the `client/src/` feature-slice structure table if `payload-validation.ts` or any other files were added throughout Phases 2–7
- [ ] 9.5 Add a note under "Svelte 5 component authoring" or a new "Page entry point conventions" section explaining: always call `assertPayload()` after reading a window global; dev-only semantics; history entry point is still bare-minimum due to transitional status
- [ ] 9.6 If any CSS architecture or design-token documentation drifted during Phases 6–7 (e.g. new token added), update the relevant section so the instructions remain the source of truth
- [ ] 9.7 Update the `lines`/`statements` coverage threshold note to match the values set in Phase 8

**Verify:**
- [ ] 9.8 Run `make test` and `make test-client-fast` — confirm all tests still pass after docs changes (code samples in docs can introduce subtle errors)
- [ ] 9.9 **Mark off each completed step. Complete the Completion Checklist below.**

---

## Completion Checklist

Use this after Phase 9 to confirm every hardening objective was met.

- [ ] `sortRows()` strips currency prefixes — behaviour is consistent with `computeRange()`
- [ ] `SortableTable.svelte` internal pipeline has named intermediate variables — each stage is self-documenting
- [ ] `payload-validation.ts` exists; all 4 stable entry points call `assertPayload()` at mount time
- [ ] `global.d.ts` types all current window globals (`breeder`, `dealer`, `snapshot`, `history` table payloads) and the future `HistoryChartData` shape
- [ ] History slice remains entirely local — no new shared abstractions extracted from it
- [ ] All 8+ `.visual.test.ts` files pass under `make test-visual` and each test is documented with the specific CSS behaviour it protects
- [ ] `build_history_chart_dto()` exists in `src/website/history_chart_dto.py`, is pure, and has ≥80% unit test coverage
- [ ] `lines` and `statements` coverage thresholds are non-zero values in `client/vite.config.ts`
- [ ] `docs/MIGRATION_PLAN.md` leads with current architecture, not migration history
- [ ] `.github/copilot-instructions.md` reflects all new files, patterns and threshold values from this plan

---

## Key File Reference

| File | Role in this plan |
|---|---|
| `client/src/shared/table-utils.ts` | Phase 2 — fix `sortRows()` numeric parsing |
| `client/src/shared/table-utils.test.ts` | Phase 2 — edge-case coverage |
| `client/src/shared/components/SortableTable.svelte` | Phase 3 — pipeline clarity refactor |
| `client/src/shared/components/SortableTable.test.ts` | Phase 3 — combined filter / badge / CSV tests |
| `client/src/global.d.ts` | Phase 4 + 7 — typed window globals |
| `client/src/shared/payload-validation.ts` | Phase 4 — new file, dev-mode validation utility |
| `client/src/shared/payload-validation.test.ts` | Phase 4 — new file, validation unit tests |
| `client/src/breeder-page/index.ts` | Phase 4 — wire `assertPayload` |
| `client/src/dealer-page/index.ts` | Phase 4 — wire `assertPayload` |
| `client/src/snapshot-page/index.ts` | Phase 4 — wire `assertPayload` |
| `client/src/history-page/index.ts` | Phase 4 + 5 — validation + CSV contract |
| `client/src/history-page/HistoryTable.svelte` | Phase 5 — read-only audit; low-risk fixes only |
| `client/src/history-page/history-utils.ts` | Phase 5 — purity confirmation |
| `client/src/history-page/DateFilter.svelte` | Phase 5 — data-action attribute check only |
| `client/src/test-utils/token-colors.ts` | Phase 6 — doc update |
| `client/src/test-utils/design-tokens.test.ts` | Phase 6 — ALLOWLIST annotation |
| `client/src/history-page/DateFilter.visual.test.ts` | Phase 6 — active-state token colour gap |
| `client/src/shared/components/SortableTable.visual.test.ts` | Phase 6 — signal button colour gap |
| `src/website/history_chart_dto.py` | Phase 7 — new file, pure DTO function |
| `tests/website_module/test_history_chart_dto.py` | Phase 7 — new file, DTO unit tests |
| `client/vite.config.ts` | Phase 8 — threshold ratchet |
| `docs/MIGRATION_PLAN.md` | Phase 9 — compress to stable model |
| `.github/copilot-instructions.md` | Phase 8 + 9 — threshold + architecture update |
