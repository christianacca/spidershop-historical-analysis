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

## Normalization And Time Definitions

### URL normalization

For the purposes of confirmed-transition detection, `normalized product URL`
means the result of applying all of the following transformations to `page_url`:

1. trim leading and trailing whitespace,
2. parse the URL and discard any query string,
3. discard any fragment,
4. lowercase the scheme and host,
5. strip a leading `www.` from the host,
6. collapse duplicate `/` characters in the path,
7. strip exactly one trailing slash from the path,
8. preserve the remaining path string as-is.

Examples:

1. `HTTPS://www.thespidershop.co.uk/product/foo/?bar=1#frag` normalizes to
   `https://thespidershop.co.uk/product/foo`,
2. `https://thespidershop.co.uk/product/foo/` normalizes to
   `https://thespidershop.co.uk/product/foo`.

This specification treats normalized product URL equality as the strongest
positive continuity signal, not as a universal guarantee that the shop will
never change URL structure.

If URL structure changes in a way that breaks equality, the transition falls to
the ambiguous fallback unless a future revision of this specification adds a new
explicit secondary continuity rule.

### Historical rows without usable product URLs

Rows with missing URLs, blank URLs, or non-product URLs cannot satisfy the
confirmed-transition URL gate.

Transitions involving such rows are therefore ambiguous by default.

This is acceptable under the conservative design because the ambiguous fallback:

1. preserves one species row,
2. preserves species-level supply interpretation,
3. only downgrades continuity-dependent evidence.

### Run definition

For all rules in this document, a `run` means one successful scrape recorded in
`spidershop_spiderlings_history.csv`.

The transition window and other bounded lookbacks are counted in successful
history runs, not in calendar weeks.

Therefore:

1. failed or skipped calendar weeks do not consume lookback slots,
2. a `3-run` transition window means the next 3 successful recorded scrapes.

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

Transition-window clarification:

1. the 3-run window is counted in successful recorded runs,
2. a failed or skipped week does not consume one of the 3 available slots.

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

Signal clarification:

1. ambiguous transition status does not directly downgrade a breeder or dealer
   headline by itself,
2. it can still cause a lower headline outcome indirectly when the higher
   outcome depended on continuity-based evidence that is no longer allowed to be
   carried across the ambiguous handoff,
3. in those cases, the downgrade is caused by loss of qualifying evidence, not
   by a second hidden signal rule.

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

### Decision 3A: Species-level supply timeline

Requirement:

1. species-level supply metrics must have an explicit aggregation rule.

Proposed solution:

1. build a species-level presence timeline across successful runs,
2. a species is considered present in a run if any size variant for that species
   is present in that run,
3. species-level OOS runs are counted as the number of consecutive absent
   species-level runs ending at the current run,
4. species-level OOS runs are not additive across lineages,
5. breeder stock pattern is recomputed from the species-level presence timeline,
   not from a retired-size lineage in isolation,
6. dealer stock reliability is computed from the species-level presence ratio on
   that timeline,
7. dealer average OOS duration and restock speed are computed from species-level
   absence events on that timeline.

Worked clarification:

1. if size `3` had 1 OOS run before size `5` appeared,
2. and size `5` later has 2 current OOS runs,
3. the species-level current OOS run count is `2` if the species was present in
   between,
4. because OOS runs are counted from the current species-level absence streak,
   not by adding retired-lineage streaks.

Justification:

1. this preserves one current species-level supply interpretation,
2. it prevents retired-size isolation from manufacturing contradictory scarcity
   states,
3. it gives dealer aggregation a deterministic, explainable basis.

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

Price sparkline construction rule:

1. `Price History` represents the last 8 successful runs,
2. for a confirmed transition, the sparkline stitches pre-transition old-size
   prices and post-transition new-size prices into one chronological lineage
   window,
3. if multiple sequential confirmed transitions fall within that 8-run window
   and belong to one defensible continuing lineage, the sparkline may stitch
   across all of them in chronological order,
4. the hidden transition metadata still reports only the most recent transition
   event even when the stitched sparkline includes earlier confirmed handoffs,
5. for a non-transition species, the sparkline preserves current behavior
   unchanged,
6. for ambiguous transitions and multi-variant cases, `Price History` is `-`
   unless a single lineage can still be justified conservatively.

Additional wishlist rule for overlapping active variants:

1. if multiple size variants are active in the current run, the row-level current
   wishlist count must equal the highest raw current-run `wishlist_count` among
   the active variants,
2. the row-level wishlist delta must downgrade to `→`,
3. the row-level wishlist history must downgrade to `-` unless a single lineage
   can still be justified conservatively.

OUT-state wishlist carryover clarification:

1. if the species is currently OUT and one single most-recent lineage can still
   be identified conservatively within the standard 5-run OOS carryover window,
   that lineage's last known wishlist count is used,
2. if the species is currently OUT and no single most-recent lineage can be
   identified conservatively, the row-level wishlist count is `0`,
