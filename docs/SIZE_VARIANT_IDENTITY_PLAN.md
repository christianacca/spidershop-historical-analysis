# Size Variant Identity — Execution Plan

## Before You Start

**Read `docs/SIZE_VARIANT_IDENTITY_REQUIREMENTS.md` in full before doing anything else.**

That document is the source of truth for:

- all logic rules and policy decisions (Decisions 1–7),
- the exact expected CSV column values and sparkline strings for each scenario,
- the normative acceptance scenarios A, B, C, D that all tests must pass,
- the tooltip message wording,
- the column contract for `Size (cm)`, `Price`, `Price History`, `Wishlist`, `Wishlist History`, `Drivers`, and the 7 hidden metadata columns.

If this plan and the requirements document disagree, the requirements document wins.

---

## TL;DR

Migrate breeder and dealer matrices from `(scientific_name, size_cm)` row-key to
`scientific_name`, via a shared transition-detection layer that carries or neutralizes
wishlist and price evidence based on confirmed / ambiguous / multi-variant lineage state.

Five sequential phases. Each phase is independently verifiable before the next begins.

---

## Key Architecture Facts

- `k2 = (scientific_name, size_cm)` — current row key in both matrices and all supporting
  code.
- `prepare_matrix_analysis()` in `matrix_workflow.py` is the shared entry point; groups
  rows, builds run index, computes `wishlist_pressure_map`.
- `compute_wishlist_pressure(rows)` keys off `k2` — a species-level equivalent is needed
  in Phase 4.
- `Drivers` column is currently **not** written to CSV (`table_columns` excludes it) — it
  must start being written in Phase 3 because hidden metadata columns come after it.
- `get_species_list()` in `species_detail.py` currently returns `list[tuple[str, str]]`
  (species, size) — becomes `list[str]` in Phase 5.
- Zero transition/lineage code exists anywhere in the codebase.

---

## Phase 1 — URL Normalization + Transition Detection

**Goal:** Pure logic layer — no matrix changes. TDD red → green for both new modules.

**Steps:**

- [ ] 1. **RED** — Write `tests/shared_module/test_url_utils.py`:
  - All 5 spec normalization examples from the requirements `URL normalization` section
  - Edge cases: empty string, missing scheme, blank URL, non-product URL

- [ ] 2. **GREEN** — Create `src/shared/url_utils.py`:
  - `normalize_product_url(url: str) -> str` per spec rules exactly
  - Use `urllib.parse.urlparse` only — no external dependencies

- [ ] 3. **RED** — Write `tests/scrape_module/test_listing_lineage.py`:
  - `none` for a species with only one historically observed size
  - `confirmed-transition`: same normalized URL + new size within 3 runs + no same-run
    overlap + no competing listing → `confirmed-transition`
  - `ambiguous-transition` from URL mismatch
  - `ambiguous-transition` from gap > 3 runs
  - `ambiguous-transition` from same-run overlap during handoff window
  - `ambiguous-transition` from missing/blank URL
  - `multi-variant`: two sizes active in current run overrides any prior state
  - Precedence: `multi-variant > ambiguous-transition > confirmed-transition > none`
  - Sequential transitions (3→5→7): hidden metadata reports most recent event only;
    `Previous Size (cm)=5`, `Current Active Size (cm)=7`
  - `Transition Date` = date portion of first run where new size appears
  - `Current Active Size (cm)`: comma-separated ascending list for `multi-variant` state
  - `Previous Size (cm)`: blank for `none` and `multi-variant`

- [ ] 4. **GREEN** — Create `src/scrape/listing_lineage.py`:
  - Define `LineageResult` dataclass with fields: `lineage_status`,
    `previous_size`, `current_active_size`, `transition_date`,
    `price_evidence_state`, `wishlist_evidence_state`, `transition_message`
  - Implement `detect_species_lineage(history_rows: list[dict], scientific_name: str) ->
    LineageResult`
  - Algorithm:
    1. Call `group_by_run(history_rows)`, produce sorted `ordered_runs`
    2. For each run, determine which sizes of this scientific name are present
    3. Detect handoff events: a size goes absent while a different size appears
    4. For each handoff, check all 5 confirmed-transition conditions (Decision 2)
    5. Apply precedence rule
    6. Derive all metadata fields per spec rules
    7. Generate `transition_message` per spec tooltip patterns
  - Imports: `normalize_product_url` from `shared.url_utils`;
    `group_by_run` from `shared.history_utils`

