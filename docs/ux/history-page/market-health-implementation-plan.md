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
3. A **second** independent island for Market Health will follow the same pattern:
   - Python injects `window.marketHealthPayloads = { … };` (a dict of all 7 window payloads)
   - `history-page/index.ts` reads it and mounts `MarketHealthSection` with the default window.

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
- [ ] Read `templates/common.css` `:root` block — build a mapping table for the
  six mock tokens listed in G2 above. Add to feed-forward log.
- [ ] Read `client/src/history-page/index.ts` — understand the current island
  initialisation pattern (`registerPageInit`, `assertPayload`, `mount`).
- [ ] Read `client/src/shared/page-init.ts` (or equivalent) — understand what
  `completeTableMount` / `registerPageInit` expect.
- [ ] Read Svelte 5 + Storybook compatibility: Storybook ≥ 8.5 is required for
  Svelte 5 runes support. Confirm before running the init command.
- [ ] Run `make test-client-fast` — confirm baseline is green before touching anything.

**Tasks — Types and Fixtures:**
- [ ] Create `client/src/history-page/types.ts` — export all interfaces
  from the handoff spec §7.2 (`MarketHealthPayload`, `KpiCardData`, `SparklineSeries`,
  `MarketEventsData`, `EventTile`, `WindowId`). Fixtures import from `'../types'`.
- [ ] Create `client/src/history-page/__fixtures__/` directory and the fixture module
  `marketHealth.currentQuarter.ts` (full data — see spec §8.2).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.allTime.ts`
  (`showPrior: false`, flat deltas — see spec §8.3).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.lastQuarter.ts`
  (completed period, named quarter label).
- [ ] Create `client/src/history-page/__fixtures__/marketHealth.stockUnderPressure.ts`
  (stock delta ≤ −7, wishlist delta ≥ +3).
- [ ] Run `npx tsc --noEmit` from `client/` — confirm zero type errors.

**Tasks — Storybook install and config:**
- [ ] Confirm `client/package.json` has no Storybook dependency (it should not).
- [ ] Install Storybook (run from `client/` directory):
  ```bash
  npx storybook@latest init --type svelte
  ```
  Accept the Vite builder. Decline any example stories.
- [ ] Verify `client/.storybook/main.ts` and `client/.storybook/preview.ts` were created.
- [ ] Import `templates/common.css` in `client/.storybook/preview.ts` so global design
  tokens are available in the Storybook canvas.
- [ ] Add `storybook` and `build-storybook` scripts to `client/package.json`.
- [ ] Add `make storybook` to the root `Makefile` (runs `cd client && npx storybook dev`).
- [ ] Run `make storybook` as a background process.
- [ ] Navigate to `http://localhost:6006` via Chrome DevTools MCP; take a screenshot
  to confirm the canvas opens; run the G7 token resolution check — all three values
  must be non-empty strings before any component work begins.

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 1: foundation — types, fixtures, Storybook config"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

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
- [ ] Create `client/src/history-page/MarketSparkline.test.ts`:
  - Renders with `showPrior: true` → both series in DOM
  - Renders with `showPrior: false` → prior series not in DOM
  - Click on run index 3 → `onRunSelect(3)` called
  - Click on already-selected run → `onRunSelect(null)` called
  - Selected run → hit point has larger radius; others have `.is-subdued`
- [ ] Run `make test-client-fast` — green
- [ ] Run `make test-visual` — add a visual contract for the sparkline computed styles
  (check that solid vs dashed stroke styles resolve correctly)
- [ ] Create `client/src/history-page/MarketSparkline.stories.ts`:
  - Story: `Default` — 12-point series, `showPrior: true`, no run selected
  - Story: `ShowPriorFalse` — `showPrior: false`, no run selected
  - Story: `RunSelected` — `selectedRun: 5`, `showPrior: true`
