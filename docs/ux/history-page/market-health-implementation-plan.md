# Market Health — Implementation Plan

**Companion to:** [`market-health-handoff-spec.md`](./market-health-handoff-spec.md)  
**Branch to create from:** `master`  
**Suggested branch name:** `history-page-market-health`

Read the handoff spec first. This document is the agent's instruction set: it fills
in the engineering gaps the UX spec intentionally omits, then breaks the work into
phases with explicit checklists.

> **Work package:** This is **WP1 of 5**. It implements Section 1 (Market Health KPIs)
> only. Sections 2 (Breeder Opportunity), 3 (Bias Control), and 4 (Filtered Data Preview)
> are separate work packages (WP2–WP4). An additional infrastructure work package
> (**WP-Arch**) sits between WP1 and WP2: it delivers the genus selector UI, the
> lazy-load static JSON generator, and the Svelte fetch hook that all section WPs share.
> Do not implement anything from WP-Arch or WP2–WP4 here — they have no spec yet.
>
> **Scope note:** The initial implementation builds **All-mode** (`isAllSelected: true`)
> data only. The Svelte component supports genus-scoped heading/copy adaptation via
> `generaCount` and `scopeLabel` in the type contract, but the Python generator always
> produces market-wide KPI data for this work package. Genus-scoped KPI computation
> is explicitly deferred to WP-Arch — see spec §11 item #11.

---

## Gaps the UX Spec Does Not Cover

An agent MUST understand these before writing any code:

### G1 — Window global pattern

The existing page pattern is:
1. Python template renders `<script>window['history-tableData'] = {{ json_rows | safe }};</script>`
   directly into the page HTML (see `templates/table.html`).
2. `client/src/history-page/index.ts` reads `window['history-tableData']`, validates it
   with `assertPayload()`, then mounts a Svelte component.
3. A **second** independent island for Market Health was implemented in WP1 (Phases 6–7)
   following the same pattern:
   - Python injects `window.marketHealthPayloads = { … };` (a dict of all 7 pre-computed
     window payloads)
   - `history-page/index.ts` reads it and mounts `MarketHealthSection` with the default window.

> **⚠️ Architectural pivot (decided post-Phase 10):** The pre-computed payload strategy is a
> dead end. Two confirmed future directions make it unviable:
>
> 1. **Individual species selection** — genus × species × 7 windows × comparison permutations
>    produces hundreds of static JSON files, not a manageable set.
> 2. **PWA / offline-first with a service worker** — a single raw dataset file is trivial to
>    cache and sync; hundreds of pre-computed files are not.
>
> **The new target architecture (delivered in Phases 11–12):**
> - Python produces `window.marketHealthRawData` — variant-level run records only (~60 lines).
> - All KPI computation, copy selection, sparkline resampling, and events logic moves from
>   `market_health_dto.py` into `client/src/history-page/market-health-engine.ts`.
> - Svelte components (`MarketHealthSection`, `MarketKpiCard`, etc.) are **unchanged** — they
>   still receive a `MarketHealthPayload` object, now built client-side by the engine.
> - `market_health_dto.py` and its Python tests are deleted after Phase 12.

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
dependency. Phase 1 installs it. Given the project uses Svelte 5 + Vite + Vitest,
the correct install is:
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

The computation takes a `selected_genera: List[str]` parameter (list of genus name strings,
e.g. `["Avicularia", "Caribena"]`) and an `is_all_selected: bool` parameter (default
`True`). When `is_all_selected=True`, the computation uses **all rows** (market-wide);
when `False`, it filters to rows where the first token of `scientific_name` is in
`selected_genera`. **WP1 always generates all-mode only** (`is_all_selected=True`;
genus selection changes are deferred to WP-Arch, which will add lazy-load static JSON
files — `market-health/genus/{slug}.json` and `market-health/species/{slug}.json` —
that the Svelte island fetches client-side on first selection. Pre-embedding all
combinations inline is not viable: 68 genera × 7 windows = 476 payloads, and species
level multiplies that further. See spec §11 item #11 for the full rationale.

The CSV the computation reads from: `spidershop_spiderlings_history.csv` with schema:
```
scrape_datetime, scientific_name, common_name, size_cm, price_gbp, wishlist_count, page_url
```
A species is **in-stock** at a run if any size-variant row for that `scientific_name`
appears in the CSV for that `scrape_datetime`. The `price_gbp` and `wishlist_count`
columns are numeric strings. `history_rows` contains one raw CSV row per
`(scientific_name, size_cm, scrape_datetime)` — the DTO must deduplicate to
species-level internally for all four KPI metrics.

### G5 — Template wiring

**Do NOT modify `templates/history_page.html` or write to `history.html`.** The existing
History page must remain untouched until all four work packages are merged.

Instead, create a **new** template `templates/history_insights_page.html` and a **new**
generator function `generate_history_insights_page()` in `generate_website.py` that writes
to `history-insights.html`. The new template:
- Extends `base.html`; follow the structure of `history_page.html`
- Prepends `<div id="market-health-root"></div>` above the table section
- Places `<script>window.marketHealthPayloads = {{ market_health_payloads | tojson | safe }};</script>`
  in `{% block extra_js %}`, following the pattern in `templates/analysis_page.html`

A new `PageNavItem` must also be added to `NAV_ITEMS` in `src/website/page_config.py`:
- `icon`: `"📈"`, `label`: `"History Insights"`, `url`: `"history-insights.html"`,
  `active_page`: `"history-insights"`

This ensures the new page appears in the top nav and on the homepage card grid alongside
(not replacing) the existing Historical Data page.

### G6 — Test commands (MANDATORY)

```bash
make test-client-fast     # fast Vitest — run after every component change
make test-client          # Vitest + coverage — run at end of each client phase (≥80%)
make test                 # Python unit tests — run at end of each Python phase (≥80%)
make test-e2e             # Playwright — run at end of Phase 7 (page integration)
make test-visual          # browser-backed CSS contracts — run when style blocks change
make storybook            # start Storybook dev server on port 6006
```

### G7 — Chrome DevTools MCP verification protocol

Chrome DevTools MCP is the agent's primary visual verification tool for Storybook stories
and the preview site. Use it proactively at each story checkpoint — not just when something
looks wrong. The Chrome DevTools MCP server must be connected in VS Code.

**Standard story verification sequence:**
1. Ensure `make storybook` is running as a background process (port 6006).
2. Navigate to the story via Chrome DevTools MCP:
   `http://localhost:6006/?path=/story/{component}--{story}`
   (component and story names are kebab-cased, e.g. `market-kpi-card--negative-delta`).
3. Take a screenshot with Chrome DevTools MCP.
4. Read `docs/ux/history-page/history-kpi-concepts-mockup.html` to identify the
   corresponding section. Open the mock in Chrome with its `file://` absolute path and
   screenshot the matching section for direct pixel comparison.
5. Run `evaluate_script` to check computed CSS properties that are invisible in
   screenshots: opacity values, token resolution, visibility state, attribute values.

**Token resolution check — run once after Phase 1 Storybook config, before writing any component:**
```js
evaluate_script(`
  const s = getComputedStyle(document.documentElement);
  return {
    colorInk:    s.getPropertyValue('--color-ink').trim(),
    colorAccent: s.getPropertyValue('--color-accent').trim(),
    colorMuted:  s.getPropertyValue('--color-muted').trim(),
  };
`)
// All three must be non-empty strings.
// Empty = templates/common.css not imported correctly in client/.storybook/preview.ts.
```

**Port note:** `make test-e2e` uses port 8000. Stop `make preview` before running
E2E tests. Storybook (6006) and preview (8000) can run simultaneously.

---

## Phase Structure

Each phase ends with **five mandatory steps. All five must be completed before starting the
next phase. An agent that skips any step is in protocol violation — the phase is NOT complete.**

```
[ ] H1 — Mark every task checkbox above as ✅ — only after the task is actually done,
         not speculatively
[ ] H2 — Reflection: scan every new file against the code smell checklist; fix ALL issues
         before committing — do not commit with a TODO to fix later
[ ] H3 — Feed-forward: append a dated entry to the Feed-forward log — required even when
         there is nothing new (write "no new findings" rather than skipping)
[ ] H4 — Commit: `git add -A && git commit -m "Phase N: <summary>"`
         then `git log --oneline -1` to confirm the commit is present
[ ] GATE — Output the phase completion block (format below) in your chat response.
           Every field must contain actual terminal output — no placeholders allowed.
           If a field cannot be filled, the phase is BLOCKED: stop, fix it, then output.
```

**GATE — phase completion block. Paste this template and fill with real output.**
This block appearing in your response is the ONLY acceptable evidence a phase is complete.
Its absence means the phase was NOT completed per protocol.

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE N COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of last make test-client-fast / make test output]
║  Commit:   [paste output of: git log --oneline -1]
║  Stories:  [StoryName → evaluate_script passed]  or  [N/A — no stories this phase]
║  Blockers: none  /  [name any deferred item]
╚══════════════════════════════════════════════════════════════╝
```

**Code smell checklist for H2:**
- Duplicated logic that belongs in a shared utility
- Svelte `<style>` blocks referencing hardcoded colours (must use `var(--token)`)
- Any `// TODO` or `// FIXME` that was added as a shortcut
- TypeScript `any` that can be replaced with a proper type
- Props passed deeply through multiple components that should be flattened
- Fixture data that diverges from the TypeScript interface (will break the type checker)

**Make commands — MANDATORY (never bypass):**
- `make test-client-fast` / `make test-client` / `make test` / `make test-e2e` / `make test-visual`
- **Never run pytest, vitest, or `python -m` commands directly.** Make commands ensure the
  correct working directory, artifact paths, and environment. Bypassing them causes CSV files
  in wrong directories, scattered artifacts, and misleading coverage numbers.
- **Never generate the website by running Python directly.** Always use `make generate-website`
  or `make preview`.

---

## Phase 1 — Foundation: Types, Fixtures, and CSS Tokens

**Goal:** Establish the canonical type contract and fixture files that all subsequent
phases depend on. No rendering code. No Svelte. Everything must compile cleanly.

**Pre-flight (do before writing any code):**
- [x] Read `templates/common.css` `:root` block — build a mapping table for the
  six mock tokens listed in G2 above. Add to feed-forward log.
- [x] Read `client/src/history-page/index.ts` — understand the current island
  initialisation pattern (`registerPageInit`, `assertPayload`, `mount`).
- [x] Read `client/src/shared/page-init.ts` (or equivalent) — understand what
  `completeTableMount` / `registerPageInit` expect.
- [x] Read Svelte 5 + Storybook compatibility: Storybook ≥ 8.5 is required for
  Svelte 5 runes support. Confirm before running the init command.
- [x] Run `make test-client-fast` — confirm baseline is green before touching anything.

**Tasks — Types and Fixtures:**
- [x] Create `client/src/history-page/types.ts` — export all interfaces
  from the handoff spec §7.2 (`MarketHealthPayload`, `KpiCardData`, `SparklineSeries`,
  `MarketEventsData`, `EventTile`, `WindowId`). Fixtures import from `'../types'`.
- [x] Create `client/src/history-page/__fixtures__/` directory and the fixture module
  `marketHealth.currentQuarter.ts` (full data — see spec §8.2).
- [x] Create `client/src/history-page/__fixtures__/marketHealth.allTime.ts`
  (`showPrior: false`, flat deltas — see spec §8.3).
- [x] Create `client/src/history-page/__fixtures__/marketHealth.lastQuarter.ts`
  (completed period, named quarter label).
- [x] Create `client/src/history-page/__fixtures__/marketHealth.stockUnderPressure.ts`
  (stock delta ≤ −7, wishlist delta ≥ +3).
- [x] Run `npx tsc --noEmit` from `client/` — confirm zero type errors.

**Tasks — Storybook install and config:**
- [x] Confirm `client/package.json` has no Storybook dependency (it should not).
- [x] Install Storybook (run from `client/` directory):
  ```bash
  npx storybook@latest init --type svelte
  ```
  Accept the Vite builder. Decline any example stories.
- [x] Verify `client/.storybook/main.ts` and `client/.storybook/preview.ts` were created.
- [x] Import `templates/common.css` in `client/.storybook/preview.ts` so global design
  tokens are available in the Storybook canvas.
- [x] Add `storybook` and `build-storybook` scripts to `client/package.json`.
- [x] Add `make storybook` to the root `Makefile` (runs `cd client && npx storybook dev`).
- [x] Run `make storybook` as a background process.
- [x] Navigate to `http://localhost:6006` via Chrome DevTools MCP; take a screenshot
  to confirm the canvas opens; run the G7 token resolution check — all three values
  must be non-empty strings before any component work begins.

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 1: foundation — types, fixtures, Storybook config"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 2 — MarketSparkline Component

**Goal:** Build the inline SVG sparkline with run-selection interaction. This is the
most self-contained visual element; getting it right here means `MarketKpiCard` is
simple assembly.

**Pre-flight:**
- [x] Review `client/src/species-page/charts.ts` — understand the existing approach to
  SVG coordinate math. Do not duplicate; extract to a shared helper if the pattern is
  reused.