- [ ] 5. `make test` — all tests green

- [ ] 6. Commit: `git add -p && git commit -m "feat(lineage): add URL normalization and transition detection (Phase 1)"`

**Phase 1 closing steps:**

- [ ] Mark all steps above completed
- [ ] **Smell review:** Should `listing_lineage.py` live in `src/shared/` rather than
  `src/scrape/`? Both matrices will consume it — check for scrape-only imports. Refactor
  placement if needed.
- [ ] **Feed forward:** Document the exact `LineageResult` field names for use in Phase 3
  metadata columns. Note that `detect_species_lineage` is called once per scientific name,
  not once per `k2` key. Update Phase 3 steps if the interface needs adjustment.
- [ ] Pause only for a critical placement decision (scrape/ vs shared/) that cannot be
  resolved from context.

---

## Phase 2 — Species-Level Supply Timeline

**Goal:** All supply metrics (OOS runs, stock pattern, stock reliability, avg OOS duration,
restock speed) computable from a species-level presence timeline. Ready to be consumed by
both matrices in Phase 4.

**Steps:**

- [ ] 1. **RED** — Write tests for `build_species_presence_timeline()`:
  - Multi-variant run (two sizes active) → `True`
  - Absent run → `False`
  - Transition run (old size gone, new size appears same run) → `True` (no gap)

- [ ] 2. **RED** — Write tests for breeder supply metrics:
  - `compute_species_current_oos_runs(timeline, ordered_runs)` — consecutive absent runs
    ending at current run; counter resets on re-presence (not additive across retired sizes
    per Decision 3A worded example)
  - `build_species_stock_pattern(timeline, ordered_runs)` — mirrors existing pattern labels:
    `Always`, `Emerging`, `Cyclical`, `Sustained`, `Newly Observed`

- [ ] 3. **RED** — Write tests for dealer supply metrics:
  - `compute_species_stock_reliability(timeline)` — presence ratio → `High`/`Medium`/`Low`
  - `compute_species_avg_oos_duration(timeline, ordered_runs)` — average length of absence
    events
  - `compute_species_restock_speed(avg_oos: float)` — `Fast`/`Moderate`/`Slow`

- [ ] 4. **GREEN** — Add all 6 functions to `src/shared/history_utils.py`:
  - `build_species_presence_timeline(history_rows, scientific_name) -> dict[str, bool]`
  - `compute_species_current_oos_runs(timeline, ordered_runs) -> int`
  - `build_species_stock_pattern(timeline, ordered_runs) -> str`
  - `compute_species_stock_reliability(timeline) -> str`
  - `compute_species_avg_oos_duration(timeline, ordered_runs) -> float`
  - `compute_species_restock_speed(avg_oos) -> str`

- [ ] 5. `make test` + `python scripts/check_coverage.py --module=shared/history_utils.py`

- [ ] 6. Commit: `git add -p && git commit -m "feat(lineage): add species-level supply timeline functions (Phase 2)"`

**Phase 2 closing steps:**

- [ ] Mark all steps above completed
- [ ] **Smell review:** Check for duplication between the new functions and the existing
  inline OOS event counting loop in `dealer_matrix.py`. Extract shared constants or
  logic if duplicated.
- [ ] **Feed forward:** `ordered_runs = sorted(group_by_run(history_rows).keys())` will be
  needed by multiple Phase 4 functions — note that it should be pre-computed once in the
  matrix workflow and passed in. Update Phase 4 step 4 accordingly.
- [ ] Pause only if a threshold alignment issue arises with existing
  `DEALER_HIGH_RELIABILITY_THRESHOLD` constants.

---

## Phase 3 — Hidden Metadata Columns (Intermediate Validation State)

**Goal:** Both matrices output `Drivers` + the 7 hidden metadata columns in their CSV files.
Matrices are **still** `(scientific_name, size_cm)`-keyed at this stage.

The spec explicitly permits this as an auditable intermediate state. It is **not** a valid
final shipped state — Phase 4 is mandatory.

**Steps:**

