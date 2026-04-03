# Size Variant Identity Requirements

## Purpose

This document turns the recommendations in
`SIZE_VARIANT_IDENTITY_RECOMMENDATION.md` into an implementable requirement set.

It resolves the open decisions left intentionally undecided in that document:

1. when a size change should count as the same continuing listing,
2. how overlapping active size variants should be treated,
3. which metrics belong to species identity vs size identity,
4. how breeder and dealer analysis should share or diverge in transition logic,
5. how the species detail page should present the result.

The goal is to preserve the project's conservative, supply-first, explainable
approach while eliminating analytically contradictory outputs such as the same
species appearing as both a high breeder opportunity and an avoid case at the
same time.

---

## Relationship To Existing Recommendation

`SIZE_VARIANT_IDENTITY_RECOMMENDATION.md` correctly identifies the core issue as
an identity-layer problem rather than a taxonomy problem.

This document does not replace that recommendation.

It operationalizes it.

Specifically, it takes the earlier conceptual model:

1. species-size = trading unit,
2. species = confidence and context layer,

and turns it into a concrete product and analysis policy.

---

## Problem Statement

The current system generally keys analysis by `(scientific_name, size_cm)`.

That creates four practical failures when the shop changes a listing's displayed
size without changing the underlying commercial listing in a meaningful way.

### 1. Contradictory headline outcomes

The same species can produce multiple current rows with materially different
signals, including combinations that are difficult to defend in practice.

Example failure mode:

1. one size variant is flagged as scarce and commercially attractive,
2. another size variant is flagged as always available or low opportunity,
3. users interpret this as the species being both hot and avoid at once.

This conflicts with the project's goal of producing calm, trustworthy,
decision-support signals.

### 2. Wishlist continuity is broken by size transitions

Wishlist counts are observed to persist with the listing when the displayed size
changes.

A strict species-size identity resets wishlist pressure, count, and momentum in
cases where the user's practical interpretation is continuous.

This causes false demand discontinuity.

### 3. Price evidence becomes either over-fragmented or misleading

Price is the metric most likely to be genuinely affected by size.

That means naive species-level aggregation is unsafe.

However, treating every size change as a brand new identity also produces a
misleading result: recent price context disappears entirely even when the user
can plainly see the same listing continuing under a new size label.

### 4. The website model no longer matches the user model

Users think in terms of species-level questions:

1. is this species a breeder opportunity,
2. is this species a dealer risk,
3. what is happening with this species over time.

The current species-plus-size analytical identity makes the main tables and the
species detail page harder to interpret than necessary.

---

## Constraints And Design Principles

This requirement set must stay aligned with the project's documented philosophy
in `README.md`.

### Constraint 1: Supply remains primary

Breeder and dealer decisions must remain supply-first.

Price and wishlist may qualify or amplify interpretation, but they must not
become primary triggers where the project explicitly avoids that.

### Constraint 2: Conservative by default

The system must prefer a qualified or neutral interpretation over an inferred one.

Size transitions should only be merged when evidence is strong.

### Constraint 3: No silent loss of explainability

Every continuity decision must be explainable in plain English.

If a price trend is affected by a size transition, the surface should say so.

### Constraint 4: One commercial conclusion per species

The main breeder and dealer tables should surface one current decision row per
species, not multiple current rows that compete with each other.

### Constraint 5: Preserve size relevance where it really matters

Price and exact listing context remain size-sensitive.

The solution must not flatten that away.

---

## Proposed Solution Summary

The proposed solution is:

1. use species as the primary reporting identity for breeder and dealer tables,
2. keep one species detail page per species,
3. introduce a shared size-transition detection layer,
4. carry wishlist continuity across confirmed size transitions,
5. keep price evidence size-aware and mark it as transition-affected when needed,
6. handle overlapping active size variants explicitly rather than pretending they
   form one clean price line,
7. share the transition-identification layer across breeder and dealer analysis,
   while allowing the two analyses to use the resulting metadata differently.

This yields one row per species, one headline signal per species, and one detail
page per species, while still preserving the fact that size can materially affect
price interpretation.

---

## Definitions

### Species

The scientific name alone.

This is the primary reporting identity for headline breeder and dealer outputs.

### Size Variant

The `(scientific_name, size_cm)` combination.