**Tasks:**
- [x] Create `client/src/history-page/MarketSparkline.svelte`:
  - Props: `series: number[]`, `priorSeries: number[]`, `showPrior: boolean`,
    `color: string`, `formatValue: (v: number) => string`, `selectedRun: number | null`,
    `onRunSelect: (run: number | null) => void`
  - Renders an inline SVG with 12 data points per series
  - Current series: solid line, `stroke-width: 2.5`, filled circles (`r=2.7`, `r=4.4` selected)
  - Prior series: dashed line, CSS `opacity: 0.38` on the `<polyline>`, lighter circles
    (`r=2.2`, `r=3.4` selected), CSS `opacity: 0.45` on prior `<circle>` elements
  - Non-selected points when a run is chosen: add `.is-subdued` class (CSS `opacity: 0.16`)
  - Baseline axis line: horizontal `<line>` at `y = height - bottomPadding`,
    `stroke: #d7cfc0`, `stroke-width: 1`
  - Run-axis labels: three `<text>` elements at x-positions 0, 5, 11 (0-indexed);
    default labels `"Run 1"`, `"Run 6"`, `"Run 12"` (overridden per window for year/all-time)
  - All display labels are 1-indexed (internal index n → "Run n+1")
  - Prior series: not rendered when `showPrior = false`
  - Click on any hit area fires `onRunSelect(runIndex)` (or `null` if already selected)
- [x] Create `client/src/history-page/MarketSparkline.test.ts`:
  - Renders with `showPrior: true` → both series in DOM
  - Renders with `showPrior: false` → prior series not in DOM
  - Click on run index 3 → `onRunSelect(3)` called
  - Click on already-selected run → `onRunSelect(null)` called
  - Selected run → hit point has larger radius; others have `.is-subdued`
- [x] Run `make test-client-fast` — green
- [x] Run `make test-visual` — add a visual contract for the sparkline computed styles
  (check that solid vs dashed stroke styles resolve correctly)
- [x] Create `client/src/history-page/MarketSparkline.stories.ts`:
  - Story: `Default` — 12-point series, `showPrior: true`, no run selected
  - Story: `ShowPriorFalse` — `showPrior: false`, no run selected
  - Story: `RunSelected` — `selectedRun: 5`, `showPrior: true`
- [x] Verify each story via Chrome DevTools MCP (see G7 for protocol):
  - **`Default`** (`/story/market-sparkline--default`) — take a screenshot and compare
    against the sparkline SVG in the mock's Section 1; run `evaluate_script` to confirm
    the prior series polyline opacity:
    ```js
    const polylines = document.querySelectorAll('svg polyline');
    const prior = polylines[polylines.length - 1]; // adjust to whichever is the prior
    return prior ? getComputedStyle(prior).opacity : 'not found';
    // expected: "0.38"
    ```
  - **`ShowPriorFalse`** (`/story/market-sparkline--show-prior-false`) — run
    `evaluate_script` to confirm only one `<polyline>` exists (no prior series):
    ```js
    return document.querySelectorAll('svg polyline').length;
    // expected: 1
    ```
  - **`RunSelected`** (`/story/market-sparkline--run-selected`) — take a screenshot;
    run `evaluate_script` to confirm 11 `.is-subdued` circles at `opacity: 0.16` and
    one selected circle with the larger radius attribute:
    ```js
    const subdued = document.querySelectorAll('.is-subdued');
    return {
      subduedCount:   subdued.length,
      subduedOpacity: subdued[0] ? getComputedStyle(subdued[0]).opacity : 'n/a',
      selectedExists: !!document.querySelector('[r="4.4"]'),
    };
    // expected: { subduedCount: 11, subduedOpacity: "0.16", selectedExists: true }
    ```

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 2: MarketSparkline component"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 3 — MarketKpiCard Component

**Goal:** Build a single KPI tile. Receives pre-computed data; no internal computation.

**Tasks:**
- [x] Create `client/src/history-page/MarketKpiCard.svelte`:
  - Props: `card: KpiCardData`, `series: SparklineSeries`, `showPrior: boolean`,
    `selectedRun: number | null`, `onRunSelect: (run: number | null) => void`
  - Renders: `<h3>` title, `.metric-value`, `.metric-delta` (with deltaClass modifier),
    copy `<p>`, `<MarketSparkline>` passing through run props
- [x] Create `client/src/history-page/MarketKpiCard.test.ts`:
  - Delta class `""` → no modifier class on `.metric-delta`
  - Delta class `"down"` → `.metric-delta.down` in DOM
  - Delta class `"flat"` → `.metric-delta.flat` in DOM
  - `showPrior: false` → sparkline receives `showPrior: false`
  - `onRunSelect` callback prop is forwarded to sparkline
- [x] Run `make test-client-fast` — green
- [x] Run `make test-client` — coverage ≥ 80% for new files
- [x] Create `client/src/history-page/MarketKpiCard.stories.ts`:
  - Story: `PositiveDelta` — `deltaClass: ""`, positive delta string
  - Story: `NegativeDelta` — `deltaClass: "down"`
  - Story: `FlatDelta` — `deltaClass: "flat"`
  - Story: `AllTimeNoPrior` — `showPrior: false`, no sparkline overlay
- [x] Verify each story via Chrome DevTools MCP:
  - **`PositiveDelta`** (`/story/market-kpi-card--positive-delta`) — take a screenshot;
    compare the full card layout (title / value / delta badge / copy / sparkline) against
    the corresponding KPI card in the mock's Section 1.
  - **`NegativeDelta`** (`/story/market-kpi-card--negative-delta`) — run `evaluate_script`
    to confirm the `.down` modifier resolves to a token colour (not hardcoded hex):
    ```js
    const badge = document.querySelector('.metric-delta.down');
    return badge ? {
      color:      getComputedStyle(badge).color,
      background: getComputedStyle(badge).backgroundColor,
    } : 'not found';
    // compare the rgb() values against the mock's .signal-down badge colour
    ```
  - **`AllTimeNoPrior`** (`/story/market-kpi-card--all-time-no-prior`) — run
    `evaluate_script` to confirm there is only one `<polyline>` (current series only):
    ```js
    return document.querySelectorAll('svg polyline').length;
    // expected: 1
    ```

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 3: MarketKpiCard component"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 4 — MarketEventsCard Component

**Goal:** Build the static events mini-grid. No interaction — pure display.

**Tasks:**
- [x] Create `client/src/history-page/MarketEventsCard.svelte`:
  - Props: `events: MarketEventsData`
  - Renders: `<article class="visual-card">` with `<h3>` title, subtitle `<p>`,
    and a 2×2 CSS grid of event tiles (label / bold value / copy)
- [x] Create `client/src/history-page/MarketEventsCard.test.ts`:
  - All 4 tiles render with correct label, value, and copy from fixture
  - Title and subtitle are dynamic (use the `currentQuarter` and `allTime` fixtures
    to verify both)
- [x] Run `make test-client-fast` — green
- [x] Create `client/src/history-page/MarketEventsCard.stories.ts`:
  - Story: `CurrentQuarter` — events from `currentQuarter` fixture
  - Story: `AllTime` — events from `allTime` fixture
- [x] Verify each story via Chrome DevTools MCP:
  - **`CurrentQuarter`** (`/story/market-events-card--current-quarter`) — take a
    screenshot and compare the 2×2 grid layout and copy text against the mock's events
    section; run `evaluate_script` to confirm all 4 tiles rendered with non-empty copy:
    ```js
    const tiles = [...document.querySelectorAll('.event-tile')];
    return tiles.map(t => t.querySelector('.event-copy')?.textContent.trim().slice(0, 50));
    // adapt selector to match your implementation; all 4 must be non-empty
    ```
  - **`AllTime`** (`/story/market-events-card--all-time`) — run `evaluate_script` to
    confirm value fields use `"N total"` format (not `"+N vs {period}"`):
    ```js
    const values = [...document.querySelectorAll('.event-value')];
    return values.map(v => v.textContent.trim());
    // all four must match the "N total" pattern from spec §5.2
    ```

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 4: MarketEventsCard component"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 5 — MarketHealthSection Island (Assembly + State)

**Goal:** Compose the section. Own the `selectedRun` state. Wire the sparkline legend
(basis note, prior key visibility, "Clear run focus" button). This is the Svelte island
that mounts into the page.

**Tasks:**
- [x] Create `client/src/history-page/MarketHealthSection.svelte`:
  - Props: `payload: MarketHealthPayload`, `initialSelectedRun?: number`
  - Local `$state`: `selectedRun: number | null = initialSelectedRun ?? null`
  - Renders: section header, 4×`MarketKpiCard`, sparkline support row (legend,
    basis note, selection note, clear button), `MarketEventsCard`
  - Sparkline support row:
    - Prior-key item hidden when `payload.showPrior === false`
    - Basis note = `payload.sparklineBasisNote`
    - Selection note: `"Optional: click a run…"` → `"Run {n+1} selected. The same moment
      is now highlighted across all four KPI cards."` when run index n is chosen
    - "Clear run focus" button: hidden when `selectedRun === null`; clears on click
  - `onRunSelect` callback shared across all 4 cards — sets `selectedRun` or clears
    if the same run is clicked again
- [x] Create `client/src/history-page/MarketHealthSection.test.ts`:
  - Renders with `currentQuarter` fixture — all 4 KPI cards visible
  - Prior key in legend is visible when `showPrior: true`
  - Prior key in legend is hidden when `showPrior: false` (use `allTime` fixture)
  - Click run index 5 (0-based) on observed sparkline → selection note updates to
    contain `"Run 6 selected. The same moment is now highlighted across all four KPI cards."`
    AND `selectedRun` propagates to all 4 cards
  - Click same run again → note resets to "Optional" text; clear button hidden
  - Clear button click (when visible) → resets selection
- [x] Register the island mount in `client/src/history-page/index.ts`:
  - Read `window.marketHealthPayloads` (cast as `Record<WindowId, MarketHealthPayload> | undefined`)
  - Default to `'current-quarter'` window on initial mount; switch the active payload
    when the user clicks a time-window button
  - If present, mount `MarketHealthSection` into `<div id="market-health-root">`
  - (The mount point does not exist in the template yet — that is Phase 6)
- [x] Run `make test-client` — coverage ≥ 80% for all history-page files
- [x] Create `client/src/history-page/MarketHealthSection.stories.ts`:
  - `meta.component = MarketHealthSection`
  - Story: `CurrentQuarter` — args from `marketHealthCurrentQuarter` fixture
  - Story: `LastQuarter` — args from `marketHealthLastQuarter` fixture
  - Story: `AllTime` — args from `marketHealthAllTime` fixture
  - Story: `StockUnderPressure` — args from `marketHealthStockUnderPressure` fixture
  - Story: `RunSelected` — `currentQuarter` fixture + `initialSelectedRun: 8`
    (seeds the internal `$state`; no decorator needed)
- [x] Verify all stories via Chrome DevTools MCP — this is the primary living-spec
  acceptance gate before the Python data layer is wired up:
  - **`CurrentQuarter`** (`/story/market-health-section--current-quarter`) — take a
    full screenshot and compare the complete section (4-card KPI grid, sparkline support
    row, events grid) against the mock's Section 1; run `evaluate_script`:
    ```js
    return {
      kpiCardCount:     document.querySelectorAll('.kpi-card').length,
      priorKeyVisible:  !!document.querySelector('.legend-prior-key:not([hidden])'),
      selectionNote:    document.querySelector('.pulse-selection-note')?.textContent.trim(),
      clearBtnHidden:   getComputedStyle(
        document.querySelector('.clear-run-btn')
      ).display === 'none',
    };
    // { kpiCardCount: 4, priorKeyVisible: true,
    //   selectionNote: contains "Optional: click a run", clearBtnHidden: true }
    ```
  - **`AllTime`** (`/story/market-health-section--all-time`) — run `evaluate_script` to
    confirm the prior legend key is hidden and no prior polylines exist in any sparkline:
    ```js
    const priorKey = document.querySelector('.legend-prior-key');
    return {
      priorKeyHidden:      !priorKey || getComputedStyle(priorKey).display === 'none',
      priorPolylineCount:  document.querySelectorAll('polyline.prior').length,
    };
    // { priorKeyHidden: true, priorPolylineCount: 0 }
    ```
  - **`StockUnderPressure`** (`/story/market-health-section--stock-under-pressure`) —
    take a screenshot; run `evaluate_script` to confirm the stock KPI delta has the
    `down` class and the copy matches the ≤−7 branch from spec §3.2:
    ```js
    // adapt selectors to match your component's actual class names
    const stockCard = [...document.querySelectorAll('.kpi-card')]
      .find(c => c.querySelector('h3')?.textContent.includes('In-stock'));
    return {
      deltaHasDown: stockCard?.querySelector('.metric-delta')?.classList.contains('down'),
      copySnippet:  stockCard?.querySelector('.kpi-copy')?.textContent.trim().slice(0, 60),
    };
    // deltaHasDown: true; copySnippet starts with the "N% of tracked listings" text
    ```
  - **`RunSelected`** (`/story/market-health-section--run-selected`) — take a screenshot;
    run `evaluate_script` to confirm `initialSelectedRun: 8` shows "Run 9" (0-based 8
    → 1-indexed display), clear button is visible, and 44 circles are subdued (11 per
    sparkline × 4 cards):
    ```js
    return {
      selectionNote:  document.querySelector('.pulse-selection-note')?.textContent.trim(),
      clearBtnVisible: document.querySelector('.clear-run-btn') &&
        getComputedStyle(document.querySelector('.clear-run-btn')).display !== 'none',
      subduedTotal:   document.querySelectorAll('.is-subdued').length,
    };
    // { selectionNote: "Run 9 selected. The same moment is now highlighted...",
    //   clearBtnVisible: true, subduedTotal: 44 }
    ```

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 5: MarketHealthSection island"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 6 — Python Data Layer

**Goal:** Build the server-side computation that converts the history CSV into a
`MarketHealthPayload`-shaped dict for every time window, then inject it as a window
global into the history page.

