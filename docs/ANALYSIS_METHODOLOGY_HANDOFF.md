# Analysis Methodology Handoff

## Mission

Implement a new static methodology section for the breeder and dealer analysis pages so users can understand:

- what thresholds are used
- how the rules are ordered
- why a row becomes Hot, Watch, Avoid, High Risk, Moderate Risk, or Low Risk
- how edge cases are handled
- at least one concrete worked example per page type

## Final Product Requirements

The final feature must:

- be static and read-only
- be sourced from the real Python analysis rules
- preserve the existing legend
- preserve the existing row-level Drivers tooltip
- avoid client-side recalculation
- avoid editable thresholds
- avoid storing methodology data in CSV rows or table row JSON

## Final UX Decision

The methodology section should not sit above the table.

Use this page order:

1. summary cards
2. short instruction box
3. table
4. legend
5. methodology section

### Why

- The table remains the primary task surface.
- The legend is quick-reference material while users are scanning rows.
- The methodology section is deeper reference content and should not push the main table down the page.

## Methodology Section Structure

Use stacked sections, not tabs.

Recommended internal order:

1. short summary of how the model works
2. worked example
3. threshold inventory
4. compact decision tree
5. edge-case notes

### Content priority

If the implementation must be simplified, keep content in this order of importance:

1. worked example
2. real thresholds
3. summary text
4. edge-case notes
5. compact decision tree

If time runs short, simplify the decision tree before cutting the worked example.

## Information Architecture

### Keep the legend

The legend must remain.

It should keep responsibility for:

- quick-reference symbol meanings
- column definitions
- short interpretation notes while reading the table

It should not become the place for the full threshold inventory or deeper branch logic.

### Add the methodology section

The methodology section should own:

- exact thresholds
- rule ordering
- branch logic
- conservative model philosophy
- edge-case explanation
- worked examples

### Keep the Drivers tooltip

The existing Drivers tooltip remains useful and should not be removed.

It provides fast row-level context. The methodology section provides deeper page-level explanation.

## Non-Negotiable Constraints

- Do not add editable thresholds.
- Do not add browser-side recalculation logic.
- Do not move methodology metadata into CSV rows.
- Do not remove the legend.
- Do not remove the Drivers tooltip.
- Do not change breeder or dealer scoring rules unless a real bug is found and intentionally addressed.
- Prefer server-rendered HTML and CSS for the first implementation.

## Source of Truth

All methodology content must come from the live production rules in these files:

- `src/scrape/breeder_matrix.py`
- `src/scrape/dealer_matrix.py`
- `src/scrape/wishlist_analysis.py`
- `src/shared/config.py`
- `src/shared/history_utils.py`
- `src/scrape/matrix_workflow.py`

Do not create hand-maintained content that can drift from these rules.

## Verified Thresholds and Rules

These thresholds and rules were already verified from the source code and must be accurately reflected in the final methodology content.

### Shared wishlist thresholds

- wishlist delta up: `delta >= 5`
- wishlist delta down: `delta <= -5`
- otherwise wishlist delta is neutral
- OOS carryover lookback: `5` runs
- OUT-row current delta lookup window: `3` runs
- previous comparable lookup window: `12` runs
- small-N flattening threshold: `max(non_zero_counts) - min(non_zero_counts) <= 1`

Wishlist pressure behavior:

- zero wishlist count => Avoid
- flat non-zero distribution within threshold => all non-zero rows become Watch
- otherwise use approximate percentile-style bands with a minimum of one top-band row:
  - top quartile-style band => Hot
  - middle band => Watch
  - bottom quartile-style band => Avoid

### Breeder stock-pattern rules

- Newly Observed:
  - present in the current run
  - observed in at most 2 runs total
  - those observed runs are the trailing current runs
- Sustained if `oos_runs >= 4`
- Emerging if `oos_runs >= 2` and `< 4`
- Cyclical if status is `IN/OUT`
- Always otherwise

### Breeder signal logic

- Newly Observed => Watch
- Sustained + price up or flat + wishlist Hot => Hot
- Sustained + price up or flat => Hot
- Emerging + price up => Hot
- Emerging + wishlist Hot + delta up => Hot
- Emerging + wishlist Hot => Watch
- Emerging => Watch
- Cyclical => Watch
- Always + wishlist Hot + delta down => Avoid
- Always + wishlist Hot => Watch
- otherwise => Avoid

### Dealer reliability and restock rules

