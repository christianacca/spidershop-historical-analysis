# Market Health — Handoff Spec

**Section:** 1. Market Health KPIs  
**Work package:** WP1 of 5 (see §12 for staged delivery model)  
**Source mock:** [`history-kpi-concepts-mockup.html`](./history-kpi-concepts-mockup.html)  
**Branch:** `history-page-market-health`

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

The entire section is wrapped in a **card container** (border, large border-radius, padding).

```
┌─ Section wrapper (card: border, radius-card-lg, padding) ─────────────────────────────┐
│                                                                                        │
│  ┌─ Section header (flex: row, gap ~18px) ──────────────────────────────────────────┐ │
│  │                                                                                  │ │
│  │  Left column (flex: 1 1 auto)            Right column (max-width ~38ch)         │ │
│  │  ─────────────────────────────────────   ─────────────────────────────────────  │ │
│  │  Eyebrow: "1. Market Health KPIs" [pill] Section note (italic, static)          │ │
│  │  Heading: dynamic — see §2.1 below                                              │ │
│  │  Sub-copy: dynamic — see §2.1 below                                             │ │
│  │                                                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                        │
│  ┌─ KPI Grid (4 cards) ───────────────────────────────────────────────────────────┐   │
│  │  [Observed species]  [In-stock rate]  [Median wishlist]  [Median price]        │   │
│  │  Each card: title + ? info button · value · delta badge (pill) · copy · spark  │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
│  ┌─ Sparkline support row ────────────────────────────────────────────────────────┐   │
│  │  Legend: "Active window" (solid) · "Matched prior-period overlay" (dashed)     │   │
│  │  Basis note (dynamic per window)                                                │   │
│  │  Selection note · "Clear run focus" button (hidden until a run is selected)    │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
│  ┌─ Events mini-grid ─────────────────────────────────────────────────────────────┐   │
│  │  [Listings added]  [Listings removed]  [OUT→IN restocks]  [IN→OUT stockouts]   │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

**Section header layout rule:** The section header is a flex row — heading+copy block on
the left grows to fill space; the section note is pinned to the right with `max-width ~38ch`.
Do **not** use a `<header>` HTML element for the section header — `common.css` applies
`background: var(--color-primary)` to `header {}` globally, which would produce an
unintended dark background. Use `<div class="section-header">` instead.

**Eyebrow pill:** The eyebrow label ("1. Market Health KPIs") is styled as a teal pill:
`background: rgba(31, 122, 107, 0.1)`, `color: #1f7a6b` (or token `--color-market-health`
once defined), `border-radius: 999px`, `padding: 5px 9px`, `font-weight: 700`.

**Delta badge visual states (all three use pill shape — `border-radius: 999px`):**

| Class | Background | Text colour | Intended signal |
|---|---|---|---|
| `""` (positive/neutral) | `rgba(31, 122, 107, 0.12)` | `#1f7a6b` (teal) | Up / healthy |
| `"down"` | `rgba(178, 76, 61, 0.12)` | `#b24c3d` (red-amber) | Down / unhealthy |
| `"flat"` | `rgba(127, 140, 141, 0.12)` | `#7f8c8d` (muted) | Neutral / all-time |

Note: the "down" background red is `rgba(178, 76, 61, 0.12)` — slightly different from
`--color-danger: #e74c3c`. The existing `.down` rule may use `--color-danger`; verify
against the mock at implementation time.

**KPI card border-radius:** Cards use a larger-than-default radius (~16–18px). A new token
`--radius-card-lg` will be required in `common.css` (see Phase 10).

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

> **Mode note:** The table shows All-mode canonical copy (used when `isAllSelected: true`). For genus-scoped mode Python substitutes: "Breadth is ahead of" → "Species breadth across your selected genera is ahead of"; "the catalog" → "your selection"; "across tracked species" → "across your selected genera". Python performs this substitution at render time — the Svelte component always receives a fully-resolved string.

