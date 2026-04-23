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
