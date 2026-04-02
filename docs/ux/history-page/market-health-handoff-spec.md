# Market Health — Handoff Spec

**Section:** 1. Market Health KPIs  
**Source mock:** [`history-kpi-concepts-mockup.html`](./history-kpi-concepts-mockup.html)  
**Branch:** `history-page-kpis`

This document is the source of truth for implementing the Market Health section of the
History page. It covers metric definitions, copy contracts, component boundaries,
fixture file shapes, and Storybook story list. Read this before writing any code for
this section.

---

## 1. Purpose and Scope

The Market Health section answers a question that adapts to the genus selection:

- **"All" mode (default on page load):** *"Is the wider tarantula market growing, becoming
  harder to source, or levelling off?"* Data scope is **all tracked species** — the
  market-wide baseline before the user narrows to a genus.
- **Genus-scoped mode:** *"Is supply and demand for your selected genera growing, tightening,
  or levelling off?"* Data scope is **selected genera only** — filtered to the genera the
  user has in scope via the global genus selector.

The genus selector includes an **"All genera" button** (default active on page load). Selecting
it resets Market Health to market-wide data. Selecting any specific genus deactivates any
active convenience button ("All", "Arboreal", "Most observed", etc.).

- Time scope: controlled by the global **time window** filter (This month / Last month /
  Current quarter / Last quarter / This year / All time).
- Audience: breeders deciding whether market or genus-level conditions support investment.

**Gate rule.** All-mode: "If the overall market looks flat, treat individual genus
comparisons cautiously." Genus-scoped: "If your selected genera look flat overall, treat
any individual genus comparison cautiously."

**Filter panel note.** Both the time window and the genus selection apply to the whole
page including this section. The filter panel description should read: *"Both the time
window and genus selection apply to every section on this page, including Market Health
KPIs. Comparison controls in sections 2 and 3 assign additional roles (focus genus, peer
set) within the genera already in scope here."*

---

## 2. Section Layout

```
┌─ Section header ─────────────────────────────────────────────────────────────┐
│  Eyebrow: "1. Market Health KPIs"                                            │
│  Heading: dynamic — see §2.1 below                                          │
│  Sub-copy: dynamic — see §2.1 below                                         │
│  Section note (static)                                                      │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ KPI Grid (4 cards) ─────────────────────────────────────────────────────────┐
│  [Observed species]  [In-stock rate]  [Median wishlist]  [Median price]      │
│  Each card: title · value · delta badge · copy sentence · sparkline          │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ Sparkline support row ──────────────────────────────────────────────────────┐
│  Legend: "Active window" (solid) · "Matched prior-period overlay" (dashed)   │
│  Basis note (dynamic per window)                                              │
│  Selection note · "Clear run focus" button (hidden until a run is selected)  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ Events mini-grid ───────────────────────────────────────────────────────────┐
│  [Listings added]  [Listings removed]  [OUT→IN restocks]  [IN→OUT stockouts] │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.1 Heading Adaptation Rules

The `<h2>` and sub-copy `<p>` in the section header are **dynamic** — they update whenever
the genus selection changes. The section note is static.

| Genus count | `<h2>` text | Sub-copy |
|---|---|---|
| All-mode | `"Is the wider tarantula market growing, becoming harder to source, or levelling off?"` | `"These metrics cover all tracked species — the widest possible lens before you narrow to a genus."` |
| 0 (specific, none added) | `"Add genera to see supply and demand health for your selection."` | `"Use the genus filter above to add genera. Market Health KPIs will reflect whichever genera are in scope."` |
| 1 | `"Is {genus} supply growing, tightening, or levelling off?"` | Static supply/demand sentence (see below) |
| 2–3 | `"For {A}, {B} and {C}: is supply growing, tightening, or levelling off?"` | Static |
| 4+ | `"How healthy is supply and demand across your {N} selected genera?"` | Static |

**Static sub-copy (1+ genera):**  
`"These metrics ask whether supply and demand for your selected genera look healthy enough to support breeding investment."`

**Section note (always static, mode-aware):**
- All-mode: `"If the overall market looks flat, treat individual genus comparisons cautiously."`
- Genus-scoped (1+ genera): `"If your selected genera look flat overall, treat any individual genus comparison cautiously."`
- Empty (0 specific genera): `"Use the genus filter above to add genera before drawing conclusions."`

**DOM requirements:**  
- `<h2 id="market-health-heading">` — updated by JS on every genus selection change  
- `<p id="market-health-scope-copy">` — updated by JS alongside the heading

---

## 3. KPI Definitions

### 3.1 Observed species

| Field | Details |
|---|---|
| **What it measures** | Count of distinct scientific names seen IN-stock at least once within the selected genera and active window |
| **Value format** | Integer — e.g. `14` |
| **Delta format** | `+N vs {prior_label}` · `No prior comparison` (all-time) |
| **Delta CSS class** | `""` (positive or neutral) · `"down"` (negative) · `"flat"` (all-time) — applied to `.metric-delta` element |
| **Sparkline colour** | `#1f7a6b` (accent) |