3. in that ambiguous OUT case, wishlist delta must be `→` and wishlist history
   must be `-`.

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

Breeder rule preservation:

1. always-available breeder cases remain `❌` even when wishlist demand is high,
   including overlap cases,
2. high wishlist may still appear in supporting evidence, but it must not elevate
   an `Always` breeder row above `❌`.

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

## Output Schema And Metadata Columns

### Public CSV schema

The public breeder and dealer CSV schemas remain the current public schemas.

No public column rename or merge is introduced by this feature.

The scenario examples in this document therefore reflect the existing public CSV
shape rather than a new flattened export format.

### Hidden metadata columns

This feature requires additional hidden metadata columns appended after
`Drivers` in both breeder and dealer CSV outputs.

Required hidden metadata columns:

1. `Lineage Status`
2. `Previous Size (cm)`
3. `Current Active Size (cm)`
4. `Transition Date`
5. `Price Evidence State`
6. `Wishlist Evidence State`
7. `Transition Message`

Allowed values:

#### `Lineage Status`

1. `none`
2. `confirmed-transition`
3. `ambiguous-transition`
4. `multi-variant`

#### `Price Evidence State`

1. `standard`
2. `transition-affected`
3. `neutralized`
4. `multi-variant`

#### `Wishlist Evidence State`

1. `standard`
2. `carried-across-transition`
3. `neutralized-ambiguous`
4. `max-active-variant`

### Transition metadata derivation rules

The hidden transition metadata columns describe the single most recent
transition event that is relevant to the row's current interpretive state.

Required derivation rules:

1. `Previous Size (cm)` is the immediately preceding size from that most recent
   transition event, not the oldest historical size ever seen for the species,
2. `Current Active Size (cm)` is:
   1. the new size from that most recent transition event when the row is in
      `confirmed-transition` or `ambiguous-transition` state,
   2. the comma-separated ascending active-size list when the row is in
      `multi-variant` state,
3. `Transition Date` is the date portion of `scrape_datetime`, formatted as
   `YYYY-MM-DD`, from the first successful recorded run in which the new size of
   that most recent transition event was observed,
4. this `Transition Date` derivation rule applies to both
   `confirmed-transition` and `ambiguous-transition` states,
5. when the current row state is `multi-variant`, `Previous Size (cm)` and
   `Transition Date` are blank because the row is not claiming one clean current
   handoff event,
6. when the current row state is `none`, `Previous Size (cm)` and
   `Transition Date` are blank.

Sequential-transition clarification:

1. if a lineage undergoes multiple sequential confirmed transitions such as
   `3 -> 5 -> 7`, the hidden metadata columns report only the most recent event,
   so `Previous Size (cm)` is `5`, `Current Active Size (cm)` is `7`, and
   `Transition Date` is the first observed `7` date,
2. earlier confirmed transitions remain part of historical lineage evidence but
   are not separately surfaced in these current-row metadata columns,
3. if a future revision needs full transition history, it must add a separate
   history structure rather than overload the current-row metadata fields.

Current-state precedence rule:

1. `multi-variant` takes precedence over any historical confirmed or ambiguous
   handoff state,
2. `ambiguous-transition` takes precedence over `confirmed-transition` when the
   most recent handoff cannot be confirmed,
3. `confirmed-transition` applies only when the most recent relevant handoff is
   confirmed and the species is not currently in a `multi-variant` state,
4. `none` applies only when no relevant recent transition state exists,
5. for example, if `3 -> 5` was previously a confirmed transition but the
   current run has concurrent `5 cm` and `7 cm` listings, `Lineage Status` is
   `multi-variant` and the current-row transition fields are blank.

Website generator requirement:

1. warning icons and tooltips must be driven from these hidden metadata columns,
2. the website must not be required to re-derive lineage logic from history CSV
   during rendering,
3. `Transition Message` is the source of truth for the tooltip copy,
4. the species detail page may reuse `Transition Message` for a banner and may
   use the structured metadata columns for richer presentation.

Compatibility note:

1. existing tests and consumers for public column names remain valid,
2. tests that assert the full exported field list must be updated to account for
   the appended hidden metadata columns.

### Drivers column

`Drivers` is not new.

It is an existing hidden CSV column and remains required.

Required format:

1. semicolon-separated plain-English clauses,
2. clause order must be `Stock`, then `Demand`, then `Price`,
3. optional transition wording may be appended after those clauses,
4. wording must remain deterministic and programmatically generated.

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
   4. `—` when the species is currently OUT and no single recent lineage can be
      identified within the standard 5-run OOS carryover window,
   5. in an ambiguous transition case, the most recent active size is still shown
      if it is uniquely most recent within that same 5-run window,
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
      currently OUT but one recent lineage is still being interpreted,
   4. `—` when the species is currently OUT and no single recent lineage can be
      identified conservatively.
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
6. `Drivers` must contain deterministic semicolon-separated explanatory text.
7. hidden metadata columns must exist after `Drivers` exactly as specified in
   `Output Schema And Metadata Columns`.