- [ ] 1. **Read** `src/shared/summary_utils.py` — confirm whether `write_matrix_outputs`
  currently writes `Drivers` to CSV (check `table_columns` vs `fallback_fieldnames`). Note
  the exact CSV-writing mechanism (`DictWriter`, `fieldnames`). The answer determines
  whether Phase 3 must add `Drivers` to `table_columns` or whether it is already there.

- [ ] 2. **RED** — Write hidden-column output tests in
  `tests/scrape_module/test_breeder_matrix.py`:
  - Scenario A fixture (confirmed transition history shape) → assert all 7 hidden column
    values exactly as specified in the requirements document
  - Scenario B fixture (ambiguous transition) → assert exact `ambiguous-transition` values
  - Scenario C fixture (two active sizes) → assert exact `multi-variant` values
  - Scenario D fixture (stable single size) → assert `none` state, blank `Previous Size`,
    blank `Transition Message`
  - Assert `Drivers` IS written to the CSV output

- [ ] 3. **Implement** `compute_lineage_metadata(scientific_name, history_rows,
  ordered_runs) -> dict` in `src/scrape/matrix_workflow.py`:
  - Calls `detect_species_lineage(history_rows, scientific_name)`
  - Returns dict with all 7 hidden column values ready to merge into a matrix row

- [ ] 4. **Update** `src/scrape/breeder_matrix.py`:
  - Group the existing `present_runs_map` keys by scientific name
  - Call `compute_lineage_metadata` once per scientific name
  - Attach the 7 hidden column values + `Drivers` to each row dict
  - Update `write_breeder_outputs`: add `Drivers` and the 7 hidden column names to
    `table_columns` (appended after the existing display columns)

- [ ] 5. **RED + GREEN** — Write dealer hidden-column tests; update
  `src/scrape/dealer_matrix.py` identically

- [ ] 6. Update snapshot tests in `tests/scrape_module/__snapshots__/` — follow the
  Snapshot Test Protocol from `copilot-instructions.md` (investigate every diff line before
  updating; never blindly run `--snapshot-update`)

- [ ] 7. `make test` + coverage check for both matrix modules

- [ ] 8. **Optional real-data audit** (only if CSVs present in `tmp/local-testing/`):
  `make generate-website`, then inspect the output CSV for `Chilobrachys sp. "South Thai"`
  to verify lineage detection is working against real history before proceeding to Phase 4.

- [ ] 9. Commit: `git add -p && git commit -m "feat(lineage): output Drivers and hidden lineage metadata columns (Phase 3)"`

**Phase 3 closing steps:**

- [ ] Mark all steps above completed
- [ ] **Smell review:** Is `compute_lineage_metadata` a thin delegation wrapper? Any
  lineage logic that has leaked into `matrix_workflow.py` rather than staying in
  `listing_lineage.py`?
- [ ] **Feed forward:** Confirm the final column order (`Drivers` followed by the 7 hidden
  columns at end of row) and document it for Phase 4, which must preserve this order when
  rows change key.
- [ ] Pause if a real-data species reveals a corner case in the detection algorithm not
  covered by the spec (e.g. a species with multiple ambiguous sequential handoffs).

---

## Phase 4 — Species-Level Row Identity (Core Migration)

**Goal:** One row per species in both matrices. All acceptance scenarios A, B, C, D from
the requirements document pass exactly. This is the mandatory final analysis state.

**Steps:**

- [ ] 1. **RED** — Write full acceptance scenario tests in
  `tests/scrape_module/test_breeder_matrix.py`:
  - **Scenario A** (confirmed transition): build exact history fixture → assert breeder row
    matches spec CSV exactly, including `Size (cm)=5`, `Wishlist=120 🔥 ↑`,
    `Wishlist History=▁▁▂▃▄▅▆█`, `Price History=▄▄▄▄▄▄▄▄`, `Signal=🔥`, `Drivers`
    containing the transition clause
  - **Scenario B** (ambiguous): `Price History=-`, `Wishlist History=-`, delta forced `→`
  - **Scenario C** (multi-variant): `Size (cm)="3, 5"`, `Price=Multiple active prices`,
    `Price History=-`, `Wishlist=120 🔥 →`
  - **Scenario D** (stable single-size): all public columns match pre-feature behavior
    exactly; `Lineage Status=none`
  - Assert each scientific name appears **exactly once** in the output (key regression guard)