**Copy states** (select from this set; do not generate free-form prose):

| When | Copy sentence |
|---|---|
| delta ≥ +3 | `"Species breadth across your selected genera is ahead of {prior_label}, so your selection still looks alive on assortment even while actual stock is getting tighter."` |
| 0 ≤ delta ≤ +2 | `"Species breadth is only slightly ahead of {prior_label}, so the selection still looks broad without signalling a step-change in assortment."` |
| delta < 0 | `"Fewer species are being seen in-stock than at {prior_label}, which may suggest some genera are becoming harder to source."` |
| all-time | `"All-time view is best read as structural context: the selection is broad enough to support opportunity hunting, but this lens is not about recent acceleration."` |

---

### 3.2 In-stock rate

| Field | Details |
|---|---|
| **What it measures** | Of all distinct species seen IN-stock at least once during the active window, what percentage are IN-stock at the **most recent scrape run** within that window. Numerator = species in-stock at the latest run; denominator = species seen in-stock at any point during the window. Answers: "how much of what appeared this period is still available right now?" |
| **Value format** | `NN%` — e.g. `61%` |
| **Delta format** | `+N pts vs {prior_label}` · `-N pts vs {prior_label}` · `No prior comparison` |
| **Delta CSS class** | `""` (positive) · `"down"` (negative) · `"flat"` (all-time) |
| **Sparkline colour** | `#cc6b49` (accent-2) |

**Copy states:**

| When | Copy sentence |
|---|---|
| delta ≤ −7 | `"{value} of listings for your selected genera are available now. That is {abs(delta)} percentage points lower than {prior_label}, so availability is slipping even while the species count remains broad."` |
| −6 ≤ delta ≤ −1 | `"Availability is a touch weaker than {prior_label}. That reads more like a near-term tightening than a structural collapse."` |
| delta = 0 | `"The in-stock rate is holding steady vs {prior_label}."` |
| delta ≥ +1 | `"Availability is firmer than {prior_label}, which suggests supply is keeping pace with demand."` |
| all-time | `"All-time availability smooths out short-term swings, so it is useful for background context rather than telling you what changed recently."` |

---

### 3.3 Median wishlist

| Field | Details |
|---|---|
| **What it measures** | Median `wishlist_count` across all IN-stock listings **within the selected genera** at the most recent run within the active window |
| **Value format** | Integer — e.g. `18` |
| **Delta format** | `+N vs {prior_label}` · `No prior comparison` |
| **Delta CSS class** | `""` (positive) · `"flat"` (all-time or no change) |
| **Sparkline colour** | `#a18b35` (accent-3) |

**Copy states:**

| When | Copy sentence |
|---|---|
| delta ≥ +4 | `"Across your selected genera, median wishlist demand is ahead of {prior_label}, reinforcing the idea that interest is improving while availability slips."` |
| +1 ≤ delta ≤ +3 | `"Median wishlist counts across your selected genera are modestly above {prior_label}, which suggests demand is holding without obviously overheating."` |
| delta = 0 | `"Median wishlist demand is stable vs {prior_label}."` |
| delta ≤ −1 | `"Demand across your selected genera looks softer than {prior_label}."` |
| all-time | `"All-time wishlist levels show the long-run demand floor for your selected genera, not whether interest just strengthened this month or quarter."` |

