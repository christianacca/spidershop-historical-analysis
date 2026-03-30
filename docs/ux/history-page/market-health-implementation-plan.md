# Market Health — Implementation Plan

**Companion to:** [`market-health-handoff-spec.md`](./market-health-handoff-spec.md)  
**Branch to create from:** `master`  
**Suggested branch name:** `history-page-market-health`

Read the handoff spec first. This document is the agent's instruction set: it fills
in the engineering gaps the UX spec intentionally omits, then breaks the work into
phases with explicit checklists.

---

## Gaps the UX Spec Does Not Cover

An agent MUST understand these before writing any code:

### G1 — Window global pattern

The existing page pattern is:
1. Python template renders `<script>window['history-tableData'] = {{ json_rows | safe }};</script>`
   directly into the page HTML (see `templates/table.html`).
2. `client/src/history-page/index.ts` reads `window['history-tableData']`, validates it
   with `assertPayload()`, then mounts a Svelte component.
3. A **second** independent island for Market Health will follow the same pattern:
   - Python injects `window.marketHealthPayload = { … };`
   - `history-page/index.ts` reads it and mounts `MarketHealthSection`.

### G2 — CSS design tokens

The mock file uses its own local token names (`--bg`, `--surface`, `--ink`, `--accent`, etc.).
Production components must use the global tokens from `templates/common.css`.
**The agent must read `templates/common.css` (`:root` block) before writing any CSS** to
find the correct token for each visual intent. Do not copy mock token names into Svelte
`<style>` blocks.

Key mappings (verify against `common.css` — do not assume names):

| Mock token | Visual intent | Production equivalent (verify) |
|---|---|---|
| `--ink` | Primary text | `--color-ink` or similar |
| `--muted` | Secondary text | `--color-muted` or similar |
| `--accent` | Teal / positive | `--color-accent` or similar |
| `--accent-2` | Amber / stock | verify |
| `--surface` | Card background | verify |
| `--line` | Borders | `--color-border-light` or similar |
| `--shadow` | Card shadow | verify |

### G3 — Storybook status

Storybook is **not installed** in this project. `client/package.json` has no Storybook
dependency. Phase 7 (Storybook) must install it from scratch. Given the project uses
Svelte 5 + Vite + Vitest, the correct install is:
```
npx storybook@latest init --type svelte
```
Choose CSF3 format. Stories co-locate with components following the existing test pattern.

### G4 — Python generator entry point

The history page is generated in `src/website/generate_website.py`. Market Health data
computation belongs in a new module `src/website/market_health_dto.py`. The generator
calls it and passes the result into the Jinja template context, which then injects it as
a window global. Follow the existing pattern in `sparkline_dto.py` for how DTOs are
computed and passed to templates.

The CSV the computation reads from: `spidershop_spiderlings_history.csv` with schema:
```
scrape_datetime, scientific_name, common_name, size_cm, price_gbp, wishlist_count, page_url
```
An "in-stock" row is any row that appears in the CSV for a given `scrape_datetime`
(presence = in-stock; absence = out-of-stock). The `price_gbp` and `wishlist_count`
columns are numeric strings.

### G5 — Template wiring

`templates/history_page.html` currently contains only the data table. A new `<section>`
must be prepended above the table for the Market Health island. The
`window.marketHealthPayload` script block goes in a `{% block extra_js %}` extension or
immediately before the table section — follow the pattern in `templates/analysis_page.html`.

### G6 — Test commands (MANDATORY)

```bash
make test-client-fast     # fast Vitest — run after every component change
make test-client          # Vitest + coverage — run at end of each client phase (≥80%)
make test                 # Python unit tests — run at end of each Python phase (≥80%)
make test-e2e             # Playwright — run at end of Phase 6 (page integration)
make test-visual          # browser-backed CSS contracts — run when style blocks change
```

---

## Phase Structure

Each phase ends with three mandatory housekeeping steps:

```
[ ] H1 — Mark all task checkboxes above as ✅
[ ] H2 — Reflection: scan all new code for code smells; commit fixes before moving on
[ ] H3 — Feed-forward: append notes to the "Feed-forward log" at the bottom of this file
```

**Code smell checklist for H2:**
- Duplicated logic that belongs in a shared utility
- Svelte `<style>` blocks referencing hardcoded colours (must use `var(--token)`)
- Any `// TODO` or `// FIXME` that was added as a shortcut
- TypeScript `any` that can be replaced with a proper type
- Props passed deeply through multiple components that should be flattened
- Fixture data that diverges from the TypeScript interface (will break the type checker)

---

## Phase 1 — Foundation: Types, Fixtures, and CSS Tokens

**Goal:** Establish the canonical type contract and fixture files that all subsequent
phases depend on. No rendering code. No Svelte. Everything must compile cleanly.

**Pre-flight (do before writing any code):**
- [ ] Read `templates/common.css` `:root` block — build a mapping table for the
  six mock tokens listed in G2 above. Add to feed-forward log.
- [ ] Read `client/src/history-page/index.ts` — understand the current island
  initialisation pattern (`registerPageInit`, `assertPayload`, `mount`).
- [ ] Read `client/src/shared/page-init.ts` (or equivalent) — understand what
  `completeTableMount` / `registerPageInit` expect.
- [ ] Run `make test-client-fast` — confirm baseline is green before touching anything.

**Tasks:**
- [ ] Create `client/src/history-page/market-health-types.ts` — export all interfaces
  from the handoff spec §7.2 (`MarketHealthPayload`, `KpiCardData`, `SparklineSeries`,
  `MarketEventsData`, `EventTile`, `WindowId`).
