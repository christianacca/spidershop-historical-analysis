# Newly Observed Taxonomy Recommendation

## Purpose

This document proposes an initial taxonomy extension for stock-pattern classification: `Newly Observed`.

The goal is to handle species that appear in the current run after never being seen in prior recorded history, without forcing them into misleading existing categories such as `Always` or `Emerging`.

This is an initial recommendation document, not a final implementation spec. It is intended to be refined.

It also captures the initial UI and content recommendations for how this state should appear in:

1. the breeder table,
2. the dealer table,
3. species detail pages.

---

## Problem Statement

The current breeder stock-pattern taxonomy is:

1. `Sustained`
2. `Emerging`
3. `Cyclical`
4. `Always`

This taxonomy breaks down for species that:

1. were absent in all earlier recorded runs,
2. are visible in the latest run,
3. may also be visible in the immediately previous run.

In that case, the current logic can classify the species as `Always` simply because it is in stock now and has no active out-of-stock streak.

That is not semantically correct.

`Always` implies stable, repeated availability across the historical window. A newly first-seen species does not satisfy that condition.

---

## Why Existing Patterns Are Insufficient

### `Always`

`Always` currently implies:

1. consistent availability,
2. no meaningful scarcity pattern,
3. frequent compatibility with `❌ Avoid` on the breeder side.

For a first-seen species, this is overconfident and can create a false negative breeding signal.

### `Emerging`

`Emerging` implies real consecutive absence inside the observed window.

For a first-seen species, pre-first-seen absence is ambiguous:

1. it may have been out of stock for a long time,
2. it may be newly introduced to the site,
3. it may have existed under a different naming or listing pattern,
4. earlier history may simply not contain enough evidence.

Treating that ambiguity as confirmed scarcity would be too aggressive.

### `Cyclical`

`Cyclical` implies repeated disappear / reappear behaviour. That evidence does not exist for a first-seen species.

### `Sustained`

`Sustained` requires strong, repeated scarcity evidence and is clearly not the right category.

---

## Recommendation

Add a new stock-pattern value:

`Newly Observed`

Meaning:

"This species is present in the current run, but there is not yet enough historical evidence to classify it as stable supply, real scarcity, or cyclical supply."

This is a conservative taxonomy addition. It avoids two failure modes:

1. falsely dismissing the species as oversupplied,
2. falsely escalating the species as a hot scarcity opportunity.

---

## Proposed Semantics

`Newly Observed` should mean all of the following:

1. the species is present in the current run,
2. the species has insufficient historical coverage to infer a stable supply pattern,
3. pre-first-seen absence is treated as ambiguous rather than true out-of-stock evidence.

This category is about epistemic uncertainty, not supply abundance.

---

## Conservative Interpretation

The project already prefers signal stability over early detection.

Under that philosophy, a first-seen or very-recently-first-seen species should be treated as:

1. not yet proven scarce,
2. not yet proven oversupplied,
3. waiting for more evidence.

That makes `Newly Observed` a hold-state, not a directional claim.

---

## Initial Breeder Recommendation Mapping

Initial recommendation for breeder-side signal mapping:

1. Stock Pattern: `Newly Observed`
2. Signal: `⚠️`
3. Recommendation text: `Monitor closely — newly observed, limited history (observed in 2/14 runs)`

Rationale:

1. `🔥` is too strong because scarcity is not yet proven.
2. `❌` is too strong because stable availability is not yet proven.
3. `⚠️` best matches the current conservative intent.

Observation coverage should be used here as a confidence qualifier, not as the
primary driver of the recommendation.

---

## Initial Dealer Recommendation Mapping

The dealer table does not currently use the breeder stock-pattern taxonomy as its primary classification system.

Its main concepts are:

1. stock reliability,
2. average out-of-stock duration,
3. restock speed,
4. dealer risk.

For that reason, `Newly Observed` should not initially replace the dealer-side reliability model.

Instead:

1. keep the existing dealer risk model supply-first,
2. expose first-observation context so users can see why a species has limited history,
3. avoid interpreting sparse observation history as evidence of healthy supply.

