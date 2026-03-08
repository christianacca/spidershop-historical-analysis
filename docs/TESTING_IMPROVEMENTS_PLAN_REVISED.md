# Testing Improvements Plan — Revised Agent Feedback Loop

**Repository:** spidershop-historical-analysis  
**Branch:** svelte-migration (PR #104)  
**Date:** 2026-03-08

---

## How to use this document

Each phase is designed to be executed in a separate AI conversation so the agent can stay
focused on one layer of the feedback loop at a time.

Start a phase with:

> Read `docs/TESTING_IMPROVEMENTS_PLAN_REVISED.md`. We are implementing **Phase N**. Begin.

At the end of each phase conversation, update this file:

- Tick completed checklist items
- Record decisions made during the phase
- Record any findings that change the assumptions of later phases
- Adjust later phases if implementation reality differs from the initial plan

This plan is intended to be a living document. The goal is not to follow it rigidly if the repo
teaches us something better during execution. The goal is to keep the next step explicit,
defensible, and easy for an agent to continue.

---

## Objective

Improve the agent feedback loop for client-side and website-facing changes so that:

1. Feedback arrives sooner
2. Failures point directly at the broken layer and state
3. Tests are easier to write and maintain
4. Visual and computed-style regressions have a real safety net

This revised plan keeps the strongest parts of the existing
`docs/TESTING_IMPROVEMENTS_PLAN.md` proposal, but changes the order of work and broadens the
scope beyond token-colour assertions so the result is faster and more maintainable in practice.

---

## Core principles

### 1. Shortest valid loop wins

The first feedback mechanism an agent should use is the cheapest one that can actually catch the
target regression.

- Pure logic should fail in tiny Vitest tests
- Component render and callback wiring should fail in ordinary Svelte Vitest tests
- Computed style and layout invariants should fail in browser-backed component tests
- Full-site assembly, URL state, downloads, and Python-generated HTML shape should fail in E2E

### 2. DevTools MCP is diagnosis, not enforcement

Chrome DevTools MCP gives the agent eyes inside a real browser. It is useful during development,
during debugging, and when designing better assertions. It is not the CI gate.

### 3. Reduce breadth in the slowest layer

The slowest tests should be the narrowest. E2E should prove assembly and browser integration, not
re-test every component state already covered below it.

### 4. Convert discoveries into durable assertions

If the agent finds a useful visual or styling invariant through DevTools MCP or debugging, that
invariant should be promoted into the lowest stable automated layer that can express it.

### 5. Reuse existing repo flows

Where the repo already has a valid generation or preview workflow, extend or alias it rather than
introducing a parallel path that will drift.

---

## Current state summary

### Existing automated layers

| Tier | Command | Approx speed | Current role |
| --- | --- | ---: | --- |
| Client Vitest with coverage | `make test-client` | ~1s | Svelte component behavior, pure utilities, coverage gate |
| Python unit tests | `make test` | ~1s | Python logic and website-generation support code |
| Playwright E2E | `make test-e2e` | ~10-20s | Full-site interaction, integration, URL state, asset load, some style checks |

### Existing interactive browser path

The repo already has a local generation and serving path:

- `make generate-website`
- `make serve-only`
- `scripts/test_website_locally.py`

That means the plan does **not** need a separate preview stack. If a new `make preview` command is
added, it should be a thin alias over existing behavior, not a new code path.

### What is still weak today

- `make test-client` is coverage-enforcing by default, which is not the fastest local iteration loop
- Large component tests still carry a lot of setup and duplicated helpers
- `happy-dom` cannot reliably validate computed styles based on CSS custom properties
- E2E still contains style assertions that are too low-level for a full-site test and uses avoidable timeout polling
- There is no static guardrail against hardcoded token-equivalent values in Svelte style blocks
- There is no formal browser-backed component test layer between happy-dom and full E2E
- DevTools-style interactive inspection is not yet documented as an explicit agent workflow

---

## Proposed feedback loop

```text
agent changes code or CSS
       |
       |  <100ms
       v
Phase 2 static guardrails
  - token drift check
  - Svelte CSS token-compliance audit
       |
       |  <1s
       v
make test-client-fast
  - no coverage
  - pure logic + component behavior + small harness tests
       |
       |  ~1-2s
       v
make test-client
  - existing coverage gate retained
       |
       |  ~2-3s interactive
       v
DevTools MCP inspection against locally served site
  - evaluate_script
  - computed styles
  - layout metrics
  - screenshots
       |
       |  ~5-10s
       v
make test-visual
  - browser-backed component visual contracts
       |
       |  ~10-20s
       v
make test-e2e
  - true page assembly and browser integration only
       |
       |  ad hoc / non-blocking initially
       v
DevTools MCP lighthouse_audit
  - accessibility/performance baseline
```

---

## Target layer responsibilities

| Layer | Purpose | What belongs here | What does not belong here |
| --- | --- | --- | --- |
| Static guardrails | Prevent obvious CSS/system mistakes | Token drift, hardcoded token-equivalent colours in Svelte styles | Runtime behavior, DOM interactions |
| Fast Vitest | Tight local iteration | Pure functions, state transforms, render output, callback props, DOM state changes that `happy-dom` can model | Computed styles, sticky positioning, real layout |
| Browser-backed component tests | Real browser contracts without full site assembly | Computed colours, borders, spacing, focus states, overflow, sticky/header behavior, responsive component states | Full navigation, downloads, Python-generated HTML shape |
| E2E | End-to-end assembly and integration | Generated site, page navigation, URL state, downloads, real browser orchestration across layers | Re-testing local component styling in isolation |
| DevTools MCP | Interactive diagnosis and discovery | Live browser inspection, debugging, screenshot sanity checks, Lighthouse audits | Repeatable CI enforcement |

---

## Phase 0 — Inventory and ownership map

**Goal:** Build the move-down map before adding new layers.

- [x] 1. Audit the current assertions in:
      - `client/src/shared/components/SortableTable.test.ts`
      - `client/src/history-page/HistoryTable.test.ts`
      - `tests/e2e/test_visual_contracts.py`
      - `tests/e2e/test_navigation_and_page_loads.py`
      - `tests/e2e/test_snapshot_filters.py`
      - `tests/e2e/test_history_date_filter.py`

- [x] 2. Tag each assertion as one of:
      - pure logic
      - component behavior
      - browser-style contract
      - full integration

- [x] 3. Produce a move-down table that records:
      - keep in place
      - move to fast Vitest
      - move to browser-backed component tests
      - keep in E2E because it depends on full-site assembly

- [x] 4. Identify the top three client test files with the highest setup friction and the top three E2E tests with the most duplicated waits or style assertions.

- [x] 5. Record the baseline timings for:
      - `make test-client`
      - `make test-e2e`
      - one representative client test file
      - one representative E2E file

### Phase 0 Outputs

- An ownership map for current assertions
- A ranked list of pain points by speed, setup cost, and flake risk
- Baseline timings to compare future phases against

### Phase 0 Verification

- No code changes required unless minor instrumentation is needed
- The output of this phase is complete only if later phases can point to a specific assertion inventory

### Phase 0 Decisions To Record

- Which current tests are the first candidates for move-down
- Whether any existing E2E files are already thin enough to leave alone
- Which client tests need helper extraction first

---

### Phase 0 Findings

#### Baseline timings (measured 2026-03-08, MacBook, macOS)

| Command | Wall time |
| --- | --- |
| `make test-client` (coverage) | **7.1s** |
| `cd client && npm test` (no coverage) | **5.1s** |
| `make test-e2e` (full suite) | **~85s** (1 pre-existing failure) |

The gap between coverage and no-coverage runs is ~2s. The test suite itself takes ~3.9s
inside Vitest; coverage instrumentation and reporting accounts for the rest.

#### Pre-existing E2E failure

`tests/e2e/test_species_page_interactions.py::test_tab_switching_between_breeder_and_dealer_views`
is **already failing** on this branch prior to any Phase 0 work. Do not break it further; leave
fix for Phase 7 cleanup or a dedicated PR.

#### Client test file inventory

| File | Tests | URL mock boilerplate | Setup friction |
| --- | ---: | ---: | --- |
| `SortableTable.test.ts` | 58 | 6 lines (duplicated) | Advanced-filters toggle required before accessing sliders; large fixture set |
| `HistoryTable.test.ts` | 26 | 6 lines (duplicated) | `openDatePicker` + `openAdvancedFilters` helpers re-invented per file; multi-step fixture |
| `table-utils.test.ts` | 0 (describe-style) | 5 matches | URL mock in non-component utility file |
| `DateFilter.test.ts` | 16 | 0 | Clean — no URL mock needed |
| `RangeSlider.test.ts` | 8 | 0 | Clean |
| `FilterButton.test.ts` | 5 | 0 | Clean |

**URL mock (`vi.stubGlobal('URL', {...})`) is duplicated in three files.**
A single shared test helper should own this setup.

`clickDownloadAndGetBlob` helper is independently re-invented in both `SortableTable.test.ts`
and `HistoryTable.test.ts` with identical logic.

#### Client assertion ownership map

All assertions in both Vitest component test files are correctly placed in the **component
behavior** layer. There are no assertions in client tests that need to move down to E2E or up
to browser-backed component tests.

No assertions in the audited client test files assert computed CSS styles — happy-dom is
not asked to resolve `var(--tokens)`. That boundary is being respected.

| Test group | Layer | Decision |
| --- | --- | --- |
| Render (rows, headers, IDs) | Component behavior | Keep in Vitest |
| Sorting (click → order) | Component behavior | Keep in Vitest |
| Signal / stock-pattern filter | Component behavior | Keep in Vitest |
| Search text filter | Component behavior | Keep in Vitest |
| Advanced-filters toggle expand/collapse | Component behavior | Keep in Vitest |
| Price / wishlist slider filter | Component behavior | Keep in Vitest |
| CSV download content (Blob) | Component behavior | Keep in Vitest |
| Signal CSS class (`signal-hot` etc.) | Component behavior | Keep in Vitest |
| Species-link column type | Component behavior | Keep in Vitest |
| Sparkline column type | Component behavior | Keep in Vitest |
| URL mock setup | Infrastructure | **Extract to shared helper (Phase 2)** |
| `clickDownloadAndGetBlob` helper | Infrastructure | **Extract to shared helper (Phase 2)** |
| `openDatePicker` / `openAdvancedFilters` helpers | Infrastructure | **Extract to shared helper (Phase 2)** |

#### E2E test file inventory

| File | Tests | `wait_for_timeout` calls | `getComputedStyle`/`rgb(` calls |
| --- | ---: | ---: | ---: |
| `test_snapshot_filters.py` | 22 | **54** | 7 |
| `test_table_interactions.py` | 25 | **34** | 31 |
| `test_species_page_interactions.py` | 15 | 14 | **30** |
| `test_history_date_filter.py` | 16 | 11 | 9 |
| `test_history_filters.py` | 17 | **30** | 3 |
| `test_breeder_page_interactions.py` | 14 | 4 | 0 |
| `test_visual_contracts.py` | 15 | 0 | 0 |
| `test_navigation_and_page_loads.py` | 5 | 0 | **23** |
| `test_top10_filter.py` | 5 | 8 | 0 |

#### E2E assertion ownership map

| Test / test group | Layer | Decision |
| --- | --- | --- |
| Page loads + titles (all pages) | Full integration | Keep in E2E |
| Navigation breeder/dealer → species link | Full integration | Keep in E2E |
| Back button rendering | Full integration | Keep in E2E |
| Table structural attributes (data-signal, data-stock-pattern) | Full integration | Keep in E2E |
| Signal / stock-pattern filter (breeder, dealer) | **Partly redundant** with SortableTable.test.ts | Keep in E2E as smoke; note overlap |
| Search filter (breeder, dealer) | **Partly redundant** with SortableTable.test.ts | Keep in E2E as smoke; note overlap |
| Advanced-filters toggle (table_interactions) | **Partly redundant** with SortableTable.test.ts | Keep for now; candidate for removal in Phase 7 |
| Filter badge with search (table_interactions) | **Partly redundant** | Keep for now |
| Price / wishlist sliders (snapshot_filters) | **Mostly redundant** with SortableTable.test.ts | Keep for now; candidate for thinning in Phase 7 |
| Stats strip count update | **Partly redundant** | Keep for now |
| Python-generated HTML structure (stat-cards, signal rows, instruction box) | Full integration | Keep in E2E |
| Sort glyph in headers | Full integration | Keep in E2E (G5 guards assembly) |
| Wishlist column non-empty | Full integration | Keep in E2E (G1 guards data pipeline) |
| Sparkline SVG fill and tooltips | Full integration | Keep in E2E (G3/G3b guards DTO pipeline) |
| Info icon in signal cells | Full integration | Keep in E2E (G4 guards Drivers field) |
| Species page tab switching + URL state | Full integration | Keep in E2E |
| Species page charts (SVG renders, data points) | Full integration | Keep in E2E |
| Species page tooltips, stock strip, gaps | Full integration | Keep in E2E |
| CSV download content + schema | Full integration | Keep in E2E |
| Header/footer computed background colour | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Homepage card grid / link colours / info-box colours | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Stat card border colours | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Species page chart legend dot colours | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Date filter section amber border / background | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Date grid display:grid, date row white background | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| Species page legend swatch colours | Browser-style contract | **Refactor: replace hardcoded rgb() with token helper (Phase 7)** |
| All `wait_for_timeout(200)` calls | Infrastructure | **Replace with wait_for() on observable DOM change (Phase 7)** |

#### Top pain points ranked

**Client tests:**

1. **`SortableTable.test.ts` (58 tests)** — Largest file; URL mock and `clickDownloadAndGetBlob`
   duplicated; requires toggle expansion before panel elements become available in DOM. High time
   cost when a global fixture change breaks many tests at once.

2. **`HistoryTable.test.ts` (26 tests) + `table-utils.test.ts`** — URL mock duplicated; local
   `openDatePicker` and `openAdvancedFilters` helpers re-invented identically to E2E helpers in
   `test_history_date_filter.py`. Three files own the same teardown pattern.

3. **No shared Vitest test-helper module** — There is no `client/src/test-utils/` or equivalent.
   Each file that needs URL mocks, download helpers, or render wrappers builds them inline.

**E2E tests:**

1. **`test_snapshot_filters.py` (54 `wait_for_timeout` calls)** — Almost every slider interaction
   is followed by a 200ms blind sleep. Largest source of gratuitous wall-clock latency in the E2E
   suite. Also tests slider behavior already covered by SortableTable.test.ts.

2. **`test_table_interactions.py` (34 timeouts, 31 style assertions)** — Mixes assembly-level
   integration checks with style contracts expressed as hardcoded rgb values. Split into two
   concerns once token helper exists.

3. **`test_species_page_interactions.py` (30 style assertions, 14 timeouts)** — Heaviest use of
   `getComputedStyle` with hardcoded rgb values. The pre-existing failure
   (`test_tab_switching_between_breeder_and_dealer_views`) is in this file.

#### Files already lean enough to leave alone

- `test_visual_contracts.py` — 0 timeouts, 0 hardcoded rgb values. Guards the DTO pipeline with
  DOM-attribute checks. Clean; low friction; no changes needed in Phase 7.
- `test_top10_filter.py` — Small and focused. Timeout calls exist but the file is short enough
  that they are not the dominant cost.
- `test_breeder_page_interactions.py` — 4 timeouts, no style assertions. Already well-scoped.

#### Phase 0 recorded decisions

1. **No client assertions need to move layers.** All Vitest component tests are correctly placed.
   Focus for Phase 2 is helper extraction, not test migration.

2. **E2E slider behavior tests (test_snapshot_filters.py) are candidates for thinning in Phase 7**
   but are NOT removed now — they currently cover slider behavior that is not yet verified in
   the Vitest suite for the snapshot/breeder pages specifically. Defer removal to Phase 7 after
   a deliberate check.

3. **Redundant E2E tests** (advanced-filters toggle, filter badge) could be removed from
   `test_table_interactions.py` in Phase 7 once we confirm the Vitest coverage is sufficient.

4. **test_visual_contracts.py** is lean and correct. Leave it alone.

5. **Pre-existing E2E failure** (`test_tab_switching_between_breeder_and_dealer_views`): do not
   fix in this plan phase. Record it here so Phase 7 includes it.

6. **Watch mode** (`npm run test`) already runs Vitest in watch mode via the `test` script.
   Phase 1 can wire `make test-client-fast` to `npm test -- --reporter=dot` and
   `make test-client-watch` to `npm test` (interactive watch mode).

7. **Fast vs coverage timing:** no-coverage run takes ~5.1s vs 7.1s with coverage — a 28% saving.
   Worthwhile for quick iteration but not dramatic. The bigger win comes from running a single file
   in watch mode (sub-second feedback) rather than the full suite.

---

## Phase 1 — Fast loop first

**Before starting:** Read the **Phase 0 Findings** section above. Decision 6 and Decision 7 give the specific commands and timing baseline to use for steps 6–10.

**Goal:** Improve the default local iteration path before adding heavier tooling.

- [x] 6. Add a fast client test command in `Makefile` that runs the client suite without coverage.
      Suggested shape:
      - `make test-client-fast`
      - or a clearly named equivalent

- [x] 7. Keep `make test-client` as the coverage-enforcing command so existing instructions and CI guarantees remain intact.

- [x] 8. Add a watch-mode client command for active component work.
      Suggested shape:
      - `make test-client-watch`
      - or `npm run test:watch` wired through `Makefile`

- [x] 9. Update the intended local order of operations in docs and agent instructions:
      - fast tests first
      - coverage second
      - visual/browser tests when CSS or layout changes are involved
      - E2E last

- [x] 10. Verify that the fast command is materially faster than the current `make test-client` path and becomes the recommended default for active iteration.

### Phase 1 Outputs

- A clearly defined fast local loop
- No regression to existing coverage enforcement

### Phase 1 Verification

- `make test-client-fast` passes
- `make test-client` still passes
- Timing delta is documented

### Phase 1 Decisions To Record

- Final command names
- Whether watch mode is practical enough to recommend by default

### Phase 1 Findings

#### Implementation

- `make test-client-fast` → `cd client && npm test -- --reporter=dot` (190 tests, no coverage thresholds)
- `make test-client-watch` → `cd client && npm run test:watch` (interactive Vitest watch mode)
- `"test:watch": "vitest"` added to `client/package.json` scripts
- `.github/copilot-instructions.md` updated: recommended order is now fast → coverage → E2E

#### Timing (measured 2026-03-08, MacBook, macOS, warm run)

| Command | Wall time |
| --- | --- |
| `make test-client-fast` | **5.9 s** |
| `make test-client` (coverage) | **6.5 s** |

Phase 0 cold-run baseline: 5.1 s (no coverage) vs 7.1 s (coverage). The savings are
consistent: skipping coverage instrumentation and reporting reliably saves ~10–28% depending
on system load and caching state.

#### Phase 1 recorded decisions

1. **Command names confirmed:** `make test-client-fast` and `make test-client-watch` match the
   Phase 0 suggestion exactly.

2. **Watch mode:** `make test-client-watch` is practical for active component development.
   It requires an interactive terminal (not suitable for make pipelines), which is the expected
   and correct behaviour for a watch-mode command.

3. **`make test-client-fast` is the new recommended default for active iteration.** The fast
   command passes the full test suite (190 tests, all 11 files) without enforcing coverage
   thresholds — useful when branching into new code before writing tests. `make test-client`
   remains the mandatory gate before committing.

---

## Phase 2 — Test helper extraction and smaller seams

**Before starting:** Read the **Phase 0 Findings** and **Phase 1 Findings** sections above. The Phase 0 "Client test file inventory", "URL mock duplicated in 3 files", `clickDownloadAndGetBlob` duplication, and `openDatePicker`/`openAdvancedFilters` duplication findings directly drive steps 11–13. Phase 1 Findings confirm the final command names and the new recommended iteration order (fast → coverage → E2E).

**Goal:** Reduce setup friction and improve failure locality in ordinary client tests.

- [x] 11. Create shared client test helpers for repeated setup patterns.
      Candidate responsibilities:
      - URL/download mocks
      - table render harnesses
      - shared row and column fixtures
      - domain-level selectors or convenience assertions

- [x] 12. Refactor `client/src/shared/components/SortableTable.test.ts` to use shared helpers and remove duplicated setup.

- [x] 13. Refactor `client/src/history-page/HistoryTable.test.ts` to use the same shared infrastructure where possible.

- [x] 14. Extract high-churn table logic into smaller pure TypeScript seams where practical.
      Prioritise:
      - filter state derivation
      - visible-row computation
      - summary/count logic
      - download row selection logic if it can be separated cleanly

- [x] 15. Add small parametrized tests for any extracted pure helpers.

- [x] 16. Confirm that failure messages now point more often at a specific helper or component state instead of a large DOM-heavy test body.

### Phase 2 Outputs

- Shared client-side test kit
- Smaller test seams for high-complexity components
- Reduced duplication across component tests

### Phase 2 Verification

- Existing component tests remain green
- Extracted helper tests remain sub-second
- No behavior drift in the affected components

### Phase 2 Decisions To Record

- Which helper patterns worked well and should be reused
- Which component logic was not worth extracting because the seam was artificial

### Phase 2 Findings

#### Implementation (completed 2026-03-08)

**New file: `client/src/test-utils/index.ts`**

Central test-helper module.  Exports four helpers:

| Export | Purpose |
| --- | --- |
| `setupBlobUrlMock()` | Installs `URL.createObjectURL` / `revokeObjectURL` stubs via `beforeAll/beforeEach/afterAll`. Replaces 6-line boilerplate duplicated in three files. |
| `clickDownloadAndGetBlob(container)` | Clicks the CSV download link and returns the `Blob`. Was independently defined in `SortableTable.test.ts` and `HistoryTable.test.ts`. |
| `openAdvancedFilters(container)` | Clicks the More Filters toggle (`:not(.date-expand-btn)` selector works for both `SortableTable` and `HistoryTable`). Replaces 2-line inline setup in four tests. |
| `openDatePicker(container)` | Clicks the date-picker expand button.  Local to `HistoryTable.test.ts` before extraction. |

**Extracted pure-TS seams:**

- `applySearchFilter(rows, columns, searchText)` added to `client/src/shared/table-utils.ts`
  – Identical logic was copy-pasted in `SortableTable.svelte` and `HistoryTable.svelte`. Both
  components now import the shared function.  7 parametrized tests added to `table-utils.test.ts`.

- `collectAllDates(rows, dateColumn)` extracted from `HistoryTable.svelte` to
  `client/src/history-page/history-utils.ts`.  8 unit tests added in the new
  `history-page/history-utils.test.ts`.  `HistoryTable.svelte` imports it from the new module.

**Seams not extracted (artificial):**

- `visibleRows` derivation in each component — tightly coupled to 6+ `$state` variables;
  the outer shape of `$derived.by(() => {...})` calling a helper function would just move the
  same code without creating a testable seam. Behavior is already well-covered by component tests.
- Price / wishlist range filters — differ slightly between components (NaN handling), so a
  shared extraction would introduce coupling without a clean contract.
- `activeFilterCount` computation — trivial arithmetic on state; extraction would add
  indirection without value.

#### Test count delta

| Before Phase 2 | After Phase 2 |
| ---: | ---: |
| 190 tests, 11 files | 205 tests, 12 files |

#### Phase 2 recorded decisions

1. **Shared test-helper location:** `client/src/test-utils/index.ts`.  Not under `shared/`
   (which is for production code) and not co-located with any one component.

2. **`setupBlobUrlMock()` call semantics:** The function calls Vitest lifecycle hooks
   (`beforeAll`, `beforeEach`, `afterAll`) inline.  It must be called at file scope or inside a
   `describe` block — not inside a `test`.  All three usages follow this constraint.

3. **`openAdvancedFilters` selector:** The `:not(.date-expand-btn)` suffix makes the helper
   correct for both `SortableTable` (no date button present) and `HistoryTable` (has a separate
   date-expand button).  Use this selector everywhere.

4. **`applySearchFilter` placement:** Added to `table-utils.ts` alongside `sortRows` and
   `buildCsv`.  It belongs there: same signature style, no Svelte dependencies, directly
   relevant to table rendering.

5. **`collectAllDates` placement:** Moved to `history-page/history-utils.ts` rather than
   `shared/table-utils.ts` because the semantics are history-page-specific (ascending date
   order, skip-empty logic tied to how the history CSV is structured).

6. **`table-utils.test.ts` URL-mock refactor:** `vi.stubGlobal` was previously called inline at
   describe scope (runs during test collection rather than as a lifecycle hook).
   Replaced with `setupBlobUrlMock()` inside `describe('triggerDownload', ...)` for consistency.
   The `vi, beforeEach, afterAll` imports were removed from the file entirely.

---

## Phase 3 — Static token guardrails

**Before starting:** Read the **Phase 0 Findings**, **Phase 1 Findings**, and **Phase 2 Findings** sections above. Phase 0 establishes the token architecture (`templates/common.css` `:root` block, naming conventions) and the CSS 3-layer model that guardrails must respect. Phase 1 Findings confirm that fast tests are the recommended default for iteration. Phase 2 Findings document the `client/src/test-utils/index.ts` shared helper module and the conventions to follow when adding new test infrastructure.

**Goal:** Shift obvious style-system failures to the cheapest possible layer.

- [x] 17. Create a shared token parser utility for `templates/common.css`.
      It should parse the `:root` block into a stable token map.

- [x] 18. Add a design-token assertion test to the ordinary client suite.
      Preferred behavior:
      - readable diff when a token changes
      - stable ordering
      - easy snapshot review or structured map comparison

- [x] 19. Add a Svelte CSS compliance audit that scans `client/src/**/*.svelte` style blocks and rejects hardcoded values that duplicate known design tokens.

- [x] 20. Keep the compliance rule intentionally narrow at first:
      - only Svelte component styles
      - only hardcoded values that match known tokens
      - clear allowlist for legitimate values like `transparent`, `none`, `0`, and other obvious non-token cases

- [x] 21. Make failure messages prescriptive.
      Example format:
      - `FilterButton.svelte uses hardcoded #3498db; use var(--color-accent)`

- [x] 22. Run these checks as part of the fast client loop only if they stay cheap enough.
      If they meaningfully slow down the loop, keep them in `make test-client` but document the tradeoff.

### Phase 3 Outputs

- Token drift guardrail
- Preventive Svelte style compliance rule

### Phase 3 Verification

- A deliberate hardcoded token-equivalent value fails with a file-specific message
- A deliberate token drift change produces a readable diff

### Phase 3 Decisions To Record

- Whether snapshot or structured token assertion is the clearer maintenance model
- Whether the compliance rule is low-noise enough to keep broad or needs tighter scoping

---

### Phase 3 Findings

#### Implementation (completed 2026-03-08)

**New file: `client/src/test-utils/design-tokens.ts`**

Parser/utility module exporting four items:

| Export | Purpose |
| --- | --- |
| `TOKEN_CSS_PATH` | Absolute path to `templates/common.css`, resolved via `import.meta.url`. |
| `CLIENT_SRC_DIR` | Absolute path to `client/src/`, used as the root for Svelte file discovery. |
| `parseTokens(cssPath?)` | Parses every `--custom-property: value;` entry from the `:root` block; returns an alphabetically-sorted `Record<string, string>` for stable diffs. |
| `findSvelteFiles(dir?)` | Recursively collects all `.svelte` file paths under `CLIENT_SRC_DIR`. |
| `extractStyleBlock(source)` | Extracts concatenated `<style>` block text from a Svelte source string, with CSS block comments stripped to prevent false positives. |
| `normalizeHex(hex)` | Expands 3-char shorthand hex to 6-char lowercase form (`#abc` → `#aabbcc`). Required for reliable equality comparison with token values. |

**New file: `client/src/test-utils/design-tokens.test.ts`**

Two describe blocks:

1. **`design tokens — templates/common.css`** (step 18)
   - `token map matches snapshot` — `toMatchSnapshot()` captures all 44 tokens sorted
     alphabetically. Snapshot file:
     `client/src/test-utils/__snapshots__/design-tokens.test.ts.snap`.
     Diff on a token change is a single property change in a compact object — instantly readable.

2. **`Svelte CSS compliance — no hardcoded token-equivalent colours`** (steps 19–21)
   - `it.each` generates one test case per `.svelte` file (currently 10 files).
   - Each case scans the file's `<style>` block for hex color literals that match a known token
     value. Violations produce a prescriptive error:
     `FileName.svelte uses hardcoded #3498db; use var(--color-accent)`.

**Allowlisted values** (accepted even if they equal a token's hex):

| Value | Reason |
| --- | --- |
| `#fff`, `#ffffff`, `white` | White text on coloured backgrounds — a conventional contrast pattern. Using `var(--color-surface)` as text colour would be semantically wrong. A dedicated `--color-text-inverse` token can address this later. |
| `transparent`, `none`, `inherit`, `currentcolor` | Structural CSS — not semantic colour choices. |

#### Pre-existing Svelte style state

All 10 existing Svelte components pass the compliance audit. The only hardcoded hex values present
(`#fff` in `FilterButton.svelte`, `#fff`/`white` in `ToggleButton.svelte`, `#856404` and
`#d3d3d3` in `HistoryTable.svelte`/`RangeSlider.svelte`) are either in the allowlist or not
in the token map and therefore not flagged.

#### Test count delta

| Before Phase 3 | After Phase 3 |
| ---: | ---: |
| 205 tests, 12 files | 216 tests, 13 files |

#### Timing

| Command | Wall time |
| --- | --- |
| `make test-client-fast` (no coverage) | **5.5 s** |
| `make test-client` (coverage) | **~6.5 s** |

The new guardrail tests add no measurable overhead — all file reads complete in < 5 ms total.
Both commands include the guardrails. Step 22 decision: **include in fast loop** (cost is negligible).

#### Phase 3 recorded decisions

1. **Snapshot is the right model for the token test.** A diff on a token change names the exact
   property and old/new value. A structured expected-object would require hand-maintenance every
   time a token is added. Snapshot is lower friction with equivalent readability.

2. **One test case per `.svelte` file** (via `it.each`) provides the tightest failure locality.
   When a violation is introduced, exactly one test case fails and names both the file and the
   fix in the error message.

3. **Compliance audit scans only hex literals.** `rgb()`, `hsl()`, and named colors other than
   `white` are not currently used in Svelte styles and are not detected. If they appear in future,
   the scanner can be extended. The narrow scope reduces false-positive risk.

4. **`#d3d3d3` and `#856404` are not flagged.** These hardcoded values exist in `RangeSlider.svelte`
   (untracked slider-track color) and `HistoryTable.svelte` (amber date-button text). Neither
   matches a token value. They are tokenization gaps but are out of scope for a compliance audit
   that only checks for token-equivalent duplicates.

5. **`import.meta.url` for path resolution.** The utility uses `import.meta.url` +
   `fileURLToPath` rather than `process.cwd()` so the paths are correct regardless of which
   directory the test runner is invoked from.

---

## Phase 4 — DevTools MCP workflow and preview ergonomics

**Before starting:** Read the **Phase 0 Findings**, **Phase 1 Findings**, **Phase 2 Findings**, and **Phase 3 Findings** sections above. Phase 0 identifies the existing `make generate-website` / `make serve-only` / `scripts/test_website_locally.py` preview path that this phase must reuse rather than duplicate. Phase 3 Findings document the new static guardrails layer and confirm that DevTools MCP is diagnosis, not enforcement — this phase makes that workflow explicit and documented.

**Goal:** Make real-browser interactive inspection an explicit part of the agent workflow.

- [ ] 23. Review the existing preview path in `scripts/test_website_locally.py` and `Makefile`.

- [ ] 24. Decide whether a new `make preview` command is needed.
      Preferred outcome:
      - it is a thin alias over existing behavior
      - it does not create a parallel serving implementation

- [ ] 25. Document the interactive inspection workflow in `.github/copilot-instructions.md`.
      Include:
      - how to generate the site
      - how to serve the site
      - how to inspect target pages through Chrome DevTools MCP
      - when to use this workflow instead of immediately writing or running E2E

- [ ] 26. Add a DevTools MCP operating playbook.
      It should define:
      - trigger conditions
      - inspection order
      - safe browser profile guidance
      - expectation that useful discoveries become automated assertions

- [ ] 27. Validate the workflow against at least one representative style question.
      Example:
      - inspect the computed background colour of an active filter button on a served page

### Phase 4 Outputs

- A documented interactive browser inspection path
- No duplicate preview stack

### Phase 4 Verification

- The agent can inspect a locally served page in a real browser without running the full E2E suite

### Phase 4 Decisions To Record

- Whether `make preview` is worth keeping as an alias
- Whether the current serve path needs port configurability or other small ergonomics improvements

---

## Phase 5 — Browser-backed visual contract foundation

**Goal:** Add the missing middle layer for computed styles and layout contracts.

- [ ] 28. Add browser-backed client test support.
      Preferred first choice:
      - Vitest Browser Mode
      Fallback if needed:
      - Playwright component tests

- [ ] 29. Create a dedicated browser-test configuration separate from the existing `client/vite.config.ts` suite.

- [ ] 30. Keep browser-visual tests separate from logic coverage.
      They should not distort or inflate normal logic coverage reporting.

- [ ] 31. Add token-aware helpers that read `templates/common.css` and convert token values into the browser-comparable format used by `getComputedStyle()`.

- [ ] 32. Confirm that global CSS tokens from `templates/common.css` are reliably loaded in the browser-backed component environment.

- [ ] 33. Add a dedicated command in `Makefile`.
      Suggested shape:
      - `make test-visual`

- [ ] 34. Record baseline runtime and failure output quality for the new browser-backed layer.

### Phase 5 Outputs

- Browser-backed component test runner
- Token-aware style assertion helpers
- Dedicated visual test command

### Phase 5 Verification

- Browser-backed test environment runs successfully in CI and locally
- Computed style assertions resolve CSS custom properties to actual rendered values

### Phase 5 Decisions To Record

- Final runner choice: Vitest Browser Mode or Playwright component tests
- Any limitations in pseudo-elements, isolation, or CSS loading

---

## Phase 6 — Visual contract rollout

**Goal:** Cover the most valuable visual regressions first, not every possible style.

### Initial contract matrix

- [ ] 35. Add `FilterButton` visual contracts:
      - active background
      - active border
      - inactive background
      - active/inactive state semantics

- [ ] 36. Add `SearchInput` visual contracts:
      - unfocused border
      - focused border
      - focus state stability

- [ ] 37. Add `FiltersPanel` visual contracts:
      - background
      - border
      - visible/collapsed state if meaningful in the component layer

- [ ] 38. Add `RangeSlider` visual contracts for inspectable elements:
      - labels
      - value text
      - any container styling that is stable and meaningful

- [ ] 39. Add `TableStats` visual contracts:
      - info-strip background
      - visible count strip styling

- [ ] 40. Add `DateFilter` visual contracts:
      - section border
      - expand button styling
      - open/closed state chrome if stable enough

- [ ] 41. Add one table-level contract for sticky header or other behavior that is hard to trust in `happy-dom` but stable in a component or narrow browser harness.

- [ ] 42. Add one responsive layout contract for a high-risk surface, such as the filter bar or filter panel arrangement.

### Contract scope rules

- [ ] 43. Keep contracts semantic and stable.
      Test what matters to the product:
      - signal state is visually distinct
      - active controls look active
      - focus states are visible
      - panels and headers retain expected chrome
      - responsive layout does not collapse incorrectly

- [ ] 44. Avoid turning browser-backed tests into screenshot diffs or giant all-style snapshots.

### Phase 6 Outputs

- A small, defensible visual contract suite
- Coverage focused on the regressions agents are most likely to introduce

### Phase 6 Verification

- Deliberately wrong token usage fails here before E2E is needed
- At least one layout-oriented contract exists, not just colour contracts

### Phase 6 Decisions To Record

- Which contracts were high-value
- Which proposed contracts were too brittle and should be removed or moved upward/downward

---

## Phase 7 — E2E cleanup and narrowing

**Goal:** Remove low-level style burden from E2E and improve signal quality in the tests that remain.

- [ ] 45. Add a Python token helper for E2E so remaining style assertions do not hardcode rgb literals.

- [ ] 46. Replace hardcoded colour values in:
      - `tests/e2e/test_navigation_and_page_loads.py`
      - `tests/e2e/test_snapshot_filters.py`
      - `tests/e2e/test_history_date_filter.py`

- [ ] 47. Remove duplicated style assertions from E2E once equivalent browser-component contracts exist.

- [ ] 48. Replace avoidable `page.wait_for_timeout(...)` calls with `wait_for_selector()` or `wait_for_function()` where observable state exists.

- [ ] 49. Improve helper-level diagnostics in E2E so failures say:
      - what state was expected
      - what selector or element was checked
      - what visible count or computed value actually occurred

- [ ] 50. Keep E2E coverage focused on:
      - generated page loads
      - navigation
      - URL state
      - downloads
      - multi-layer integration
      - asset and data-shape correctness

### Phase 7 Outputs

- Thinner, more maintainable E2E suite
- Less brittle style coupling in full-site tests

### Phase 7 Verification

- `make test-e2e` remains green
- E2E runtime and setup noise decrease or at least do not worsen

### Phase 7 Decisions To Record

- Which E2E style assertions remained because they genuinely test page-level composition
- Which waits could not be removed and why

---

## Phase 8 — CI ordering and workflow guidance

**Goal:** Ensure CI surfaces the fastest, most localising failure first.

- [ ] 51. Reorder `.github/workflows/test.yml` so failure order is:
      - fast client guardrails and fast client tests
      - browser-backed visual contracts
      - Python tests
      - conditional E2E

- [ ] 52. Cache Node dependencies and Playwright browser binaries so browser-backed visual tests do not introduce avoidable CI cost.

- [ ] 53. Update `docs/MIGRATION_PLAN.md` with the revised testing pyramid once the new layers are stable enough to document as authoritative.

- [ ] 54. Update `.github/copilot-instructions.md` so future agents know:
      - the intended local command order
      - when DevTools MCP should be used
      - when browser-backed visual tests are required
      - when E2E is required versus unnecessary

- [ ] 55. Run a controlled failure-order test by introducing one deliberate failure in each layer and confirming that CI fails first at the cheapest valid layer.

### Phase 8 Outputs

- CI workflow aligned with the revised pyramid
- Agent-facing docs aligned with actual practice

### Phase 8 Verification

- CI ordering behaves as intended
- Documentation and commands match reality

### Phase 8 Decisions To Record

- Whether any browser-backed visual suite is too expensive for the main workflow and should be conditionally triggered

---

## Phase 9 — Accessibility baseline (optional after core loop lands)

**Goal:** Capture accessibility and page-quality signals without delaying the core redesign.

- [ ] 56. Use DevTools MCP `lighthouse_audit` on representative pages:
      - `breeder.html`
      - `snapshot.html`
      - `history.html`

- [ ] 57. Record baseline results in a dedicated markdown document.

- [ ] 58. Decide whether a future `make test-a11y` or other formal gate is justified once the baseline is stable and the false-positive rate is understood.

### Phase 9 Outputs

- Accessibility/performance baseline document

### Phase 9 Verification

- None required for the main delivery path; this phase is intentionally non-blocking

### Phase 9 Decisions To Record

- Whether accessibility should become a formal gate later

---

## File inventory

### Likely new files

| File | Purpose |
| --- | --- |
| `docs/TESTING_IMPROVEMENTS_PLAN_REVISED.md` | This revised phase plan |
| `client/src/shared/__tests__/token-parser.ts` or equivalent | Parse design tokens from `templates/common.css` |
| `client/src/shared/__tests__/design-tokens.test.ts` or equivalent | Token drift guardrail |
| `client/src/shared/__tests__/css-token-compliance.test.ts` or equivalent | Svelte style compliance audit |
| `client/vite.browser.config.ts` or equivalent | Browser-backed visual test configuration |
| `client/src/test-utils/token-colors.ts` or equivalent | Token-aware browser assertion helper |
| `tests/e2e/css_tokens.py` or equivalent | Python token-aware style helper for E2E |
| Additional `*.visual.test.ts` files | Component visual contracts |
| Optional accessibility baseline document | Lighthouse audit record |

### Likely modified files

| File | Purpose |
| --- | --- |
| `Makefile` | Add fast client, watch, visual, and optional preview alias commands |
| `client/package.json` | Add scripts and browser-backed test dependencies |
| `client/vite.config.ts` | Coverage exclusions and shared test behavior updates |
| `.github/copilot-instructions.md` | Document the revised agent workflow |
| `docs/MIGRATION_PLAN.md` | Record the updated test pyramid once stabilized |
| `tests/e2e/test_navigation_and_page_loads.py` | Token-aware style assertions or moved-down checks |
| `tests/e2e/test_snapshot_filters.py` | Timeout cleanup and E2E narrowing |
| `tests/e2e/test_history_date_filter.py` | Timeout cleanup and moved-down style duplication |

---

## Acceptance criteria

1. The repo has a fast client command that is the recommended first loop for active work.
2. Design-token drift and hardcoded token-equivalent values are caught before E2E.
3. Browser-backed component tests catch at least one deliberately introduced computed-style regression before E2E is needed.
4. E2E becomes narrower and more integration-focused, not broader.
5. DevTools MCP is documented as an agent workflow and used as a bridge from diagnosis to durable tests.
6. CI failure ordering reflects the cheapest valid test layer first.

---

## Key decisions

- The revised plan keeps the strongest parts of `docs/TESTING_IMPROVEMENTS_PLAN.md`, especially:
  - token-aware style assertions
  - browser-backed visual contracts
  - E2E style cleanup
  - DevTools MCP as a complementary workflow

- The revised plan changes the order of work to prioritize:
  - fast local feedback
  - test-helper extraction
  - smaller seams in large component tests
  - reuse of existing preview infrastructure
  - broader visual contracts beyond colour-only checks

- DevTools MCP remains non-blocking and interactive.

- E2E remains required for page-level and full-site behavior.

---

## Further considerations

### Runner choice

Start with Vitest Browser Mode because it fits the current Vite and Testing Library setup.
If CSS loading, isolation, or debugging quality is materially worse than Playwright component
tests, switch early rather than forcing a poor fit.

### Pseudo-elements

Pseudo-elements like slider thumbs remain hard to validate through ordinary computed-style
assertions. Static compliance rules plus limited interactive inspection are acceptable guards for
those cases.

### Keep the contract matrix small

The purpose of browser-backed visual tests is not to mirror the entire CSS layer. The purpose is
to protect the highest-value regressions with direct, explainable failures.

### This document must evolve

After each phase, update the next phases based on what was learned. If a phase reveals a better
runner, a better helper shape, or a better division between browser-backed tests and E2E, the plan
should reflect that immediately rather than preserving outdated assumptions.