| When | Copy sentence (All-mode; see mode note for genus-scoped) |
|---|---|
| delta ≥ +3 | `"Breadth is ahead of {prior_label}, so the market still looks alive on assortment even while actual stock is getting tighter."` |
| 0 ≤ delta ≤ +2 | `"Breadth is only slightly ahead of {prior_label}, so the catalog still looks broad without signalling a step-change in assortment."` |
| delta < 0 | `"Fewer species are being seen in-stock than at {prior_label}, which may suggest some genera are becoming harder to source."` |
| all-time | `"All-time view is best read as structural context: the catalog is broad enough to support opportunity hunting, but this lens is not about recent acceleration."` |

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
| **What it measures** | Median `wishlist_count` across all IN-stock **species** within the selected genera at the most recent run. One data point per species: for species with multiple active size variants, the highest `wishlist_count` among active variants is used (per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4). |
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
| **What it measures** | Median `price_gbp` across all IN-stock **species** within the selected genera at the most recent run. One data point per species: for species with multiple active size variants, the price from the current active size lineage is used (per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4). |
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
- **Prior series**: dashed line, same colour, CSS `opacity: 0.38` on the `<polyline>`. Open/lighter circles (r=2.2px; r=3.4px when run-selected), CSS `opacity: 0.45`.
- Prior series hidden (not rendered) when `showPrior = false` (all-time window only).
- **Baseline axis line**: horizontal `<line>` at `y = chartHeight − bottomPadding`, `stroke: #d7cfc0`, `stroke-width: 1`. Renders for all windows.
- **Run-axis labels**: three `<text>` elements at x-positions 0, 5, 11 (0-indexed). Default labels for weekly data: `"Run 1"`, `"Run 6"`, `"Run 12"`. Window config may override with human-readable labels (e.g. `"Jan"`, `"Jun"`, `"Dec"` for year windows; `"Start"`, `"Middle"`, `"Now"` for all-time).

### 4.2 Run-selection interaction

All 4 sparklines are coupled — clicking any data point selects that run index across all cards simultaneously.

| State | Behaviour |
|---|---|
| No run selected | All points normal size and opacity |
| Run N selected | Selected point: larger radius. All other points: `.is-subdued` (CSS `opacity: 0.16`) |
| "Clear run focus" button | Hidden when no run selected; visible when one is selected |
| Selection note | Changes from `"Optional: click a run…"` to `"Run {n+1} selected. The same moment is now highlighted across all four KPI cards."` |

> **Index convention:** Internal run index is 0-based. All user-facing displays are 1-based: index `n` is displayed as `Run n+1`.

### 4.3 Prior-period legend key

The "Matched prior-period overlay" key item in the sparkline support row is **hidden** when
`showPrior = false`.

### 4.4 Sparkline basis note (dynamic)

The note below the sparkline legend (rendered in `#market-sparkline-basis-note`, sourced from `sparklineBasisNote` in the payload) changes per window:

| Window | Sparkline basis note |
|---|---|
| This month | `"Compare within a row. Solid shows this month; dashed shows the matched point last month."` |
| Last month | `"Compare within a row. Solid shows last month; dashed shows the prior full month."` |
| Current quarter | `"Compare within a row. Solid shows the current quarter; dashed shows the matched point last quarter."` |
| Last quarter | `"Compare within a row. Solid shows last quarter; dashed shows the prior full quarter."` |
| This year | `"Compare within a row. Solid shows this year to date; dashed shows the matched point last year."` |
| Last year | `"Compare within a row. Solid shows last year; dashed shows the prior full year."` |
| All time | `"All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale."` |

### 4.5 Run readout text

Each KPI card has a `<p class="sparkline-readout">` element below the sparkline SVG. Its text updates whenever `selectedRun` changes.

| State | Readout text |
|---|---|
| No run selected, `showPrior: true` | `"{metric label} shown as active window vs matched prior-period overlay."` |
| No run selected, `showPrior: false` | `"{metric label} shown as {windowScopeLabel} context with no prior-period overlay."` |
| Run N selected, `showPrior: true` | `"{pointLabel}: {currentValue} current vs {priorValue} matched prior period."` |
| Run N selected, `showPrior: false` | `"{pointLabel}: {currentValue} within {windowScopeLabel}, with no prior-period overlay."` |