- [ ] 2. **RED** — Write the same scenario tests for
  `tests/scrape_module/test_dealer_matrix.py`

- [ ] 3. Add `k1(row) -> str` (returns `row["scientific_name"]`) to
  `src/shared/history_utils.py`

- [ ] 4. **Refactor** `src/scrape/matrix_workflow.py`:
  - `prepare_matrix_analysis` now also returns `species_lineage_map: dict[str,
    LineageResult]` (calls `detect_species_lineage` once per unique scientific name)
  - Add `build_species_wishlist_pressure_map(history_rows, current_run_rows,
    species_lineage_map) -> dict[str, str]`:
    - Compute effective current wishlist count per species: max of active variants for
      `multi-variant`; confirmed lineage count for confirmed transition; `0` for ambiguous
      OUT per spec Decision 4 OUT-state carryover rules
    - Apply same relative ranking algorithm as existing `compute_wishlist_pressure`
  - Add `generate_stitched_price_sparkline(scientific_name, lineage_result, by_run, runs,
    max_runs=8) -> str`:
    - Confirmed transition: stitch pre-transition (old `k2`) + post-transition (new `k2`)
      prices into one 8-run chronological window per Price sparkline construction rule
    - All other states: return `"-"`
  - Add `iter_lookback_rows_for_species(scientific_name, by_run, runs, current_run,
    run_index, lookback_window)` for species-level OOS state iteration

- [ ] 5. **Update** `src/scrape/wishlist_analysis.py`:
  - Add `compute_species_wishlist_delta(scientific_name, lineage_result, by_run, runs,
    cur_run) -> str`:
    - Confirmed transition: compare count at confirmed-lineage anchor points
    - Ambiguous / multi-variant: always `"→"`
    - None: existing `compute_wishlist_delta` behavior on current `k2` key
  - Add `get_species_wishlist_count(scientific_name, lineage_result, by_run, runs,
    cur_run) -> int`:
    - Multi-variant: max current-run count across all active variants
    - OUT with confirmed lineage: carry from that lineage (≤ 5 runs)
    - OUT with ambiguous / none: `0`

- [ ] 6. **Rewrite** outer loop in `src/scrape/breeder_matrix.py`:
  - Key by `scientific_name`; use Phase 2 species-level timeline functions for all supply
    metrics
  - Use `species_lineage_map[sci]` for lineage metadata
  - Use Phase 4 wishlist functions for count, delta, and pressure
  - Use `generate_stitched_price_sparkline` for `Price History`
  - Compute `Size (cm)` per column contract rules:
    - Single active size → plain string
    - Multiple active sizes → comma-separated ascending list (quoted)
    - OUT with one identifiable recent lineage → last-active size string
    - OUT with no identifiable recent lineage → `—`
    - Ambiguous transition: show most recent active size within the 5-run OOS window
  - Compute `Price`: `"Multiple active prices"` for multi-variant; standard
    `format_price_cell` otherwise
  - Previous price comparison: use active lineage's most recent `k2` row
  - Preserve existing breeder signal logic; `Always` species remain `❌` regardless of
    wishlist demand

- [ ] 7. **Rewrite** outer loop in `src/scrape/dealer_matrix.py` using the same pattern

- [ ] 8. Verify `sort_matrix_table` still sorts correctly on species-level rows (the
  `Wishlist` column format is unchanged; `Avg OOS Duration` is now a species-level float)

- [ ] 9. **GREEN** — all acceptance scenario tests from steps 1–2 pass

- [ ] 10. `make test` + coverage checks; run `make generate-website` for visual sanity
  check if CSVs are available in `tmp/local-testing/`

- [ ] 11. Commit: `git add -p && git commit -m "feat(lineage): migrate matrices to species-level row identity (Phase 4)"`

**Phase 4 closing steps:**

- [ ] Mark all steps above completed
- [ ] **Smell review:** `matrix_workflow.py` now has both `k2`-based and species-level
  helpers — is the separation of concerns clear? Any logic duplicated between breeder and
  dealer that belongs in `matrix_workflow.py`? Is `wishlist_analysis.py` getting
  unwieldy?
- [ ] **Feed forward:** Read `src/website/table_data_helpers.py` (or equivalent) now.
  Note the exact JSON payload field name casing. Update Phase 5 step 1 with concrete
  findings so Phase 5 starts with a clear interface contract.
