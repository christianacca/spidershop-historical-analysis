# Size Variant Identity Recommendation

## Purpose

This document captures a separate recommendation from the `Newly Observed`
taxonomy proposal.

The issue here is not taxonomy wording. It is entity identity.

The current analysis generally treats a row as identified by:

1. scientific name,
2. size.

That means a newly listed size variant of an already well-observed species can be
treated as a genuinely new analytical entity.

This document proposes how to think about and address that problem.

---

## Why This Is Separate From The Taxonomy Proposal

The `Newly Observed` taxonomy proposal answers this question:

1. what label should we give sparse-history cases?

This identity issue answers a different question:

1. what counts as the same thing across history?

If identity is wrong, taxonomy will inherit distorted inputs.

So this should be treated as an adjacent but independent recommendation.

---

## Current Behavior

The current logic keys most analysis by `(scientific_name, size_cm)`.

As a result, if the shop starts listing a known species at a new size, the system
can treat that size as:

1. newly observed,
2. thin-history,
3. disconnected from the species' broader historical evidence.

That affects breeder, dealer, wishlist, price, and species-detail behavior.

---

## Problem Statement

When a new entry is first seen, there are at least two very different realities:

1. it is a genuinely new species listing,
2. it is an already known species offered at a different size.

The current identity model does not distinguish those cases well enough.

That can overstate novelty and underuse valid species-level context.

---

## Practical Consequences

### Breeder Perspective

A new size variant can look newly observed even if the species has long history.

That may:

1. create overly cautious `Newly Observed` treatment,
2. suppress meaningful species-level continuity,
3. make a familiar species look less understood than it really is.

### Dealer Perspective

A new size variant can appear to have weak reliability simply because that exact
size has limited observations.

That may:

1. exaggerate uncertainty,
2. distort reliability interpretation,
3. make low evidence look like poor supply rather than a size-specific listing change.

### Wishlist And Price Context

Demand and price continuity may also reset for the new size variant, even where the
species has established market history.

That can fragment a species-level story into size-level silos.

### Species Detail Pages

Species detail pages are conceptually species-oriented, but much of the underlying
data is species-plus-size oriented.

That creates a mismatch between:

1. how users think about a species,
2. how the analysis currently tracks it.

---

## Recommendation

Treat this as an identity-layer issue with a two-level model:

1. species-size = trading unit,
2. species = confidence and context layer.

This means the system should keep size-specific analysis where size actually matters,
but should not lose species-level historical context when interpreting novelty.

---

## Recommended Conceptual Model

### Level 1: Species-Size Identity

Continue using species plus size when the question is about the concrete listing:

1. exact price point,
2. exact stock line,
3. exact displayed size variant.

This preserves size-specific trading relevance.

### Level 2: Species-Level Context

Also compute species-level context across all sizes for:

1. first-observed confidence,
2. observation depth,
3. broad supply familiarity,
4. broad market familiarity.

This prevents a newly listed size from being interpreted as a totally unknown species
when it is not.

---

## Initial Recommendation For Analysis

When a species-size row is first seen, the model should ask both:

1. is this exact species-size line new?
2. is the parent species already well observed across any size?

Those answers should influence interpretation differently.

Suggested handling:

1. exact species-size new + species also new = true novelty,
2. exact species-size new + species well observed = new size variant of known species,
3. exact species-size well observed = normal continuity case.

---

## Recommended Interaction With `Newly Observed`

This identity recommendation should inform the `Newly Observed` taxonomy, but not be
merged into it.

Suggested relationship:

1. `Newly Observed` remains the row-level label,
2. species-level context determines whether that label means truly unknown vs new size variant,
3. recommendation text and supporting metadata should reflect that distinction.

That allows the taxonomy to stay simple while the identity logic becomes smarter.

---

## Initial UX Recommendation

If the system later distinguishes new size variant from truly new species, surfaces
should explain that explicitly.

### Breeder Table

Possible supporting text:

1. `newly observed size variant of known species`,
2. `limited size history; species well observed overall`.

### Dealer Table

Possible supporting text:

1. `limited size history`,
2. `species has broader observation history`.

### Species Detail Page

This is the best place to expose both layers:

1. first observed for this size,
2. first observed for this species,
3. observed in X/Y runs for this size,
4. observed in X/Y runs for this species.

---

## Non-Goals

This document does not yet decide:

1. whether all metrics should gain species-level aggregation,
2. whether breeder and dealer should use the same species-level rollups,
3. how to normalize borderline size strings,
4. exact implementation mechanics for multi-size aggregation,
5. whether species pages should remain slugged by species only or become size-specific.

---

## Expected Benefits

Addressing this identity issue should:

1. reduce false novelty,
2. preserve valid species-level history,
3. improve interpretation of new size variants,
4. make `Newly Observed` more accurate,
5. improve trust in breeder and dealer recommendations.

---

## Risks And Tradeoffs

### Added model complexity

The analysis would no longer rely on a single identity layer.

### Potential user confusion

If the UI is not explicit, users may not understand the difference between:

1. this size is new,
2. this species is new.

### Aggregation choices matter

Species-level rollups can hide meaningful size-specific differences if used too
aggressively.

---

## Open Questions For Refinement

1. Which metrics should remain strictly species-size only?
2. Which metrics should gain species-level context?
3. Should the `Newly Observed` label be modified when a species is already well observed in another size?
4. How should recommendation text distinguish `new size variant` from `truly new species`?
5. Should species detail pages show both size-level and species-level observation coverage by default?
6. Should website routing for species detail pages remain species-only if analysis stays size-aware?

---

## Initial Recommendation Summary

Recommended first step:

1. treat size-variant identity as a separate analysis issue from taxonomy,
2. keep species-size as the trading unit,
3. add species-level historical context as an interpretation layer,
4. use that layer to distinguish true novelty from a newly listed size variant,
5. refine how taxonomy and UI should respond after the identity model is clarified.