`pointLabel` is window-specific (e.g. `"Run 4"` for weekly windows, `"Mar"` for year windows). Default: `"Run {n+1}"` (1-indexed). `windowScopeLabel` = human-readable window scope string (e.g. `"current quarter"`, `"all time"`).

### 4.6 Sparkline shell and box structure

Each KPI card wraps its sparkline and readout text in a two-element shell:

```html
<div class="metric-sparkline-shell">
  <div class="metric-sparkline">
    <!-- SVG rendered by MarketSparkline component — scales to 100% width -->
  </div>
  <p class="sparkline-readout">…text per §4.5…</p>
</div>
```

**`.metric-sparkline-shell`** — outer wrapper:
- `display: grid; gap: 8px` (stacks the box above the readout text)
- `margin-top: 6px; padding-top: 10px`
- `border-top: 1px dashed rgba(31, 42, 44, 0.12)` (dashed separator line between copy and sparkline area)

**`.metric-sparkline`** — bordered box around the SVG:
- `border: 1px solid rgba(215, 207, 192, 0.9)` (warm sand, same as card border but opaque)
- `border-radius: 14px`
- `background: rgba(255, 255, 255, 0.72)` (semi-transparent white inset)
- `overflow: hidden`
- The SVG inside must scale to `width: 100%; height: auto;` to fill the box.

**`.sparkline-readout`** — text below the box:
- `color: var(--color-text-muted)`
- `font-size: 0.79rem`
- Text content per §4.5 above.

> **Implementation note:** The `MarketSparkline` SVG component must have CSS
> `width: 100%; height: auto` applied so it fills the `.metric-sparkline` container.
> Setting `viewBox` on the SVG element ensures proportional scaling.
> The `windowScopeLabel` needed for the §4.5 readout text is derived from the payload's
> `windowId` (`windowId.replaceAll('-', ' ')`) and passed as a prop to `MarketKpiCard`.

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

> **Species-level counting:** All four event counts are species-level. A confirmed size
> transition (same `page_url`, same species, ≤3-run window per SIZE_VARIANT_IDENTITY_REQUIREMENTS
> Decision 2) must **not** be counted as a `droppedListings` + `newListings` pair — it is
> the same listing continuing. Restocks and stockouts are species-level: a species restocks
> when it goes from absent to present (any active size variant); a species stockouts when
> it goes from present to absent (all size variants absent).

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
| removals outpace inflow | `"Removals are outpacing new additions, which suggests the listing set is contracting rather than growing."` |
| all-time | `"All-time churn is useful for scale, but weak for saying what changed recently."` |

**OUT → IN restocks:**

> Active = restock count ≥ 1 for the period.

| When | Copy |
|---|---|
| active (count ≥ 1) | `"Movement is active; stock is not simply frozen, even though the in-stock rate is weaker than {prior_label}."` |
| inactive (count = 0) | `"No OUT-to-IN restocks occurred this period. If the in-stock rate is also falling, supply may have stalled rather than just tightened."` |
| all-time | `"This shows how much movement exists in the market overall, not whether it is improving now."` |

**IN → OUT stockouts:**

| When | Copy |
|---|---|
| stockouts up vs prior | `"More listings are moving from IN to OUT than at the same point last {period}, which helps explain why availability is softer even while breadth is still expanding."` |
| stockouts down vs prior | `"Fewer listings moved from IN to OUT than at the same point last {period}, which is consistent with availability stabilising."` |
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

The `{prior_label}` token in §3/§5 copy sentences resolves to the **copy sentence label** (natural-language form). The delta badge text uses the **prior label token** (technical form). Python computes both and provides fully-resolved strings; the Svelte component does no token substitution.