- High reliability if presence percentage `>= 0.8`
- Medium reliability if `>= 0.4` and `< 0.8`
- Low reliability otherwise

- Slow restock if `avg_oos >= 3`
- Moderate restock if `avg_oos == 2`
- Fast restock otherwise

### Dealer risk logic

- Low + Slow + wishlist Hot => High Risk
- Low + Slow => High Risk
- Low + wishlist Hot => High Risk
- Low + delta up => High Risk
- Medium + wishlist Hot + delta up => High Risk
- Medium + wishlist Hot => Moderate Risk
- Medium => Moderate Risk
- High + wishlist Avoid or Watch => Low Risk
- High + delta down => Low Risk
- High + wishlist Hot => Low Risk
- otherwise => Low Risk

### Dealer price pressure

- dealer price pressure is informational only
- it is displayed and included in driver text
- it does not participate in dealer risk classification

### Edge cases that must remain explicit

#### Breeder Newly Observed

This is a real breeder-side classification, not just a generic sparse-history warning.

#### Dealer limited history

This is different from breeder Newly Observed.

It is an appended caution note when:

- observed run count is at most 2
- and earlier runs before first observation are ambiguous

It should not become a separate dealer risk bucket.

## Implementation Strategy

Implement the feature in the server-rendered website layer.

Do not build it as a client-side feature first.

### Why this approach

- the feature is page-level and static
- the site already uses Python templates for page generation
- it avoids duplicated rule logic in the browser
- it matches the refined UX direction from the mock

## Files to Add or Update

### Add

- `src/website/analysis_methodology.py`

Likely new test file:

- `tests/website_module/test_analysis_methodology.py`

### Update

- `src/website/page_config.py`
- `src/website/generate_website.py`
- `templates/analysis_page.html`
- `templates/macros.html`
- `templates/analysis.css`
- `src/website/local_demo_data.py` only if necessary for clearer worked examples in local preview

## Required Implementation Approach

### 1. Create methodology builder module

Create `src/website/analysis_methodology.py`.

It should expose structured methodology data, not one giant raw HTML blob.

At minimum it should provide:

- summary text
- worked example data
- threshold groups
- compact decision-tree data
- edge-case notes

Keep breeder and dealer methodology content separate.

### 2. Extend page config and page generation

Update `src/website/page_config.py` and `src/website/generate_website.py` so breeder and dealer analysis pages receive methodology data as page-level template context.

Hard requirement:

- do not add methodology data to row payloads or `json_rows`

### 3. Render methodology in templates

Update `templates/analysis_page.html` so the final page order is:

1. summary cards
2. instruction box
3. table
4. legend
5. methodology section

Use `templates/macros.html` if reusable rendering helpers make the template cleaner.

Useful macro candidates:

- methodology wrapper
- threshold group renderer
- worked example renderer
- compact decision-tree renderer

### 4. Style the methodology section

Update `templates/analysis.css`.

Requirements:

- use tokens from `templates/common.css`
- keep the table visually primary
- ensure mobile readability
- ensure desktop readability
- do not introduce tabs in the real implementation

### 5. Support worked examples in preview if needed

Review `src/website/local_demo_data.py`.

Only update it if existing local preview data does not clearly support:

- breeder Hot example
- breeder Watch or edge-case example
- dealer High Risk example
- dealer Low Risk example

Avoid unnecessary churn in local demo data.

## Suggested Data Shape

The exact structure can vary, but it should resemble this:

```python
{
    "summary": {
        "title": "How the breeder analysis works",
        "intro": "Supply-first model with demand as modifier"
    },
    "worked_example": {
        "species": "Aphonopelma seemanni",
        "result": "🔥 Hot",
        "steps": [...]
    },
    "threshold_groups": [
        {
            "title": "Stock pattern rules",
            "items": [...]
        }
    ],
    "decision_tree": {
        "title": "Compact breeder decision tree",
        "nodes": [...]
    },
    "edge_cases": [...]
}
```

## Exact File Edit Order

Use this order unless there is a strong reason not to:

1. `src/website/analysis_methodology.py`
2. `src/website/page_config.py`
3. `src/website/generate_website.py`
4. `templates/macros.html`
5. `templates/analysis_page.html`
6. `templates/analysis.css`
7. `src/website/local_demo_data.py` only if needed
8. `tests/website_module/...`
9. `tests/e2e/...` if needed

## Execution Checklist

### Phase 0: Confirm baseline