This remains a supporting evidence identity for exact listing context.

### Listing Lineage

A continuity chain representing the same commercial listing over time, even if
the displayed size changes.

### Confirmed Size Transition

A change from one recorded size variant to another that should be treated as the
same continuing listing lineage.

### Overlapping Active Variants

Two or more size variants for the same species that are simultaneously active in
the current run, or otherwise overlap closely enough that they cannot be treated
as a single clean handoff.

### Transition-Affected Price Evidence

Price evidence that remains useful but is not fully like-for-like because the
active listing changed displayed size within the recent interpretation window.

---

## Resolved Policy Decisions

This section explicitly resolves the open questions left by the earlier
recommendation.

### Decision 1: Primary table identity

Requirement:

1. breeder and dealer tables must contain one current row per species.

Proposed solution:

1. species is the row identity for both tables,
2. size variants become supporting evidence attached to that species row,
3. the current active size or sizes are displayed as context, not as separate
   competing rows.

Justification:

1. users make a single practical decision about the species,
2. contradictory row-level outcomes undermine trust,
3. this is the simplest way to align the output with the project's explainable
   decision-support goal.

### Decision 2: Same continuing listing rule

Requirement:

1. the system must decide when a size change counts as continuity rather than a
   brand new identity.

Proposed solution:

A size change is treated as a confirmed size transition only when all of the
following are true:

1. the scientific name is unchanged,
2. the normalized product URL is unchanged,
3. the new size appears within a bounded recent transition window of the old
   size's final observation,
4. there is no same-run overlap between the old and new sizes during the handoff,
5. there is no evidence of two distinct active listings for the same species
   competing during the transition window.

Recommended interpretation window:

1. a recent transition window of up to 3 runs.

If any condition fails, the transition is ambiguous and must not be merged
silently.

Justification:

1. same URL is the strongest practical evidence that the shop listing is the same,
2. bounded recency preserves the project's conservative cadence-aware design,
3. the no-overlap rule avoids inventing continuity where the site may actually be
   offering distinct active variants,
4. ambiguity should degrade to caution rather than inference.

### Decision 2A: Ambiguous transition fallback behavior

Requirement:

1. ambiguous transitions must not silently merge evidence,
2. ambiguous transitions must also not re-fragment the breeder and dealer tables
   back into multiple current rows.

Proposed solution:

When a transition is ambiguous:

1. the breeder table still shows one species row,
2. the dealer table still shows one species row,
3. the species-level supply interpretation still drives the headline outcome,
4. wishlist continuity must not be carried across the ambiguous handoff,
5. wishlist delta should degrade to a conservative neutral state unless a
   defensible same-lineage comparison still exists,
6. current wishlist context may still be shown when there is a clearly current
   active listing, but it must not imply proven historical continuity across the
   ambiguous handoff,
7. price trend and sparkline must downgrade to a qualified or neutral state
   rather than present a clean like-for-like continuation,
8. the species detail page must explain that the row remains species-level while
   continuity-dependent evidence was downgraded because the handoff was not
   confirmed.

This means the fallback is:

1. keep one species row,
2. preserve species-level supply conclusions,
3. degrade ambiguous price and momentum evidence rather than recreating multiple
   competing rows.

Justification:

1. this preserves the central product goal of one practical conclusion per
   species,
2. it avoids the user-facing contradiction of returning to multiple current rows,
3. it stays conservative by refusing to invent continuity for price or momentum,
4. it keeps ambiguity visible in the metrics that genuinely depend on confirmed
   lineage continuity.

### Decision 3: Overlapping active size variants

Requirement:

1. the system must define what happens when multiple size variants are active at
   the same time.

Proposed solution:

1. overlapping active size variants are not treated as one clean transition,
2. the species still gets a single breeder row and a single dealer row,
3. supply status at the species level is considered active if any tracked size
   variant is active,
4. price evidence must be marked as multi-variant and therefore not strictly
   comparable as one single uninterrupted series,
5. the species detail page must expose the active variants explicitly.

For overlapping active variants, a single authoritative price trend arrow should
not be shown unless a single active lineage can be justified conservatively.

Justification:

1. this avoids the false precision of pretending multiple active variants are one
   exact trading unit,
2. it still preserves one species-level decision row,
3. it prevents the system from hiding ambiguity in the one metric where size is
   most likely to matter.