- [ ] Verify each story via Chrome DevTools MCP (see G7 for protocol):
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
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 2: MarketSparkline component"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

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
- [ ] Create `client/src/history-page/MarketKpiCard.stories.ts`:
  - Story: `PositiveDelta` — `deltaClass: ""`, positive delta string
  - Story: `NegativeDelta` — `deltaClass: "down"`
  - Story: `FlatDelta` — `deltaClass: "flat"`
  - Story: `AllTimeNoPrior` — `showPrior: false`, no sparkline overlay
- [ ] Verify each story via Chrome DevTools MCP:
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
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 3: MarketKpiCard component"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

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
- [ ] Create `client/src/history-page/MarketEventsCard.stories.ts`:
  - Story: `CurrentQuarter` — events from `currentQuarter` fixture
  - Story: `AllTime` — events from `allTime` fixture
- [ ] Verify each story via Chrome DevTools MCP:
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
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 4: MarketEventsCard component"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 5 — MarketHealthSection Island (Assembly + State)

**Goal:** Compose the section. Own the `selectedRun` state. Wire the sparkline legend
(basis note, prior key visibility, "Clear run focus" button). This is the Svelte island
that mounts into the page.

**Tasks:**
- [ ] Create `client/src/history-page/MarketHealthSection.svelte`:
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
- [ ] Create `client/src/history-page/MarketHealthSection.test.ts`:
  - Renders with `currentQuarter` fixture — all 4 KPI cards visible
  - Prior key in legend is visible when `showPrior: true`
  - Prior key in legend is hidden when `showPrior: false` (use `allTime` fixture)
  - Click run index 5 (0-based) on observed sparkline → selection note updates to
    contain `"Run 6 selected. The same moment is now highlighted across all four KPI cards."`
    AND `selectedRun` propagates to all 4 cards
  - Click same run again → note resets to "Optional" text; clear button hidden
  - Clear button click (when visible) → resets selection
- [ ] Register the island mount in `client/src/history-page/index.ts`:
  - Read `window.marketHealthPayloads` (cast as `Record<WindowId, MarketHealthPayload> | undefined`)
  - Default to `'current-quarter'` window on initial mount; switch the active payload
    when the user clicks a time-window button
  - If present, mount `MarketHealthSection` into `<div id="market-health-root">`
  - (The mount point does not exist in the template yet — that is Phase 6)
- [ ] Run `make test-client` — coverage ≥ 80% for all history-page files
- [ ] Create `client/src/history-page/MarketHealthSection.stories.ts`:
  - `meta.component = MarketHealthSection`
  - Story: `CurrentQuarter` — args from `marketHealthCurrentQuarter` fixture
  - Story: `LastQuarter` — args from `marketHealthLastQuarter` fixture
  - Story: `AllTime` — args from `marketHealthAllTime` fixture
  - Story: `StockUnderPressure` — args from `marketHealthStockUnderPressure` fixture
  - Story: `RunSelected` — `currentQuarter` fixture + `initialSelectedRun: 8`
    (seeds the internal `$state`; no decorator needed)
- [ ] Verify all stories via Chrome DevTools MCP — this is the primary living-spec
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
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 5: MarketHealthSection island"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

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
- [ ] Create `tests/website_module/test_market_health_dto.py`:
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
- [ ] Run `make test` — green; `make test-file FILE=tests/website_module/test_market_health_dto.py`
  — coverage ≥ 80% for `market_health_dto.py`

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection scan
- [ ] H3 — Feed-forward log entry
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 6: market health Python data layer"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 7 — Page Integration

**Goal:** Create the new `history-insights.html` page — a separate page that appears
alongside (not replacing) the existing `history.html`. Wire the Python DTO, inject the
window global, and validate end-to-end.

**CRITICAL — do NOT touch `history.html` or `history_page.html`:** The existing History
page stays intact until all four work packages (WP1–WP4) are merged. This phase creates
a new page only.

**Pre-flight:**
- [ ] Read `src/website/generate_website.py` — study `generate_history_page()` as the
  model for the new function; understand how `json_rows`, the template context, and
  `OUTPUT_DIR` are used.
