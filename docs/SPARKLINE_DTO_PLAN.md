# Sparkline Hybrid DTO Architecture — Migration Plan

## How to use this document

Each phase should be executed in a **separate AI conversation** to keep context tight.
Open a new conversation and start with:

> "Read `docs/SPARKLINE_DTO_PLAN.md`. We are implementing **Phase X**. Begin."

At the end of each phase conversation, ask the AI to update this file — tick off completed
steps and record any decisions that deviated from the plan.

---

## TL;DR

Python already has all correct sparkline semantics in `sparkline_conversion.py`. The
client-side `unicodeToSvg()` reimplements a simplified, semantically inferior version —
losing actual-value bar heights, carry-forward tooltip brackets, and gap positioning.

The fix: Python emits a pre-computed rendering DTO (bars with exact heights, colors,
tooltips, opacity) that a new `SparklineBar.svelte` component renders as real SVG DOM.
No client-side business logic. No `{@html}`.

**Phase sequence:**
A0 (coverage scan) → A (DTO contract + tests RED) → B (Python implementation GREEN) →
C (Vitest RED) → D (SparklineBar.svelte GREEN) → E (wire into tables) →
F (E2E gate) → G (cleanup + deletion)

**Primary rollback point:** end of Phase F (before any deletion).

---

## Target Architecture

### DTO Schema

```python
{
    "bars": [
        # One entry per character position in the unicode string (includes gap slots)
        {
            "bar_height": 14.0,     # px — computed from actual values in Python
            "fill": "#22c55e",      # trend color — Python decides this
            "opacity": 0.73,        # 0.7 + (i / len(bars)) * 0.3
            "tooltip": "£15.00"     # "[£15.00]" for carry-forward
        },
        None,                       # gap slot in stock sparklines
        ...
    ],
    "svg_width": 40,                # len(bars) * 10
    "svg_height": 20,
    "title": "Price History"        # "Wishlist History" / "Stock History"
}
```

### Logic split

| What | Where |
|---|---|
| Trend color (rising/falling/stable, carry-forward override) | Python only |
| Bar height (actual-value proportional normalization, 10% floor) | Python only |
| Tooltip text (£ formatting, bracket notation, singular/plural) | Python only |
| Opacity gradient | Python only |
| Gap detection and placement for stock sparklines | Python only |
| `x` position (`i × BAR_SPACING`) | Svelte only — view math |
| `y` position (`svg_height − bar_height`) | Svelte only — view math |
| SVG DOM creation | Svelte only |

### Files affected

| File | Change |
|---|---|
| `src/website/sparkline_conversion.py` | Add `_compute_bar_data`, `sparkline_to_dto`, `build_sparkline_dto_rows`; old SVG functions deleted in Phase G |
| `src/website/generate_website.py` | Replace `convert_sparklines_in_rows()` with `build_sparkline_dto_rows()` |
| `src/website/table_data_helpers.py` | Phase G: remove stale `startswith("<svg")` guard |
| `src/shared/sparkline_helpers.py` | **Unchanged throughout** |
| `client/src/shared/types.ts` | New — `SparklineDto`, `SparklineBarData` interfaces |
| `client/src/shared/components/SparklineBar.svelte` | New — view-only SVG renderer |
| `client/src/shared/components/SortableTable.svelte` | Replace `{@html unicodeToSvg(...)}` with `<SparklineBar dto={...} />` |
| `client/src/history-page/HistoryTable.svelte` | Same as SortableTable |
| `client/src/shared/sparklines.ts` | Phase G: delete `sparklineFillColor`; simplify or delete `unicodeToSvg` |
| `tests/website_module/test_sparkline_dto.py` | New — comprehensive DTO tests |
| `tests/website_module/test_table_data_helpers.py` | Add one test: DTO dict survives `rows_to_json()` |
| `tests/shared_module/test_convert_sparkline_to_svg.py` | Phase G: redirect to `sparkline_to_dto` |
| `client/src/shared/components/SparklineBar.test.ts` | New — Vitest component tests |
| `client/src/shared/sparklines.test.ts` | Phase G: remove `sparklineFillColor` group |
| `client/src/shared/components/SortableTable.test.ts` | Phase E: update sparkline cell assertions |
| `tests/e2e/test_visual_contracts.py` | Phase F: update fill test; add tooltip presence test |

---

## Verification gates (apply at every phase boundary)