### Decision 4: Metric ownership policy

Requirement:

1. each metric must have a clear identity layer and continuity rule.

Proposed solution:

| Metric | Reporting identity | Continuity rule | Required behavior | Justification |
| --- | --- | --- | --- | --- |
| Stock presence / OOS state | Species | Any active size keeps the species active; confirmed transitions preserve lineage continuity | One species-level supply interpretation | Supply is the project's primary signal and should answer the practical species-level question |
| OOS runs / scarcity pattern | Species | Count species-level continuity, not retired-size isolation | Prevent one species from being simultaneously scarce and oversupplied | A retired size should not create a competing current headline if the species clearly continues |
| Stock reliability / restock speed | Species | Same as stock presence; use species-level availability across active lineages | Dealer analysis stays supply-first | Dealer risk is about lost sales on the species, not about one retired size label |
| Wishlist count | Species or confirmed listing lineage | Carry across confirmed size transitions; do not reset on clean handoff | One continuous demand context for the species row | Wishlist behavior is observed to travel with the listing and is described conceptually as species interest in the README |
| Wishlist pressure | Species | Derived from current species-level demand context | One current pressure classification per species | Avoids false demand discontinuity |
| Wishlist delta | Species | Compute momentum across the same continuing lineage where transition is confirmed | Keep momentum conservative and bounded | Delta should not reset merely because the displayed size changed |
| Current price | Active size lineage | Show current price from the active lineage; mark as transition-affected when recent size handoff exists | Preserve size realism without hiding continuity context | Price is the metric most sensitive to size |
| Price trend arrow | Active size lineage, qualified | Show only when the active lineage supports a defensible comparison; otherwise qualify or neutralize | Avoid false precision | The project should not present like-for-like price movement when the unit changed |
| Price sparkline | Active size lineage, qualified | Allow continuity display, but mark the series as transition-affected when size changed recently | Keep useful context without implying a pure same-unit series | The user still benefits from seeing listing continuity, but needs the caveat |
| Observation coverage | Both species and size | Show species-level familiarity plus size-level specificity | Use both layers on the detail page | This directly solves the identity/context mismatch described in the earlier recommendation |

Additional wishlist rule for overlapping active variants:

1. if multiple size variants are active in the current run, the row-level current
   wishlist count must equal the highest current `wishlist_count` among the active
   variants,
2. the row-level wishlist delta must downgrade to `→`,
3. the row-level wishlist history must downgrade to `-` unless a single lineage
   can still be justified conservatively.

Justification:

1. using the maximum active count avoids inflating demand by summing parallel
   listings,
2. neutralizing delta avoids inventing a stitched momentum story across multiple
   active variants,
3. this preserves one species row while staying conservative about continuity.

### Decision 5: Breeder vs dealer shared logic

Requirement:

1. the system must decide what breeder and dealer logic share and where they
   diverge.

Proposed solution:

Shared across breeder and dealer:

1. size-transition detection,
2. overlap detection,
3. species-level row identity,
4. wishlist continuity metadata,
5. size-transition warning metadata for surfaces.

Different between breeder and dealer:

1. breeder analysis consumes qualified price evidence as a modifier,
2. dealer analysis does not use price as a classifier, only as supporting detail,
3. breeder recommendation text may reference transition-affected price context,
4. dealer recommendation text should stay supply-first and only mention the size
   transition when it affects confidence or interpretation.

Justification:

1. identity truth should not diverge by audience,
2. signal semantics should still reflect the different questions each table is
   designed to answer,
3. shared identity metadata reduces inconsistency without forcing identical
   business logic.

### Decision 6: Species detail page model

Requirement:

1. the detail page must reconcile species-level reporting with size-aware
   evidence.

Proposed solution:

The species detail page must remain species-routed and species-oriented.

It must show:

1. one species-level breeder summary,
2. one species-level dealer summary,
3. current active size or sizes,
4. a transition banner when a confirmed size transition occurred in the recent
   interpretation window,
5. species-level observation coverage,
6. size-level observation coverage,
7. a price section labeled when transition-affected,
8. a wishlist section treated as continuous across confirmed handoffs,
9. explicit notes when multiple active variants make price comparison ambiguous.

Justification:

1. users come to the detail page to understand the species,
2. this is the correct place to expose nuance that would otherwise overload the
   table row,
3. one page per species matches the user's mental model and the static-site UX.

### Decision 7: Routing

Requirement:

1. the product must decide whether routing remains species-only or becomes
   size-specific.

Proposed solution:

1. routing remains species-only,
2. size is exposed as state and evidence inside the species page,
3. the URL remains stable even if the currently active size changes.

Justification:

1. species is the headline identity,
2. species-only routing preserves stable shareable URLs,
3. this avoids repeated page churn for what is often the same continuing listing.

---

## Surface Requirements

### Main Tables

Requirement:

1. the main tables must remain compact and readable.

Proposed solution:

1. each species appears once,
2. the `Size (cm)` column must show:
   1. the single current active size when exactly one size is active,
   2. the most recent last-active size when the species is currently OUT but a
      single recent lineage is still being interpreted,
   3. a comma-separated ascending list when multiple sizes are currently active,
3. the current size or active sizes are shown as compact context,
4. price cells that are affected by a recent confirmed size transition show a
   warning icon,
5. the warning tooltip must explain:
   1. the size change,
   2. when it occurred,
   3. that wishlist continuity is preserved,
   4. that price continuity is not fully like-for-like,
6. if overlapping active sizes prevent a clean single price interpretation, the
   price field must downgrade to an explicitly qualified state rather than show a
   precise unqualified trend.

Justification:

1. this keeps the tables simple,
2. it avoids hiding the only important caveat,
3. it uses warning disclosure to preserve information without fragmenting the row
   model.

### Species Detail Page

Requirement:

1. the species page must explain the same caveat in plain text, not only via
   tooltip.

Proposed solution:

1. the page shows a visible transition summary near the top,
2. it explains the most recent old size, new size, and transition date,
3. it states whether the continuity was treated as confirmed,
4. it explains the likely impact on price interpretation,
5. it shows the active size history used for chart interpretation.

Justification:

1. the detail page is an explanatory surface,
2. hidden tooltip-only disclosure is too weak for the page whose purpose is to
   explain why the species is flagged.

---

## Tooltip And Messaging Requirements

### Required Tooltip Content For Transition-Affected Price Evidence

The warning tooltip should communicate all of the following in plain English:

1. the species changed listed size,
2. the old and new sizes,
3. the date of the first observed new size,
4. that wishlist continuity was retained because the listing continuity was
   treated as confirmed,
5. that the price series may not represent a pure like-for-like unit comparison.

### Suggested Message Pattern

Example:

`Size changed from 3 cm to 5 cm on 2026-02-04. Wishlist continuity is treated as
continuous for this listing. Price evidence is still useful, but recent movement
may partly reflect the size change rather than a pure same-unit price move.`

Justification:

1. this is explicit,
2. it is conservative,
3. it does not imply more certainty than the data supports.

---

## Acceptance Criteria

The solution is acceptable only if all of the following are true.

### Identity And Table Output

1. a species appears once in the breeder table,
2. a species appears once in the dealer table,
3. the same species cannot receive two competing current headline classifications
   through size fragmentation alone.

### Column Contract

1. `Size (cm)` must contain exactly one of:
   1. a single size string such as `5`,
   2. a quoted comma-separated active size list such as `"3, 5"`,
   3. the most recent last-active size string such as `5` when the species is
      currently OUT but one recent lineage is still being interpreted.
2. `Price` must contain exactly one of:
   1. a standard value such as `£35.00 →`,
   2. a transition-affected standard value such as `£35.00 →` with a rendered
      warning icon,
   3. `Multiple active prices` when overlapping active variants prevent a single
      authoritative current price statement.
3. `Price History` must contain exactly one of:
   1. a lineage sparkline string,
   2. `-` when no defensible single lineage sparkline should be shown.
4. `Wishlist` must contain exactly one numeric count followed by pressure and
   delta symbols, for example `120 🔥 ↑` or `120 🔥 →`.
5. `Wishlist History` must contain exactly one of:
   1. a lineage sparkline string,
   2. `-` when continuity is ambiguous or overlapping active variants make a
      single momentum series unsafe.
6. rendered warning icons and tooltips are website-table concerns and are not
   encoded directly in the CSV string values shown below.

### Transition Handling