---

### 3.4 Median price

| Field | Details |
|---|---|
| **What it measures** | Median `price_gbp` across all IN-stock listings **within the selected genera** at the most recent run within the active window |
| **Value format** | `GBP NN` — e.g. `GBP 24` |
| **Delta format** | `+GBP N vs {prior_label}` · `No prior comparison` |
| **Delta CSS class** | `"flat"` (0 change) · `""` (positive) · `"down"` (negative) |
| **Sparkline colour** | `#5d6a6d` (muted) |

**Copy states:**

| When | Copy sentence |
|---|---|
| delta = 0 | `"Price is steady, so the main movement appears to be availability rather than inflation."` |
| delta ≥ +2 | `"Prices are somewhat firmer than {prior_label}, but the move is still smaller than the availability shift. Supply pressure remains the more important signal."` |
| delta = +1 | `"Prices edged up a little relative to {prior_label}, which fits a market that is tightening gradually rather than repricing sharply."` |
| delta ≤ −1 | `"Prices have softened vs {prior_label}, which runs counter to the tighter-supply read."` |
| all-time | `"All-time price mainly describes the market baseline. It is less useful than shorter windows when you are deciding whether recent conditions have shifted."` |

---

## 4. Sparkline Design Contract

### 4.1 Rendering rules

- **12 data points** per series.
- X-axis: evenly spaced — left = period start, right = period end.
- Y-axis: auto-range — current and prior series share the same scale for the same metric.
- **Current series**: solid line, 2.5px stroke. Filled circles at each point (r=2.7px; r=4.4px when run-selected).
- **Prior series**: dashed line, same colour, `stroke-opacity: 0.65`. Open/lighter circles (r=2.2px; r=3.4px when run-selected).
- Prior series hidden (not rendered) when `showPrior = false` (all-time window only).

### 4.2 Run-selection interaction

All 4 sparklines are coupled — clicking any data point selects that run index across all cards simultaneously.

| State | Behaviour |
|---|---|
| No run selected | All points normal size and opacity |
| Run N selected | Selected point: larger radius. All other points: `.is-subdued` (opacity 0.3) |
| "Clear run focus" button | Hidden when no run selected; visible when one is selected |
| Selection note | Changes from "Optional: click a run…" to "Run N selected. Same moment highlighted across all four KPI cards." |

### 4.3 Prior-period legend key

The "Matched prior-period overlay" key item in the sparkline support row is **hidden** when
`showPrior = false`.

### 4.4 Basis note (dynamic)

The note below the sparkline legend changes per window:

| Window | Basis note |
|---|---|
| This month | `"Compare within a row. Solid shows this month; dashed shows the matched point last month."` |
| Last month | `"Compare within a row. Solid shows last month; dashed shows the prior full month."` |
| Current quarter | `"Compare within a row. Solid shows the current quarter; dashed shows the matched point last quarter."` |
| Last quarter | `"Compare within a row. Solid shows last quarter; dashed shows the prior full quarter."` |
| This year | `"Compare within a row. Solid shows this year to date; dashed shows the matched point last year."` |
| Last year | `"Compare within a row. Solid shows last year; dashed shows the prior full year."` |
| All time | `"All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale."` |

---

## 5. Events Mini-Grid Contract

### 5.1 Layout

2×2 grid. Each tile: label text · bold value · supporting copy sentence.

### 5.2 Event types

| ID | Default label | Value format (comparative windows) | Value format (all-time) |
|---|---|---|---|
| `newListings` | Listings added | `+N vs {period}` | `N total` |
| `droppedListings` | Listings removed | `N vs {period}` | `N total` |
| `restocks` | OUT → IN restocks | `N vs {period}` | `N total` |
| `oosFlips` | IN → OUT stockouts | `+N vs {period}` | `N total` |

### 5.3 Copy rules — bounded set

Copy is selected from a small fixed set per event type; do not generate prose dynamically.

**Listings added:**

| When | Copy |
|---|---|
| value clearly ahead of prior | `"Introductions are materially ahead of the matched point last {period}, which supports the breadth expansion visible in the chart."` |
| value slightly ahead | `"Fresh introductions are only slightly ahead of the same point last {period}, so the catalog is still expanding but not surging."` |
| all-time | `"Use this as background volume, not as a directional comparison."` |