- `make test` — Python unit tests green, coverage ≥ 80%
- `make test-client` — Vitest green
- `make coverage-client` — Vitest coverage ≥ 80% branches/functions
- `make test-e2e` — Playwright green (required before Phase G)

---

## Step A0 — Coverage scan (pre-Phase A gate)

**Goal:** Confirm existing `sparkline_conversion.py` behavior is fully locked down in tests
before writing any DTO code.

- [x] A0.1. Run `python scripts/check_coverage.py --module=website/sparkline_conversion.py`.
           If branch coverage < 80%, read `tests/shared_module/test_convert_sparkline_to_svg.py`
           and plug gaps. Gate: ≥ 80% branch coverage on `sparkline_conversion.py`.
- [x] A0.2. Verify `make test` is green before proceeding.

---

## Phase A — DTO contract (RED phase)

**Goal:** Define the TypeScript DTO interface and write all Python DTO tests before touching
production code. Every new test must FAIL (import error) before Phase B begins.

- [x] A1. Create `client/src/shared/types.ts` (new file):
         ```ts
         export interface SparklineBarData {
           bar_height: number;
           fill: string;
           opacity: number;
           tooltip: string;
         }
         export interface SparklineDto {
           bars: (SparklineBarData | null)[];
           svg_width: number;
           svg_height: number;
           title: string;
         }
         ```

- [x] A2. Write `tests/website_module/test_sparkline_dto.py` (new file). All tests import
         `sparkline_to_dto` and `build_sparkline_dto_rows` from `website.sparkline_conversion`.
         These functions do not exist yet — every test must fail with `ImportError`.
         
         Required test classes and cases (see Test Strategy section for full details):
         - `TestBarHeightPrice` — specific pixel values per formula
         - `TestBarHeightStock` — height from unicode level, not actual values
         - `TestGaps` — None entries in bars list; gap slots count toward svg_width
         - `TestColors` — rising/falling/stable/all-CF/stock color codes
         - `TestTooltips` — all metric types, carry-forward brackets, singular/plural
         - `TestOpacity` — gradient direction confirmed
         - `TestSvgMeta` — svg_width, svg_height, title per metric type
         - `TestEdgeCases` — empty, dash, single bar, no historical data
         - `TestBuildSparklineDtoRows` — pipeline integration

- [x] A3. Confirm `make test` fails with `ImportError` on `test_sparkline_dto.py`.
         Do NOT proceed to Phase B until all tests are written and confirmed RED.

---

## Phase B — Python DTO implementation (GREEN phase)

**Goal:** Make all Phase A tests pass. No client-side changes.

- [x] B1. In `src/website/sparkline_conversion.py`, extract internal function
         `_compute_bar_data(unicode_sparkline, bars, metric_type, compact_values,
         compact_is_carried_forward, color) -> List[Optional[tuple]]`.
         Extracts the per-bar `(bar_height, fill, opacity, tooltip | None)` computation
         currently inlined in `convert_sparkline_to_svg()`.
         Update `convert_sparkline_to_svg()` to call `_compute_bar_data()` internally.
         **External behavior of `convert_sparkline_to_svg()` is unchanged.**

- [x] B2. Implement `sparkline_to_dto(unicode_sparkline, values, metric_type,
         is_carried_forward) -> Optional[dict]` in `sparkline_conversion.py`.
         Returns `None` for empty/dash inputs.
         Returns dict matching schema from A1.

- [x] B3. Implement `build_sparkline_dto_rows(headers, rows, historical_data,
         csv_filename) -> List[List[Any]]` in `sparkline_conversion.py`.
         Logic parallel to `convert_sparklines_in_rows()`: iterates sparkline columns,
         calls `extract_historical_values_with_carryforward`, calls `sparkline_to_dto()`.
         Sparkline cells become DTO dicts; non-sparkline cells unchanged.
         When historical data unavailable for a species, cell stays as unicode string.

- [x] B4. Update each `generate_*` function in `generate_website.py`:
         replace `convert_sparklines_in_rows()` call with `build_sparkline_dto_rows()`.
         DTOs flow into `json_rows` via existing `rows_to_json()` — dict values are
         pass-through (the `startswith("<svg")` filter does not affect them).

- [x] B5. `make test` → all Python tests green. Confirm `test_sparkline_dto.py` fully green.

- [x] B6. Update `tests/website_module/test_table_data_helpers.py` — add one test:
         a sparkline cell containing a DTO dict passes through `rows_to_json()` intact
         (not stripped by the `startswith("<svg")` guard).
         `make test` → still green.

---