- [ ] Pause if real-data run shows unexpected ranking instability the spec did not
  anticipate.

---

## Phase 5 — Website Surface Updates

**Goal:** Main tables show warning icons and tooltips on affected cells. Species pages are
species-only routed with a transition banner.

**Steps:**

- [ ] 1. **Read** `src/website/generate_website.py` and the module that builds the JSON
  payload for TypeScript pages (likely `src/website/table_data_helpers.py`). Note exact
  field name casing in the payload and how rows from the matrix CSV become page data.

- [ ] 2. **RED** — Write tests for the updated `get_species_list()` returning `list[str]`
  in `tests/website_module/test_species_detail.py`

- [ ] 3. **Update** `src/website/species_detail.py`:
  - `get_species_list(breeder_csv, dealer_csv) -> list[str]` — unique species names only
  - `_extract_csv_row_data(csv_path, scientific_name)` — match by species name only
  - `get_species_data(sci, breeder_csv, dealer_csv, history_csv)` — drop the `size`
    parameter
  - `build_chart_data(sci, history_csv, window_size=26)` — species-level timeline; drop
    the size filter
  - `get_observation_metadata(sci, history_csv)` — use `build_species_presence_timeline`
    for coverage
  - `generate_species_page(sci, common_name, species_data, chart_data, ...)` — accept
    lineage metadata from hidden columns; pass to template

- [ ] 4. **Update** `src/website/generate_website.py`:
  - Change loop from `for sci, size in get_species_list(...)` to
    `for sci in get_species_list(...)`
  - Drop `size` from all `species_detail` function calls
  - URL path remains `species/<slug>/index.html` (routing does not change per Decision 7)

- [ ] 5. **Update** the JSON payload builder:
  - Include `lineageStatus`, `priceEvidenceState`, `wishlistEvidenceState`,
    `transitionMessage` in the per-row payload — these drive client-side warning icons

- [ ] 6. **Update** `templates/species_detail.html`:
  - Transition banner near the top — shown for `confirmed-transition` and
    `ambiguous-transition`; hidden for `none` (Scenario D must have no banner)
  - Banner content: old size, new size, transition date, confirmation status, price
    interpretation note using `Transition Message` as the body text
  - Multi-variant panel: list active variants explicitly

- [ ] 7. **Update CSS** (`templates/analysis.css` or `templates/species-detail.css`):
  - Warning icon style for transition-affected price cells
  - BEM Layer 2 naming conventions; use design tokens from `templates/common.css`

- [ ] 8. **Update TypeScript** in `client/src/breeder-page/index.ts` and
  `client/src/dealer-page/index.ts`:
  - Read `priceEvidenceState` from payload; render warning icon on `Price` and
    `Price History` cells when state is `transition-affected`, `neutralized`, or
    `multi-variant`
  - Show tooltip from `transitionMessage` on icon hover
  - No warning icon on `Wishlist` or `Wishlist History` cells (Scenario A requirement)
  - Add a TypeScript interface for the lineage-metadata payload fields

- [ ] 9. Write Vitest unit tests for warning icon rendering logic; `make test-client-fast`

- [ ] 10. Update existing website tests that reference the changed function signatures
  or species list shape

- [ ] 11. `make test` + `make test-client` — all green

- [ ] 12. `make test-e2e` — E2E tests must cover:
  - Warning icon visible on `Price` cell for a transition-affected species
  - Tooltip text matches the `Transition Message` value from the spec
  - Transition banner shown on species page for confirmed/ambiguous cases
  - No transition banner for a stable single-size species (Scenario D regression guard)
  - Exactly ONE row per species in both breeder and dealer tables (primary regression guard)

- [ ] 13. Commit: `git add -p && git commit -m "feat(lineage): website warning icons, tooltips, and species page transition banner (Phase 5)"`

- [ ] 14. Publish branch and open PR:
  ```bash
  git push -u origin HEAD
  gh pr create --title "feat: size variant identity — one species row per table with lineage metadata" \
    --body "Implements SIZE_VARIANT_IDENTITY_REQUIREMENTS.md end-to-end. Phases 1–5: URL normalization, species-level supply timeline, hidden lineage metadata columns, species-keyed matrix rows, and website warning affordances." \
    --base master
  ```