**Listings removed:**

| When | Copy |
|---|---|
| low count | `"Some churn is present, but the removal count is too small to imply retreat."` |
| notable count but offset by inflow | `"Churn also rose, but the balance still favors broader assortment rather than retreat."` |
| all-time | `"All-time churn is useful for scale, but weak for saying what changed recently."` |

**OUT → IN restocks:**

| When | Copy |
|---|---|
| active | `"Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than {prior_label}."` |
| all-time | `"This shows how much movement exists in the market overall, not whether it is improving now."` |

**IN → OUT stockouts:**

| When | Copy |
|---|---|
| stockouts up vs prior | `"More listings are moving from IN to OUT than at the same point last {period}, which helps explain why availability is softer even while breadth is still expanding."` |
| all-time | `"Use this as structural supply-friction context, not as a directional signal about what changed recently."` |

### 5.4 Title and subtitle (dynamic per window)

| Window | Title | Subtitle |
|---|---|---|
| This month | `"Run-to-run market events this month"` | `"This month event totals against the same point last month."` |
| Last month | `"Run-to-run market events last month"` | `"Last month event totals against the prior full month."` |
| Current quarter | `"Run-to-run market events this quarter"` | `"Current-quarter event totals against the same point last quarter."` |
| Last quarter | `"Run-to-run market events last quarter"` | `"Last-quarter event totals against the prior full quarter."` |
| This year | `"Run-to-run market events this year"` | `"Year-to-date event totals against the same point last year."` |
| Last year | `"Run-to-run market events last year"` | `"Last-year event totals against the prior full year."` |
| All time | `"Market events across all time"` | `"All-time event totals as structural context only."` |

---

## 6. Time Window Behaviour Summary

| Window | `showPrior` | Delta basis | Prior label token |
|---|---|---|---|
| This month | `true` | vs prior month MTD | `"prior month MTD"` |
| Last month | `true` | vs prior full month | `"prior full month"` / `"Jan"` etc. |
| Current quarter | `true` | vs prior quarter QTD | `"prior quarter QTD"` |
| Last quarter | `true` | vs prior full quarter | `"Q3 '25"` (named quarter) |
| This year | `true` | vs prior year YTD | `"prior year YTD"` |
| Last year | `true` | vs prior full year | `"2024"` (named year) |
| All time | `false` | `"No prior comparison"` + `flat` class | n/a |

---

## 7. Component Boundaries

### 7.1 Proposed Svelte component split

| Component | Proposed file | Receives | Responsibility |
|---|---|---|---|
| `MarketHealthSection` | `history-page/MarketHealthSection.svelte` | `MarketHealthPayload` | Section shell, header, layout. Passes slices to children. |
| `MarketKpiCard` | `history-page/MarketKpiCard.svelte` | `KpiCardData`, `SparklineSeries`, `showPrior`, `selectedRun` | Single KPI tile — value, delta, copy, sparkline. Fires `onRunSelect` callback. |
| `MarketSparkline` | `history-page/MarketSparkline.svelte` | `series`, `priorSeries`, `showPrior`, `color`, `formatValue`, `selectedRun` | Inline SVG sparkline. Emits run-click events. |
| `MarketEventsCard` | `history-page/MarketEventsCard.svelte` | `MarketEventsData` | The events mini-grid visual card. |

> **Simpler alternative:** if the sparkline click interaction is the only stateful part,
> a single `MarketHealthSection.svelte` island receiving the full `MarketHealthPayload`
> keeps all state in one place. `MarketEventsCard` can then be a pure sub-component with
> no state.

### 7.2 Payload type contract