| Window | `showPrior` | Delta basis | Prior label token (delta badge) | Copy sentence label (`{prior_label}`) |
|---|---|---|---|---|
| This month | `true` | vs prior month MTD | `"prior month MTD"` | `"the same point last month"` |
| Last month | `true` | vs prior full month | `"prior full month"` / `"Jan"` etc. | `"the prior full month"` / `"Jan"` etc. |
| Current quarter | `true` | vs prior quarter QTD | `"prior quarter QTD"` | `"the same point last quarter"` |
| Last quarter | `true` | vs prior full quarter | `"Q3 '25"` (named quarter) | `"Q3 '25"` (named quarter already natural) |
| This year | `true` | vs prior year YTD | `"prior year YTD"` | `"the same point last year"` |
| Last year | `true` | vs prior full year | `"2024"` (named year) | `"2024"` (named year already natural) |
| All time | `false` | `"No prior comparison"` + `flat` class | n/a | n/a |

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
  windowLabel: string;          // window display name; available for client-side use but has no
                                // fixed DOM target in Market Health — do not require for rendering
  windowBasisNote: string;      // renders as filter-panel period summary below time-window buttons
                                // (#time-window-basis-note)
  showPrior: boolean;           // drives prior sparkline series visibility
  sparklineBasisNote: string;   // renders in sparkline support row (#market-sparkline-basis-note);
                                // values defined in §4.4
  isAllSelected: boolean;       // true = All-mode (all tracked species); false = genus-scoped
  generaCount: number;          // drives heading adaptation (0 = empty genus-scoped state)
  scopeLabel: string;           // ≤3 genera: "Avicularia, Caribena and Psalmopoeus";
                                // 4+: "your {N} selected genera"; All-mode: "" (empty)

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
  id: 'observed' | 'stock' | 'wishlist' | 'price';  // used by MarketKpiCard to look up the
                                                      // constant tooltip text (see §7.2 note)
  title: string;                          // static heading e.g. "Observed species"
  value: string;                          // formatted value e.g. "184" or "61%"
  delta: string;                          // formatted delta e.g. "+7 vs prior quarter QTD"
  deltaClass: '' | 'down' | 'flat';       // maps to CSS modifier on .metric-delta
  copy: string;                           // one interpretation sentence (see §3); fully resolved,
                                          // no {token} substitution needed by the component
  // NOTE: the `?` info-icon tooltip text (e.g. "Of species seen in-stock this period…") is
  // a hardcoded constant inside MarketKpiCard.svelte, keyed by `id`. It is NOT in the
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

> `selectedRun` is seeded via `initialSelectedRun` prop in Storybook story args. No separate fixture file is needed.

### 8.2 Canonical fixture — current quarter