- [ ] Create `client/src/history-page/__fixtures__/` directory and the fixture module
  `marketHealth.currentQuarter.ts` (full data — see spec §8.2).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.allTime.ts`
  (`showPrior: false`, flat deltas — see spec §8.3).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.lastQuarter.ts`
  (completed period, named quarter label).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.stockUnderPressure.ts`
  (stock delta ≤ −7, wishlist delta ≥ +3).
- [ ] Run `npx tsc --noEmit` from `client/` — confirm zero type errors.

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 2 — MarketSparkline Component

**Goal:** Build the inline SVG sparkline with run-selection interaction. This is the
most self-contained visual element; getting it right here means `MarketKpiCard` is
simple assembly.

**Pre-flight:**
- [ ] Review `client/src/species-page/charts.ts` — understand the existing approach to
  SVG coordinate math. Do not duplicate; extract to a shared helper if the pattern is
  reused.

**Tasks:**
- [ ] Create `client/src/history-page/MarketSparkline.svelte`:
  - Props: `series: number[]`, `priorSeries: number[]`, `showPrior: boolean`,
    `color: string`, `formatValue: (v: number) => string`, `selectedRun: number | null`,
    `onRunSelect: (run: number | null) => void`
  - Renders an inline SVG with 12 data points per series
  - Current series: solid line, `stroke-width: 2.5`, filled circles (`r=2.7`, `r=4.4` selected)
  - Prior series: dashed line, `stroke-opacity: 0.65`, lighter circles (`r=2.2`, `r=3.4` selected)
  - Non-selected points when a run is chosen: add `.is-subdued` class (opacity 0.3)
  - Prior series: not rendered when `showPrior = false`
  - Click on any hit area fires `onRunSelect(runIndex)` (or `null` if already selected)
- [ ] Create `client/src/history-page/MarketSparkline.test.ts`:
  - Renders with `showPrior: true` → both series in DOM
  - Renders with `showPrior: false` → prior series not in DOM
  - Click on run index 3 → `onRunSelect(3)` called
  - Click on already-selected run → `onRunSelect(null)` called
  - Selected run → hit point has larger radius; others have `.is-subdued`
- [ ] Run `make test-client-fast` — green
- [ ] Run `make test-visual` — add a visual contract for the sparkline computed styles
  (check that solid vs dashed stroke styles resolve correctly)

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 3 — MarketKpiCard Component

**Goal:** Build a single KPI tile. Receives pre-computed data; no internal computation.

**Tasks:**
- [ ] Create `client/src/history-page/MarketKpiCard.svelte`:
  - Props: `card: KpiCardData`, `series: SparklineSeries`, `showPrior: boolean`,
    `selectedRun: number | null`, `onRunSelect: (run: number | null) => void`
  - Renders: `<h3>` title, `.metric-value`, `.metric-delta` (with deltaClass modifier),
    copy `<p>`, `<MarketSparkline>` passing through run props
- [ ] Create `client/src/history-page/MarketKpiCard.test.ts`:
  - Delta class `""` → no modifier class on `.metric-delta`
  - Delta class `"down"` → `.metric-delta.down` in DOM
  - Delta class `"flat"` → `.metric-delta.flat` in DOM
  - `showPrior: false` → sparkline receives `showPrior: false`
  - `onRunSelect` callback prop is forwarded to sparkline
- [ ] Run `make test-client-fast` — green
- [ ] Run `make test-client` — coverage ≥ 80% for new files

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 4 — MarketEventsCard Component

**Goal:** Build the static events mini-grid. No interaction — pure display.

**Tasks:**
- [ ] Create `client/src/history-page/MarketEventsCard.svelte`:
  - Props: `events: MarketEventsData`
  - Renders: `<article class="visual-card">` with `<h3>` title, subtitle `<p>`,
    and a 2×2 CSS grid of event tiles (label / bold value / copy)
- [ ] Create `client/src/history-page/MarketEventsCard.test.ts`:
  - All 4 tiles render with correct label, value, and copy from fixture
  - Title and subtitle are dynamic (use the `currentQuarter` and `allTime` fixtures
    to verify both)
- [ ] Run `make test-client-fast` — green

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 5 — MarketHealthSection Island (Assembly + State)

**Goal:** Compose the section. Own the `selectedRun` state. Wire the sparkline legend
(basis note, prior key visibility, "Clear run focus" button). This is the Svelte island
that mounts into the page.

**Tasks:**
- [ ] Create `client/src/history-page/MarketHealthSection.svelte`:
  - Props: `payload: MarketHealthPayload`
  - Local `$state`: `selectedRun: number | null = null`
  - Renders: section header, 4×`MarketKpiCard`, sparkline support row (legend,
    basis note, selection note, clear button), `MarketEventsCard`
  - Sparkline support row:
    - Prior-key item hidden when `payload.showPrior === false`
    - Basis note = `payload.compareNote`
    - Selection note: `"Optional: click a run…"` → `"Run N selected…"` when a run is chosen
    - "Clear run focus" button: hidden when `selectedRun === null`; clears on click
  - `onRunSelect` callback shared across all 4 cards — sets `selectedRun` or clears
    if the same run is clicked again
- [ ] Create `client/src/history-page/MarketHealthSection.test.ts`:
  - Renders with `currentQuarter` fixture — all 4 KPI cards visible
  - Prior key in legend is visible when `showPrior: true`
  - Prior key in legend is hidden when `showPrior: false` (use `allTime` fixture)
  - Click run 5 on observed sparkline → selection note updates to "Run 6 selected"
    AND `selectedRun` propagates to all 4 cards
  - Click same run again → note resets to "Optional" text; clear button hidden
  - Clear button click (when visible) → resets selection
- [ ] Register the island mount in `client/src/history-page/index.ts`:
  - Read `window.marketHealthPayload` (cast as `MarketHealthPayload | undefined`)
  - If present, mount `MarketHealthSection` into `<div id="market-health-root">`
  - (The mount point does not exist in the template yet — that is Phase 6)
- [ ] Run `make test-client` — coverage ≥ 80% for all history-page files

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 6 — Python Data Layer

**Goal:** Build the server-side computation that converts the history CSV into a
`MarketHealthPayload`-shaped dict for every time window, then inject it as a window
global into the history page.

**Pre-flight:**
- [ ] Read `src/website/sparkline_dto.py` — understand the existing DTO pattern
  (how data is computed and returned as a Python dict that Jinja serialises).
- [ ] Read `src/website/history_chart_dto.py` — understand if any reusable aggregation
  helpers already exist.

**Tasks:**
- [ ] Create `src/website/market_health_dto.py`:
  - Public function: `build_market_health_payload(history_rows: List[dict], window_id: str) -> dict`
  - Accepts the same list-of-dicts that the history table uses, plus the selected
    time window ID.
  - Returns a Python dict matching the `MarketHealthPayload` TypeScript interface.
  - Computation rules:
    - **Observed species**: `COUNT DISTINCT scientific_name` where `scrape_datetime`
      falls within the active window period AND the row exists (= in-stock).
    - **In-stock rate**: `(in-stock rows at the latest scrape within window) /
      (all species tracked within window) × 100`. Round to integer.
    - **Median wishlist**: `MEDIAN(wishlist_count)` at the latest scrape within window,
      for in-stock rows. Convert to integer.
    - **Median price**: `MEDIAN(price_gbp)` at the latest scrape within window, for
      in-stock rows. Format as `"GBP N"`.
    - **Prior period computation**: for each window ID, derive the matched prior period
      (e.g. "current quarter" → "same dates last quarter") and compute the same
      four metrics for that period. Delta = current − prior.
    - **Sparkline series**: 12 evenly-spaced runs within the window; compute each
      metric at each run point. For `showPrior: false` windows, return `[]` for prior.
    - **Events**: count new/dropped/restock/stockout transitions across the window runs.
    - **Copy selection**: use the bounded copy sets from spec §3 and §5.
    - When fewer than 2 scrapes exist for a window: raise a domain-level warning
      (not an exception) and return safe fallback values with `showPrior: false`.
  - Build a second public function:
    `build_market_health_payload_all_windows(history_rows) -> dict[str, dict]`
    returning one payload per window ID.
- [ ] Create `tests/website_module/test_market_health_dto.py`:
  - Test observed species count for a minimal fixture (2 scrapes, 3 species each)
  - Test in-stock rate computation
  - Test median wishlist with even vs odd number of in-stock rows
  - Test prior period boundary derivation for each `window_id`
  - Test `showPrior: false` for `all-time` window
  - Test events counting (new listings, dropped, restocks, oos flips)
  - Test fewer-than-2-scrapes edge case — returns fallback, no crash
- [ ] Run `make test` — green; `make test-file FILE=tests/website_module/test_market_health_dto.py`
  — coverage ≥ 80% for `market_health_dto.py`

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 7 — Page Integration

**Goal:** Wire the Python DTO into the generator, inject the window global into the
template, add the mount point to the HTML, and validate end-to-end.

**Pre-flight:**
- [ ] Read `src/website/generate_website.py` — find the `generate_history_page` function
  (or equivalent) and understand where `json_rows` is computed and passed to the template.

**Tasks:**
- [ ] In `src/website/generate_website.py`:
  - Import `build_market_health_payload_all_windows` from `market_health_dto`
  - After loading history rows, call it and pass `market_health_payloads` into the
    Jinja template context.
- [ ] In `templates/history_page.html`:
  - Add `<div id="market-health-root"></div>` above the table section.
  - Add `<script>window.marketHealthPayload = {{ market_health_payload | tojson | safe }};</script>`
    in the extra_js block (or immediately below the root div). Choose `current-quarter`
    as the default window — the client can re-derive other windows if needed, or
    the Python can inject all windows and the client picks by `windowId`.
    **Decision to make and log:** inject one pre-selected window payload vs all windows.
    See open decision #2 in spec §11.
- [ ] In `client/src/history-page/index.ts`:
  - Ensure the `marketHealthPayload` read and `MarketHealthSection` mount added in
    Phase 5 is guarded: only mount if the element and payload both exist.
- [ ] Update `client/src/shared/payload-validation.ts` (or a separate validation call)
  to validate `window.marketHealthPayload` shape in dev mode — check it has `kpis`,
  `sparklineSeries`, and `events` keys.
- [ ] Run `make generate-website` — spot-check the generated `history.html` for the
  mount point and the `window.marketHealthPayload` script block.
- [ ] Run `make test-e2e` — confirm the history page loads without errors, the market
  health section renders, and no console errors.
- [ ] Run `make test` and `make test-client` — full clean pass.

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry

---

## Phase 8 — Storybook Setup and Stories

**Goal:** Install Storybook for Svelte/Vite, create the Market Health slice as the
pattern for the rest of the page's stories.

**Pre-flight:**
- [ ] Confirm `client/package.json` still has no Storybook dependency (it should not).
- [ ] Read Svelte 5 + Storybook compatibility notes: Storybook ≥ 8.5 is required for
  Svelte 5 runes support.

**Tasks:**
- [ ] Install Storybook (run from `client/` directory):
  ```bash
  npx storybook@latest init --type svelte
  ```
  Accept the Vite builder. Decline any example stories.
- [ ] Verify `client/.storybook/main.ts` and `client/.storybook/preview.ts` were created.
- [ ] Import `templates/common.css` in `client/.storybook/preview.ts` so global design
  tokens are available in the Storybook canvas.
- [ ] Add a `storybook` script to `client/package.json` (`"storybook": "storybook dev -p 6006"`)
  and a `build-storybook` script.
- [ ] Create `client/src/history-page/MarketHealthSection.stories.ts`:
  - `meta.component = MarketHealthSection`
  - Story: `CurrentQuarter` — args from `marketHealthCurrentQuarter` fixture
  - Story: `LastQuarter` — args from `marketHealthLastQuarter` fixture
  - Story: `AllTime` — args from `marketHealthAllTime` fixture; verify prior key hidden
  - Story: `StockUnderPressure` — args from `marketHealthStockUnderPressure` fixture
  - Story: `RunSelected` — args from `currentQuarter` fixture with `selectedRun: 8`
    set via Storybook args (requires making `selectedRun` an initial-state prop or
    using a decorator — document the approach in feed-forward)
- [ ] Create `client/src/history-page/MarketEventsCard.stories.ts`:
  - `CurrentQuarter` — events from `currentQuarter` fixture
  - `AllTime` — events from `allTime` fixture
- [ ] Create `client/src/history-page/MarketKpiCard.stories.ts`:
  - `PositiveDelta`, `NegativeDelta`, `FlatDelta`, `AllTimeNoPrior`
- [ ] Run `npx storybook dev` from `client/` — manually verify all stories render
  without errors in the browser.
- [ ] Add `make storybook` to the root `Makefile` (runs `cd client && npx storybook dev`).

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan (focus especially on the Storybook config — check for
  global CSS leakage or token resolution gaps in the canvas)
- [ ] H3 — Feed-forward log entry: document the story pattern and any gotchas so
  that writing stories for the Breeder and Bias sections is easier

---

## What Is Not In Scope for This Work Package

| Item | Status |
|---|---|
| Time window switcher UI | Separate component; exists in the mock filter panel. Out of scope. |
| Genus selector | Irrelevant to Market Health (section is market-wide). Out of scope. |
| Breeder Opportunity section implementation | Next work package after this one. |
| Bias Control section implementation | After Breeder. |
| History table CSV export | Already implemented; do not touch. |
| Mobile / responsive breakpoints | Apply existing grid breakpoints from `common.css`; do not design new breakpoints. |

---

## Feed-Forward Log

*Agent: append a dated entry here after every H3. Entries accumulate and carry context
from one phase to the next, and from this work package to the next.*

```
[Phase 1 — not yet started]
```