```typescript
// Canonical shape — use for Storybook fixtures, unit tests, and window global payload

export interface MarketHealthPayload {
  windowId: WindowId;
  windowLabel: string;
  basisNote: string;           // human-readable basis sentence for sparkline legend
  showPrior: boolean;          // drives prior sparkline series visibility
  compareNote: string;         // drives sparkline-support basis note text
  isAllSelected: boolean;      // true = All-mode (all tracked species); false = genus-scoped
  generaCount: number;         // drives heading adaptation (0 = empty genus-scoped state)
  scopeLabel: string;          // e.g. "Avicularia, Caribena and 2 more" for heading copy

  kpis: {
    observed: KpiCardData;
    stock: KpiCardData;
    wishlist: KpiCardData;
    price: KpiCardData;
  };

  sparklineSeries: {
    observed: SparklineSeries;
    stock: SparklineSeries;
    wishlist: SparklineSeries;
    price: SparklineSeries;
  };

  events: MarketEventsData;
}

export interface KpiCardData {
  title: string;                          // static heading e.g. "Observed species"
  value: string;                          // formatted value e.g. "184" or "61%"
  delta: string;                          // formatted delta e.g. "+7 vs prior quarter QTD"
  deltaClass: '' | 'down' | 'flat';       // maps to CSS modifier on .metric-delta
  copy: string;                           // one interpretation sentence (see §3)
  // NOTE: the `?` info-icon tooltip text (e.g. "Of species seen in-stock this period…") is
  // a hardcoded constant inside MarketKpiCard.svelte, keyed by metric ID. It is NOT in the
  // payload because it never varies by window, genus selection, or data.
}

export interface SparklineSeries {
  current: number[];    // 12 values
  prior: number[];      // 12 values; empty array [] when showPrior = false
}

export interface MarketEventsData {
  title: string;
  subtitle: string;
  newListings: EventTile;
  droppedListings: EventTile;
  restocks: EventTile;
  oosFlips: EventTile;
}

export interface EventTile {
  label: string;
  value: string;
  copy: string;
}

export type WindowId =
  | 'this-month'
  | 'last-month'
  | 'current-quarter'
  | 'last-quarter'
  | 'this-year'
  | 'last-year'
  | 'all-time';
```

---

## 8. Fixture Files (Storybook + Tests)

Proposed location: `client/src/history-page/__fixtures__/`

### 8.1 File list

| File | Scenario |
|---|---|
| `marketHealth.currentQuarter.ts` | Default story — current quarter, all deltas present, `showPrior: true` |
| `marketHealth.lastQuarter.ts` | Completed period — named quarter label, completed data |
| `marketHealth.allTime.ts` | All-time window — `showPrior: false`, flat deltas, `"No prior comparison"` values |
| `marketHealth.stockUnderPressure.ts` | Stock delta ≤ −7, wishlist rising — highest-stakes KPI read |
| `marketHealth.runSelected.ts` | Same data as `currentQuarter`, with `selectedRun: 8` (tests run-selection state) |

> `runSelected` doesn't need a separate fixture file — the `selectedRun` prop can be set
> in the Storybook story args directly. Use a fixture only if the data shape differs.

### 8.2 Canonical fixture — current quarter

