# Market Health — Implementation Extensions

This document records features added during the actual implementation that are **not**
present in the UX mock (`history-kpi-concepts-mockup.html`) or the handoff spec
(`market-health-handoff-spec.md`). They represent decisions made during engineering
that improve the experience beyond what was prototyped.

---

## IE-1 — Run selection note includes dates of selected and prior runs

**Scope:** Sparkline support row — `.pulse-selection-note`  
**Implemented:** Phase (TBC — history-page-market-health branch)

### What the mock says

When a user clicks a run on any mini-chart, the mock shows:

> _Run N selected. The same moment is now highlighted across all four KPI cards._

### What the implementation adds

The note now also shows the **scrape date** of the selected run, and (when a prior-period
overlay is active) the **matched prior-period date**:

> _Run N selected — 14 Apr 2026 vs 14 Jan 2026. The same moment is now highlighted across all four KPI cards._

When `showPrior` is `false` (e.g. all-time window), only the current date is shown:

> _Run N selected — 14 Apr 2026. The same moment is now highlighted across all four KPI cards._

### Why

Without the dates, "Run 6 selected" is abstract. Showing the calendar date of the run lets
the user immediately relate the selected moment to external events (e.g. a listing change
they noticed in the data table). The prior date makes the comparison concrete —
"I'm comparing 14 Apr 2026 against 14 Jan 2026" — rather than relying on the user to
mentally map "same-point-last-quarter" to an actual date.

### Type contract change

`SparklineSeries` gained two new fields:

```typescript
currentRunDates: string[];   // 12 ISO date strings, resampled at same indices as current[]
priorRunDates: string[];     // 12 ISO date strings; [] when showPrior is false
```

Date format displayed in the note: `"14 Apr 2026"` (day + abbreviated month + full year,
no leading zero on day — produced by `toLocaleDateString('en-GB', { day: 'numeric',
month: 'short', year: 'numeric' })`).

### Scope boundary

The date display lives entirely in `MarketHealthSection.svelte` — `MarketKpiCard` and
`MarketSparkline` are unchanged. The `currentRunDates` array on `SparklineSeries` is the
data contract; the component reads from `payload.sparklineSeries.observed.currentRunDates`
and `priorRunDates` (any series works — all four share identical run ordering).

---

_Add new entries below as further extensions are made._

---

## IE-2 — Redundant filter-note sentence removed from FiltersPanel

**Scope:** `FiltersPanel.svelte` — `.scope-inline` block  
**Implemented:** WP-Arch (pre-WP2 height-reduction pass)

### What the mock says

Below the global scope lozenge, the mock renders:

> _All KPIs, charts, preview rows, and CSV export reflect this scope._

### What the implementation does

That sentence is omitted. The paragraph immediately above the scope lozenge already reads
"Both the time window and genus selection apply to every section on this page." — which
conveys the same intent. Repeating it in the lozenge area added vertical clutter without
adding information.

### Why

On mobile portrait the filters panel occupies significant vertical real estate. Removing the
duplicate sentence reduces height with no information loss.

---

## IE-3 — Collapsible filters panel

**Scope:** `FiltersPanel.svelte`  
**Implemented:** WP-Arch (pre-WP2 height-reduction pass)

### What the mock says

The mock has no collapse mechanism for the filters panel. The full panel (genus selector +
time window selector + scope note) is always visible, offset by the large "Three ways to
assess the market" hero copy on the left which fills the available vertical space.

### What the implementation adds

A **Hide / Show** toggle button sits in the panel header row alongside the "Global filters"
heading. Clicking it collapses the panel body, leaving only:

1. The panel header row (heading + toggle button)
2. The global scope lozenge ("Current market scope: …")

The genus selector, time window selector, and the filter-note paragraph are hidden when
collapsed.

The panel starts **expanded** by default. Users who have set their filters and want to
reclaim vertical space can collapse it.

### Why

Without the "Three ways to assess the market" left-panel content (which is explicitly
out of scope for WP-Arch, per §2 of the spec), the filters panel dominates the hero area
on narrower viewports. On mobile portrait this is especially pronounced — the time window
pills wrap across multiple lines and the genus selector adds further height. The collapse
toggle lets users recover that space once they have selected their filters.

### Scope boundary

State (`panelExpanded`) is local to `FiltersPanel.svelte`. No changes to
`HistoryInsightsRoot.svelte`, `GenusSelector.svelte`, or `TimeWindowSelector.svelte`.