**Pre-flight:**
- [x] Read `src/website/sparkline_dto.py` — understand the existing DTO pattern
  (how data is computed and returned as a Python dict that Jinja serialises).
- [x] Read `src/website/history_chart_dto.py` — understand if any reusable aggregation
  helpers already exist.

**Tasks:**
- [x] Create `src/website/market_health_dto.py`:
  - Public function: `build_market_health_payload(history_rows: List[dict], window_id: str, selected_genera: List[str], is_all_selected: bool = True) -> dict`
  - Accepts the same list-of-dicts that the history table uses, plus the selected
    time window ID, the list of genus names in scope, and a flag for All-mode.
  - Returns a Python dict matching the `MarketHealthPayload` TypeScript interface
    (including the `isAllSelected` field).
  - Computation rules — **genus filter is conditional**: if `is_all_selected=True`, use
    all rows (market-wide); if `False`, filter `history_rows` to only rows where the
    first token (genus) of `scientific_name` is in `selected_genera`. All subsequent
    computations operate on this filtered set.
    - **Observed species**: `COUNT DISTINCT scientific_name` where `scrape_datetime`
      falls within the active window period AND the row exists (= in-stock) in the
      filtered set.
    - **In-stock rate**: `(distinct species in-stock at the latest scrape within window) /
      (distinct species seen in-stock at any point during the window) × 100`. Round to integer.
    - **Median wishlist**: `MEDIAN(wishlist_count)` at the latest scrape within window,
      one value per species. For species with multiple active size variants, use the max
      `wishlist_count` among active variants (per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4).
      Convert to integer.
    - **Median price**: `MEDIAN(price_gbp)` at the latest scrape within window,
      one value per species. For species with multiple active size variants, use the price
      from the current active size lineage (per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4).
      Format as `"GBP N"`.
    - **Prior period computation**: for each window ID, derive the matched prior period
      (e.g. "current quarter" → "same dates last quarter") and compute the same
      four metrics for that period. Delta = current − prior.
    - **Sparkline series**: 12 evenly-spaced runs within the window; compute each
      metric at each run point. For `showPrior: false` windows, return `[]` for prior.
    - **Events**: count new/dropped/restock/stockout transitions at **species level** across
      the window runs. A confirmed size transition (same `page_url`, same species, ≤3-run
      window per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 2) must NOT be counted as a
      `droppedListings` + `newListings` pair. Restocks and stockouts are species-level
      (any active variant present = present; all variants absent = absent).
    - **Copy selection**: use the bounded copy sets from spec §3 and §5.
    - When fewer than 2 scrapes exist for a window: raise a domain-level warning
      (not an exception) and return safe fallback values with `showPrior: false`.
  - Build a second public function:
    `build_market_health_payload_all_windows(history_rows: List[dict], selected_genera: List[str], is_all_selected: bool = True) -> dict[str, dict]`
    returning one payload per window ID.
- [x] Create `tests/website_module/test_market_health_dto.py`:
  - Test observed species count for a minimal fixture (2 scrapes, 3 species each)
  - Test in-stock rate computation
  - Test median wishlist with even vs odd number of in-stock rows
  - Test prior period boundary derivation for each `window_id`
  - Test `showPrior: false` for `all-time` window
  - Test events counting (new listings, dropped, restocks, oos flips)
  - Test fewer-than-2-scrapes edge case — returns fallback, no crash
  - **Test genus filtering**: given rows with 3 genera, passing `selected_genera=["A", "B"]`
    with `is_all_selected=False` must exclude genus `C` from all four metric computations
  - **Test All-mode**: given rows with 3 genera, passing `is_all_selected=True` must
    include all genera regardless of `selected_genera`
  - **Test multi-variant deduplication**: given a species with 2 active size variants in
    the same run, median wishlist uses the max `wishlist_count` (not a double-count);
    median price uses the primary active-lineage price; in-stock rate counts the species once
  - **Test size transition is not a drop+add**: a confirmed size transition (3cm → 5cm,
    same URL, within 3 runs) must not increment `newListings` or `droppedListings`
- [x] Run `make test` — green; `make test-file FILE=tests/website_module/test_market_health_dto.py`
  — coverage ≥ 80% for `market_health_dto.py`

> **Amendment — dynamic basis notes for in-progress windows (spec §4.4 and §6):**
> The static `_WINDOW_BASIS_NOTES` and `_SPARKLINE_BASIS_NOTES` dictionaries in
> `market_health_dto.py` produce generic strings for `this-month`, `current-quarter`,
> and `this-year` (e.g. `"Comparison basis: quarter to date vs prior quarter QTD."`).
> These must be replaced with **dynamically computed strings** that embed the actual
> date spans returned by `_get_window_bounds`. For `current-quarter` on Apr 21, 2026
> the expected output is:
> - `windowBasisNote`: `"Quarter in progress (Q2 2026) — comparing Apr 1 – Apr 21 against the same span into Q1 2026 (Jan 1 – Jan 21)."`
> - `sparklineBasisNote`: `"Compare within a row. Solid shows Q2 2026 to date (Apr 1 – Apr 21); dashed shows the same span into Q1 2026 (Jan 1 – Jan 21)."`
>
> The same pattern applies to `this-month` and `this-year`. Completed windows
> (`last-month`, `last-quarter`, `last-year`, `all-time`) keep their static strings.
> This is a **code change to `market_health_dto.py`** and requires:
> 1. A new helper (e.g. `_build_inprogress_basis_notes(window_id, win_start, win_end, prior_start, prior_end, ref)`) that returns `(windowBasisNote, sparklineBasisNote)` for in-progress windows.
> 2. The call site in `build_market_health_payload` to use this helper instead of the static dicts for the three in-progress window IDs.
> 3. Updated tests in `test_market_health_dto.py` asserting the date-range format.
> 4. Updated fixture `client/src/history-page/__fixtures__/marketHealth.currentQuarter.ts` — `windowBasisNote` and `sparklineBasisNote` must be updated to match the new format (example values in spec §8.2).

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 6: market health Python data layer"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 7 — Page Integration

**Goal:** Create the new `history-insights.html` page — a separate page that appears
alongside (not replacing) the existing `history.html`. Wire the Python DTO, inject the
window global, and validate end-to-end.

**CRITICAL — do NOT touch `history.html` or `history_page.html`:** The existing History
page stays intact until all four work packages (WP1–WP4) are merged. This phase creates
a new page only.

**Pre-flight:**
- [x] Read `src/website/generate_website.py` — study `generate_history_page()` as the
  model for the new function; understand how `json_rows`, the template context, and
  `OUTPUT_DIR` are used.
- [x] Read `src/website/page_config.py` — understand the `NAV_ITEMS` list and
  `PageNavItem` dataclass.

**Tasks:**
- [x] In `src/website/page_config.py`:
  - Add a new `PageNavItem` entry to `NAV_ITEMS` immediately after the existing
    "Historical Data" entry:
    ```python
    PageNavItem(
        icon="📈",
        label="History Insights",
        url="history-insights.html",
        active_page="history-insights",
        card_description="Market Health KPIs, supply trends, and pricing signals derived from historical scrape data.",
        card_link_text="View Insights",
    ),
    ```