```typescript
// client/src/history-page/__fixtures__/marketHealth.currentQuarter.ts
import type { MarketHealthPayload } from '../types';

export const marketHealthCurrentQuarter: MarketHealthPayload = {
  windowId: 'current-quarter',
  windowLabel: 'Current quarter',
  basisNote: 'Comparison basis: quarter to date vs prior quarter QTD.',
  showPrior: true,
  compareNote: 'Compare within a row. Solid shows the current quarter; dashed shows the matched point last quarter.',

  kpis: {
    observed: {
      title: 'Observed species',
      value: '184',
      delta: '+7 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Breadth is ahead of prior quarter QTD, so the market still looks alive on assortment even while actual stock is getting tighter.',
    },
    stock: {
      title: 'In-stock rate',
      value: '61%',
      delta: '-4 pts vs prior quarter QTD',
      deltaClass: 'down',
      copy: '61% of tracked listings are available now. That is 4 percentage points lower than prior quarter QTD, so availability is slipping even while the catalog remains broad.',
    },
    wishlist: {
      title: 'Median wishlist',
      value: '18',
      delta: '+3 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Across tracked species, median wishlist demand is ahead of prior quarter QTD, reinforcing the idea that interest is improving while availability slips.',
    },
    price: {
      title: 'Median price',
      value: 'GBP 24',
      delta: '+GBP 1 vs prior quarter QTD',
      deltaClass: 'flat',
      copy: 'Prices edged up a little relative to prior quarter QTD, which fits a market that is tightening gradually rather than repricing sharply.',
    },
  },

  sparklineSeries: {
    observed: {
      current: [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184],
      prior:   [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177],
    },
    stock: {
      current: [67, 66, 66, 65, 64, 63, 63, 62, 62, 61, 61, 61],
      prior:   [69, 68, 68, 67, 67, 66, 66, 65, 65, 65, 65, 65],
    },
    wishlist: {
      current: [14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 18, 18],
      prior:   [12, 12, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15],
    },
    price: {
      current: [23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24],
      prior:   [22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23],
    },
  },

  events: {
    title: 'Run-to-run market events this quarter',
    subtitle: 'Current-quarter event totals against the same point last quarter.',
    newListings: {
      label: 'Listings added',
      value: '+29 vs prior quarter QTD',
      copy: 'Introductions are materially ahead of the matched point last quarter, which supports the breadth expansion visible in the chart.',
    },
    droppedListings: {
      label: 'Listings removed',
      value: '17 vs prior quarter QTD',
      copy: "There is real churn, but not enough to erase the stronger inflow.",
    },
    restocks: {
      label: 'OUT → IN restocks',
      value: '43 vs prior quarter QTD',
      copy: 'Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than last quarter.',
    },
    oosFlips: {
      label: 'IN → OUT stockouts',
      value: '+21 vs prior quarter QTD',
      copy: 'More listings are moving from IN to OUT than at the same point last quarter, which helps explain why availability is softer even while breadth is still expanding.',
    },
  },
};
```

### 8.3 All-time fixture (key differences)

```typescript
// Abbreviated — show only what differs from currentQuarter fixture
export const marketHealthAllTime: MarketHealthPayload = {
  windowId: 'all-time',
  windowLabel: 'All time',
  basisNote: 'Comparison basis: structural context only, with no prior-period delta.',
  showPrior: false,
  compareNote: 'All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale.',

  kpis: {
    observed: { ..., delta: 'No prior comparison', deltaClass: 'flat', copy: 'All-time view is best read as structural context...' },
    stock:    { ..., delta: 'No prior comparison', deltaClass: 'flat', copy: 'All-time availability smooths out short-term swings...' },
    wishlist: { ..., delta: 'No prior comparison', deltaClass: 'flat', copy: 'All-time wishlist levels show the long-run demand floor...' },
    price:    { ..., delta: 'No prior comparison', deltaClass: 'flat', copy: 'All-time price mainly describes the market baseline...' },
  },

  sparklineSeries: {
    observed: { current: [130, 140, 149, 156, 162, 167, 171, 175, 179, 181, 183, 184], prior: [] },
    stock:    { current: [72, 70, 69, 68, 67, 66, 65, 64, 63, 62, 62, 61], prior: [] },
    wishlist: { current: [8, 10, 11, 13, 14, 15, 16, 17, 17, 18, 18, 18], prior: [] },
    price:    { current: [19, 20, 21, 21, 22, 22, 23, 23, 24, 24, 24, 24], prior: [] },
  },

  events: {
    title: 'Market events across all time',
    subtitle: 'All-time event totals as structural context only.',
    newListings:    { label: 'Listings added',         value: '286 total', copy: 'Use this as background volume, not as a directional comparison.' },
    droppedListings:{ label: 'Listings removed',       value: '172 total', copy: 'All-time churn is useful for scale, but weak for saying what changed recently.' },
    restocks:       { label: 'OUT → IN restocks',      value: '391 total', copy: 'This shows how much movement exists in the market overall, not whether it is improving now.' },
    oosFlips:       { label: 'IN → OUT stockouts',     value: '214 total', copy: 'Use this as structural supply-friction context, not as a directional signal about what changed recently.' },
  },
};
```

---

## 9. Storybook Story List

### `MarketHealthSection`