```typescript
// client/src/history-page/__fixtures__/marketHealth.currentQuarter.ts
import type { MarketHealthPayload } from '../types';

export const marketHealthCurrentQuarter: MarketHealthPayload = {
  windowId: 'current-quarter',
  windowLabel: 'Current quarter',
  windowBasisNote: 'Comparison basis: quarter to date vs prior quarter QTD.',
  showPrior: true,
  sparklineBasisNote: 'Compare within a row. Solid shows the current quarter; dashed shows the matched point last quarter.',
  isAllSelected: true,
  generaCount: 0,
  scopeLabel: '',

  kpis: {
    observed: {
      id: 'observed',
      title: 'Observed species',
      value: '184',
      delta: '+7 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Breadth is ahead of the same point last quarter, so the market still looks alive on assortment even while actual stock is getting tighter.',
    },
    stock: {
      id: 'stock',
      title: 'In-stock rate',
      value: '61%',
      delta: '-4 pts vs prior quarter QTD',
      deltaClass: 'down',
      copy: 'Availability is a touch weaker than the same point last quarter. That reads more like a near-term tightening than a structural collapse.',
    },
    wishlist: {
      id: 'wishlist',
      title: 'Median wishlist',
      value: '18',
      delta: '+3 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Median wishlist counts are modestly above the same point last quarter, which suggests demand is holding without obviously overheating.',
    },
    price: {
      id: 'price',
      title: 'Median price',
      value: 'GBP 24',
      delta: '+GBP 1 vs prior quarter QTD',
      deltaClass: '',
      copy: 'Prices edged up a little relative to the same point last quarter, which fits a market that is tightening gradually rather than repricing sharply.',
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
      copy: "Churn also rose, but the balance still favors broader assortment rather than retreat.",
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
  windowBasisNote: 'Comparison basis: structural context only, with no prior-period delta.',
  showPrior: false,
  sparklineBasisNote: 'All-time view has no dashed overlay. Compare within a row; each metric keeps its own vertical scale.',

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
| 8 | **`scopeLabel` format** | For ≤ 3 genera: natural list `"Avicularia, Caribena and Psalmopoeus"`. For 4+: `"your {N} selected genera"`. All-mode: `""` (empty string — heading templates for All-mode do not reference the scope label). Computed server-side. |
| 9 | **`isAllSelected` default** | `true` — the page generates with All-mode as the default. The Python generator passes the active genus selection and whether it is "All". Selecting a specific genus requires a new page render (static site). |
| 10 | **Multi-window payload injection** | **Resolved → Option A.** All 7 window payloads are pre-embedded in the page as `window.marketHealthPayloads` (a `Record<WindowId, MarketHealthPayload>` dict). The Svelte island reads the active window's payload when the user clicks a time-window button. This matches the mock architecture and the existing `window.*` pattern used throughout the site. |
| 11 | **Genus-scoped and species-level KPI scope** | **Resolved → All-mode only for WP1; lazy-load JSON for WP-Arch.** WP1 produces only market-wide KPI data (`isAllSelected: true`). The type contract already carries `isAllSelected`, `generaCount`, and `scopeLabel` so genus-scoped heading/copy adaptation is ready, but KPI *values* are all-mode only in this work package. Pre-embedding all genus × window combinations inline is ruled out: ~68 genera × 7 windows = 476 payloads, and the same problem recurs at species level (~180 species × 7 windows = 1,260 payloads). Instead, **WP-Arch** will deliver a lazy-load static JSON pattern — Python pre-generates `market-health/genus/{slug}.json` and `market-health/species/{slug}.json` files (one per scope × window set); the Svelte island fetches the relevant file on first selection. This scales to any granularity, requires no server, and adds one shared loading-state pattern reused by all WPs. |
| 12 | **Run display is 1-indexed** | **Resolved.** Internal run index is 0-based. All user-facing labels are 1-based: index n is displayed as "Run n+1". Selection note format: `"Run {n+1} selected. The same moment is now highlighted across all four KPI cards."` |

---

## 12. What This Spec Intentionally Excludes

### Staged delivery model

The mock defines four sections delivered across five work packages (the extra WP adds the
filter architecture that all section WPs share). Each WP has its own spec and implementation
plan:

| WP | Scope | Dependency |
|---|---|---|
| **WP1 (this spec)** | Section 1 — Market Health KPIs (all-mode only) | None |
| **WP-Arch** | Filter architecture — genus selector UI, lazy-load JSON generator (`market-health/genus/{slug}.json`, `market-health/species/{slug}.json`), Svelte fetch hook + loading state | WP1 merged |
| WP2 | Section 2 — Breeder Opportunity KPIs (consumes WP-Arch fetch hook; genus-scoped from day one) | WP-Arch merged |
| WP3 | Section 3 — Bias Control KPIs | WP2 merged |
| WP4 | Section 4 — Filtered Data Preview | WP3 merged |

**New page, not replacement.** WP1 delivers a new `history-insights.html` page that
appears in the top nav and homepage card grid alongside the existing `history.html`. The
existing History page is not modified or removed until all work packages are merged.
At that point the old page is retired and `history-insights.html` becomes the canonical
History page.

### Items explicitly excluded from this spec

- **Breeder Opportunity section (Section 2)** — WP2; separate spec after WP1 merges.
- **Bias Control section (Section 3)** — WP3.
- **Filtered Data Preview (Section 4)** — WP4.
- **Replacing `history.html`** — deferred until all work packages are merged.
- **Time window filter UI** — separate panel component; out of scope for this spec.
- **Genus selector UI and per-genus/species KPI data** — delivered by WP-Arch. WP-Arch
  adds the genus selector panel, the lazy-load static JSON generator, and the Svelte fetch
  hook. WP1 must not build any of this — WP-Arch's spec does not exist yet.
- **CSV export** — not relevant to this section.