**Phase 5 closing steps:**

- [ ] Mark all steps above completed
- [ ] **Smell review:** Duplicated lineage-reading logic between breeder and dealer
  TypeScript? Add a shared TypeScript helper if so. Verify the JSON payload type has a
  proper TypeScript interface.
- [ ] Feed forward: n/a — this is the final phase.
- [ ] Pause only if the TypeScript payload shape has an impedance mismatch with how
  `SortableTable.svelte` renders cells.

---

## Relevant Files

### New files

| File | Purpose |
|---|---|
| `src/shared/url_utils.py` | `normalize_product_url()` |
| `src/scrape/listing_lineage.py` | `LineageResult`, `detect_species_lineage()` |
| `tests/shared_module/test_url_utils.py` | URL normalization tests |
| `tests/scrape_module/test_listing_lineage.py` | Lineage detection tests |

### Modified files — Python

| File | Changes |
|---|---|
| `src/shared/history_utils.py` | Species-level timeline + supply functions, `k1` |
| `src/scrape/matrix_workflow.py` | Species-level helpers, lineage metadata compute, stitched sparkline |
| `src/scrape/wishlist_analysis.py` | Species-level wishlist count, delta, pressure |
| `src/scrape/breeder_matrix.py` | Species-keyed outer loop + evidence rules |
| `src/scrape/dealer_matrix.py` | Species-keyed outer loop + evidence rules |
| `src/website/species_detail.py` | Species-only routing, lineage metadata passthrough |
| `src/website/generate_website.py` | Species-only page loop |
| `src/website/table_data_helpers.py` | Hidden columns in JSON payload |

### Modified files — templates and client

| File | Changes |
|---|---|
| `templates/species_detail.html` | Transition banner |
| `templates/analysis.css` or `templates/species-detail.css` | Warning icon style |
| `client/src/breeder-page/index.ts` | Warning icon + tooltip rendering |
| `client/src/dealer-page/index.ts` | Warning icon + tooltip rendering |

### Test files to update

- `tests/scrape_module/test_breeder_matrix.py`
- `tests/scrape_module/test_dealer_matrix.py`
- `tests/scrape_module/test_matrix_workflow.py`
- `tests/scrape_module/test_wishlist_analysis.py`
- `tests/website_module/test_species_detail.py`
- `tests/e2e/test_species_page_interactions.py`
- Snapshot files in `tests/scrape_module/__snapshots__/` (follow Snapshot Protocol)

---

## Verification — Per Phase

| Phase | Command |
|---|---|
| 1 | `make test` |
| 2 | `make test` + `python scripts/check_coverage.py --module=shared/history_utils.py` |
| 3 | `make test` + coverage for both matrix modules |
| 4 | `make test` + coverage + optional `make generate-website` visual check |
| 5 | `make test` + `make test-client` + `make test-e2e` |

---

## Standing Decisions

| Decision | Rule |
|---|---|
| Phase 3 is not a final state | Spec explicitly requires Phase 4 to ship; Phase 3 is an intermediate |
| `Drivers` written to CSV in Phase 3 | Hidden metadata columns come after `Drivers`; verify current state in `summary_utils.py` first |
| Routing stays species-only | `species/<slug>/index.html` path unchanged per Decision 7 |
| Warning icons are a website concern | Not encoded in CSV string values |
| `listing_lineage.py` placement | Tentatively `src/scrape/`; Phase 1 close reviews placement |
| Wishlist pressure ranking | Remains relative per-run; Phase 4 operates on species-level effective counts, not summed variants |
| Price sparkline stitching | Only for confirmed transition; ambiguous + multi-variant → `"-"` |

---

## Pre-Implementation Checks

1. **`Drivers` current CSV state** — read `src/shared/summary_utils.py` at the start of
   Phase 3 Step 1 to confirm whether `Drivers` is already in `table_columns`. If it is
   already written, Phase 3 is smaller. If not (likely based on current code), add it to
   `table_columns` before the 7 hidden metadata columns.

2. **Wishlist pressure map key change** — in Phase 4 the existing `k2`-keyed
   `compute_wishlist_pressure` function stays unchanged for internal use; a new
   `compute_species_pressure_from_counts(species_counts: dict[str, int]) -> dict[str, str]`
   function is needed so that existing `k2`-based tests are not broken.