1. confirmed size transitions preserve wishlist continuity,
2. confirmed size transitions do not silently present price evidence as fully
   like-for-like,
3. ambiguous transitions are not merged silently,
4. ambiguous transitions do not recreate multiple current rows for the same
   species,
5. ambiguous transitions downgrade continuity-dependent price and momentum
   evidence instead,
6. overlapping active variants are not forced into one clean price series.

### UX And Explainability

1. the main table row remains readable,
2. transition caveats are visible through a warning affordance,
3. the species detail page explains the transition in plain text,
4. the user can understand why the row is treated as one species decision rather
   than multiple size decisions.

### Philosophy Alignment

1. supply remains the primary driver of breeder and dealer outcomes,
2. wishlist remains an amplifier or urgency modifier rather than a primary trigger,
3. price remains qualified where size makes it unsafe,
4. no continuity rule depends on unbounded inference.

---

## Normative Given / When / Then Acceptance Scenarios

The following scenarios are normative.

If implementation behavior differs from these examples, the implementation does
not satisfy this specification.

Conventions used in these examples:

1. the CSV blocks show the exact expected row values,
2. rendered warning icons and tooltips are listed separately because they are
   website affordances rather than CSV string content,
3. `·` in `Stock Availability` represents a space character for readability in
   Markdown examples.

### Scenario A: Confirmed size transition with preserved wishlist continuity

Given:

1. a species was last observed at `3 cm`,
2. the same scientific name later appears at `5 cm`,
3. the normalized product URL is unchanged,
4. the new size appears within 3 runs of the old size's final observation,
5. there is no same-run overlap between the old and new sizes,
6. recent wishlist counts rise from `100` to `120` across the confirmed handoff,
7. the species is currently OUT for 2 consecutive runs,
8. the most recent active price remains `£35.00`.

When:

1. the breeder row is generated,
2. the dealer row is generated,
3. the website tables are rendered.

Then the breeder row must be exactly:

```csv
Species,Size (cm),OOS,OOS Runs,Stock Pattern,Price,Price History,Wishlist,Wishlist History,Signal,Recommendation,Drivers
Example species confirmed,5,OUT,2,Emerging,£35.00 →,▄▄▄▄▄▄▄▄,120 🔥 ↑,▁▁▂▃▄▅▆█,🔥,Consider pairing — emerging scarcity with surging interest,Stock: Emerging (OOS 2 runs; currently OUT); Demand: Wishlist High + rising; Price: Stable; Size transition: confirmed 3→5 on 2026-02-04
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species confirmed,5,Medium,2.0,Moderate,£35.00 →,▄▄▄▄▄▄▄▄,120 🔥 ↑,▁▁▂▃▄▅▆█,██████··,🔥,"Actively seek breeders — surging demand, variable supply",Stock: Reliability Medium (Restock Moderate); Demand: Wishlist High + rising; Price: Stable; Size transition: confirmed 3→5 on 2026-02-04
```

Then the rendered website behavior must be exactly:

1. the `Price` cell shows a warning icon,
2. the `Price History` cell shows a warning icon,
3. the tooltip text is exactly:
   `Size changed from 3 cm to 5 cm on 2026-02-04. Wishlist continuity is treated as continuous for this listing. Price evidence is still useful, but recent movement may partly reflect the size change rather than a pure same-unit price move.`,
4. the `Wishlist` cell shows no warning icon,
5. the `Wishlist History` cell shows no warning icon.

### Scenario B: Ambiguous size transition without row fragmentation

Given:

1. a species was last observed at `3 cm`,
2. a later `5 cm` listing appears,
3. the scientific name is unchanged,
4. at least one confirmation rule for a clean handoff fails,
5. the most recent active wishlist count is `120`,
6. the species is currently OUT for 2 consecutive runs,
7. the most recent active price is `£35.00`.

When:

1. the breeder row is generated,
2. the dealer row is generated,
3. the website tables are rendered.

Then the breeder row must be exactly:

```csv
Species,Size (cm),OOS,OOS Runs,Stock Pattern,Price,Price History,Wishlist,Wishlist History,Signal,Recommendation,Drivers
Example species ambiguous,5,OUT,2,Emerging,£35.00 →,-,120 🔥 →,-,⚠️,Monitor closely — emerging scarcity; lineage continuity unconfirmed,Stock: Emerging (OOS 2 runs; currently OUT); Demand: Wishlist High (momentum neutralized; continuity unconfirmed); Price: Stable; Size transition: ambiguous 3→5 on 2026-02-04
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species ambiguous,5,Medium,2.0,Moderate,£35.00 →,-,120 🔥 →,-,██████··,⚠️,Buy opportunistically — lineage continuity unconfirmed,Stock: Reliability Medium (Restock Moderate); Demand: Wishlist High (momentum neutralized; continuity unconfirmed); Price: Stable; Size transition: ambiguous 3→5 on 2026-02-04
```

Then the rendered website behavior must be exactly:

1. there is still one breeder row for the species,
2. there is still one dealer row for the species,
3. the `Price` cell shows a warning icon,
4. the `Price History` cell shows a warning icon,
5. the tooltip text is exactly:
   `Size handoff from 3 cm to 5 cm could not be confirmed as one continuing listing. Wishlist continuity is not carried across the handoff. Price and momentum evidence are shown in a conservative downgraded state.`,
6. the `Wishlist` cell shows no warning icon,
7. the `Wishlist History` cell value is `-`.

### Scenario C: Overlapping active size variants in the current run

Given:

1. a species has `3 cm` and `5 cm` rows active in the current run,
2. the current `3 cm` price is `£25.00`,
3. the current `5 cm` price is `£35.00`,
4. the current `3 cm` wishlist count is `80`,
5. the current `5 cm` wishlist count is `120`,
6. the species is otherwise continuously present and therefore well supplied.

When:

1. the breeder row is generated,
2. the dealer row is generated,
3. the website tables are rendered.

Then the breeder row must be exactly:

```csv
Species,Size (cm),OOS,OOS Runs,Stock Pattern,Price,Price History,Wishlist,Wishlist History,Signal,Recommendation,Drivers
Example species overlap,"3, 5",IN,0,Always,Multiple active prices,-,120 🔥 →,-,⚠️,Watch closely — high latent demand across active size variants,Stock: Always (currently IN); Demand: Wishlist High (active variants overlap; delta neutralized); Price: Multiple active sizes
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species overlap,"3, 5",High,0.0,Fast,Multiple active prices,-,120 🔥 →,-,████████,❌,"Well-supplied, but monitor demand across active size variants",Stock: Reliability High (Restock Fast); Demand: Wishlist High (active variants overlap; delta neutralized); Price: Multiple active sizes
```

Then the rendered website behavior must be exactly:

1. the `Size (cm)` cell displays `3, 5`,
2. the `Price` cell shows a warning icon,
3. the `Price History` cell shows a warning icon,
4. the tooltip text is exactly:
   `This species has multiple active size variants in the current run (3 cm and 5 cm). The row remains species-level. Current wishlist context uses the highest active variant count without summing listings. Price evidence is not shown as one clean single-line series.`,
5. the `Wishlist` cell shows `120 🔥 →`,
6. the `Wishlist History` cell value is `-`.

### Historical Anchor: Chilobrachys sp. "South Thai"

The observed `3 cm` to `5 cm` handoff for `Chilobrachys sp. "South Thai"`
should be interpreted according to Scenario A if the continuity checks confirm a
clean handoff, or Scenario B if those continuity checks do not all pass.

It must not revert to multiple current breeder or dealer rows.

---

## Non-Goals

This document does not require:

1. changing the taxonomy labels themselves,
2. collapsing all evidence to species-level and ignoring size,
3. summing wishlist counts across multiple concurrent listings without explicit
   justification,
4. making price the primary driver in dealer analysis,
5. introducing a full app-style routing model for species pages.

---

## Final Recommendation

The recommended product policy is:

1. one species row per table,
2. one species detail page per species,
3. a shared confirmed-transition layer used by both breeder and dealer analysis,
4. wishlist continuity across confirmed handoffs,
5. price evidence preserved but qualified when a recent size transition affects
   interpretation,
6. explicit handling of overlapping active variants rather than silent forced
   aggregation.

This is the simplest solution that:

1. resolves the contradictory row problem,
2. stays conservative,
3. preserves size-aware price interpretation,
4. matches how users understand the species,
5. fully closes the open policy gaps left by
   `SIZE_VARIANT_IDENTITY_RECOMMENDATION.md`.