- [ ] Read this file fully before coding.
- [ ] Read `tmp/analysis-methodology-mockup.html` for visual intent only.
- [ ] Review current analysis page flow in:
  - `src/website/generate_website.py`
  - `src/website/page_config.py`
  - `templates/analysis_page.html`
  - `templates/macros.html`
  - `templates/analysis.css`
- [ ] Review the live rule sources listed earlier.

Stop if the page order or section ownership becomes ambiguous. The correct ownership is legend for quick reference, methodology for deep explanation.

### Phase 1: Build methodology data source

- [ ] Create breeder methodology builder
- [ ] Create dealer methodology builder
- [ ] Include summary text
- [ ] Include worked example
- [ ] Include threshold groups
- [ ] Include compact decision tree content
- [ ] Include edge-case notes
- [ ] Keep breeder and dealer variants separate

Minimum breeder content:

- [ ] Newly Observed rule
- [ ] Sustained threshold
- [ ] Emerging threshold
- [ ] Cyclical explanation
- [ ] Always explanation
- [ ] wishlist delta thresholds
- [ ] carryover and lookback windows
- [ ] escalation rules

Minimum dealer content:

- [ ] reliability thresholds
- [ ] restock thresholds
- [ ] Low and Medium escalation rules
- [ ] note that High reliability remains Low Risk even under strong demand
- [ ] limited-history caveat

### Phase 2: Pass methodology data into analysis page rendering

- [ ] Extend page config contract
- [ ] Build breeder methodology during breeder page generation
- [ ] Build dealer methodology during dealer page generation
- [ ] Pass methodology into template context
- [ ] Leave row payloads unchanged

### Phase 3: Render methodology section

- [ ] Place methodology after legend
- [ ] Keep instruction box near top
- [ ] Keep table before legend and methodology
- [ ] Render summary text
- [ ] Render worked example
- [ ] Render threshold inventory
- [ ] Render compact decision tree
- [ ] Render edge-case notes
- [ ] Use stacked details or stacked content blocks, not tabs

### Phase 4: Style methodology section

- [ ] Add section styling in `templates/analysis.css`
- [ ] Add worked-example styling
- [ ] Add threshold group styling
- [ ] Add decision-tree styling
- [ ] Add edge-case note styling
- [ ] Ensure mobile readability
- [ ] Ensure desktop readability
- [ ] Ensure the table remains visually primary

### Phase 5: Review local preview examples

- [ ] Confirm demo data supports clear breeder example(s)
- [ ] Confirm demo data supports clear dealer example(s)
- [ ] Only edit local demo data if the examples would otherwise be weak or confusing

### Phase 6: Add or update tests

Python/content tests:

- [ ] breeder thresholds present and correct
- [ ] dealer thresholds present and correct
- [ ] breeder Newly Observed content present
- [ ] dealer limited-history content present
- [ ] worked examples are page-specific

Website rendering tests:

- [ ] breeder page includes methodology section
- [ ] dealer page includes methodology section
- [ ] legend still present
- [ ] methodology rendered after legend
- [ ] table rendered before methodology
- [ ] worked example content rendered

E2E checks:

- [ ] methodology section exists on breeder page
- [ ] methodology section exists on dealer page
- [ ] details open correctly if details blocks are used
- [ ] table interactions still work

### Phase 7: Run required commands

- [ ] `make test`
- [ ] `make test-visual`
- [ ] `make test-e2e`

Do not declare completion until these commands pass or any unrelated failure is explicitly documented.

## Acceptance Criteria

The work is complete only when all of the following are true:

1. Breeder page includes methodology content below the legend.
2. Dealer page includes methodology content below the legend.
3. The legend still exists.
4. The Drivers tooltip still exists.
5. The methodology is static and read-only.
6. A worked example is present on each page type.
7. The threshold inventory includes the real thresholds.
8. The compact decision tree reflects the real logic ordering.
9. Edge-case notes clearly distinguish breeder Newly Observed from dealer limited history.
10. Required tests pass.

## If Time Runs Short

Reduce scope in this order only:

1. simplify the compact decision tree
2. reduce the number of threshold groups
3. tighten explanatory copy

Do not cut:

- the worked example
- the legend
- the real thresholds
- the below-the-legend placement

## Final Instructions to the Coding Agent

- Implement the feature end-to-end.
- Do not stop at planning.
- Make the code changes.
- Add the tests.
- Run the required commands.
- Report exactly what changed and what passed.

## Related Artifacts

These are supporting materials for context, not required for handoff:

- `tmp/analysis-methodology-mockup.html`

This file is the canonical handoff document.