Observation coverage should factor into dealer interpretation mainly as a confidence
qualifier.

That means:

1. it can soften recommendation text when history is thin,
2. it can explain low-confidence reliability conclusions,
3. it should not become the primary driver of dealer risk.

---

## Initial Sort Recommendation

Within breeder sorting, `Newly Observed` rows should rank:

1. below evidence-backed `⚠️ Watch` rows such as true `Emerging` or `Cyclical` cases,
2. above true `❌ Avoid` rows that are genuinely `Always` / oversupplied.

If the current sort implementation only sorts by signal, wishlist count, and a tertiary metric, then `Newly Observed` should initially live at the bottom of the `⚠️` bucket.

---

## Suggested Qualification Rules

The exact rule can be refined later, but an initial conservative rule could be:

Classify as `Newly Observed` when:

1. the species is present in the current run,
2. it was absent in all runs before its first recorded appearance,
3. the observed presence history is too short to justify `Always`, `Cyclical`, or scarcity-driven labels.

Potential initial thresholds to refine later:

1. present in 1 run only,
2. present in the latest 2 consecutive runs but absent in all earlier runs,
3. total observed run count below a chosen minimum confidence threshold.

Recommended planning assumption:

1. classify a species as `Newly Observed` when it is present in the current run,
2. it has been observed in no more than the latest 2 consecutive runs,
3. it was absent in all earlier recorded runs.

Recommended exit rule:

1. once a species has been observed across 3 runs, it stops being eligible for `Newly Observed`,
2. after that point it should be evaluated using the normal stock-pattern taxonomy,
3. pre-first-seen absence should still not be retroactively treated as confirmed out-of-stock evidence.

---

## UI Recommendations By Surface

### Breeder Table

The breeder table is the primary place where `Newly Observed` should be visible as taxonomy.

Initial recommendation:

1. add `Newly Observed` to the stock-pattern filter values,
2. render the row with signal `⚠️`,
3. use recommendation text centered on insufficient history,
4. sort these rows below evidence-backed `⚠️` rows,
5. avoid presenting them as `Always` or oversupplied.

Recommended supporting metadata:

1. include `First observed in dataset` in tooltip or supporting text,
2. include compact observation coverage such as `2/14 runs` where practical.

If table width is limited, coverage metadata is more immediately useful than a full date column.

Recommendation-text guidance for breeder rows:

1. use observation coverage directly in short recommendation text mainly for `Newly Observed` rows,
2. keep the recommendation action-oriented, with coverage as a suffix or qualifier,
3. do not make coverage standard short-text content for all `⚠️`, `🔥`, or `❌` rows,
4. do not let coverage replace stock-state language such as `IN`, `OUT`, or `OOS Runs`.

Recommended pattern:

1. recommendation text explains what to do,
2. stock-state fields and drivers explain what is happening,
3. observation coverage explains how much confidence to place in the interpretation.

Example recommendation text for `Newly Observed`:

`Monitor closely — newly observed, limited history (observed in 2/14 runs)`

Example driver text can still separately describe stock state, such as `currently IN`
or `currently OUT`.

### Dealer Table

The dealer table should receive supporting context, but not necessarily the same taxonomy treatment in the first pass.

Initial recommendation:

1. keep dealer risk driven by reliability and restock metrics,
2. add first-observation context to reduce overconfidence when history is sparse,
3. prefer compact observation metadata over a wide always-visible date column.

Recommended presentation options:

1. add `Observed` or `Coverage` as a compact field such as `2/14`,
2. include `First observed in dataset` in driver text or tooltip,
3. avoid treating early low coverage as proof of stable supply.

Recommendation-text guidance for dealer rows:

1. use observation coverage in short recommendation text mainly for sparse-history cases,
2. use it to reduce overconfidence rather than to drive the recommendation,
3. keep reliability, restock speed, and demand as the primary recommendation inputs,
4. do not use coverage as a replacement for dealer-side supply metrics.

Recommended pattern:

1. dealer recommendation text explains what to do,
2. dealer metrics explain what the supply pattern currently looks like,
3. observation coverage explains how much confidence to place in the conclusion.

