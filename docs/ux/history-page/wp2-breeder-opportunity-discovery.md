# WP2 — Breeder Opportunity KPIs: Discovery Memo

> **Status:** Discovery complete. Not yet specced or planned.
> **Date:** 8 May 2026
> **Scope:** Section 2 Comparison Controls + Breeder Opportunity KPIs (mock `#breeder-section` and `.comparison-panel`)
> **Next step:** See §14 Recommended Next Workflow

---

## 1. Purpose and Scope Summary

This memo captures the findings of the WP2 discovery phase for the History Insights page. WP2
delivers the Comparison Controls panel and the Breeder Opportunity KPIs section — Section 2 of
the three-section KPI layout defined in the mock
(`docs/ux/history-page/history-kpi-concepts-mockup.html`).

**In scope:**
1. Comparison controls panel — focus genus picker, peer set editor, compare mode toggle ("Peer
   average" | "Market baseline"), state badge and copy.
2. Empty/placeholder state for the breeder section when no focus genus is selected.
3. Four Breeder KPI cards: Focus genus scarcity rate, Median wishlist in-stock, Restock cadence,
   Opportunity score (with inline "How this works" expandable, richer than WP1's `?` popover).
4. Opportunity score bar chart with 3 switchable compare views: `none` (all peers ranked),
   `peer-average`, `market-baseline`.
5. Opportunity ingredients rank table (per-genus scarcity / demand / restock / read badges;
   highlighted row for the focus genus).
6. A new `breeder-opportunity-engine.ts` that derives a Breeder Opportunity payload from
   `MarketHealthRawData`. Includes the Opportunity Score formula — see §12.
7. Fixture files and Storybook stories following the WP1 pattern.

**Explicitly out of scope:**
- Section 3 Bias Control KPIs (WP3).
- Section 4 Filtered Data Preview (WP4).
- Replacing `history.html` with `history-insights.html` as the canonical page.
- Global genus selector UI (WP-Arch — see §12 Blockers).
- Time window filter UI panel (WP-Arch).
- Python-side generator changes.

---

## 2. Existing Architecture and Feature Boundaries

### WP1 delivery (all phases complete)

All 13 WP1 implementation phases are complete and merged. The current state of
`client/src/history-page/` is:

| File | Role |
|---|---|
| `index.ts` | Page entry point. Mounts `MarketHealthSection` into `#market-health-root`. Reads `window.marketHealthRawData`, builds all 7 window payloads via `buildMarketHealthPayloadAllWindows`, passes `current-quarter` payload to the component. Genus is hardcoded to all-mode. Window is hardcoded to `current-quarter`. |
| `market-health-engine.ts` | ~1 100-line pure-function computation engine. Builds `MarketHealthPayload` from `MarketHealthRawData` for any of 7 window IDs. Supports `selectedGenera` / `isAllSelected` filtering via `options` param. No module-level state. |
| `types.ts` | Canonical TypeScript interfaces: `WindowId`, `MarketHealthPayload`, `KpiCardData`, `SparklineSeries`, `MarketEventsData`, `RawRunRecord`, `MarketHealthRawData`. |
| `MarketHealthSection.svelte` | Section shell. Receives `MarketHealthPayload`. Renders 4 `MarketKpiCard` children + `MarketEventsCard`. Manages `selectedRun` state for cross-card sparkline highlighting. |
| `MarketKpiCard.svelte` | Single KPI tile. Receives `KpiCardData` + `SparklineSeries`. Has a `?` `<details>` popover with a hardcoded tooltip per metric id. |
| `MarketSparkline.svelte` | Inline SVG sparkline with run-selection hit areas. Fixed 12-point grid. |
| `MarketEventsCard.svelte` | Static 4-tile events grid. |
| `DateFilter.svelte`, `HistoryTable.svelte` | History table filtering (not relevant to KPI island). |
| `__fixtures__/` | 4 typed fixture files + 1 raw fixture for engine tests. |
| `*.stories.ts` | Storybook stories for all WP1 components. |
| `*.visual.test.ts` | Browser-backed visual contract tests for all WP1 components. |

### Data flow (post WP1 Phase 12 cutover)

```
Python  →  window.marketHealthRawData (variant-level records)
           ↓
index.ts   buildMarketHealthPayloadAllWindows(rawData)  →  allPayloads[7 windows]
           ↓
MarketHealthSection  ←  allPayloads['current-quarter']  (static on mount)
```

Time window and genus selection are not yet wired. The engine supports both; nothing calls it
with updated params.

### WP-Arch status: **NOT STARTED** (hard blocker — see §12)

No genus selector component exists. No time window switcher component exists. `index.ts` has
no reactive loop for re-running the engine on selection change. WP2 cannot be implemented
until WP-Arch delivers these primitives.

---

## 3. Candidate Implementation Approaches

### Approach A — Extend `market-health-engine.ts`

Add a `buildBreederOpportunityPayload()` export to the existing engine file.

**Tradeoff:** The file is already ~1 100 lines. Adding cross-genus aggregation logic (which is
a different computational pattern — ranking across genera rather than windowed time-series
reduction) bloats it further and blurs the module's responsibility. The existing engine's API,
types, and test infrastructure are tuned to the `MarketHealthPayload` shape. WP2 output is a
structurally different payload type.

**Verdict:** Not recommended.

### Approach B — New sibling `breeder-opportunity-engine.ts` *(recommended)*

Add `client/src/history-page/breeder-opportunity-engine.ts` as a peer to the existing engine.
It imports `MarketHealthRawData` and the window-bounds helpers it needs, then exposes a single
`buildBreederOpportunityPayload(rawData, windowId, focusGenus, peerGenera, compareMode)` export.

**Tradeoff:** A second file, a second set of unit tests. But: clean separation of concerns,
independently mockable in Storybook, independently testable, matches the project convention
against monolithic files. The engine becomes an import rather than a host.

**Verdict:** Recommended.

### Approach C — Derive Breeder payload inside the page root component

Compute the Breeder payload reactively inside a root Svelte component (e.g. a new
`HistoryInsightsRoot.svelte`) without a separate engine file.

**Tradeoff:** Business logic in a Svelte component violates the established WP1 pattern
(engine = pure TS, component = rendering only). Makes unit testing much harder. Only viable
if the computation is trivial — it is not.

**Verdict:** Not recommended.

---

## 4. Recommended Approach and Why

**Use Approach B: sibling `breeder-opportunity-engine.ts`.**

Rationale:
- Matches WP1's engine pattern exactly (pure functions, no module state, typed inputs/outputs).
- The market-health engine and the breeder engine have different primary aggregation patterns:
  the former does windowed time-series reduction per metric; the latter does cross-genus ranking
  with a composite score. Keeping them separate makes each easier to read and test.
- Storybook fixtures for WP2 are independent of WP1 fixtures — no shared mutation risk.
- Future WP3 (Bias Control) will add a third engine; the sibling pattern scales cleanly.

The root orchestration challenge (one mount point, multiple sections) is addressed in §6 below.

---

## 5. Reuse Opportunities

| WP1 artifact | WP2 reuse plan |
|---|---|
| `MarketKpiCard.svelte` | Reuse for 3 of the 4 Breeder KPI cards (scarcity, wishlist, restock). The Opportunity Score card needs a variant with an inline `<details class="metric-method">` expandable below the copy — not a floating popover. Recommend a new `BreederKpiCard.svelte` or a conditional slot extension. |
| `MarketSparkline.svelte` | Not used in WP2 Breeder KPI cards (mock shows no sparklines in the breeder section, only bar chart and table). |
| `types.ts` | Extend with new WP2 types: `BreederOpportunityPayload`, `BreederKpiCardData`, `IngredientsRow`, `CompareMode`, `ComparisonState`. |
| `market-health-engine.ts` | Import `getWindowBounds()` (or its logic) for window-scoped record filtering. Import `RawRunRecord` type. |
| `__fixtures__/marketHealthRaw.ts` | Reuse as input to the breeder engine in unit tests. |
| `*.stories.ts` pattern | Follow exactly: named exports, typed args, `satisfies Story`. |
| `*.visual.test.ts` pattern | Follow exactly for computed CSS assertions. |

---

## 6. Likely Files / Modules / Templates / Components to Touch

### New files

| File | Purpose |
|---|---|
| `client/src/history-page/breeder-opportunity-engine.ts` | Computation engine: derives `BreederOpportunityPayload` from raw data |
| `client/src/history-page/breeder-opportunity-engine.test.ts` | Unit tests for engine |
| `client/src/history-page/ComparisonPanel.svelte` | Shared comparison controls (owned by WP2, consumed by WP3) |
| `client/src/history-page/ComparisonPanel.test.ts` | Unit tests |
| `client/src/history-page/ComparisonPanel.visual.test.ts` | Computed CSS assertions |
| `client/src/history-page/ComparisonPanel.stories.ts` | Storybook stories (4 states) |
| `client/src/history-page/BreederSection.svelte` | Section shell: placeholder ↔ live reveal, owns section header |
| `client/src/history-page/BreederSection.test.ts` | Unit tests |
| `client/src/history-page/BreederSection.visual.test.ts` | Reveal animation and placeholder style assertions |
| `client/src/history-page/BreederSection.stories.ts` | Storybook stories (placeholder, 3 live compare views) |
| `client/src/history-page/BreederKpiCard.svelte` | KPI card variant with inline `metric-method` expandable |
| `client/src/history-page/BreederKpiCard.test.ts` | Unit tests |
| `client/src/history-page/BreederKpiCard.visual.test.ts` | Computed CSS for card, badge, expandable |
| `client/src/history-page/BreederKpiCard.stories.ts` | Storybook stories |
| `client/src/history-page/OpportunityScoreChart.svelte` | 3-state bar chart (none / peer-average / market-baseline) |
| `client/src/history-page/OpportunityScoreChart.test.ts` | Unit tests (view switching, bar rendering) |
| `client/src/history-page/OpportunityScoreChart.visual.test.ts` | Bar fill gradient color assertions |
| `client/src/history-page/OpportunityScoreChart.stories.ts` | Storybook stories (3 views) |
| `client/src/history-page/IngredientsTable.svelte` | Rank table with badge coloring + focus row highlight |
| `client/src/history-page/IngredientsTable.test.ts` | Unit tests |
| `client/src/history-page/IngredientsTable.visual.test.ts` | Highlight row color, badge color assertions |
| `client/src/history-page/IngredientsTable.stories.ts` | Storybook stories |
| `client/src/history-page/__fixtures__/breederOpportunity.focusSelected.ts` | Fixture: focus genus selected, no compare mode |
| `client/src/history-page/__fixtures__/breederOpportunity.peerAverage.ts` | Fixture: peer-average compare mode |
| `client/src/history-page/__fixtures__/breederOpportunity.marketBaseline.ts` | Fixture: market-baseline compare mode |

### Modified files

| File | Change |
|---|---|
| `client/src/history-page/types.ts` | Add `BreederOpportunityPayload`, `BreederKpiCardData`, `IngredientsRow`, `CompareMode`, `ComparisonState`, `ComparisonPanelProps` |
| `client/src/history-page/index.ts` | **Major surgery.** Currently a simple mount. Must become a reactive orchestrator: receives `selectedGenera`, `windowId`, `focusGenus`, `peerGenera`, `compareMode` from WP-Arch; re-runs both engines on change; mounts `BreederSection`. Mount point strategy — see below. |
| `templates/history_insights_page.html` | Add a second mount point `<div id="breeder-section-root"></div>` or adopt a single root component strategy. |
| `templates/common.css` | Add `--color-breeder-focus` token (see §7). |

### Mount point strategy

`index.ts` currently mounts `MarketHealthSection` into `#market-health-root`. WP2 adds
`ComparisonPanel` and `BreederSection`. Two options:

**Option M1 — Multiple mount points (simpler)**
Add `<div id="comparison-panel-root">` and `<div id="breeder-section-root">` to the template.
Each is a separate `mount()` call. State shared between them (focusGenus, compareMode) must live
in `index.ts` and be passed to each component. Svelte 5 makes this workable via callback props.

**Option M2 — Single root component (cleaner for WP3+)**
Wrap everything in a new `HistoryInsightsRoot.svelte` that orchestrates all sections. One
`mount()` call in `index.ts`. State lives in the root component. Easier for WP3 and WP4 to join.

Recommendation: **Option M2**. WP3 and WP4 will also need shared state (`focusGenus`,
`compareMode`, `selectedGenera`). A root component makes that clean. The cost is one additional
file and slightly more complex initial mount. The spec must decide which to commit to.

---

## 7. CSS Token and Global Selector Constraints

### Missing token — blocking design decision

The mock uses `--accent-2: #cc6b49` (warm orange) for all focus-genus emphasis: selected pills,
bar fill `.alt`, `.compare-state-badge.broad`, `.rank-table tr.highlight`, and several border
colors. **No equivalent token exists in `templates/common.css`.** The closest existing tokens are:

| Existing token | Value | Verdict |
|---|---|---|
| `--color-signal-hot` | #ef4444 (red) | Wrong — different hue |
| `--color-danger` | #e74c3c (red) | Wrong — different hue |
| `--color-accent` | #3498db (blue) | Wrong — different hue |

**Resolution:** A new token `--color-breeder-focus: #cc6b49` must be added to the `:root`
block in `templates/common.css` before any WP2 component can reference it. This is a
pre-implementation gate.

### Additional token gap

The mock's `.badge.warn` uses `--warn: #c9861a` (dark amber). The repo has
`--color-signal-watch: #f59e0b` (lighter amber). These are close but not identical. A visual
contract test against the live page will surface any divergence. The spec should document this
as a "verify and decide" item.

### Mock-to-repo token mapping (confirmed)

| Mock variable | Maps to | Verified |
|---|---|---|
| `--accent` (#1f7a6b, teal) | `--color-market-health` | ✓ |
| `--accent-2` (#cc6b49, warm orange) | **NEW** `--color-breeder-focus` | ❌ needs adding |
| `--line` (#d7cfc0) | `--color-border-warm` | ✓ |
| `--ink` (#1f2a2c) | `--color-text` | ✓ |
| `--muted` (#5d6a6d) | `--color-text-label` | ✓ |
| `--good` (#1f7a6b) | `--color-market-health` | ✓ |
| `--warn` (#c9861a) | `--color-signal-watch` (close, verify) | ⚠️ |
| `--risk` (#b24c3d) | `--color-danger` (close, verify) | ⚠️ |
| `--surface` (#fffaf2) | `--color-surface` | ✓ |
| `--shadow` | `--shadow-popover` | ✓ |
| `--radius` (20px) | Between `--radius-card-lg` (16px) and `--radius-popover` (14px) | ⚠️ |

The mock uses `--radius: 20px` for `.section` and `.comparison-panel` border-radius. The repo
token `--radius-card-lg` is 16px. The KPI cards in WP1 already use 18px hardcoded (overriding
the token). The spec must decide whether to adopt 18px to match WP1 cards, 20px to match the
mock outer panels, or to add a token. Given WP1 precedent (18px hardcoded), use 18px for KPI
cards and specify `border-radius: 18px` directly on `.comparison-panel`.

### Global CSS collision risk

The mock uses `.section` as a class on outer section elements. The existing WP1 page uses
`#market-health-root` as the mount point (Svelte-scoped). As long as WP2 components also live
inside Svelte, the `.section` class from Layer 2 (`templates/analysis.css`, `homepage.css`)
should not collide. Verify during integration that no Layer 2 rule bleeds into the Svelte
island unexpectedly.

`<table>`, `<th>`, `<td>` in `IngredientsTable.svelte` may inherit global table styles. The
spec must mandate Svelte-scoped styles on the table element to prevent bleed.

---

## 8. Data / API / DTO / Backend Implications

### Payload type extensions needed in `types.ts`

```typescript
// New in WP2
export type CompareMode = 'none' | 'peer-average' | 'market-baseline';

export interface IngredientsRow {
  genus: string;
  scarcityLabel: 'High' | 'Medium' | 'Low';
  scarcityClass: '' | 'warn' | 'risk';        // maps to .badge modifier
  demandLabel: 'High' | 'Good' | 'Moderate' | 'Low';
  demandClass: '' | 'warn' | 'risk';
  restockLabel: 'Fast' | 'Healthy' | 'Slow';
  restockClass: '' | 'warn' | 'risk';
  read: string;                                // plain-text summary sentence
  isHighlighted: boolean;                      // true for focus genus row
}

export interface BreederKpiCardData {
  id: 'scarcity' | 'wishlist' | 'restock' | 'score';
  title: string;
  value: string;
  deltaLabel: string;                          // e.g. "Middle of pack", "High", "Slow"
  deltaClass: '' | 'down' | 'flat';
  copy: string;                                // single interpretation sentence
  // Only for id='score':
  methodBody?: string[];                       // ordered list items for "How this works"
}

export interface OpportunityScoreChartData {
  view: CompareMode;
  // 'none' view:
  noneRows?: Array<{ genus: string; score: number; isFocus: boolean }>;
  // 'peer-average' view:
  peerAverageScore?: number;
  focusScore?: number;
  focusGenus?: string;
  // 'market-baseline' view:
  marketScore?: number;
  peerSummaryScore?: number;
  peerSummaryLabel?: string;       // e.g. "4 peers saved"
}

export interface BreederOpportunityPayload {
  focusGenus: string;
  peerGenera: string[];
  compareMode: CompareMode;
  kpis: {
    scarcity: BreederKpiCardData;
    wishlist: BreederKpiCardData;
    restock: BreederKpiCardData;
    score: BreederKpiCardData;
  };
  chart: OpportunityScoreChartData;
  ingredients: IngredientsRow[];
}
```

### Engine inputs

```typescript
buildBreederOpportunityPayload(
  rawData: MarketHealthRawData,
  windowId: WindowId,
  focusGenus: string,
  peerGenera: string[],
  compareMode: CompareMode
): BreederOpportunityPayload
```

The engine reads `rawData.records` and `rawData.referenceDate`. It applies the same
window-bounds logic as the market-health engine to scope records. No Python changes needed —
`window.marketHealthRawData` already contains all variant-level records.

### No Python or backend changes

The Python generator outputs `window.marketHealthRawData` which is sufficient. WP2 derives
everything client-side from the same raw dataset.

---

## 9. Verification Harness Recommendation

Use the same four-layer pyramid established in WP1:

| Layer | Scope | Commands |
|---|---|---|
| Vitest unit | Engine pure logic, component prop rendering, state transitions | `make test-client-fast` (iteration), `make test-client` (gate) |
| Storybook | Isolated component states: all ComparisonPanel states, all bar chart views, placeholder vs live, ingredients table with/without focus row | repo Storybook command |
| Visual contracts (`*.visual.test.ts`) | Computed CSS: badge colors, bar fill gradients, `.rank-table tr.highlight` background, reveal animation class presence | `make test-visual` |
| E2E (Playwright) | Section reveal interaction (click focus genus → live state animates in), compare mode switching, bar chart view toggle, ingredients table highlight update | `make test-e2e` |

E2E tests are mandatory for WP2 because the section reveal, view switching, and comparison panel
state machine are client-side interactions that Vitest/happy-dom cannot model.

---

## 10. Storybook Recommendation

**Mandatory** (forced-on per work-package instructions).

Storybook is the correct primary harness for `ComparisonPanel` and `BreederSection` because:

- `ComparisonPanel` has at least 5 distinct interactive states that must be visually verified
  in isolation (all-selected-disabled, narrow-no-focus, focus-selected, peer-average-active,
  market-baseline-active).
- `BreederSection` has a placeholder state that must be visually verified before the live
  state is wired.
- `OpportunityScoreChart` has 3 mutually exclusive views — isolating them in Storybook catches
  layout bugs before page integration.

Storybook is **not sufficient** for:
- The section reveal animation (requires actual DOM mounted with CSS transitions).
- Global CSS collision checks (requires the integrated page).
- `window.marketHealthRawData` data shape validation (requires E2E or page integration).

Story files to create:
1. `ComparisonPanel.stories.ts` — 5 named exports (one per state)
2. `BreederSection.stories.ts` — 4 named exports (Placeholder, LiveNone, LivePeerAverage, LiveMarketBaseline)
3. `BreederKpiCard.stories.ts` — 4 named exports (one per card id, including expanded method panel)
4. `OpportunityScoreChart.stories.ts` — 3 named exports (None, PeerAverage, MarketBaseline)
5. `IngredientsTable.stories.ts` — 2 named exports (WithFocusHighlight, NoHighlight)

---

## 11. Risks and Likely Drift Points

| Risk | Severity | Mitigation |
|---|---|---|
| **WP-Arch not merged** | Critical | Hard blocker for WP2 implementation. WP-Arch must ship first. |
| **Opportunity Score formula undefined** | Critical | See §12. Cannot finalize engine or fixtures without formula sign-off. |
| **`--color-breeder-focus` token missing** | High | Add token to `templates/common.css` as a pre-implementation gate before any component references it. |
| **Single mount point must become multi-section orchestrator** | High | `index.ts` currently mounts one component. Root component restructure is required. Decide M1 vs M2 (see §6) during spec phase. |
| **Section reveal animation** | Medium | The mock uses CSS `max-height` + `opacity` + `transform` toggled by `.is-ready`. In Svelte, `{#if}` destroys DOM. Must use class binding (`$state` flag → `class={{ 'is-ready': ready }}`) with the live content always rendered but visually hidden. `await tick()` may be needed before triggering the transition to allow layout to compute the initial `max-height`. |
| **Bar chart is custom div/SVG, not a library** | Medium | Must stay consistent with the existing non-library pattern. The `none` view bar chart is a `<div class="bar-list">` with percentage-width inner divs — not SVG. Ingredients table is an HTML `<table>`. Both are fine; just not interchangeable with `MarketSparkline`'s SVG approach. |
| **`<table>` global style bleed** | Medium | The repo may have global `th`, `td` resets in `templates/common.css` or analysis.css. Svelte scoped styles must explicitly override these inside `IngredientsTable.svelte`. |
| **Comparison panel state machine complexity** | Medium | The panel has ~5 states and several legal/illegal transitions. A state machine approach (`$derived` from `selectedGenera`, `focusGenus`, `compareMode`) is safer than ad hoc conditionals. The spec must enumerate all states and their allowed transitions. |
| **`warn`/`risk` badge color divergence** | Low | Mock `--warn` (#c9861a) vs repo `--color-signal-watch` (#f59e0b) are different shades. A visual contract test against the live page will catch this. Document as "verify and decide" in the spec. |
| **`max-height: 2200px` transition** | Low | The mock uses `max-height: 2200px` as the expanded value. This is a browser hack for `max-height` transitions (can't animate to `auto`). This value needs to be large enough to contain the section but not so large the animation feels slow. Adjust during implementation and visual testing. |

---

## 12. Open Questions

### Resolved conservatively

**Q1: Which file should own `ComparisonPanel.svelte`?**
→ WP2 owns it. WP3 consumes the same `focusGenus`/`peerGenera`/`compareMode` state from the
  parent root (M2) or `index.ts` (M1). `ComparisonPanel` emits those values via callback props;
  the parent distributes them to `BreederSection` and (later) `BiasSection`. WP3 does not own
  or duplicate `ComparisonPanel`.

**Q2: How do the two selection layers interact when the global genus selection changes?**
→ If the current focus genus is removed from the global genus selection, the focus genus is
  cleared immediately (revert to placeholder state). The peer set is pruned to the intersection
  of current global selection and existing peer set. If fewer than 2 genera remain in scope,
  compare mode is disabled and the state card shows the "broad/all-selected" state. No partial
  state is persisted through a scope reduction.

**Q3: `BreederKpiCard` vs extending `MarketKpiCard`?**
→ New `BreederKpiCard.svelte`. The Opportunity Score card needs an inline `<details>` expandable
  (`.metric-method`) below the interpretation copy, which is structurally different from WP1's
  floating `<details>` popover. Extending `MarketKpiCard` with a conditional slot would create
  a prop-prop footgun and make both components harder to understand. A new component is cleaner.
  The other 3 Breeder KPI cards (scarcity, wishlist, restock) also use `BreederKpiCard` to keep
  the card grid visually uniform (same structure, no sparkline, same `.metric-method` slot
  — even if only the score card uses it).

**Q4: Mount point strategy — M1 or M2?**
→ M2 (single root component `HistoryInsightsRoot.svelte`) is recommended but this is a spec-
  phase decision, not a discovery-phase decision. It must be confirmed by the spec because WP3
  and WP4 are affected.

### Explicitly unresolved — requires human sign-off

**Q5: Opportunity Score formula and weights.**

This is a **blocking open question**. The formula cannot be invented by the agent because the
market analysis philosophy ("signal stability over early detection", "no single metric may
dominate decisions") requires explicit human judgment about weighting.

**What the mock says:** The score is a "scarcity + demand + restock cadence composite". It
combines three ingredient signals into a single 0–10 numeric score used to rank genera.

**What is needed to implement the engine:**
1. How each ingredient is measured from raw data:
   - Scarcity: % of this genus's runs where it was OOS within the window? Or latest-run OOS%?
   - Demand: median wishlist of in-stock listings at latest run? Or windowed median?
   - Restock cadence: mean OOS duration in days across all OOS episodes within window?
2. How each ingredient is normalized to a common scale (e.g. 0–10 percentile rank among
   in-scope genera, or min-max normalization, or fixed thresholds).
3. The composite weights (or explicit "equal thirds").

**Conservative default if human approves:** Equal thirds, each ingredient normalized 0–10
by percentile rank among in-scope genera (not fixed thresholds). This is the most conservative
choice because it avoids any opinion about which signal dominates — it simply ranks genera
relative to each other within the current scope.

**Human sign-off needed on:** (a) ingredient definitions, (b) normalization method,
(c) composite weights. Without this, the engine, the fixtures, and the copy generation
cannot be finalized.

---

## 13. Recommended Work-Package Boundaries

WP2 as scoped is appropriately sized given the dependency chain. No further splitting is
recommended within WP2 itself. The boundaries between WP-Arch → WP2 → WP3 → WP4 are
already clean.

However, the following **sequencing decision** is important:

1. **WP-Arch first** — delivers genus selector + time window selector (immediately useful to
   WP1 Market Health section even before WP2 exists).
2. **Opportunity Score formula sign-off** — can happen in parallel with WP-Arch.
3. **WP2 spec + plan** — after WP-Arch is merged and formula is signed off.
4. **WP2 implementation** — after WP2 spec and plan are approved.

---

## 14. Recommended Next Workflow

**`stop for human decision`** — then **`MOCK_TO_SPEC_PLAN`**

Two gates must clear before spec/plan work begins:

- **Gate 1:** Opportunity Score formula signed off by human (see §12 Q5).
- **Gate 2:** WP-Arch implemented and merged.

After both gates clear, the correct next workflow is **`MOCK_TO_SPEC_PLAN`** using
`docs/prompt-templates/MOCK_TO_SPEC_PLAN_PROMPT_TEMPLATE.md`. The mock is a live runnable
HTML file with a rich state machine — it must be translated into a precise component/engine
spec before implementation planning. The discovery memo should be passed as the
`[DISCOVERY_PATH]` input.

---

## 15. Handoff Inputs for the Next Stage

### Downstream workflow

Run `MOCK_TO_SPEC_PLAN` after both gates clear.

### Recommended spec path

`docs/ux/history-page/wp2-breeder-opportunity-spec.md`

### Recommended plan path

`docs/ux/history-page/wp2-breeder-opportunity-implementation-plan.md`

### Must-capture visual requirements the spec must spell out explicitly

1. **Section reveal pattern.** The `.section-placeholder` / `.section-live` transition uses
   `max-height` + `opacity` + `transform` toggled by `.is-ready` on the parent `.section`.
   This is a CSS class toggle, not a `{#if}` destroy/recreate. The spec must state this
   explicitly: "the live content is always rendered in the DOM; `.is-ready` drives
   `max-height: 0 → 2200px`, `opacity: 0 → 1`, `transform: translateY(18px) → translateY(0)`."

2. **Three-state bar chart switching.** The mock uses `[hidden]` attribute to show/hide
   `<div class="compare-view" data-compare-view="...">` blocks. The spec must enumerate what
   each of the 3 views renders:
   - `none`: sorted bar list; focus genus bar uses `.alt` gradient; other bars use default gradient or `.warn`
   - `peer-average`: exactly 2 bars (peer average + focus); peer uses default gradient, focus uses `.alt`
   - `market-baseline`: exactly 3 bars (market average + focus + "Saved peer set" dimmed to opacity 0.35)

3. **Comparison controls panel states.** The spec must enumerate all 5 states and their
   exact visual treatment:
   - All-selected (isAllSelected=true): mode buttons `disabled` + `disabled-control` class, badge reads "All mode"
   - Narrow no-focus (2+ genera in scope, no focus chosen): focus genus pills shown as buttons, peer set empty, mode buttons `inactive-context`
   - Focus selected no mode: focus pill uses `.focus` style (warm orange background), peer pills shown, mode buttons enabled
   - Peer-average active: "Peer average" button is `active`, chart shows peer-average view
   - Market-baseline active: "Market baseline" button is `active`, chart shows market-baseline view

4. **Opportunity Score card vs other KPI cards.** The Opportunity Score card has an inline
   `<details class="metric-method">` section below the copy (not a floating popover). The
   `<summary>` reads "How this works" and expands to a numbered list of 3 items. This is
   structurally different from the `?` `<details class="metric-info">` pattern used by the
   other 3 cards and all WP1 cards. The spec must capture this distinction in the DOM structure
   requirements.

5. **Ingredients table badge coloring.** Three badge classes map to:
   - No modifier (`.badge`): `background: rgba(31,122,107,0.10)`, `color: var(--color-market-health)` (green = "good")
   - `.badge.warn`: `background: rgba(201,134,26,0.12)`, `color: var(--warn)` (amber = "caution")
   - `.badge.risk`: `background: rgba(178,76,61,0.12)`, `color: var(--risk)` (red = "risk")
   The focus genus row uses `background: rgba(204,107,73,0.08)` — the `--color-breeder-focus`
   at very low opacity. The spec must state that `tr.highlight` is a class, not an inline style,
   and that its background uses the `--color-breeder-focus` token once that token is added.

### Must-check integration risks the plan must include

1. **WP-Arch dependency** — verify WP-Arch is merged and `selectedGenera`, `windowId` are
   flowing from a real component before any WP2 engine or component is wired into `index.ts`.

2. **Opportunity Score formula** — the plan must gate on formula sign-off before writing engine
   unit tests. Tests written against an unconfirmed formula will need rewriting.

3. **`--color-breeder-focus` token** — the plan must add this token to `templates/common.css`
   in Phase 1 (foundation) before any component references it, and include a visual contract
   test that reads the computed value to confirm it resolves correctly.

4. **Root component restructure** — `index.ts` and `history_insights_page.html` must be
   updated to support the orchestration pattern chosen (M1 or M2). This is Phase 1 work,
   not an afterthought.

5. **`<table>` global style bleed** — the plan must include an explicit task to audit global
   table styles in `templates/common.css` and `templates/analysis.css` before `IngredientsTable`
   is integrated into the live page, and to add Svelte-scoped overrides if any bleed is found.