## Phase C — SparklineBar.svelte Vitest tests (RED phase)

**Goal:** Write all component tests before creating the component. Every test must FAIL.

- [x] C1. Create `client/src/shared/components/SparklineBar.test.ts`.
         Import `SparklineBar` from `./SparklineBar.svelte` — file does not exist yet.
         
         Required test cases:
         - Renders `<svg>` with correct `width`, `height`, `viewBox` from DTO
         - Renders outer `<title>` with DTO's `title` value
         - Renders correct number of `<rect>` elements (null gaps excluded)
         - Each `<rect>` has `fill` attribute matching bar data
         - Each `<rect>` has `opacity` attribute matching bar data
         - Each `<rect>` has a child `<title>` with bar's tooltip string
         - Gap handling: two bars with a null gap → rects at `x=0` and `x=20`
           (gap slot still advances x-position)
         - `dto` is a plain string `"-"`: no `<svg>`, string content present
         - `dto` is a plain string `"▁▂▃"` (no DTO): no `<svg>`, rendered as text
         - Single-bar DTO (`bar_height == 20`): rect has `height="20"`, `y="0"`

- [x] C2. Confirm `make test-client` fails with a module-not-found error.
         Do NOT proceed to Phase D until C1 is complete and confirmed RED.

---

## Phase D — SparklineBar.svelte (GREEN phase)

**Goal:** Make all Phase C tests pass.

- [ ] D1. Create `client/src/shared/components/SparklineBar.svelte`. Props:
         `dto: SparklineDto | string` (import `SparklineDto` from `'../types.js'`).
         
         Two render paths:
         - DTO object: render `<svg>` with outer `<title>`, `{#each bars as bar, i}`,
           `{#if bar !== null}` guard, `<rect>` per bar with `x={i * 10}`,
           `y={dto.svg_height - bar.bar_height}`, `width="8"`, `height={bar.bar_height}`,
           `fill={bar.fill}`, `opacity={bar.opacity}`, child `<title>{bar.tooltip}</title>`.
         - String (fallback): render the string directly with no SVG wrapper.
         
         `isDto` detection: `typeof dto === 'object' && dto !== null && 'bars' in dto`.
         
         `<style>` block: `.sparkline { vertical-align: middle }`.
         No design tokens needed. No business logic.

- [ ] D2. `make build-client && make test-client && make coverage-client` → all green.

---

## Phase E — Wire into SortableTable and HistoryTable

**Goal:** Replace `{@html unicodeToSvg(...)}` with `<SparklineBar>` in both table components.

- [ ] E1. Update `client/src/shared/components/SortableTable.svelte`:
         - Add `import SparklineBar from './SparklineBar.svelte';`
         - For cells where `col.type === 'sparkline'`, replace:
           `{@html unicodeToSvg(row[col.key])}`
           with: `<SparklineBar dto={row[col.key]} />`
         - No changes to column config, filter logic, or any other rendering.

- [ ] E2. Update `client/src/history-page/HistoryTable.svelte` — same replacement.

- [ ] E3. Update `client/src/shared/components/SortableTable.test.ts`:
         Any test asserting sparkline rendering should assert that a `type: 'sparkline'`
         column with a DTO object value renders an `<svg>` element, not a raw string.

- [ ] E4. `make build-client && make test-client` → green.

---

## Phase F — E2E validation gate

**Goal:** Confirm all existing browser behaviour preserved. This is the primary rollback point.

- [ ] F1. `make test-e2e` → all existing 126+ E2E tests pass unmodified.

- [ ] F2. Update `tests/e2e/test_visual_contracts.py`:
         - Update existing `test_sparkline_fill_is_not_currentColor`: assert sparkline
           SVG bars are present with a non-`currentColor` `fill` attribute (mechanism-agnostic).
         - Add new test `test_sparkline_bar_has_tooltip`: find a `<rect>` inside a `.sparkline`
           SVG on the breeder page; assert its `<title>` child exists and contains `£`.

- [ ] F3. `make test && make test-client && make coverage-client && make test-e2e` → all green.
         
         **Do NOT proceed to Phase G unless all four suites are green.**
         If E2E fails here, rollback to Phase D state — `convert_sparkline_to_svg()` still
         exists and no dead code has been removed yet.

---

## Phase G — Cleanup and deletion

**Goal:** Remove all code made dead by the DTO migration.