Example sparse-history dealer recommendation text:

`Monitor supply — limited history (observed in 2/14 runs)`

If a dealer row has strong evidence, coverage usually belongs in tooltip or detail
context rather than in the short recommendation sentence.

### Species Detail Pages

Species detail pages are the best place to explain `Newly Observed` in full.

Initial recommendation:

1. show `First observed in dataset` prominently,
2. show `Observed in X/Y runs`,
3. explain that pre-first-seen absence is ambiguous,
4. if the species is tagged `Newly Observed`, explain that the label reflects insufficient historical evidence rather than proven scarcity or abundance.

Dealer perspective on the species detail page should also use observation coverage as
an explanation layer.

That is, the dealer view should make it clear whether:

1. supply is genuinely unreliable,
2. or the model is working with sparse evidence and should be interpreted cautiously.

Observation coverage should therefore be visible in dealer species-detail context even
when it is not part of the short dealer recommendation text.

Recommended species-detail metadata block:

1. `First observed in dataset`
2. `Latest observed`
3. `Observed in X/Y runs`
4. optional `Observation coverage: low / medium / high`

This page should carry the explanatory burden so table rows can stay compact.

---

## Naming Recommendation For Observation Metadata

If first-observation metadata is added to any surface, prefer labels that make the data source explicit.

Recommended labels:

1. `First observed in dataset`
2. `Observed in X/Y runs`

Avoid ambiguous labels such as:

1. `First seen`
2. `New species`
3. `Introduced`

Those alternatives risk implying more than the data actually proves.

---

## Non-Goals

This proposal does not yet decide:

1. whether `Newly Observed` should later split into sub-cases such as first-seen vs recently established,
2. exact final UI copy for every page surface,
3. exact filter ordering once the new pattern is added to production UI,
4. exact CSV backward-compatibility handling.

---

## Expected Benefits

Adding `Newly Observed` should improve the model in the following ways:

1. reduces false `Always` classifications,
2. prevents newly seen species from being prematurely labeled oversupplied,
3. makes the breeder table align better with the project’s conservative analysis philosophy,
4. creates a cleaner explanation for users when a species lacks enough history,
5. separates uncertainty from abundance.

---

## Risks And Tradeoffs

### Added complexity

The taxonomy becomes five stock-pattern values instead of four.

### UI and filter changes

Any stock-pattern filter UI, count display, legends, tooltips, and tests will need to acknowledge the new category.

### Transitional ambiguity

Some species near the threshold may move between `Newly Observed` and `Always` as more runs accumulate.

This is acceptable as long as the threshold is documented and deterministic.

---

## Decision Points For Planning

This section states the recommended decisions the planning phase should use as the
default implementation assumptions.

### 1. Qualification Threshold

Decision point:

When should a species qualify as `Newly Observed`?

Recommendation:

1. qualify it when it is present in the current run,
2. it has been observed in no more than the latest 2 consecutive runs,
3. all earlier recorded runs are absent.

Justification:

1. 1 run alone is too narrow and misses the exact false-`Always` problem,
2. more than 2 runs starts to look like normal observed supply rather than pure ambiguity,
3. this keeps the rule simple, deterministic, and conservative.

### 2. Exit Rule

Decision point:

When should a species stop being `Newly Observed`?

Recommendation:

1. after a species has been observed across 3 runs,
2. move it into normal stock-pattern evaluation,
3. do not retroactively convert pre-first-seen absence into confirmed OOS evidence.

Justification:

1. the category should be temporary,
2. three observations is enough to stop treating the row as purely unknown,
3. this preserves conservative interpretation of historical absence.

### 3. Taxonomy Scope

Decision point:

Should `Newly Observed` be a breeder-only taxonomy value or shared directly with dealer classification?

Recommendation:

1. make it a breeder stock-pattern value in phase 1,
2. do not add it as a primary dealer taxonomy value in phase 1,
3. use observation coverage as confidence context on the dealer side instead.

Justification:

1. breeder logic is where the false-`Always` problem is most acute,
2. dealer logic already has a separate supply-first reliability model,
3. this limits implementation scope while still improving dealer explainability.