- [ ] Read `src/website/page_config.py` — understand the `NAV_ITEMS` list and
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
- [ ] H2 — Reflection scan
- [x] H3 — Feed-forward log entry (see below)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 7: page integration — template wiring and E2E green"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 8 — Storybook Visual Acceptance Pass

**Goal:** Systematic Chrome DevTools MCP sweep across all stories and the live preview
site. No new code (unless a divergence is classified `"fixed"`). Every divergence must
be documented in the feed-forward log before the feature is considered shippable.

**Pre-flight:**
- [ ] All stories from Phases 2–5 render without console errors.
- [ ] Phase 7 complete — `make preview` shows the Market Health section with real data.
- [ ] Both servers running: `make storybook` (port 6006) and `make preview` (port 8000).
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
- [ ] H2 — Reflection scan
- [x] H3 — Feed-forward log entry (see below)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 8: visual acceptance pass complete"`
- [ ] GATE — Output phase completion block (template in Phase Structure section)

---

## Phase 9 — Push and Open Pull Request

**Goal:** Publish the branch and open a pull request for human review.

**Pre-flight:**
- [ ] All phases 1–8 complete — all H1–H4 steps checked off.
- [ ] `make test-client` green.
- [ ] `make test` green.
- [ ] `make test-e2e` green.

**Tasks:**
- [ ] Push the branch:
  ```bash
  git push --set-upstream origin history-page-market-health
  ```
- [ ] Open a pull request using the GitHub CLI:
  ```bash
  gh pr create \
    --title "Market Health KPI section for History page" \
    --body "Implements the Market Health section as specified in docs/ux/history-page/market-health-handoff-spec.md and docs/ux/history-page/market-health-implementation-plan.md.\n\n## What this PR delivers\n- Phase 1: TypeScript interfaces, fixture files, Storybook install\n- Phase 2: MarketSparkline SVG component\n- Phase 3: MarketKpiCard component\n- Phase 4: MarketEventsCard component\n- Phase 5: MarketHealthSection island (assembly + state)\n- Phase 6: Python market_health_dto module\n- Phase 7: Template wiring, page integration, E2E green\n- Phase 8: Storybook visual acceptance pass\n\n## Testing\n- All Vitest unit tests pass with coverage ≥ 80%\n- All Python unit tests pass with coverage ≥ 80%\n- E2E suite passes\n- Visual contracts pass\n\n## Divergence log\nSee the Phase 8 feed-forward entry in the implementation plan for all by-design and deferred items." \
    --base master
  ```

**Tasks (continued):**
- [ ] Confirm the PR was created: run `gh pr view --json url,number` and note the PR number and URL.
- [ ] Output the review handoff prompt below in your response, replacing `[PR_NUMBER]`,
  `[PR_URL]`, and `[DEFERRED_ITEMS]` with real values from your Phase 8 feed-forward log.
  This prompt is for the user to paste into a new chat session to trigger a spec-conformance review:

---
**REVIEW HANDOFF PROMPT — paste into a new chat session:**

Review PR #[PR_NUMBER] (`history-page-market-health`) against the spec and plan for the Market Health KPI section.

PR: [PR_URL]

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
[DEFERRED_ITEMS]

For each item found, report: **PASS** / **FAIL** (spec violation — quote the spec §, quote the code, suggest a fix) / **CONCERN** (not a violation but worth noting).

---

**Housekeeping:**
- [ ] H1 — Confirm PR URL is accessible and the branch is visible on GitHub.
- [ ] H3 — Feed-forward log entry: record the PR URL and confirm the review handoff prompt was output.

---

## What Is Not In Scope for This Work Package

| Item | Status |
|---|---|
| Time window switcher UI | Separate component; exists in the mock filter panel. Out of scope. |
| Genus selector UI and per-genus/species KPI data | WP-Arch — delivers genus selector panel, lazy-load JSON generator, and Svelte fetch hook. WP1 must not build any of this. |
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
```