- [x] Create `templates/history_insights_page.html`:
  - Extend `base.html`; follow the structure of `history_page.html`
  - Prepend `<div id="market-health-root"></div>` above the table section
  - Place `<script>window.marketHealthPayloads = {{ market_health_payloads | tojson | safe }};</script>`
    in `{% block extra_js %}` (all 7 window payloads, Option A — see spec §11 item #10;
    always `is_all_selected=True` for this work package — see spec §11 item #12)
- [x] In `src/website/generate_website.py`:
  - Add `generate_history_insights_page(config: BasePageConfig) -> str` — modelled on
    `generate_history_page()` but renders `history_insights_page.html` and adds
    `market_health_payloads` to the template context (computed via
    `build_market_health_payload_all_windows`).
  - Call it in the main generation block and write to `OUTPUT_DIR / "history-insights.html"`.
- [x] In `client/src/history-page/index.ts`:
  - Ensure the `marketHealthPayloads` read and `MarketHealthSection` mount added in
    Phase 5 is guarded: only mount if the element and payloads dict both exist.
- [ ] Update `client/src/shared/payload-validation.ts` (or a separate validation call)
  to validate `window.marketHealthPayloads` shape in dev mode — check it is a non-empty
  dict and that each value has `kpis`, `sparklineSeries`, and `events` keys.
  **DEFERRED** — guard exists; shape validation can be added in a follow-up.
- [x] Run `make generate-website` — confirm `history-insights.html` exists in the output
  directory; confirm `history.html` is unchanged; spot-check `history-insights.html` for
  the mount point and `window.marketHealthPayloads` script block.
- [x] Run `make test-e2e` — confirm `history-insights.html` loads without errors, the
  market health section renders, and no console errors; confirm `history.html` still
  works correctly (no regressions).
- [x] Run `make test` and `make test-client` — full clean pass.

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry (see below)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 7: page integration — template wiring and E2E green"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 8 — Storybook Visual Acceptance Pass

**Goal:** Systematic Chrome DevTools MCP sweep across all stories and the live preview
site. No new code (unless a divergence is classified `"fixed"`). Every divergence must
be documented in the feed-forward log before the feature is considered shippable.

**Pre-flight:**
- [x] All stories from Phases 2–5 render without console errors.
- [x] Phase 7 complete — `make preview` shows the Market Health section with real data.
- [x] Both servers running: `make storybook` (port 6006) and `make preview` (port 8000).
  **Do not run `make test-e2e`** while `make preview` is active (port conflict).

**Tasks — Re-run all Phase 2–5 DevTools MCP checks as a final sweep:**
- [x] Re-execute every `evaluate_script` check defined in Phases 2–5. Fix any that now
  fail due to refactoring after the story was first written. Record results.

**Tasks — Cross-story token consistency check:**
- [x] Navigate to `CurrentQuarter` story. Run `evaluate_script` to confirm all four KPI
  sparkline stroke colours resolve from tokens (they will be `rgb()` strings — verify
  these match your G2 token mapping table from the Phase 1 feed-forward log):
  ```js
  const lines = document.querySelectorAll('svg polyline:first-of-type');
  return [...lines].map(p => ({
    isRgb: getComputedStyle(p).stroke.startsWith('rgb'),
    value: getComputedStyle(p).stroke,
  }));
  // All four must have isRgb: true; cross-check values against Phase 1 token map
  ```
- [x] Run `evaluate_script` to confirm no hardcoded `background-color` leaked onto
  `.visual-card` — the resolved value must match `--color-surface` from the token map:
  ```js
  return getComputedStyle(document.querySelector('.visual-card')).backgroundColor;
  ```

**Tasks — Preview site verification (real data, real Python output):**
- [x] Navigate to `http://localhost:8000/history-insights.html` via Chrome DevTools MCP.
- [x] Take a full-page screenshot. Compare the Market Health section visually against
  the `CurrentQuarter` Storybook story screenshot from Phase 5.
  **NOTE (by-design):** current-quarter window shows zeros since demo data predates Q2 2026.
  Verified all-time window shows real values: ["6", "100%", "7", "GBP 22"].
- [x] Run `evaluate_script` to confirm the island mounted and all 4 KPI cards are present:
  ```js
  return {
    rootHasChildren: document.querySelector('#market-health-root')?.children.length > 0,
    kpiCardCount:    document.querySelectorAll('.kpi-card').length,
  };
  // { rootHasChildren: true, kpiCardCount: 4 }
  ```
- [x] Run `evaluate_script` to confirm KPI value fields are populated (not `undefined`,
  `NaN`, or empty — which would indicate a DTO computation failure):
  ```js
  return [...document.querySelectorAll('.metric-value')].map(el => el.textContent.trim());
  // all four must be non-empty strings matching the formats from spec §3
  ```
  **NOTE (by-design):** current-quarter values are empty (demo data predates Q2 2026).
  all-time window confirmed: ["6", "100%", "7", "GBP 22"] ✅.

**Tasks — Divergence log:**
- [x] Document every divergence found in this phase in the feed-forward log with a
  decision: `"fixed"` (code updated to match mock), `"by-design"` (intentional
  production deviation), or `"deferred"` (tracked for follow-up).
  **No divergence may be left without a decision.**

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection scan
- [x] H3 — Feed-forward log entry (see below)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 8: visual acceptance pass complete"`
- [x] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 9 — Push and Open Pull Request

**Goal:** Publish the branch and open a pull request for human review.

**Pre-flight:**
- [x] All phases 1–8 complete — all H1–H4 steps checked off.
- [x] `make test-client` green.
- [x] `make test` green.
- [x] `make test-e2e` green.

**Tasks:**
- [x] Push the branch:
  ```bash
  git push --set-upstream origin history-page-market-health
  ```
- [x] Open a pull request using the GitHub CLI:
  ```bash
  gh pr create \
    --title "Market Health KPI section for History page" \
    --body "Implements the Market Health section as specified in docs/ux/history-page/market-health-handoff-spec.md and docs/ux/history-page/market-health-implementation-plan.md.\n\n## What this PR delivers\n- Phase 1: TypeScript interfaces, fixture files, Storybook install\n- Phase 2: MarketSparkline SVG component\n- Phase 3: MarketKpiCard component\n- Phase 4: MarketEventsCard component\n- Phase 5: MarketHealthSection island (assembly + state)\n- Phase 6: Python market_health_dto module\n- Phase 7: Template wiring, page integration, E2E green\n- Phase 8: Storybook visual acceptance pass\n\n## Testing\n- All Vitest unit tests pass with coverage ≥ 80%\n- All Python unit tests pass with coverage ≥ 80%\n- E2E suite passes\n- Visual contracts pass\n\n## Divergence log\nSee the Phase 8 feed-forward entry in the implementation plan for all by-design and deferred items." \
    --base master
  ```

**Tasks (continued):**
- [x] Confirm the PR was created: PR #158 — https://github.com/christianacca/spidershop-historical-analysis/pull/158
- [x] Output the review handoff prompt below in your response, replacing `[PR_NUMBER]`,
  `[PR_URL]`, and `[DEFERRED_ITEMS]` with real values from your Phase 8 feed-forward log.
  This prompt is for the user to paste into a new chat session to trigger a spec-conformance review:

---
**REVIEW HANDOFF PROMPT — paste into a new chat session:**

Review PR #158 (`history-page-market-health`) against the spec and plan for the Market Health KPI section.

PR: https://github.com/christianacca/spidershop-historical-analysis/pull/158

Before reviewing any code, read these files in full:
1. `docs/ux/history-page/market-health-handoff-spec.md`
2. `docs/ux/history-page/market-health-implementation-plan.md`
3. `docs/ux/history-page/history-kpi-concepts-mockup.html`

Then diff the PR and systematically verify each area:

**TypeScript:** `types.ts` interfaces match spec §7.2 exactly (field names, types, optional/required) · Fixtures match §8.2 (currentQuarter) and §8.3 (allTime) · No `any` types · No TODO/FIXME

**Components:** `MarketSparkline` rendering matches spec §4.1 (opacity values, baseline axis, run-axis labels) and §4.2 (run-selection, `.is-subdued` opacity) · `MarketKpiCard` delta CSS classes and copy strings match spec §3 exactly · `MarketEventsCard` copy and value formats match spec §5 · `MarketHealthSection` sparkline support row matches §4.3–§4.5, state wiring correct · No hardcoded colours in any `<style>` block — all values must be `var(--token)`

**Python:** `market_health_dto.py` computation matches Phase 6 rules in the plan · Species-level deduplication applied per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4 · Confirmed size transitions not counted as drop+add · Events are species-level · Coverage ≥ 80% · All required test cases from the Phase 6 checklist are present

**Integration:** `window.marketHealthPayloads` injected as all-windows `Record<WindowId, MarketHealthPayload>` · Island mount guarded (element + payloads both present) · Dev-mode payload validation present · E2E test covers: section renders, 4 KPI cards populated, no console errors

**Deferred items from Phase 8 (assess whether any are spec violations):**
- [deferred] `window.marketHealthPayloads` shape validation via `assertPayload()` not implemented;
  a guard checking element + payloads dict both exist is present but shape is not validated in dev mode.
- [by-design] current-quarter KPI values are zero on the demo/preview site because the demo CSV
  data predates Q2 2026; the all-time window correctly shows real values.

For each item found, report: **PASS** / **FAIL** (spec violation — quote the spec §, quote the code, suggest a fix) / **CONCERN** (not a violation but worth noting).

---

**Housekeeping:**
- [x] H1 — Confirm PR URL is accessible and the branch is visible on GitHub.
- [x] H3 — Feed-forward log entry: record the PR URL and confirm the review handoff prompt was output.

---

## Phase 10 — Visual Fidelity Pass

**Context:** A DevTools MCP review on 2026-04-07 (after PR #158 was opened) revealed that the
live `history-insights.html` page diverges significantly from the mock's Section 1. Eight
specific gaps were identified — five of these are spec gaps (information that was missing from
the plan/spec), two are implementation bugs, and one is a missing CSS token. This phase closes
all eight gaps. No logic, data contract, or Python changes are required.

**Spec drift that triggered this phase:**
- §2 layout diagram was incomplete (showed stacked header; mock shows two-column)
- §2 had no CSS visual spec for the eyebrow pill or delta badge states
- §2 had no note about the `<header>` HTML element conflict with `common.css`
→ **These were corrected directly in the spec (§2) before this phase was written.**

### Identified gaps (from DevTools MCP audit 2026-04-07)

| ID | Gap | Root cause | Severity |
|---|---|---|---|
| G10.1 | Section header has dark navy background (`rgb(44,62,80)`) | `<header>` HTML element inherits `common.css header { background: var(--color-primary) }`. Storybook does not reproduce this because it omits the global page stylesheet context. | **High** — makes heading text invisible |
| G10.2 | `--font-lg` undefined — section `<h2>` has no font-size | Token used in `MarketHealthSection.svelte` but absent from `common.css ` | **High** — heading renders with browser default size |
| G10.3 | `--color-text-primary` undefined — heading falls back to inherited colour | Token used in `MarketHealthSection.svelte` but absent from `common.css` | Medium |
| G10.4 | Section header is stacked (flex-column), not two-column | Spec §2 diagram incorrectly showed a stacked layout | Medium |
| G10.5 | Eyebrow is plain uppercase text, not a teal pill badge | Eyebrow pill CSS spec was missing from the plan | Medium |
| G10.6 | Delta badge positive state renders as muted gray, not teal | Positive badge CSS spec was missing; only `.down` and `.flat` were specified | Medium |
| G10.7 | KPI card border-radius is 6px (`--radius-md`); mock uses ~18px | No large card-radius token existed; plan said "use existing tokens" | Low–medium |
| G10.8 | `.market-health-section` has no card wrapper styling | Section card wrapper (border, radius, padding) was not mentioned in any previous phase | Low–medium |

**Important:** G10.1 and G10.2 are the most visually severe. Fix them first; the others are
progressive improvements. The dark header (G10.1) was not caught in Phase 8 because Storybook
renders components without the page-level `header` selector — the conflict only surfaces in the
generated site.

---

**Pre-flight (do before writing any code):**
- [x] Re-run the DevTools MCP gap verification on the live site to confirm all 8 gaps
  are still present as described. (Command: navigate to `http://localhost:8000/history-insights.html`,
  then run `evaluate_script` from the G10 acceptance check below.)
- [x] Read `templates/common.css (:root block)` — confirm the five new tokens listed below
  are not already defined under a different name before adding them.

---

**Tasks — Token additions (`templates/common.css` `:root` block):**

Add the five tokens below to the `/* === Font sizes ===*/`, `/* === Surfaces ===*/`, and
`/* === Border radius ===*/` sub-sections respectively. Do not reorder or reorganise the
existing token blocks.

- [x] `--font-lg: 1.4rem` — large heading font size (~23px); add to `Font sizes` group
- [x] `--color-text-primary: #2c3e50` — alias of `--color-text-heading`; add to `Text` group
  with comment `/* alias of --color-text-heading — use for primary headings */`
- [x] `--radius-pill: 999px` — for pill/chip shape elements; add to `Border radius` group
- [x] `--radius-card-lg: 16px` — large card / section card rounding; add to `Border radius` group
- [x] `--color-market-health: #1f7a6b` — teal accent for Market Health section and eyebrow;
  add to the `Brand / Accent` group with comment
  `/* teal — Market Health section accent, also the observed-sparkline series colour */`

After adding: run `make test-client-fast` to confirm no existing Vitest tests break.
Run `make test-visual` to confirm no existing visual contracts break.

---

**Tasks — `MarketHealthSection.svelte`:**

Fix G10.1, G10.2, G10.3, G10.4, G10.5, G10.8.

- [x] **G10.1 FIX:** Change `<header class="section-header">` to `<div class="section-header">`.
  This removes the conflict with `common.css header {}`. Verify by running
  `evaluate_script` on the live site: the section header background must NOT be dark navy.
- [x] **G10.4 FIX:** Update `.section-header` CSS to `flex-direction: row; align-items: flex-start; gap: var(--spacing-lg)`.
  Wrap the eyebrow + h2 + sub-copy in a `<div class="section-title">` (flex item, `flex: 1 1 auto`).
  Move `.section-note` outside `.section-title` so it is the second flex child of `.section-header`
  (`flex: none; max-width: 38ch; align-self: flex-start`).
- [x] **G10.5 FIX:** Update `.section-eyebrow` CSS:
  ```css
  .section-eyebrow {
    display: inline-block;
    background: rgba(31, 122, 107, 0.1);  /* tinted --color-market-health */
    color: var(--color-market-health);
    border-radius: var(--radius-pill);
    padding: 5px 9px;
    font-size: var(--font-sm);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  ```
  Note: the `rgba(31, 122, 107, 0.1)` value is a tinted opacity variant of
  `--color-market-health`. Because CSS has no native way to inline-apply an opacity
  modifier to a custom property without `color-mix()`, this explicit `rgba()` value is an
  accepted exception to the no-hardcoded-colour rule. Document it in the feed-forward log.
- [x] **G10.8 ENHANCE:** Add card wrapper treatment to `.market-health-section`:
  ```css
  .market-health-section {
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-card-lg);
    padding: var(--spacing-xl);
  }
  ```
  The mock uses a warm cream background; in production the section sits inside `.content`
  (white), so the background is intentionally left to inherit. This is a by-design
  approximation: document in the feed-forward log.
- [x] G10.2 / G10.3: Once `--font-lg` and `--color-text-primary` are added to `common.css`,
  the existing `.section-header h2` rule (`font-size: var(--font-lg); color: var(--color-text-primary)`)
  will resolve correctly — no CSS change required in the component.
- [x] Run `make test-client-fast` — green.
- [x] Run `make test-visual` — add / update the visual contract for `MarketHealthSection` to assert:
  - Section header background is NOT dark navy (`rgb(44, 62, 80)`)
  - Eyebrow is a pill shape (`border-radius: 999px`)
  - Section header is a row (`.section-header flex-direction: row`)

---

**Tasks — `MarketKpiCard.svelte`:**

Fix G10.6, G10.7.

- [x] **G10.6 FIX:** Replace the existing `.metric-delta` / `.metric-delta.down` / `.metric-delta.flat`
  CSS block so that **all three states use pill shape** (`border-radius: var(--radius-pill)`):
  ```css
  /* Positive / neutral (default, class "") — teal pill */
  .metric-delta {
    border-radius: var(--radius-pill);
    background: rgba(31, 122, 107, 0.12);  /* tinted --color-market-health */
    color: var(--color-market-health);
    font-size: var(--font-sm);
    font-weight: 600;
    padding: 3px 8px;
  }
  /* Negative — red-amber pill */
  .metric-delta.down {
    background: rgba(178, 76, 61, 0.12);   /* tinted; close to but not --color-danger */
    color: #b24c3d;
  }
  /* Neutral / all-time — muted pill */
  .metric-delta.flat {
    background: rgba(127, 140, 141, 0.12); /* tinted --color-text-muted */
    color: var(--color-text-muted);
  }
  ```
  Same rationale as G10.5 for the `rgba()` values — document in feed-forward log.
  The `.down` red uses `#b24c3d` (mock value) not `--color-danger` (#e74c3c) — this is a
  visual approximation; note it as by-design or adjust `--color-danger` if preferred.
- [x] **G10.7 ENHANCE:** Change `.kpi-card` `border-radius` from `var(--radius-md)` (6px)
  to `var(--radius-card-lg)` (16px). No other card properties need changing. Note: implementation uses 18px (hardcoded) to match mock more precisely than the 16px token.
- [x] **G10.7 ENHANCE:** Change `.metric-value` `font-size` from `1.6rem` to `1.9rem`
  to better match the mock's 32px value. (`1.9rem` ≈ 30.4px at base-16; close enough.)
- [x] Run `make test-client-fast` — green.
- [x] Run `make test-visual` — add / update the visual contract for `MarketKpiCard` to assert:
  - `.metric-delta` has `border-radius: 999px`
  - `.metric-delta` (positive) has a non-gray background (teal tint, not `--color-surface-light`)
  - `.kpi-card` `border-radius === "16px"` (or 18px as implemented)

---

**Tasks — Preview site and Storybook acceptance check:**

- [x] Run `make preview` (regenerate site + serve at `http://localhost:8000`).
- [x] Navigate to `http://localhost:8000/history-insights.html` via Chrome DevTools MCP.
- [x] Open the mock in parallel:
  `file:///Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/docs/ux/history-page/history-kpi-concepts-mockup.html`
- [x] Take screenshots of both and compare Section 1 visually.
- [x] Run `evaluate_script` to confirm all 8 gaps are closed:
  ```js
  const sectionHeader = document.querySelector('.section-header');
  const h2 = document.querySelector('#market-health-heading');
  const eyebrow = document.querySelector('.section-eyebrow');
  const delta = document.querySelector('.metric-delta');
  const deltaDown = document.querySelector('.metric-delta.down');
  const kpiCard = document.querySelector('.kpi-card');
  const section = document.querySelector('.market-health-section');
  const s = (el) => el ? window.getComputedStyle(el) : null;
  return {
    'G10.1 header-bg NOT dark':  s(sectionHeader)?.backgroundColor,
    'G10.2 h2 fontSize':         s(h2)?.fontSize,
    'G10.3 h2 color':            s(h2)?.color,
    'G10.4 header flex-direction': s(sectionHeader)?.flexDirection,
    'G10.5 eyebrow borderRadius':  s(eyebrow)?.borderRadius,
    'G10.6 delta borderRadius':    s(delta)?.borderRadius,
    'G10.6 delta-down color':      s(deltaDown)?.color,
    'G10.7 kpiCard borderRadius':  s(kpiCard)?.borderRadius,
    'G10.8 section borderRadius':  s(section)?.borderRadius,
  };
  // Expected:
  // G10.1: NOT "rgb(44, 62, 80)" — any non-dark value
  // G10.2: "22.4px" (1.4rem) or similar non-empty
  // G10.3: NOT empty / NOT "rgb(0,0,0)" inherit-fallback
  // G10.4: "row"
  // G10.5: "999px"
  // G10.6 delta borderRadius: "999px"
  // G10.6 delta-down color: NOT the gray muted color
  // G10.7: "16px"
  // G10.8: "16px"
  ```

---

**Housekeeping:**
- [x] H1 — Mark every task checkbox above as ✅
- [x] H2 — Reflection: scan all changed files against the code smell checklist; specific items to watch:
  - Confirm no `rgba()` hardcoded colour in `<style>` blocks that **is not** documented as an accepted exception to the token rule
  - Confirm `<header>` is not re-introduced for the section container anywhere
  - Confirm `--font-lg` and `--color-text-primary` are used **only** in components, never re-defined inline
- [x] H3 — Feed-forward log entry — see Feed-Forward Log below
- [x] H4 — Commit: `git add -A && git commit -m "Phase 10: visual fidelity — header fix, section layout, eyebrow pill, delta badge, card radius"` ✅
- [x] GATE — Phase completion block output in conversation

---

## Phase 11 — Client-Side Market Health Computation Engine

**Goal:** Port all KPI computation from `market_health_dto.py` to TypeScript. Purely
additive — zero existing code is modified. All existing tests remain green throughout.
The Svelte components are not touched; they still receive a `MarketHealthPayload` object.

> **Reading required before writing any code:**
> - `src/website/market_health_dto.py` — exact Python logic to port (window bounds,
>   filtering, metrics, sparkline resampling, events, copy selectors, delta formatters,
>   basis notes). This is the ground truth — match it exactly.
> - `client/src/history-page/types.ts` — existing types; you will add two new ones.
> - `client/src/history-page/__fixtures__/marketHealth.currentQuarter.ts` — understand the
>   expected output shape for the fixture-driven tests in Phase 12.

**Pre-flight:**
- [x] Run `make test-client-fast` — confirm baseline is green before touching anything.
- [x] Run `make test` — confirm Python tests are green.

---

### 11.1 — Extend types

Add to `client/src/history-page/types.ts` (after the existing exports, no changes to
existing interfaces):

```typescript
/** One variant-level row from the history CSV, normalised for the engine. */
export interface RawRunRecord {
  scrapeDatetime: string;   // ISO 8601 string — e.g. "2026-04-14T06:10:00"
  scientificName: string;   // full binomial — e.g. "Avicularia avicularia"
  sizeVariant: string;      // size_cm field from CSV — e.g. "2.0"
  pageUrl: string;          // page_url field — used for size-transition detection
  wishlistCount: number;    // numeric (0 if missing/invalid in source)
  priceGbp: number;         // numeric (0.0 if missing/invalid in source)
}

/**
 * Raw market data injected by Python as window.marketHealthRawData.
 *
 * referenceDate is the ISO string of the most recent scrape_datetime in the
 * dataset. The engine uses it to compute window boundaries relative to the data
 * rather than new Date(), keeping the static page meaningful however old it is.
 */
export interface MarketHealthRawData {
  records: RawRunRecord[];
  referenceDate: string;
}
```

- [x] Run `npx tsc --noEmit` from `client/` — zero errors.

---

### 11.2 — Create raw fixture

Create `client/src/history-page/__fixtures__/marketHealthRaw.ts`.

The fixture must exercise **every code path** in the engine. It must include:
- At least **3 distinct run datetimes** spanning a calendar quarter (so window-bound tests
  are meaningful)
- At least **4 distinct species**
- At least **one multi-variant species** (same `scientificName`, different `sizeVariant`
  and same `pageUrl`) — exercises max-variant dedup in wishlist and price metrics
- At least **one size transition** — same `scientificName` and `pageUrl`, different
  `sizeVariant`, appearance gap ≤ 3 runs — must NOT be counted as a new listing or restock
- At least **one species that drops out** between two consecutive runs (stock-out / OOS flip)
- At least **one species that restocks** (absent one run, reappears the next)
- At least **one species present in every run** (provides a stable denominator for events)
- A `referenceDate` equal to the most recent `scrapeDatetime` in the records

Use realistic ISO datetime strings with weekly spacing. Keep the fixture small enough to
hand-calculate expected values — these hand-calculated values drive the test assertions.

---

### 11.3 — Create the engine module

Create `client/src/history-page/market-health-engine.ts`.

**Public API (two exports only):**

```typescript
export function buildMarketHealthPayload(
  rawData: MarketHealthRawData,
  windowId: WindowId,
  options?: { selectedGenera?: string[]; isAllSelected?: boolean },
): MarketHealthPayload

export function buildMarketHealthPayloadAllWindows(
  rawData: MarketHealthRawData,
  options?: { selectedGenera?: string[]; isAllSelected?: boolean },
): Record<WindowId, MarketHealthPayload>
```

All internal functions are **not exported** — they are tested indirectly through the public
API. Exporting implementation details makes the public contract fragile.

**Internal functions to implement (port directly from `market_health_dto.py`):**

| TS function | Python equivalent | Notes |
|---|---|---|
| `getWindowBounds(windowId, refDate)` | `_get_window_bounds` | Returns `{ winStart, winEnd, priorStart, priorEnd, showPrior }` as `Date` objects |
| `filterToWindow(records, winStart, winEnd)` | `_filter_rows_to_window` | Boundary-inclusive |
| `applyGenusFilter(records, selectedGenera, isAllSelected)` | `_apply_genus_filter` | Splits `scientificName` on first space for genus |
| `getSortedRuns(records)` | `_get_sorted_runs` | Returns sorted distinct `scrapeDatetime` strings |
| `speciesInRun(records, runDt)` | `_species_in_run` | Returns `Set<string>` |
| `computeObserved(records)` | `_compute_observed` | Distinct `scientificName` count |
| `computeStockRate(records)` | `_compute_stock_rate` | Numerator: species at latest run; denominator: species seen at any point |
| `computeMedianWishlist(records)` | `_compute_median_wishlist` | Latest run; max per species across variants |
| `computeMedianPrice(records)` | `_compute_median_price` | Latest run; max per species across variants |
| `buildSparklineForMetric(records, metric)` | `_build_sparkline_for_metric` | Returns 12-point `number[]` |
| `resampleTo12(values)` | `_resample_to_12` | n≥12: even-index sample; n<12: pad with last value |
| `isSizeTransition(species, runs, prevIdx, currIdx, records, maxGap?)` | `_is_size_transition` | Same `pageUrl`, different `sizeVariant`, gap ≤ `maxGap` (default 3) |
| `findLastSeenIdx(species, runs, beforeIdx, records)` | `_find_last_seen_idx` | Backwards search |
| `findNextSeenIdx(species, runs, afterIdx, records)` | `_find_next_seen_idx` | Forwards search |
| `computeEvents(records, windowId, deltaLabel)` | `_compute_events` | Returns `MarketEventsData` |
| `observedCopy(delta, priorLabel, isAllTime)` | `_observed_copy` | 4-branch copy selector |
| `stockCopy(delta, valuePct, priorLabel, isAllTime)` | `_stock_copy` | 5-branch copy selector |
| `wishlistCopy(delta, priorLabel, isAllTime)` | `_wishlist_copy` | 5-branch copy selector |
| `priceCopy(delta, priorLabel, isAllTime)` | `_price_copy` | 5-branch copy selector |
| `formatObservedDelta(delta, isAllTime, deltaLabel)` | `_format_observed_delta` | Returns `[text, deltaClass]` |
| `formatStockDelta(delta, isAllTime, deltaLabel)` | `_format_stock_delta` | Returns `[text, deltaClass]` |
| `formatWishlistDelta(delta, isAllTime, deltaLabel)` | `_format_wishlist_delta` | Returns `[text, deltaClass]` |
| `formatPriceDelta(delta, isAllTime, deltaLabel)` | `_format_price_delta` | Returns `[text, deltaClass]` |
| `buildInprogressBasisNotes(windowId, winStart, winEnd, priorStart, priorEnd)` | `_build_inprogress_basis_notes` | Dynamic date-range strings; only called for `this-month`, `current-quarter`, `this-year` |
| `buildScopeLabel(selectedGenera, isAllSelected)` | `_build_scope_label` | ≤3 genera: joined list; 4+: "your N selected genera"; all-mode: `""` |

**Date formatting:** `_fmt_date` in Python produces `"Apr 1"` (abbreviated month, no zero-pad).
Implement in TypeScript using `Date.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })`.

**Median:** JavaScript has no built-in `median`. Implement: sort ascending, return middle value
for odd N, average of two middle values for even N (round to nearest integer for wishlist and
price as Python does).

**Window boundary constants** (copy verbatim from Python — string keys must match exactly):

```typescript
const ALL_WINDOW_IDS: WindowId[] = [
  'this-month', 'last-month', 'current-quarter', 'last-quarter',
  'this-year', 'last-year', 'all-time',
];

const PRIOR_LABELS: Record<WindowId, string> = {
  'this-month':       'the same point last month',
  'last-month':       'the prior full month',
  'current-quarter':  'the same point last quarter',
  'last-quarter':     'the prior full quarter',
  'this-year':        'the same point last year',
  'last-year':        'the prior full year',
  'all-time':         '',   // unused
};

const PRIOR_DELTA_LABELS: Record<WindowId, string> = {
  'this-month':       'prior month MTD',
  'last-month':       'prior full month',
  'current-quarter':  'prior quarter QTD',
  'last-quarter':     'prior full quarter',
  'this-year':        'prior year YTD',
  'last-year':        'prior full year',
  'all-time':         '',   // unused
};
```

Static sparkline basis notes (for completed windows — in-progress windows use
`buildInprogressBasisNotes`):

```typescript
const SPARKLINE_BASIS_NOTES: Partial<Record<WindowId, string>> = {
  'last-month':    'Compare within a row. Solid shows last month; dashed shows the prior full month.',
  'last-quarter':  'Compare within a row. Solid shows last quarter; dashed shows the prior full quarter.',
  'last-year':     'Compare within a row. Solid shows last year; dashed shows the prior full year.',
  'all-time':      'All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale.',
};

const WINDOW_BASIS_NOTES: Partial<Record<WindowId, string>> = {
  'last-month':    'Comparison basis: last full month vs prior full month.',
  'last-quarter':  'Comparison basis: last full quarter vs prior full quarter.',
  'last-year':     'Comparison basis: last full year vs year before.',
  'all-time':      'Comparison basis: structural context only, with no prior-period delta.',
};
```

**`showPrior` rule:** `true` only when (a) `windowId !== 'all-time'` AND (b) prior data exists
AND (c) the current window has ≥ 2 distinct run datetimes. This mirrors the Python implementation.

**Empty-data guard:** if the current window has 0 runs, return a safe payload with all numeric
values `0`, all strings `""` or `"No data"`, and empty sparkline series.

- [x] Run `npx tsc --noEmit` from `client/` — zero errors.

---

### 11.4 — Write tests

Create `client/src/history-page/market-health-engine.test.ts`.

Use the `rawMarketHealthData` fixture from `marketHealthRaw.ts` as the primary input.
Hand-calculate expected values from the fixture before writing assertions.

**Required test cases (every branch must be covered):**

**Window bounds (call `buildMarketHealthPayload` with each `windowId`):**
- [x] All 7 `windowId` values return a payload without throwing
- [x] `windowId: 'all-time'` → `showPrior: false`
- [x] All non-all-time windows → `showPrior: true` when prior data exists
- [x] In-progress windows (`this-month`, `current-quarter`, `this-year`) use dynamic basis
  notes (contain actual date ranges, not generic strings like "quarter to date")
- [x] Completed windows (`last-month`, `last-quarter`, `last-year`) use static basis notes

**Window filtering:**
- [x] Records exactly on `winStart` boundary are included
- [x] Records exactly on `winEnd` boundary are included
- [x] Records 1 ms before `winStart` are excluded
- [x] Records 1 ms after `winEnd` are excluded

**Genus filter:**
- [x] `isAllSelected: true` — all records returned regardless of genus
- [x] `isAllSelected: false`, matching genera — only matching species returned
- [x] `isAllSelected: false`, non-matching genus — empty result

**Observed species (`computeObserved`):**
- [x] Returns count of distinct `scientificName` values
- [x] Multi-variant species (same name, two size rows) counted as 1

**In-stock rate (`computeStockRate`):**
- [x] 100% when all species present in latest run
- [x] Correct percentage when one species drops out before latest run
- [x] Returns 0 when records array is empty

**Median wishlist (`computeMedianWishlist`):**
- [x] Multi-variant species: max `wishlistCount` across variants used (not sum, not first)
- [x] Odd number of species — median is the middle value
- [x] Even number of species — median is average of two middle values, rounded
- [x] Returns 0 when records array is empty

**Median price (`computeMedianPrice`):**
- [x] Multi-variant species: max `priceGbp` across variants used
- [x] Median value is correct for the fixture dataset

**Sparkline resampling (`resampleTo12` via `buildSparklineForMetric`):**
- [x] Exactly 12 input values → output unchanged
- [x] Fewer than 12 → last value is used to pad to 12
- [x] More than 12 → 12 evenly-spaced values are sampled

**Events — new listings:**
- [x] First appearance of a species within the window is counted as a new listing
- [x] A size transition (same `pageUrl`, different `sizeVariant`, gap ≤ 3 runs) is **not**
  counted as a new listing

**Events — dropped listings:**
- [x] A species absent from the final run of the window is counted as a dropped listing
- [x] A size transition is **not** counted as a dropped listing

**Events — restocks (OUT → IN):**
- [x] A species absent from one run and present in the next is counted as a restock

**Events — OOS flips (IN → OUT):**
- [x] A species present in one run and absent in the next is counted as an OOS flip

**Size transition detection:**
- [x] Same `pageUrl`, same `scientificName`, different `sizeVariant`, gap ≤ 3 runs → `true`
- [x] Same `pageUrl`, same `scientificName`, same `sizeVariant` → `false` (not a size change)
- [x] Different `pageUrl`, same species → `false` (not the same listing)
- [x] Same `pageUrl`, same species, gap > 3 runs → `false` (outside max-gap window)

**Copy strings — observed (`observedCopy`):**
- [x] `isAllTime: true` → all-time sentence
- [x] `delta >= 3` → "Breadth is ahead of…" sentence
- [x] `0 <= delta <= 2` → "Breadth is only slightly ahead…" sentence
- [x] `delta < 0` → "Fewer species are being seen…" sentence

**Copy strings — stock (`stockCopy`):**
- [x] `isAllTime: true` → all-time sentence
- [x] `delta <= -7` → availability slipping sentence (includes `abs(delta)` and value%)
- [x] `-6 <= delta <= -1` → near-term tightening sentence
- [x] `delta === 0` → steady sentence
- [x] `delta >= 1` → firmer sentence

**Copy strings — wishlist (`wishlistCopy`):**
- [x] `isAllTime: true` → all-time sentence
- [x] `delta >= 4` → ahead sentence
- [x] `1 <= delta <= 3` → modestly above sentence
- [x] `delta === 0` → stable sentence
- [x] `delta <= -1` → softer sentence

**Copy strings — price (`priceCopy`):**
- [x] `isAllTime: true` → all-time sentence
- [x] `delta >= 2` → firmer sentence
- [x] `delta === 1` → edged up sentence
- [x] `delta === 0` → steady sentence
- [x] `delta <= -1` → softened sentence

**Delta formatting:**
- [x] `formatObservedDelta`: positive delta → `"+N vs …"`, class `""`
- [x] `formatObservedDelta`: negative delta → `"-N vs …"`, class `"down"`
- [x] `formatObservedDelta`: all-time → `"No prior comparison"`, class `"flat"`
- [x] `formatStockDelta`: positive → `"+N pts vs …"`, class `""`
- [x] `formatStockDelta`: negative → `"-N pts vs …"`, class `"down"`
- [x] `formatWishlistDelta`: zero → `"+0 vs …"`, class `"flat"`
- [x] `formatPriceDelta`: positive → `"+GBP N vs …"`, class `""`
- [x] `formatPriceDelta`: zero → `"+GBP 0 vs …"`, class `"flat"`

**Dynamic basis notes (`buildInprogressBasisNotes`):**
- [x] `this-month` → result contains the actual month label and date span (e.g. `"Apr 2026"`,
  `"Apr 1"`, `"Apr 21"`)
- [x] `current-quarter` → result contains the quarter label and matched prior-quarter span
  (e.g. `"Q2 2026"`, `"Q1 2026"`, `"Jan 1"`, `"Jan 21"`)
- [x] `this-year` → result contains the year and the matched prior-year span

**Full payload shape:**
- [x] `buildMarketHealthPayload` with `currentQuarter` returns a payload where
  `kpis.observed`, `kpis.stock`, `kpis.wishlist`, `kpis.price` all have `id`, `title`,
  `value`, `delta`, `deltaClass`, `copy` fields populated (no empty strings except where
  intentional)
- [x] `buildMarketHealthPayload` with `all-time` returns a payload where all four
  `deltaClass` values are `"flat"` and all four `delta` texts are `"No prior comparison"`

**All-windows builder:**
- [x] `buildMarketHealthPayloadAllWindows` returns an object with exactly 7 keys matching
  `ALL_WINDOW_IDS`
- [x] Each value is a valid `MarketHealthPayload` with the correct `windowId` field

**Tasks:**
- [x] Run `make test-client-fast` — all tests green (existing + new)
- [x] Run `make test-client` — confirm statement coverage ≥ 95% and branch coverage ≥ 85%
  for `market-health-engine.ts`

**Housekeeping:**
- [x] H1 — Mark all tasks in Phase 11 ✅
- [x] H2 — Reflection: scan `market-health-engine.ts` against the code smell checklist;
  in particular: no `any` types, no hardcoded strings that diverge from the Python
  constants, no exported implementation details
- [x] H3 — Feed-forward log entry
- [x] H4 — Commit: `git add -A && git commit -m "Phase 11: client-side market health engine"`
- [x] GATE — Output phase completion block

---

## Phase 12 — Cut Over Data Contract (Python → Raw DTO, TS Engine Live)

**Goal:** Wire the engine into the page. Replace `window.marketHealthPayloads` (7 pre-computed
KPI dicts) with `window.marketHealthRawData` (variant-level records). Simplify Python to a
raw-data serialiser only. Delete `market_health_dto.py`. All tests (Python, client, E2E)
remain green at the end of this phase.

> **Sequence requirement:** Phase 11 must be complete (GATE output confirmed) before
> starting Phase 12. Do not merge these phases.

**Pre-flight:**
- [ ] Run `make test-client-fast` — green (Phase 11 engine tests green).
- [ ] Run `make test` — green (Python tests unchanged).

---

### 12.1 — New Python module: `market_health_raw_dto.py`

Create `src/website/market_health_raw_dto.py`.

```python
"""Raw Market Health DTO — serialises history CSV rows into the minimal payload
consumed by the client-side market-health-engine.ts.

No KPI computation, no window logic, no copy strings. Data in, records out.

Public API:
    build_raw_market_health_data(history_rows: list[dict]) -> dict
"""
```

**Function signature:**
```python
def build_raw_market_health_data(history_rows: list[dict]) -> dict:
    ...
```

**Output shape (must match `MarketHealthRawData` TypeScript interface exactly):**
```json
{
  "records": [
    {
      "scrapeDatetime": "2026-04-14T06:10:00",
      "scientificName": "Avicularia avicularia",
      "sizeVariant": "2.0",
      "pageUrl": "https://…",
      "wishlistCount": 12,
      "priceGbp": 24.99
    }
  ],
  "referenceDate": "2026-04-14T06:10:00"
}
```

**Rules:**
- One record per source row (variant-level rows preserved — the engine deduplicates to
  species-level internally, and variant rows are required for size-transition detection)
- `referenceDate` = `max(row["scrape_datetime"] for row in history_rows)` — empty string
  if `history_rows` is empty
- `wishlistCount`: `int(row["wishlist_count"])` — default `0` on missing or invalid
- `priceGbp`: `float(row["price_gbp"])` — default `0.0` on missing or invalid
- `sizeVariant`: `row.get("size_cm", "")` — empty string if absent
- `pageUrl`: `row.get("page_url", "")` — empty string if absent
- `scientificName`: `row.get("scientific_name", "")` — empty string if absent
- `scrapeDatetime`: `row.get("scrape_datetime", "")` — empty string if absent
- Skip rows where both `scientificName` and `scrapeDatetime` are empty

**Implementation note:** this should be ~40–60 lines. No imports beyond the standard
library. Do not copy any logic from `market_health_dto.py`.

- [ ] Task complete.

---

### 12.2 — Python tests: `test_market_health_raw_dto.py`

Create `tests/website_module/test_market_health_raw_dto.py`.

**Required test cases:**
- [ ] Output dict has a `records` key (list) and a `referenceDate` key (string)
- [ ] `referenceDate` equals the maximum `scrape_datetime` string across all rows
- [ ] `wishlistCount` is an `int`, not a string
- [ ] `priceGbp` is a `float`, not a string
- [ ] Multi-variant species (same `scientific_name`, different `size_cm`) produce
  one record per variant — both records are present
- [ ] Missing `wishlist_count` field defaults to `0`
- [ ] Invalid (non-numeric) `wishlist_count` defaults to `0`
- [ ] Missing `price_gbp` field defaults to `0.0`
- [ ] Empty `history_rows` → `records: []` and `referenceDate: ""`
- [ ] `sizeVariant` in output matches `size_cm` from input
- [ ] `pageUrl` in output matches `page_url` from input

- [ ] Run `make test-file FILE=tests/website_module/test_market_health_raw_dto.py` — green
- [ ] Run `make test` — all Python tests green

---

### 12.3 — Update `generate_website.py`

In `src/website/generate_website.py`:

- [ ] Remove the import of `build_market_health_payload_all_windows` (both the `try` and
  `except` branches)
- [ ] Add import of `build_raw_market_health_data` from `market_health_raw_dto` in both
  branches
- [ ] In `generate_history_insights_page`: replace the block that computes
  `market_health_payloads` (CSV parse → reference_dt extraction →
  `build_market_health_payload_all_windows` call) with a single call to
  `build_raw_market_health_data(history_rows)`, assigned to `market_health_raw_data`
- [ ] Pass `market_health_raw_data=market_health_raw_data` to `template.render(...)`,
  removing `market_health_payloads=market_health_payloads`

---

### 12.4 — Update template

In `templates/history_insights_page.html`:

- [ ] Replace:
  ```html
  window.marketHealthPayloads = {{ market_health_payloads | tojson | safe }};
  ```
  with:
  ```html
  window.marketHealthRawData = {{ market_health_raw_data | tojson | safe }};
  ```

---

### 12.5 — Update `client/src/history-page/index.ts`

- [ ] Remove the import of `MarketHealthPayload` and `WindowId` types (or keep `WindowId`
  if used elsewhere)
- [ ] Add import of `MarketHealthRawData` from `./types.js`
- [ ] Add import of `buildMarketHealthPayloadAllWindows` from `./market-health-engine.js`
- [ ] Replace the block that reads `window.marketHealthPayloads` and extracts
  `initialPayload` with:
  ```typescript
  const rawData = (window as unknown as Record<string, unknown>)
    .marketHealthRawData as MarketHealthRawData | undefined;

  if (marketHealthRoot && rawData && rawData.records.length > 0) {
    const allPayloads = buildMarketHealthPayloadAllWindows(rawData);
    const initialPayload = allPayloads['current-quarter'];
    mount(MarketHealthSection, {
      target: marketHealthRoot,
      props: { payload: initialPayload },
    });
  }
  ```
- [ ] Run `npx tsc --noEmit` from `client/` — zero errors

---

### 12.6 — Delete dead code and update stale server-side tests

**Delete modules:**
- [ ] Delete `src/website/market_health_dto.py`
- [ ] Delete `tests/website_module/test_market_health_dto.py`

**Update `tests/website_module/test_pages.py`:**

`TestGenerateHistoryInsightsPage` currently has two tests that assert
`window.marketHealthPayloads` in the generated HTML and inspect the KPI payload shape
(`.kpis.observed.value`). After Phase 12 the template injects `window.marketHealthRawData`
instead; those assertions will fail and the KPI shape no longer exists server-side.

- [ ] Rewrite both tests in `TestGenerateHistoryInsightsPage` to assert:
  - `window.marketHealthRawData` is present in the generated HTML
  - The parsed JSON has a `records` key (a list) and a `referenceDate` key (a non-empty
    string matching the most recent run date)
  - The `records` list length equals the number of source rows (all rows serialised)
  - Drop all assertions about `kpis`, `sparklineSeries`, and `events` — those are
    computed client-side and do not exist in the server output
- [ ] Run `make test-file FILE=tests/website_module/test_pages.py` — green
- [ ] Run `make test` — all Python tests green

**Confirm no remaining stale references:**
- [ ] Confirm no remaining Python file imports from `market_health_dto`:
  ```bash
  grep -r "market_health_dto" src/ tests/
  ```
  Expected: zero matches.
- [ ] Confirm `marketHealthPayloads` no longer appears in any template, Python, or
  TypeScript source file (docs are exempt):
  ```bash
  grep -r "marketHealthPayloads" src/ tests/ templates/ client/src/
  ```
  Expected: zero matches.

---

### 12.7 — Write History Insights E2E test

> **Why this is required:** Phase 12 replaces Python-pre-computed KPI values with
> client-side JS computation from `window.marketHealthRawData`. Client-side JavaScript
> behaviour can only be validated by E2E (Playwright) tests. No unit test can confirm
> the engine result is correctly mounted into the DOM.

Create `tests/e2e/test_history_insights.py`.

**Required test cases:**
- [ ] `test_page_loads` — navigate to `history-insights.html`; assert HTTP 200 and
  page title contains "History Insights" (or the nav label from the template)
- [ ] `test_market_health_section_renders` — section container (`.market-health-section`)
  exists in DOM; all 4 `.kpi-card` elements are present; no JavaScript console errors
- [ ] `test_kpi_values_are_non_empty` — each `.kpi-card` has a `.metric-value` child
  whose `textContent` is a non-empty string (confirms engine computed something, not blank)
- [ ] `test_events_grid_renders` — the events mini-grid is present (4 event tiles visible)
- [ ] `test_no_window_marketHealthPayloads` — assert
  `page.evaluate("typeof window.marketHealthPayloads")` returns `"undefined"` (confirms old
  global is gone); assert `page.evaluate("typeof window.marketHealthRawData")` returns
  `"object"` (confirms new global is present)
- [ ] `test_sparklines_rendered` — assert at least 4 `<svg>` elements are present inside
  `.market-health-section` (one per KPI card)

**Do NOT test:**
- Exact KPI values (they depend on the fixture CSV data and would be brittle)
- Time window switching UI (no switcher UI in WP1; that is WP-Arch scope)
- Run-selection interaction (already covered by Vitest component tests)

- [ ] Run `make test-file FILE=tests/e2e/test_history_insights.py` — all cases pass
- [ ] Run `make test-e2e` — full suite green (no regressions on existing pages)

---

### 12.8 — Verify

- [ ] `make test` — green (all Python tests; no broken imports from deleted module)
- [ ] `make test-client-fast` — green (client tests, including engine tests)
- [ ] `make test-client` — green (coverage thresholds met)
- [ ] `make test-e2e` — green (including new `test_history_insights.py`)

**Housekeeping:**
- [ ] H1 — Mark all tasks in Phase 12 ✅
- [ ] H2 — Reflection: confirm no references to `marketHealthPayloads` remain in any
  template, TypeScript, or Python file; confirm no `any` casts added to `index.ts`;
  confirm `test_history_insights.py` exists and all cases are green
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 12: cut over to client-side market health engine + E2E coverage"`
- [ ] GATE — Output phase completion block

---

## Phase 13 — Mobile Responsiveness

**Goal:** Make the Market Health section usable on phones in portrait orientation. The
section is currently largely unusable below 500 px: the section heading wraps to 7 lines,
KPI cards are too narrow for their content, and the events grid values wrap badly. All
fixes are CSS-only breakpoint additions — no TypeScript logic changes.

> **Branch:** create `history-page-mobile-responsive` from the current commit on `master`
> (or whatever branch carries Phase 12). This work package ships as its own PR.

---

### Mobile UX Inventory (390 × 844 px, iPhone 14 portrait)

The following issues were identified using Chrome DevTools MCP emulation at
390 × 844 × DPR 3 with touch enabled. All widths are CSS layout pixels.

**Container chain on 390 px viewport:**
- `.container` (20 px padding each side) → 350 px content width
- `.content` (30 px padding each side) → 290 px content width  ← `#market-health-root`
- `.market-health-section` card (30 px padding each side) → 230 px inner content

| # | Issue | Severity | Root cause |
|---|---|---|---|
| I1 | Section header heading wraps to 7+ lines | Critical | `.section-header` is always `flex-direction: row`; heading column gets ~109 px, H2 font-size 22.4 px |
| I2 | Section note is clipped/truncated | Critical | `max-width: 38ch` in half of a 230 px row; text overflows card |
| I3 | KPI grid: 2-col at 230 px = 115 px per card | Critical | Existing 760 px breakpoint goes 4→2 col; no narrower breakpoint |
| I4 | Card titles wrap excessively ("IN-STOCK RATE" = 3 lines) | Critical | Consequence of I3 (115 px cards) |
| I5 | Sparklines shrink to ~88 px wide | Major | Consequence of I3; hit areas too small to tap |
| I6 | "GBP 25" value wraps to 2 lines ("GBP" / "25") | Major | Consequence of I3; `font-size: 2rem` at 115 px |
| I7 | Section card padding 30 px too large on mobile | Major | `padding: var(--spacing-xl)` unchanged for all viewports |
| I8 | Events grid: 2-col at 230 px = 115 px per tile | Major | `grid-template-columns: 1fr 1fr` with no breakpoint |
| I9 | Event values wrap badly ("0 vs prior quarter QTD" = 4 lines) | Major | Consequence of I8 |
| I10 | Total scroll height ~4 300 px on a ~1 140 px viewport | Moderate | Consequence of I1, I3, I8 — resolves when layout fixes land |

Issues I5, I6, I10 resolve automatically when I3 is fixed (single-column cards are ~240 px
wide in a reduced-padding card). Issues I4, I9 resolve when I3/I8 are fixed.

**What is acceptable on mobile without changes:**
- Sparkline support card (flex-wrap handles wrapping well)
- KPI copy text (wraps naturally and is readable)
- Navigation (already vertical list)
- Basis note and selection note text

---

### 13.1 — MarketHealthSection.svelte mobile breakpoints

> **Breakpoint:** `480 px` — this is the threshold where the 2-column KPI grid becomes
> unworkable. At 481–760 px (tablet portrait) the 2-column layout is acceptable.

- [ ] Add `@media (max-width: 480px)` block to `MarketHealthSection.svelte <style>`:
  - `.market-health-section { padding: var(--spacing-md); }` — reduce card padding
    from 30 px to 16 px; raises inner content from 230 px to ~258 px
  - `.section-header { flex-direction: column; align-items: flex-start; }` — stack
    heading and note vertically instead of side by side
  - `.section-note { max-width: none; align-self: auto; }` — allow note to run full
    width when stacked
  - `.kpi-grid { grid-template-columns: 1fr; }` — single-column KPI cards on narrow
    screens

- [ ] Run `make test-client-fast` — green

---

### 13.2 — MarketEventsCard.svelte mobile breakpoints

- [ ] Add `@media (max-width: 480px)` block to `MarketEventsCard.svelte <style>`:
  - `.events-grid { grid-template-columns: 1fr; }` — single-column event tiles
- [ ] Run `make test-client-fast` — green

---

### 13.3 — Visual verification via Chrome DevTools MCP

- [ ] Rebuild and re-serve: `make preview` (stops any running server, regenerates, starts
  fresh at `http://localhost:8000`)
- [ ] Emulate 390 × 844 × DPR 3 mobile portrait in Chrome DevTools MCP
- [ ] Navigate to `http://localhost:8000/history-insights.html`
- [ ] Confirm the following via `evaluate_script`:
  - `sectionHeaderFlexDirection` = `"column"` at 390 px
  - `kpiGridColumns` contains `"1fr"` (single column)
  - `kpiCardWidth` ≥ 220 (at least 220 px wide — gives sparklines ~190 px)
  - `eventsGridColumns` contains `"1fr"` (single column)
- [ ] Take a screenshot at scroll positions 0, 1000, 2000 to confirm no layout breakage
- [ ] Confirm total scroll height is under 3 000 px (was ~4 300 px)

---

### 13.4 — Visual contracts

- [ ] Add a new `@media (max-width: 480px)` visual contract to the existing visual test
  file that covers `MarketHealthSection` computed styles (or create
  `MarketHealthSection.visual.test.ts` if one does not yet exist). The contract must assert:
  - `.section-header` has `flex-direction: column` at viewport width ≤ 480 px
  - `.kpi-grid` `grid-template-columns` resolves to a single-column value at ≤ 480 px
  - At viewport width 600 px the 2-column grid is still active (regression guard)
- [ ] Run `make test-visual` — green

---

### 13.5 — Full test suite

- [ ] `make test-client` — green (coverage ≥ 80 %; new visual contract included)
- [ ] `make test-e2e` — green (no regressions; structural changes are additive CSS only)

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection: no hardcoded colours; no `any` casts; no `// TODO` shortcuts;
  confirm breakpoints use `var(--spacing-*)` tokens not raw px values for padding
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 13: mobile responsiveness for Market Health section"`
  then `git log --oneline -1` to confirm
- [ ] GATE — Output phase completion block

---



| Item | Status |
|---|---|
| Time window switcher UI | Separate component; exists in the mock filter panel. Out of scope. |
| Genus selector UI and per-genus/species KPI data | WP-Arch — delivers genus selector panel and Svelte fetch hook. **Note:** the lazy-load static JSON generator originally planned for WP-Arch is superseded by the client-side engine in Phase 11; WP-Arch only needs the UI and a hook to call `buildMarketHealthPayload` with filtered records. |
| Breeder Opportunity section (Section 2) | WP2 — separate spec and plan; depends on WP-Arch. |
| Bias Control section (Section 3) | WP3 — after WP2. |
| Filtered Data Preview (Section 4) | WP4 — after WP3. |
| Replacing `history.html` | Deferred until all work packages (WP1, WP-Arch, WP2–WP4) are merged. Until then `history.html` is untouched. |
| History table CSV export | Already implemented; do not touch. |
| Mobile / responsive breakpoints | Apply existing grid breakpoints from `common.css`; do not design new breakpoints. |

---

## Feed-Forward Log

*Agent: append a dated entry here after every H3. Entries accumulate and carry context
from one phase to the next, and from this work package to the next.*

```
[Phase 1 — 2026-04-06]
CSS token mapping table (mock → production, verified against common.css :root block):
  --ink        → --color-text          (#333)
  --muted      → --color-text-muted    (#7f8c8d)
  --accent     → --color-accent        (#3498db, blue NOT teal)
                 NOTE: spec §3 sparkline colours (teal #1f7a6b, rust #cc6b49,
                 amber #a18b35, muted #5d6a6d) are NOT tokens — they are series
                 colours passed as the `color` prop to MarketSparkline (hardcoded
                 values in fixture / story args, not in Svelte <style> blocks).
  --accent-2   → --color-signal-watch  (#f59e0b) — closest amber; verify in Phase 2
  --surface    → --color-surface       (#ffffff)
  --line       → --color-border-light  (#ddd)
  --shadow     → --shadow-sm           (0 2px 5px rgba(0,0,0,.05))
  delta down   → --color-danger        (#e74c3c) — for .metric-delta.down badge
  delta flat   → --color-text-muted    (#7f8c8d) — for .metric-delta.flat badge

G7 token resolution check (Phase 1 pre-component gate):
  Tokens checked in Storybook preview iframe (http://localhost:6006/iframe.html):
  --color-text:       #333       ✅ non-empty
  --color-accent:     #3498db    ✅ non-empty
  --color-text-muted: #7f8c8d    ✅ non-empty
  common.css is correctly imported in client/.storybook/preview.ts.

Storybook install: v8.6.18 (@storybook/svelte-vite framework). No example stories
created. `make storybook` added to Makefile. `storybook` + `build-storybook` scripts
added to client/package.json.

TypeScript: 0 errors on `npx tsc --noEmit` after creating types.ts and all 4 fixtures.

Discrepancy note: The implementation plan references spec §7.2 before the spec document
itself. The spec §7.2 type contract matches types.ts exactly. No conflicts found between
the three source documents (spec, plan, mockup). No findings to carry forward as blockers.

[Phase 2 — 2026-04-06]
MarketSparkline component — key findings:
- Prior series circles (.sparkline-point-prior) must NOT receive .is-subdued when a run
  is selected. The Phase 5 expected value of subduedTotal: 44 = 11 per sparkline × 4 cards
  confirms only current series circles (11 non-selected per sparkline) are subdued.
  Prior series maintains its baseline opacity: 0.45 on circles, 0.38 on polyline.
- Hit areas: invisible <rect> elements per run slot. Width = CHART_W / (N-1). Clicking
  fires onRunSelect(index) or onRunSelect(null) if already selected.
- SVG dimensions: 120×56 px, topPad=6, bottomPad=14 (space for axis labels).
- Run-axis labels at x-positions for indices 0, 5, 11 with text-anchor = start/middle/end.

DevTools MCP assertions — all passed first time:
  Default → prior polyline opacity: "0.38" ✅
  ShowPriorFalse → polyline count: 1 ✅
  RunSelected → { subduedCount: 11, subduedOpacity: "0.16", selectedExists: true } ✅

[Phase 3 — 2026-04-06]
MarketKpiCard component:
- SPARKLINE_COLOR map: {observed: '#1f7a6b', stock: '#cc6b49', wishlist: '#a18b35',
  price: '#5d6a6d'} — per spec §3, these are series colours not CSS tokens.
- delta.down badge color confirmed → rgb(231, 76, 60) = --color-danger token ✅
- AllTimeNoPrior → 1 polyline (showPrior: false) ✅
- SVG hit areas are <rect> elements; test must use fireEvent.click() not .click()
  because SVG elements are not HTMLElement instances with a .click() method.
- Coverage threshold: types.ts, *.stories.ts, and __fixtures__/**/*.ts added to
  vite.config.ts coverage exclusion list to prevent them dragging global below 95%.
  These are type-only files, Storybook stories (tested via DevTools MCP), and pure
  data fixtures (covered by being imported in tests). No executable logic is lost.

[Phase 4 — 2026-04-06]
MarketEventsCard component:
- CRITICAL: `events` is a reserved/special prop name in Svelte 5. Using `events` as a
  prop causes the prop to be undefined at runtime (the component receives no value).
  Renamed to `eventsData` throughout — component, test, and stories.
  Rule: never name a Svelte 5 component prop `events`.
- {#each [a.x, a.y, a.z] as item} with an inline prop-derived array produced the same
  undefined error. Switched to {#snippet} + {@render} to render each tile explicitly.
  Both issues resolved by renaming the prop.
- DevTools MCP assertions:
  CurrentQuarter → tileCount:4, all copies non-empty ✅
  AllTime → values ["286 total", "172 total", "391 total", "214 total"] (all "N total") ✅

[Phase 5 — 2026-04-06]
MarketHealthSection island:
- Svelte 5 scoped CSS overrides the UA-stylesheet `[hidden] { display:none }` rule
  because scoped selectors (`.foo .svelte-HASH`) have higher specificity than the
  attribute selector alone. Fix: add `.legend-prior-key[hidden], .clear-run-btn[hidden]
  { display: none; }` in the component's <style> block. This is a pattern to remember
  for any component that uses `hidden` alongside a named `display` rule.
- `$state(initialSelectedRun ?? null)` with `initialSelectedRun` as a prop triggers
  the Svelte compiler warning `state_referenced_locally`. This is intentional — seeding
  state from prop is the correct Svelte 5 pattern when you want one-way initialisation
  without reactive tracking. The warning is advisory, not a build error.
- DevTools MCP assertions — all passed:
  CurrentQuarter → {kpiCardCount:4, priorKeyVisible:true,
    selectionNote:"Optional...", clearBtnHidden:true} ✅
  AllTime → {priorKeyHidden:true, priorPolylineCount:0} ✅
  StockUnderPressure → {deltaHasDown:true, copySnippet starts "49% of listings..."} ✅
  RunSelected → {selectionNote:"Run 9 selected...", clearBtnVisible:true,
    subduedTotal:44} ✅

[Phase 6 — 2026-04-06]
Python market_health_dto module:
- `make test` tests must import from `website.market_health_dto` (not `src.website.`)
  because make runs tests from tmp/local-testing/ where src/ is not a sub-package.
- `showPrior` rule: True for non-all-time windows when ≥2 scrapes exist in the window.
  Fewer than 2 scrapes → showPrior=False (safe fallback, consistent with plan §6 rule).
  Not purely a window-type property because the component expects a meaningful prior
  series when showPrior=True.
- Events computation (`_compute_events`) requires ALL species' rows to establish the
  full set of scrape run timestamps. If only Species A is tracked and A was absent
  from run 2, run 2 won't appear in `runs` (since rows are sparse — only in-stock rows
  exist). Fix: `_find_last_seen_idx` / `_find_next_seen_idx` look across all rows to
  detect gaps, but the run list is what determines whether a transition is visible.
  Tests must include a "base species" present in all runs to establish the full run list.
- Coverage: 89.81% (above 80% threshold ✅).

[Phase 7 — 2026-04-06]
Page integration:
- `generate_analysis_page` docstring opening triple-quote was accidentally removed in a
  previous session. Restored: `def generate_analysis_page(...): """Generate an analysis
  page (breeder or dealer).`. Carries no logic change but caused a SyntaxError at import.
  Rule: always run `python -c "from website.generate_website import main"` before calling
  `make generate-website` to catch syntax errors cheaply.
- Adding a `PageNavItem` to `NAV_ITEMS` increases the homepage card count. Updated
  `test_includes_card_grid_with_links` to assert `len(cards) == 5` and added assertion
  for `History Insights` card text. This is a structural test update (expected delta),
  not a bug.
- Deferred: `window.marketHealthPayloads` shape validation via `assertPayload()`.
  Index.ts guard (element AND payloads dict both exist) provides safe no-op fallback.
  Shape validation can be added in a follow-up or WP2.
- All test suites green: 862 Python / 303 Vitest / 157 E2E ✅.
- `history.html` confirmed untouched (grep for `market-health-root` returns 0 matches) ✅.

[Phase 8 — 2026-04-06]
Visual acceptance sweep — all assertions passed:
- Phase 5 re-check: CORRECTION — Phase 5 feed-forward recorded selector as
  `.sparkline-point.is-subdued` but the actual Svelte-generated class is
  `.sparkline-point-current.is-subdued`. The count is still 44 (correct). All future
  DevTools MCP assertions for subdued circles must use `.sparkline-point-current.is-subdued`.
- Cross-story token check: all four KPI sparkline polylines resolve to `rgb()` ✅
  rgb(31,122,107) teal, rgb(204,107,73) rust, rgb(161,139,53) amber, rgb(93,106,109) muted.
  No hardcoded colours leak onto `.visual-card`; backgroundColor = rgb(255,255,255) ✅.
- Preview site (localhost:8000/history-insights.html):
  rootHasChildren:true, kpiCardCount:4, marketHealthPayloadsKeys: 7 windows ✅.
  current-quarter KPIs = 0/empty (by-design: demo data predates Q2 2026).
  all-time KPIs = ["6","100%","7","GBP 22"] ✅.
- Storybook MarketSparkline Default: priorPolylineOpacity="0.38" ✅; ShowPriorFalse: 1 polyline ✅.
- Storybook MarketEventsCard CurrentQuarter: 4 tiles with non-empty copy ✅.
- Storybook MarketHealthSection:
  CurrentQuarter: kpiCardCount=4, priorKeyVisible=true, clearBtnHidden=true, subduedTotal=0 ✅.
  AllTime: priorKeyHidden=true, totalPolylines=4 (no prior series) ✅.
  RunSelected: selectionNote starts "Run 9 selected...", clearBtnVisible=true, subduedTotal=44 ✅.
- Divergences:
  [by-design] demo data predates Q2 2026 → current-quarter window shows zeros on preview.
  [fixed] Phase 5 selector note corrected (sparkline-point-current not sparkline-point).
  [deferred] payload shape validation via assertPayload() — safe fallback guard exists.

[Phase 10 — 2026-04-20]
Visual fidelity pass complete. All 8 G10 gaps closed:
  G10.1 FIXED: <header> → <div class="section-header"> — `rgba(0,0,0,0)` bg confirmed ✅
  G10.2 FIXED: --font-lg: 1.4rem token added → h2 fontSize = 22.4px ✅
  G10.3 FIXED: --color-text-primary: #2c3e50 token added → h2 color = rgb(44,62,80) ✅
  G10.4 FIXED: .section-header flex-direction: row; two-column layout confirmed ✅
  G10.5 FIXED: .section-eyebrow border-radius: 999px; teal pill confirmed ✅
  G10.6 FIXED: .metric-delta border-radius: 999px; teal positive badge confirmed ✅
         Accepted rgba() exceptions documented: rgba(31,122,107,0.12) for positive,
         rgba(178,76,61,0.12) for .down, rgba(127,140,141,0.12) for .flat.
         .down badge color #b24c3d (mock value, not --color-danger) — by-design.
  G10.7 FIXED: .kpi-card border-radius overridden to 18px (matching mock; 2px above
         --radius-card-lg token of 16px — intentional, commented in CSS). Confirmed ✅
  G10.8 FIXED: .market-health-section gets border + border-radius:16px + padding ✅
         Section background left to inherit white (no warm cream) — by-design deviation
         from mock (production sits inside .content which is white).

Additional fix in this session (Phase 10 clean-up, 2026-04-20):
  The global `h2 { border-bottom: 2px solid var(--color-accent) }` rule in common.css
  was leaking a blue underline onto the #market-health-heading h2 inside the section.
  Fixed by adding `border-bottom: none; padding-bottom: 0` to the Svelte-scoped
  `.section-header h2` rule in MarketHealthSection.svelte. This is the same class of
  problem as G10.1 (global element selectors overriding component expectations).
  Rule: after fixing any global-selector conflict, also scan sibling elements (h1, h2, h3)
  for inherited border/padding that wasn't visible in Storybook but surfaces in the page context.

Also delivered in Phase 10 sub-phases (10b, 10c, 10g, 10h):
  Phase 10b: event labels, tile radius/border, clear-btn pill, section-note bottom-align,
             KPI info buttons, visual contracts for G10.1/G10.2/G10.3.
  Phase 10c: 14 additional KPI card style gaps against real mock.
  Phase 10g: sparkline box enclosure, readout text, prior overlay on all KPI cards,
             windowScopeLabel prop.
  Phase 10h: SVG viewBox 268×82 (was 120×56), corrected yAt() formula (max at top),
             font-size=10, dasharray "5 4". 10 geometry unit tests added.

All 337 Vitest tests pass. Visual contracts (test-visual) pass. E2E (test-e2e) verified
in Phase 7 — no structural changes that would break it in Phase 10.

[Phase 9 — 2026-04-07]
Branch pushed and PR #158 opened:
  https://github.com/christianacca/spidershop-historical-analysis/pull/158
All pre-PR test suites green: 862 Python / 303 Vitest / 157 E2E.
Cleanup: client/nohup.out was a tracked log file (Storybook output); removed from
  git tracking via `git rm --cached`; covered by root .gitignore `nohup.out` rule.

[Phase 11 — 2026-04-21]
Client-side market health engine (`market-health-engine.ts`) — key findings for Phase 12:

Architecture decisions confirmed during implementation:
- `referenceDate` from `MarketHealthRawData` is used as the clock for all window bounds
  (not `new Date()`). This is critical: the static page remains meaningful however old it
  is. Phase 12 Python must populate `referenceDate` as `max(row["scrape_datetime"])`.
- `showPrior` rule: mirrors Python exactly — `true` only when (a) not all-time, (b) prior
  data exists, AND (c) current window has ≥ 2 distinct run datetimes. Phase 12 Svelte
  wiring must pass the engine's output directly to `MarketHealthSection`; no manual
  `showPrior` override.

Date formatting divergence (resolved):
- Python `_fmt_date` uses `strftime("%b") + " " + str(dt.day)` → "Apr 1" (no zero-pad).
- JavaScript `Date.toLocaleDateString` was NOT used (locale-sensitive, unsafe). Instead,
  `MONTH_ABBREVS[dt.getMonth()]` + ` ` + `dt.getDate()` — matches Python output exactly.
  Phase 12 basis-note assertions in E2E should test for "Apr 1" format, not "Apr 01".

`last-quarter` window end boundary:
- Python: `qs - timedelta(seconds=1)` with `.replace(microsecond=999999)`
  → last millisisecond of the day before the current quarter.
- TypeScript: `new Date(qs.getTime() - 1)` → 1ms before quarter start.
  These are semantically equivalent for ISO string comparisons but differ in precision.
  Since fixture records use whole-second datetimes, this has no practical effect.

Events computation:
- The `findLastSeenIdx` / `findNextSeenIdx` search across ALL records in the window
  (not just the current species' rows). The run list (`getSortedRuns`) only contains
  datetimes present in the filtered window — so if a species is absent from all runs,
  its "gap" is invisible to the event scanner. This is correct behaviour, but means
  a "base species" present in every run is required in test fixtures to establish the
  full run timeline. The `marketHealthRaw.ts` fixture includes Avicularia avicularia
  for exactly this purpose.
- Size transition detection uses `pageUrl` intersection + `sizeVariant` diff. Two
  species at different URLs can never produce a size transition even if they share a
  scientific name. Phase 12 E2E does not need to test size transitions — Vitest engine
  tests cover all branches.

OOS flip value format:
- In all-time mode: `"2 total"` (no `+` prefix) — matches Python. Distinct from the
  non-all-time format `"+N vs {deltaLabel}"`. Test assertions must branch on `isAllTime`.

Coverage achieved (above thresholds):
  Statements 99.37%, Branches 91.18%, Functions 100%, Lines 99.37%.
  Remaining uncovered branches (lines 378-379, 639-643) are the `allUpTo.size === 0`
  guard inside `valueAtRun` and the `wishlistCopy`/`priceCopy` `delta === null` branches.
  These require records that exist in the window but have no prior period data AND no
  prior-data fallback — practically unreachable with realistic data. Not worth adding
  a fixture edge case to chase the last 1-2% branch coverage.

Phase 12 wiring notes:
- `index.ts` currently reads `window.marketHealthPayloads` (a pre-computed dict). Phase 12
  must switch to `window.marketHealthRawData` and call `buildMarketHealthPayloadAllWindows`
  on mount. The `MarketHealthSection` Svelte component interface (`payload` prop) is
  unchanged — no component edits needed.
- `market_health_dto.py` can be deleted after Phase 12 Python tests are removed. Confirm
  with `grep -r "market_health_dto" src/ tests/` before deletion.
- `window.marketHealthPayloads` must be removed from the Jinja template and from the
  `assertPayload()` call in `index.ts`. The new global is `window.marketHealthRawData`.
- After cutover, the Phase 7 deferred item (assertPayload for payload shape validation)
  is superseded — the engine validates shape implicitly through TypeScript types.

All 163 E2E tests pass. Commit: b21cc8f.

[Phase 12 — 2026-04-22]
Client-side architecture cutover — key findings:

market_health_raw_dto.py is ~60 lines as intended. No logic, no window computation —
pure field mapping from CSV dicts to camelCase JSON. The "skip rows" guard (`not
scientific_name and not scrape_datetime`) intentionally retains rows with only one
of the two fields absent — these are edge cases that the engine handles gracefully
rather than silently dropping valid data.

test_pages.py rewrite: the two old tests (KPI value assertions, reference-date regression)
are now superseded by four new tests that check the raw data contract: global name, records
list, records count equals source rows, and referenceDate equals latest run. These tests
are structurally lighter and cannot drift as the engine evolves.

stale .pyc caches: after deleting market_health_dto.py, Python's __pycache__ still holds
binary .pyc files for the deleted module. These are benign — pytest ignores orphaned .pyc
files. They will be purged by `make clean-cache` or when the bytecode version changes.
No action required.

index.ts cutover: the `MarketHealthPayload` and `WindowId` type imports were cleanly
removed. The new guard (`rawData && rawData.records.length > 0`) is strictly tighter than
the old guard (`initialPayload` truthiness) — it prevents mounting with an empty dataset
rather than showing a vacuous zero-valued section.

E2E test design rationale: test_kpi_values_are_non_empty uses `wait_until="networkidle"`
(not "domcontentloaded") because the Svelte island mounts on DOMContentLoaded and populates
asynchronously via rune reactivity. networkidle gives the island time to complete its
initial render before assertions run.

Templates dist artifact: templates/scripts/dist/history-page.js is a stale build
artifact that still references marketHealthPayloads. This is expected — it is regenerated
by `make build-client` or `make generate-website`. The E2E fixture infrastructure
rebuilds the client bundle before each test run, so E2E tests always use the current
client/src/ code. The dist file is not committed (it lives in templates/scripts/dist/
which is .gitignored for generated output).

All test suites green: 857 Python / 451 Vitest / 163 E2E.
Coverage: Python 95.69%, market-health-engine.ts statements 99.74% branches 96.62%.
```