### 4. Signal Mapping

Decision point:

What signal should `Newly Observed` map to?

Recommendation:

1. always map `Newly Observed` to `⚠️` in phase 1.

Justification:

1. `🔥` is too strong for sparse evidence,
2. `❌` is too strong for sparse evidence,
3. `⚠️` correctly communicates uncertainty plus monitor-worthy status.

### 5. Breeder Sort Treatment

Decision point:

Where should `Newly Observed` rows sort relative to other breeder rows?

Recommendation:

1. place them at the bottom of the `⚠️` bucket,
2. below evidence-backed `Emerging` and `Cyclical` watch rows,
3. above true `❌ Avoid` rows.

Justification:

1. it preserves conservative urgency ordering,
2. it avoids overstating ambiguous rows,
3. it still prevents them from being buried among genuinely oversupplied species.

### 6. Breeder Recommendation Text Policy

Decision point:

Should observation coverage appear in breeder recommendation text?

Recommendation:

1. yes, but mainly for `Newly Observed` rows,
2. use it as a confidence qualifier,
3. keep stock-state fields and driver text separate.

Recommended form:

`Monitor closely — newly observed, limited history (observed in 2/14 runs)`

Justification:

1. this makes the uncertainty legible,
2. it avoids making coverage standard text for every row,
3. it preserves the distinction between recommendation, stock state, and evidence depth.

### 7. Dealer Recommendation Text Policy

Decision point:

Should observation coverage appear in dealer recommendation text?

Recommendation:

1. yes, but only for sparse-history cases,
2. use it to soften certainty,
3. do not use it as a primary reason for dealer risk.

Example:

`Monitor supply — limited history (observed in 2/14 runs)`

Justification:

1. dealer recommendations should remain driven by reliability and restock metrics,
2. sparse history still needs to be visible so low-confidence conclusions do not sound overconfident,
3. this keeps the dealer model supply-first.

### 8. Observation Metadata In Tables

Decision point:

How should first-observation context appear in breeder and dealer tables?

Recommendation:

1. prefer compact coverage metadata such as `Observed 2/14`,
2. prefer tooltip or driver text for `First observed in dataset`,
3. avoid adding a wide always-visible date column in phase 1.

Justification:

1. the tables are already dense,
2. compact coverage is more immediately interpretable than a raw date,
3. this yields the context benefit without degrading table scan speed.

### 9. Species Detail Page Metadata

Decision point:

What should species detail pages show?

Recommendation:

1. show `First observed in dataset`,
2. show `Latest observed`,
3. show `Observed in X/Y runs`,
4. optionally show `Observation coverage: low / medium / high`.

Justification:

1. species detail pages are the best place to carry explanatory context,
2. this gives users the timeline and confidence information behind the table row,
3. it keeps the dense summary tables simpler.

### 10. Explanation Wording

Decision point:

Should the model explicitly say that pre-first-seen absence is ambiguous?

Recommendation:

1. yes, in species detail explanations and supporting tooltip/driver context for `Newly Observed` rows.

Justification:

1. this is the core analytical distinction behind the new taxonomy,
2. without it, users are likely to misread low-history absence as real OOS evidence,
3. the wording improves trust and interpretability.

---

## Initial Recommendation Summary

Recommended planning baseline:

1. introduce `Newly Observed` as a new breeder stock-pattern taxonomy value,
2. qualify it for species seen in the current run and no more than the latest 2 consecutive runs,
3. end the category after 3 observations and then use the normal taxonomy,
4. map it to a conservative `⚠️` signal,
5. sort it at the bottom of the `⚠️` bucket,
6. use observation coverage as a confidence qualifier in breeder and sparse-history dealer text,
7. use compact coverage in tables and fuller first-observation metadata on species detail pages,
8. refine only the secondary UI and future taxonomy-splitting questions during planning.

This preserves the project’s conservative stance:

1. do not jump to `🔥` on sparse evidence,
2. do not jump to `❌` on sparse evidence,
3. make uncertainty explicit in the taxonomy rather than hiding it inside `Always`.