- [ ] G0. Rename `src/website/sparkline_conversion.py` → `src/website/sparkline_dto.py`.
         Update `src/website/__init__.py` and all
         `from website.sparkline_conversion import ...` references in `src/` and `tests/`.
         `make test` → green after rename.

- [ ] G1. Delete `convert_sparkline_to_svg()` from `sparkline_dto.py`.
         Redirect `tests/shared_module/test_convert_sparkline_to_svg.py`: change the import
         to `from website.sparkline_dto import sparkline_to_dto` and rewrite assertions
         to call `sparkline_to_dto` instead. Test cases themselves are preserved.
         `make test` → green.

- [ ] G2. Delete `convert_sparklines_in_rows()` from `sparkline_dto.py`.
         Confirm no remaining callers in `generate_website.py`.
         `make test` → green.

- [ ] G3. In `client/src/shared/sparklines.ts`:
         - Delete `sparklineFillColor()` function.
         - Decision: if `SparklineBar.svelte` handles the string fallback inline (renders
           raw string text, no `unicodeToSvg` call), delete `unicodeToSvg()` and the
           entire file. If `unicodeToSvg` is still used elsewhere, retain it stripped of
           color logic.

- [ ] G4. Update `client/src/shared/sparklines.test.ts`:
         - Delete the `sparklineFillColor` color test group.
         - If `unicodeToSvg` was deleted in G3, delete this file entirely.
         - If `unicodeToSvg` retained, keep structural tests only.

- [ ] G5. Remove the `startswith("<svg")` guard from `rows_to_json()` in
         `src/website/table_data_helpers.py` — dead code now that SVG strings never
         reach the serializer. Remove the corresponding assertion from
         `tests/website_module/test_table_data_helpers.py`.

- [ ] G6. Final gate:
         `make test && make test-client && make coverage-client && make test-e2e` → all green.

---

## Test Strategy (full detail)

### `tests/website_module/test_sparkline_dto.py` — required test cases

#### `TestBarHeightPrice`

| Test | Input | Expected |
|---|---|---|
| Single bar max value | `("▄", ["15.00"], "price", [False])` | `bars[0].bar_height == 20.0` |
| Two bars proportional | `("▁█", ["10.00", "20.00"], "price", [False, False])` | bar[0] ≈ 11.0, bar[1] == 20.0 |
| Zero-based normalization floor | `("▁█", ["5.00", "10.00"], "price", [False, False])` | bar[0] == 2.0, bar[1] == 20.0 |
| Flat values | `("▄▄▄", ["15.00","15.00","15.00"], "price", ...)` | all bars same height |

Formula: `bar_height = (0.1 + (val / max_val) * 0.9) * 20`

Use `pytest.approx()` for float comparisons.

#### `TestBarHeightStock`

- `sparkline_to_dto("▁▄█", None, "stock", None)` →
  bar heights == `[2.5, 10.0, 20.0]` (from `(level/8) * 20`)

#### `TestGaps`

- Stock with space: `sparkline_to_dto("█ █", None, "stock", None)` →
  `bars == [BarData, None, BarData]` (three slots, middle is `None`)
- `svg_width == 30` (3 slots × 10px — gap positions count toward width)
- Price/wishlist: no `None` gaps (carry-forward fills them with real bar entries)

#### `TestColors`

- Rising trend (actual values first→last rise by >1): `fill == "#22c55e"`
- Falling trend: `fill == "#ef4444"`
- Stable (flat values): `fill == "#3b82f6"`
- All-carry-forward after first bar: `fill == "#3b82f6"` even if unicode levels differ
- Stock: always `fill == "#22c55e"`

#### `TestTooltips`

- Price real bar: `"£15.00"`
- Price carry-forward bar: `"[£15.00]"`
- Wishlist singular: `"1 wishlist"`
- Wishlist plural: `"7 wishlists"`
- Wishlist carry-forward: `"[7 wishlists]"`
- Stock: `"IN"`

#### `TestOpacity`

- `bars[0].opacity < bars[-1].opacity` for any multi-bar sparkline
- First bar ≈ 0.70, last bar ≈ 1.00

#### `TestSvgMeta`

- `svg_width == len(bars) * 10`
- `svg_height == 20`
- `title == "Price History"` / `"Wishlist History"` / `"Stock History"`

#### `TestEdgeCases`