8. rendered warning icons and tooltips are website-table concerns and are not
   encoded directly in the public CSV string values shown below.

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

### Stable Non-Transition Species

1. species with no size transition history preserve current behavior unchanged,
2. for those species, `Lineage Status` is `none`,
3. for those species, `Price Evidence State` is `standard`,
4. for those species, `Wishlist Evidence State` is `standard`,
5. for those species, `Transition Message` is blank.

### Delivery Sequencing

1. the transition detection and metadata layer must be implemented and tested in
   isolation first,
2. an intermediate validation phase is acceptable in which hidden lineage
   metadata is computed and audited against real history while public analysis is
   still species-size keyed,
3. that intermediate validation phase is not an acceptable final shipped state,
4. the feature is only complete when table row identity becomes species-level and
   the acceptance scenarios in this document pass.

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

Then the hidden breeder metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
confirmed-transition,3,5,2026-02-04,transition-affected,carried-across-transition,Size changed from 3 cm to 5 cm on 2026-02-04. Wishlist continuity is treated as continuous for this listing. Price evidence is still useful, but recent movement may partly reflect the size change rather than a pure same-unit price move.
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species confirmed,5,Medium,2.0,Moderate,£35.00 →,▄▄▄▄▄▄▄▄,120 🔥 ↑,▁▁▂▃▄▅▆█,██████··,🔥,"Actively seek breeders — surging demand, variable supply",Stock: Reliability Medium (Restock Moderate); Demand: Wishlist High + rising; Price: Stable; Size transition: confirmed 3→5 on 2026-02-04
```

Then the hidden dealer metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
confirmed-transition,3,5,2026-02-04,transition-affected,carried-across-transition,Size changed from 3 cm to 5 cm on 2026-02-04. Wishlist continuity is treated as continuous for this listing. Price evidence is still useful, but recent movement may partly reflect the size change rather than a pure same-unit price move.
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

Then the hidden breeder metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
ambiguous-transition,3,5,2026-02-04,neutralized,neutralized-ambiguous,Size handoff from 3 cm to 5 cm could not be confirmed as one continuing listing. Wishlist continuity is not carried across the handoff. Price and momentum evidence are shown in a conservative downgraded state.
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species ambiguous,5,Medium,2.0,Moderate,£35.00 →,-,120 🔥 →,-,██████··,⚠️,Buy opportunistically — lineage continuity unconfirmed,Stock: Reliability Medium (Restock Moderate); Demand: Wishlist High (momentum neutralized; continuity unconfirmed); Price: Stable; Size transition: ambiguous 3→5 on 2026-02-04
```

Then the hidden dealer metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
ambiguous-transition,3,5,2026-02-04,neutralized,neutralized-ambiguous,Size handoff from 3 cm to 5 cm could not be confirmed as one continuing listing. Wishlist continuity is not carried across the handoff. Price and momentum evidence are shown in a conservative downgraded state.
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
Example species overlap,"3, 5",IN,0,Always,Multiple active prices,-,120 🔥 →,-,❌,Avoid for profit — oversupplied,Stock: Always (currently IN); Demand: Wishlist High (active variants overlap; delta neutralized); Price: Multiple active sizes
```

Then the hidden breeder metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
multi-variant,,"3, 5",,multi-variant,max-active-variant,This species has multiple active size variants in the current run (3 cm and 5 cm). The row remains species-level. Current wishlist context uses the highest active variant count without summing listings. Price evidence is not shown as one clean single-line series.
```

Then the dealer row must be exactly:

```csv
Species,Size (cm),Stock Reliability,Avg OOS Duration,Restock Speed,Price,Price History,Wishlist,Wishlist History,Stock Availability,Dealer Risk,Dealer Recommendation,Drivers
Example species overlap,"3, 5",High,0.0,Fast,Multiple active prices,-,120 🔥 →,-,████████,❌,"Well-supplied, but monitor demand across active size variants",Stock: Reliability High (Restock Fast); Demand: Wishlist High (active variants overlap; delta neutralized); Price: Multiple active sizes
```

Then the hidden dealer metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
multi-variant,,"3, 5",,multi-variant,max-active-variant,This species has multiple active size variants in the current run (3 cm and 5 cm). The row remains species-level. Current wishlist context uses the highest active variant count without summing listings. Price evidence is not shown as one clean single-line series.
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

### Scenario D: Stable species with no transition history

Given:

1. a species has only one historically observed size variant,
2. no size transition metadata exists for that species,
3. current breeder and dealer calculations are otherwise unchanged.

When:

1. the breeder row is generated,
2. the dealer row is generated.

Then:

1. all public column values must match the pre-feature behavior exactly,
2. the hidden metadata columns must be exactly:

```csv
Lineage Status,Previous Size (cm),Current Active Size (cm),Transition Date,Price Evidence State,Wishlist Evidence State,Transition Message
none,,<current size>,,standard,standard,
```

3. no warning icon is rendered for `Price` or `Price History`,
4. no species-detail transition banner is rendered.

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