| Story name | Fixture | Highlights |
|---|---|---|
| `CurrentQuarter` | `marketHealth.currentQuarter` | Default view; `showPrior: true`; all 4 KPIs with deltas |
| `LastQuarter` | `marketHealth.lastQuarter` | Completed period; named quarter label in deltas |
| `AllTime` | `marketHealth.allTime` | `showPrior: false`; prior sparkline series hidden; "No prior comparison" labels |
| `StockUnderPressure` | `marketHealth.stockUnderPressure` | Stock delta ≤ −7; wishlist rising — shows maximum-tension KPI read |
| `RunSelected` | `marketHealth.currentQuarter` + `args.selectedRun: 8` | Run 8 highlighted across all 4 cards; "Clear run focus" button visible |

### `MarketKpiCard`

| Story name | Scenario |
|---|---|
| `PositiveDelta` | deltaClass `""` — standard up state |
| `NegativeDelta` | deltaClass `"down"` — stock rate falling |
| `FlatDelta` | deltaClass `"flat"` — price unchanged or all-time window |
| `AllTime_NoPrior` | `showPrior: false` — sparkline prior series not rendered |
| `RunSelected` | Run N selected; larger hit circle, other points subdued |

### `MarketEventsCard`

| Story name | Scenario |
|---|---|
| `CurrentQuarter` | Comparative values with `"+N vs …"` format |
| `AllTime` | Absolute totals with `"N total"` format |

---

## 10. Production Copy Pattern

**Rule: no dynamic prose generation for KPI copy.** Every interpretation sentence is
selected from the bounded sets defined in §3 and §5. The only dynamic substitution
allowed is inserting `{value}`, `{delta}`, and `{prior_label}` into a pre-written
template string.

**KPI card rendering order:**
1. Static heading (never changes per window)
2. Dynamic value (from data)
3. Dynamic delta + class (from data + window rule)
4. Copy sentence (from bounded lookup in §3)
5. Sparkline (from series data)

**Events tile rendering order:**
1. Dynamic label (matches window — see §5.4 title options)
2. Dynamic value (from data)
3. Copy sentence (from bounded lookup in §5.3)

---

## 11. Open Decisions

| # | Question | Recommendation |
|---|---|---|
| 1 | **Svelte island vs server-render?** If sparkline run-click is the only stateful interaction, a single `MarketHealthSection.svelte` island receiving a fully-computed payload is the cleanest fit for the existing window-global pattern. | Go with single island. |
| 2 | **Where does sparkline series data come from?** The mock uses interpolated shapes. In production, aggregate weekly snapshots per metric per window from the history CSV, filtered to the selected genera. | Build a `computeMarketHealthPayload(window, genera, rows)` utility in `history-page/`. |
| 3 | **All-time Y-axis** | `showPrior: false` → auto-range solely from the current series. No shared-scale constraint with prior. |
| 4 | **Run-click interaction scope** | Only the sparklines in the Market Health section participate. The run index is local state inside `MarketHealthSection` — it does not affect other sections. |
| 5 | **Responsive grid** | KPI grid: 4-column → 2-column at < 760px (matches existing CSS breakpoint). Events grid: 2-column at all widths. |
| 6 | **Residual CSS** | `.pulse-series`, `.pulse-end-label`, `.pulse-end-label[hidden]`, `.pulse-end-label.prior`, `.pulse-selection-note`, `.pulse-scale-note` are present in the mock CSS but unused. Remove before implementation. |
| 7 | **Empty genus state** | When `generaCount === 0` AND `isAllSelected === false`, show the empty-state heading and hide all KPI cards and event tiles. The section remains visible as a structural placeholder. |
| 8 | **`scopeLabel` format** | For ≤ 3 genera: `"Avicularia, Caribena and Psalmopoeus"`. For 4+: `"your 4 selected genera"`. Computed server-side; passed in payload so the client does not need to re-derive the genus list. |
| 9 | **`isAllSelected` default** | `true` — the page generates with All-mode as the default. The Python generator passes the active genus selection and whether it is “All”. Selecting a specific genus requires a new page render (static site). |

---

## 12. What This Spec Intentionally Excludes

- **Breeder Opportunity section** — covered by a separate spec once this one is implemented.
- **Bias Control section** — same.
- **Time window filter UI** — that is a separate panel component.
- **Genus selector UI** — the filter panel component itself is out of scope for this spec.
  How the selection (and whether “All” is active) is communicated to the Python generator
  is covered in the implementation plan.
- **CSV export** — not relevant to this section.