- Empty string → returns `None`
- `"-"` → returns `None`
- Single bar → valid DTO, `len(bars) == 1`
- Stock with no values arg → DTO produced (stock doesn't need values)

#### `TestBuildSparklineDtoRows`

- 2-row input with Price History column → result has DTO dicts in sparkline cells
- Non-sparkline cells pass through as original strings
- Species with no historical data → sparkline cell stays as unicode string (not a DTO)

---

### `client/src/shared/components/SparklineBar.test.ts` — required test cases

- Renders `<svg>` with `width`, `height`, `viewBox` matching DTO fields
- Renders outer `<title>` inside `<svg>` with `dto.title` value
- Correct `<rect>` count — null gap bars excluded from count
- Each `<rect>` has `fill` attribute matching `bar.fill`
- Each `<rect>` has `opacity` attribute matching `bar.opacity`
- Each `<rect>` has a child `<title>` with `bar.tooltip` string
- Gap x-positioning: null gap at index 1 → rects at `x="0"` and `x="20"` (not `x="10"`)
- String fallback `"-"`: no `<svg>` rendered, string `"-"` present in DOM
- String fallback `"▁▂▃"`: no `<svg>` rendered, string present in DOM
- Single-bar DTO with `bar_height == 20`: rect `height="20"`, `y="0"`

---

## Risks / Tradeoffs

**Payload size.** Unicode string ≈ 8 bytes/cell. DTO ≈ 400–600 bytes/cell.
50-row table × 3 sparkline columns ≈ 75–90 KB added. Acceptable for a weekly static site.
If size becomes a concern, only `opacity` is safe to compute client-side
(`0.7 + i/n * 0.3`) — everything else is semantic.

**No historical data fallback.** When `build_sparkline_dto_rows()` finds no history for a
species, the cell stays as a unicode string. `SparklineBar` renders it as plain text (no
tooltips, coarse height). Visually degraded but never blank.

**`test_table_data_helpers.py` SVG assertions.** Existing tests may assert that SVG strings
are stripped. Update these in B6 when adding the DTO pass-through test.

**Phase G ordering.** The `startswith("<svg")` removal (G5) is only safe after confirming
no SVG strings reach `rows_to_json()` — i.e. after G2 deletes `convert_sparklines_in_rows`.
Do G2 before G5.

---

## Decisions log

*(Record decisions that deviate from this plan here, to inform the next phase conversation.)*

| Phase | Decision | Reason |
|---|---|---|
| A | `TestBarHeightPrice` — "Zero-based normalization floor" test corrected: input changed from `["5.00", "10.00"]` to `["0.00", "10.00"]` | The plan's stated expected value (bar[0] == 2.0) is only achievable with val=0. Formula is `(0.1 + val/max * 0.9) * 20`; for val=5, max=10 → 11.0 not 2.0. Test now correctly demonstrates the 10% floor (2.0px) triggered by a zero-valued price. |
| B | `generate_analysis_page` json_rows ordering kept BEFORE `build_sparkline_dto_rows` | For Phase B (no client changes), json_rows must remain unicode strings so the existing Svelte `unicodeToSvg` renderer is not broken. DTOs will flow into json_rows in Phase E when SortableTable.svelte is updated to use SparklineBar. |
| B | `generate_snapshot_page` and `generate_history_page` effectively unchanged | These pages read CSVs without sparkline columns ("History"/"Availability" headers), so `build_sparkline_dto_rows` finds no sparkline columns and returns rows unchanged. No behavioral difference from swapping the function. |
| C | `{#if bar !== null}` guard must be INSIDE `{#each bars as bar, i}`, not replacing it | The gap x-positioning test asserts that null at index 1 → second real rect has `x="20"` (i=2). If the `{#if}` were outside the `{#each}` (e.g. filtering nulls first), `i` would reset and the second rect would get `x="10"`. The loop index `i` must advance for every slot including nulls. |
| C | Outer `<title>` must be a direct child of `<svg>`, not nested inside `{#each}` | The test queries `:scope > title` on the `<svg>` element, which only matches immediate children. Place `<title>{dto.title}</title>` before the `{#each}` block. |
| C | `opacity` attribute — Svelte coerces `1.0` → `"1"` in HTML | `toHaveAttribute('opacity', '1')` (not `'1.0'`) is the correct assertion. The Phase D implementor does not need to do anything special — Svelte's default attribute binding handles this automatically. |
| C | String fallback covers both `"-"` and unicode strings | Tests confirm that any non-DTO value (including real unicode sparkline strings like `"▁▂▃"`) must be rendered as plain text with no `<svg>` wrapper. This is the graceful degradation path for species with no historical data (Phase B decision: unicode strings still flow into `json_rows` until Phase E). |

