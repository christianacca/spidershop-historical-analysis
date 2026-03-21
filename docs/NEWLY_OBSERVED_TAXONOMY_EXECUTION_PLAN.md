# Newly Observed Taxonomy Execution Plan

This document converts the recommendation in [NEWLY_OBSERVED_TAXONOMY_RECOMMENDATION.md](./NEWLY_OBSERVED_TAXONOMY_RECOMMENDATION.md) into a direct execution script for a coding agent.

It is intentionally conservative, repo-specific, and phased for reviewability.

## 1. Mission

- Implement a conservative `Newly Observed` treatment for sparse-history species so first-seen or very recently first-seen species are not mislabeled as stable `Always` supply.
- Fix the false-negative breeder outcome where current logic classifies late-appearing species as `Always` simply because they are currently `IN` and have no active OOS streak.
- Non-goals:
- Do not redesign dealer taxonomy.
- Do not infer historical OOS before first appearance.
- Do not add wide new breeder/dealer table columns.
- Do not split `Newly Observed` into subtypes.
- Do not change historical CSV schema unless it is unavoidable.
- Do not edit generated build output directly.

## 2. Locked Decisions

- Add `Newly Observed` as a breeder stock-pattern value.
- Qualification rule: species is present in the current run, observed in no more than the latest 2 consecutive runs, and absent in all earlier recorded runs.
- Exit rule: once observed across 3 runs, the species stops qualifying for `Newly Observed` and is evaluated by the normal stock-pattern taxonomy; pre-first-seen absence still does not become confirmed OOS evidence.
- Breeder signal mapping: `Newly Observed` always maps to `⚠️` in phase 1.
- Breeder recommendation text should stay action-oriented and include coverage as a confidence qualifier for this pattern, for example: `Monitor closely — newly observed, limited history (observed X/Y runs)`.
- Breeder sorting: put `Newly Observed` at the bottom of the `⚠️` bucket, below evidence-backed `Emerging` and `Cyclical`, above true `❌` rows.
- Dealer taxonomy scope: do not add `Newly Observed` as a primary dealer classification in phase 1.
- Dealer behavior: keep reliability/restock/risk logic supply-first; only use observation coverage to soften sparse-history wording or drivers.
- Table metadata scope: prefer compact coverage context in recommendation/drivers; do not add a wide always-visible first-observed column in phase 1.
- Species detail metadata: show `First observed in dataset`, `Latest observed`, and `Observed in X/Y runs`; explain that pre-first-seen absence is ambiguous.
- `Needs confirmation`: canonical legacy value mismatch between Python `Always` and client filter label `Always Available`. Narrowest safe default: keep `Always` as the data value everywhere and use display copy only for labels.
- `Needs confirmation`: optional qualitative coverage labels (`low` / `medium` / `high`). Narrowest safe default: do not add the qualitative label in phase 1 unless it falls out naturally from the same metadata without extra UI complexity.

## 3. Repo Impact Map

- `analysis logic`
- Breeder stock-pattern qualification, recommendation text, and breeder-only sort precedence must change.
- Dealer risk logic may only gain sparse-history confidence wording.
- `shared sorting/workflow`
- Add one reusable observation-metadata helper path so breeder logic, dealer wording, and species-detail rendering agree on first observed, latest observed, observed runs, and total runs.
- `website generation`
- Breeder/dealer analysis-page copy and legend text likely need updates so user-facing semantics match the new taxonomy and sparse-history behavior.
- `species detail output`
- Surface first-observed and coverage metadata, plus explicit ambiguity wording, in the species detail context where the recommendation says explanation should live.
- `client/UI layer`
- Extend the hard-coded breeder stock-pattern filter list to include `Newly Observed`.
- Verify counts, filtering, and ordering without redesigning the table component.
- `tests`
- Update Python unit, website unit, client unit, visual, E2E, and affected snapshot/legend tests in the same phases as the behavior changes.
- `docs`
- The recommendation doc remains the source of truth.
- Only update docs if implementation discovers a repo-specific constraint that needs to be recorded after the code is settled.

## 4. File Target List

### Must change

- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/shared/history_utils.py`
  - Add pure observation coverage / first-seen helpers used across scrape and website code.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/scrape/breeder_matrix.py`
  - Add `Newly Observed` qualification, breeder recommendation text, breeder drivers text coverage handling, and breeder-specific sort precedence if needed.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/shared_module/test_history_utils.py`
  - New unit tests for shared observation helpers.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/scrape_module/test_breeder_matrix.py`
  - Add failing tests for qualification, exit, no retroactive OOS inference, recommendation text, and sort position.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/website/species_detail.py`
  - Compute and pass observation metadata into the species detail template context.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/templates/species_detail.html`
  - Render first observed, latest observed, and observed runs metadata plus ambiguity wording.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/website_module/test_species_detail.py`
  - Add failing tests for new metadata extraction and rendered copy.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/client/src/shared/components/SortableTable.svelte`
  - Add `Newly Observed` stock-pattern filter option using the canonical data value.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/client/src/shared/components/SortableTable.test.ts`
  - Add failing tests for new button label/count/filter behavior.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/website_module/test_interactive.py`
  - Update JSON payload assertions and stock-pattern count coverage.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/e2e/test_table_interactions.py`
  - Add breeder table interaction coverage for filtering `Newly Observed`.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/e2e/helpers.py`
  - Extend E2E fixture data to include at least one `Newly Observed` breeder row.

### Likely change

- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/scrape/dealer_matrix.py`
  - Add sparse-history coverage qualifier to dealer recommendation or drivers only when confidence is thin.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/scrape_module/test_dealer_matrix.py`
  - Cover dealer sparse-history wording without changing dealer risk classification.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/website/generate_website.py`
  - Update breeder page summary tooltip copy so `⚠️` semantics include sparse-history ambiguity.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/templates/legend.md`
  - Update stock-pattern legend and explanation text to include `Newly Observed` and the no-retroactive-inference rule.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/src/scrape/legend_examples.py`
  - Add or adjust breeder legend examples if the legend gains a new pattern example.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/scrape_module/test_legend_examples.py`
  - Update assertions if legend examples change.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/scrape_module/test_scrape_spidershop_spiderlings.py`
  - Update end-to-end scrape/legend/snapshot expectations if the generated outputs change.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/client/src/shared/components/SortableTable.visual.test.ts`
  - Add browser-backed assertion if button layout or visible filter UI is intentionally extended.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/e2e/test_species_page_interactions.py`
  - Add species-detail UI assertions for new metadata if rendered in browser-visible sections.

### Maybe change

- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/client/src/breeder-page/config.ts`
  - Inspect only; likely no structural change beyond using the existing stock-pattern filter config.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/templates/macros.html`
  - Inspect only if existing tooltip/callout macros need copy support.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/shared_module/test_driver_text_helpers.py`
  - Update only if shared driver wording contract changes.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/tests/website_module/test_summary_stats.py`
  - Update only if summary tooltip wording changes.
- `/Users/christian.crowhurst/Documents/git/spidershop-historical-analysis/docs/NEWLY_OBSERVED_TAXONOMY_RECOMMENDATION.md`
  - Treat as read-only source of truth unless a final implementation note is explicitly needed.

## 5. Execution Rules For The Coding Agent

- Use TDD in every phase that changes behavior: write the failing test first, run it to confirm the expected failure, then implement the smallest fix.
- Use repo commands only: `make test`, `make test-client-fast`, `make test-client`, `make test-visual`, `make test-e2e`, and module coverage checks; do not run `pytest` directly.
- Validate each phase before moving on; do not stack unverified phases.
- Keep each phase scoped to its stated files and behavior; do not mix opportunistic refactors.
- Do not edit generated output in `templates/scripts/dist`; change sources and rebuild through the normal workflow.
- Follow snapshot protocol: investigate diffs, explain them, then update snapshots only if the changes are intentional.
- Record discoveries that affect later phases in working notes and update later phases if a safer path emerges.
- If implementation reality changes a later phase, revise the remaining plan before continuing.
- Commit each phase separately with a scoped commit message after that phase’s tests pass.
- Create a PR only after all phases are complete, validated, and committed cleanly.

## 6. Milestone Table

| Phase | Milestone title | Goal | Main files | Main tests | Completion signal |
|---|---|---|---|---|---|
| 1 | Shared Observation Metadata | Create one reusable, full-history observation coverage helper contract without changing unrelated behavior. | `src/shared/history_utils.py`; `tests/shared_module/test_history_utils.py` | `tests/shared_module/test_history_utils.py`; `make test`; coverage check for `shared/history_utils.py` | Helper API exists, tests prove first/latest/coverage behavior, no downstream regressions. |
| 2 | Breeder Taxonomy And Sorting | Introduce `Newly Observed` into breeder classification, recommendation text, and breeder sort ordering. | `src/scrape/breeder_matrix.py`; `tests/scrape_module/test_breeder_matrix.py` | breeder matrix unit tests; `make test`; coverage checks; targeted snapshot updates only if justified | Breeder rows classify correctly, `⚠️` mapping is stable, sort order matches contract. |
| 3 | Dealer And Explanatory Copy Alignment | Keep dealer risk model unchanged while adding sparse-history confidence wording and aligning legend/summary copy. | `src/scrape/dealer_matrix.py`; `src/website/generate_website.py`; `templates/legend.md`; related tests | dealer unit tests; legend/example tests; `make test`; snapshot review where needed | Dealer taxonomy is unchanged, sparse-history wording is conservative, user-facing explanatory copy matches logic. |
| 4 | Species Detail Metadata | Surface first observed, latest observed, and observed runs metadata plus ambiguity wording on species pages. | `src/website/species_detail.py`; `templates/species_detail.html`; `tests/website_module/test_species_detail.py` | species detail unit tests; `make test`; coverage checks for `website/species_detail.py` | Species pages render the new metadata and explain ambiguous pre-first-seen absence clearly. |
| 5 | Client Filter And Browser Coverage | Add `Newly Observed` to breeder stock-pattern filters and verify count/filter/browser behavior. | `client/src/shared/components/SortableTable.svelte`; client tests; website interactive tests; E2E fixtures/tests | `make test-client-fast`; `make test-client`; `make test-visual` if visual assertions changed; `make test`; `make test-e2e` | Breeder UI exposes the new filter, counts are correct, filtering works in browser, no stale payload assumptions remain. |
| 6 | Final Integration And PR Prep | Run final validation, review commit boundaries, and prepare a clean branch/PR. | all impacted source and test files | full required validation suite | All phases validated, commits are cleanly separated, acceptance checklist is satisfied, PR is ready. |

## 7. Phase-by-Phase Execution Script

### Phase 1: Shared Observation Metadata

#### Purpose

- Establish one pure, reusable source of truth for observation coverage before touching breeder/dealer/species-page behavior.
- This must happen first so later phases do not duplicate slightly different first-seen logic.

#### Files in Scope

- `src/shared/history_utils.py`
- `tests/shared_module/test_history_utils.py`

#### Pre-Phase Checks

- Read `docs/NEWLY_OBSERVED_TAXONOMY_RECOMMENDATION.md` fully.
- Inspect `src/shared/history_utils.py`, `src/scrape/breeder_matrix.py`, `src/scrape/dealer_matrix.py`, and `src/website/species_detail.py` to see every current caller that reasons about runs.
- Inspect current history-row test helpers in `tests/conftest.py`.

#### Ordered Steps

1. Add failing shared-unit tests first for: full-run timeline coverage, first observed run, latest observed run, observed count, total run count, consecutive current observations, and pre-first-seen ambiguity.
2. Run only the new shared-unit test file to confirm the expected red state.
3. Add the smallest pure helper API in `src/shared/history_utils.py` that works on full history rows and species/size keys.
4. Re-run the new shared-unit tests until green.
5. Confirm no existing callers are broken before moving to breeder logic.

#### Tests To Add Or Modify First

- `tests/shared_module/test_history_utils.py`
- Tests must prove:
- a species first seen late in history reports full dataset denominator,
- runs before first appearance are not treated as observed,
- consecutive-current-observation counting distinguishes 1-run, 2-run, and 3-run cases,
- latest observed can differ from first observed when the species disappears later.

#### Validation Steps

1. Run the new shared test file through the repo-supported single-file workflow if available, otherwise `make test`.
2. Run `make test` because `src/shared` changes affect both scrape and website code paths.
3. Run `.venv/bin/python scripts/check_coverage.py --module=shared/history_utils.py` because `src/shared` coverage is phase-blocking.

#### Exit Criteria

- Shared helper functions express the observation contract unambiguously.
- Tests prove the helper distinguishes ambiguous pre-first-seen gaps from real post-observation gaps.
- No other behavior has changed yet.

#### Phase Checklist

- Failing shared tests written first.
- Shared helper API implemented.
- Shared tests green.
- `make test` green.
- Coverage check green.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize discoveries, surprises, and repo facts from the phase.
- Feed those findings into Phase 2 before editing breeder logic.
- Update later phases if helper shape or naming changed the safest path.
- Create a separate commit for this phase with a scoped commit message.

### Phase 2: Breeder Taxonomy And Sorting

#### Purpose

- Fix the core false-`Always` problem in breeder analysis.
- This phase must land before UI work so downstream pages and payloads expose the right breeder stock pattern.

#### Files in Scope

- `src/scrape/breeder_matrix.py`
- `tests/scrape_module/test_breeder_matrix.py`
- `tests/scrape_module/test_scrape_spidershop_spiderlings.py` if integrated outputs change

#### Pre-Phase Checks

- Re-read the locked decisions in the recommendation doc.
- Inspect current breeder pattern classification, recommendation branches, drivers text, and sort path.
- Inspect any snapshot-backed scrape tests before changing outputs.

#### Ordered Steps

1. Add failing breeder tests first for `Newly Observed` qualification on 1-run and 2-consecutive-run cases.
2. Add a failing breeder test proving the exit rule: 3 observed runs must fall back to normal taxonomy, not `Newly Observed`.
3. Add a failing breeder test proving no retroactive OOS inference before first appearance.
4. Add a failing breeder test proving strong wishlist signals do not escalate `Newly Observed` above `⚠️`.
5. Add a failing breeder sort test proving `Newly Observed` sits below evidence-backed `⚠️` rows and above `❌` rows.
6. Run the targeted breeder tests to confirm the expected red state.
7. Implement `Newly Observed` qualification in `breeder_matrix` using the Phase 1 helper.
8. Add breeder recommendation text and driver text coverage handling using observed X/Y runs.
9. Extend the breeder sort key only as far as needed to enforce the new warning-bucket ordering. Do not redesign global sorting.
10. Re-run targeted breeder tests, then the broader scrape suite.
11. If snapshot-backed outputs changed, inspect the diff line by line and update snapshots only after the changes are explained.

#### Tests To Add Or Modify First

- `tests/scrape_module/test_breeder_matrix.py`
- `tests/scrape_module/test_scrape_spidershop_spiderlings.py` if integrated markdown/CSV output changes
- Tests must prove:
- current-run `IN` plus no more than 2 latest observations plus no earlier presence results in `Newly Observed`,
- 3 observations exit the category,
- breeder `OOS Runs` does not count pre-first-seen absences,
- recommendation text includes limited-history coverage,
- sort order keeps `Newly Observed` at the bottom of the `⚠️` bucket.

#### Validation Steps

1. Run targeted breeder tests first during red/green.
2. Run `make test` because `src/scrape` changed.
3. Run `.venv/bin/python scripts/check_coverage.py --module=scrape/breeder_matrix.py`.
4. If integrated scrape output changed, run `.venv/bin/python scripts/check_coverage.py --module=scrape/legend_examples.py` or other edited modules as applicable.

#### Exit Criteria

- Breeder rows no longer misclassify late-appearing species as `Always`.
- `Newly Observed` is breeder-only and always `⚠️`.
- Sort behavior matches the contract.
- Any snapshot updates are reviewed and explained.

#### Phase Checklist

- Failing breeder tests written first.
- Qualification rule implemented.
- Exit rule implemented.
- Sort precedence implemented.
- Recommendation/drivers text updated.
- `make test` green.
- Coverage check green.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize findings, surprises, and repo discoveries from the phase.
- Feed forward any payload/copy implications into Phase 3 and Phase 4.
- Update later phases if the safest implementation path changed.
- Create a separate commit for this phase with a scoped commit message.

### Phase 3: Dealer And Explanatory Copy Alignment

#### Purpose

- Keep dealer classification conservative and unchanged while making sparse-history uncertainty visible.
- Align public-facing explanation surfaces so the new breeder taxonomy does not contradict tooltips or legends.

#### Files in Scope

- `src/scrape/dealer_matrix.py`
- `tests/scrape_module/test_dealer_matrix.py`
- `src/website/generate_website.py`
- `templates/legend.md`
- `src/scrape/legend_examples.py` if the legend gets a new example
- `tests/scrape_module/test_legend_examples.py`
- `tests/website_module/test_summary_stats.py` and related snapshot/integration tests if copy changes surface there

#### Pre-Phase Checks

- Inspect current dealer recommendation branches and drivers text.
- Inspect analysis-page summary tooltip copy in `src/website/generate_website.py`.
- Inspect `templates/legend.md` and any legend example generation/tests.

#### Ordered Steps

1. Add failing dealer tests first for sparse-history wording that preserves the existing dealer risk class.
2. Add failing tests or snapshot expectations for legend and summary copy updates before changing those texts.
3. Run the targeted tests to confirm the expected red state.
4. Implement the smallest dealer-side change: add observation coverage as a confidence qualifier only for sparse-history cases. Do not add a dealer taxonomy value.
5. Update analysis-page tooltip copy so breeder `⚠️` semantics include limited-history uncertainty where appropriate.
6. Update `templates/legend.md` to include `Newly Observed`, its hold-state meaning, and the no-retroactive-inference rule.
7. Add or adjust a legend example only if the legend now promises one.
8. Re-run unit tests and inspect any snapshot diffs before accepting them.

#### Tests To Add Or Modify First

- `tests/scrape_module/test_dealer_matrix.py`
- `tests/scrape_module/test_legend_examples.py`
- `tests/website_module/test_summary_stats.py` or the most direct copy-bearing tests
- relevant snapshot-backed scrape/website tests
- Tests must prove:
- dealer risk stays supply-first,
- sparse-history dealer wording becomes more cautious without changing the risk class,
- legend/copy mentions the new taxonomy accurately,
- no legacy copy still claims the breeder taxonomy has only four patterns.

#### Validation Steps

1. Run targeted dealer/legend/copy tests first.
2. Run `make test` because `src/scrape`, `src/website`, and `templates` are affected.
3. Run coverage checks for each edited Python module.
4. If snapshots changed, review the diffs and then update them deliberately.

#### Exit Criteria

- Dealer output remains supply-first.
- Sparse-history caution is visible where the recommendation requires it.
- Legend and summary copy no longer contradict the new taxonomy.

#### Phase Checklist

- Failing dealer/copy tests written first.
- Dealer wording updated without taxonomy drift.
- Legend and summary copy updated.
- Snapshot diffs reviewed and justified.
- `make test` green.
- Coverage checks green.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize findings, surprises, and repo discoveries from the phase.
- Feed forward any UI-text or payload consequences into Phase 4 and Phase 5.
- Update later phases if the safest execution path changed.
- Create a separate commit for this phase with a scoped commit message.

### Phase 4: Species Detail Metadata

#### Purpose

- Put the full explanation burden on the species detail page, as directed by the recommendation.
- This phase must happen before final browser validation so the E2E/species-page surface reflects the full contract.

#### Files in Scope

- `src/website/species_detail.py`
- `templates/species_detail.html`
- `tests/website_module/test_species_detail.py`
- `tests/e2e/test_species_page_interactions.py` if browser-visible assertions are added

#### Pre-Phase Checks

- Inspect current species detail data extraction, chart-data generation, and template sections.
- Inspect current species detail tests for existing metadata and callout patterns.

#### Ordered Steps

1. Add failing species-detail tests first for first observed, latest observed, observed X/Y runs, and ambiguity explanation text.
2. Add failing tests for rendering breeder `Newly Observed` context distinctly from generic `⚠️` copy when applicable.
3. Run the targeted species-detail tests to confirm the red state.
4. Extend `species_detail.py` to compute full-history observation metadata using the shared helper from Phase 1.
5. Pass the new metadata into the template context without changing unrelated chart/table behavior.
6. Update the template to render the metadata block and ambiguity explanation conservatively.
7. Keep any optional qualitative coverage label out of scope unless it is already trivial and well-covered.
8. Re-run species-detail tests and then the broader Python suite.

#### Tests To Add Or Modify First

- `tests/website_module/test_species_detail.py`
- `tests/e2e/test_species_page_interactions.py` only if browser-visible layout/assertion coverage is added in this phase
- Tests must prove:
- first observed and latest observed are rendered correctly,
- observed X/Y runs uses full dataset run count,
- pre-first-seen absence is described as ambiguous,
- breeder sparse-history callout text matches the new contract.

#### Validation Steps

1. Run targeted species-detail tests first.
2. Run `make test` because `src/website` and `templates` changed.
3. Run `.venv/bin/python scripts/check_coverage.py --module=website/species_detail.py`.
4. Run `make test-e2e` only if this phase adds or changes browser-visible species-page interactions beyond unit-covered HTML structure. Otherwise defer full browser validation to Phase 5 or 6.

#### Exit Criteria

- Species detail pages expose the required metadata and explanatory wording.
- Metadata is derived from the same shared contract as breeder/dealer behavior.
- No unrelated species-page behavior regressed.

#### Phase Checklist

- Failing species-detail tests written first.
- Metadata extraction implemented.
- Template rendering implemented.
- `make test` green.
- Coverage check green.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize findings, surprises, and repo discoveries from the phase.
- Feed forward any browser-visible implications into Phase 5.
- Update later phases if the safest execution path changed.
- Create a separate commit for this phase with a scoped commit message.

### Phase 5: Client Filter And Browser Coverage

#### Purpose

- Expose the new taxonomy in the breeder UI and verify real browser behavior.
- This phase happens after backend/species-detail work so the client consumes final payload semantics rather than chasing moving targets.

#### Files in Scope

- `client/src/shared/components/SortableTable.svelte`
- `client/src/shared/components/SortableTable.test.ts`
- `client/src/shared/components/SortableTable.visual.test.ts` if visual assertions are updated
- `tests/website_module/test_interactive.py`
- `tests/e2e/helpers.py`
- `tests/e2e/test_table_interactions.py`
- `tests/e2e/test_species_page_interactions.py` if browser assertions are needed for metadata

#### Pre-Phase Checks

- Inspect current hard-coded stock-pattern button array and existing button-count/filter tests.
- Verify whether the canonical payload value is `Always` or `Always Available` before touching the new option.
- Inspect E2E fixture helpers so the new pattern is represented in generated browser data.

#### Ordered Steps

1. Add failing client unit tests first for `Newly Observed` button rendering, count labeling, and filter behavior.
2. Add failing website-unit tests for breeder JSON payload assumptions that now need to include `Newly Observed`.
3. Add failing E2E fixture/test coverage for clicking the new stock-pattern filter and combining it with signal filters.
4. Run the targeted client/unit/E2E tests to confirm the expected red state.
5. Update `SortableTable.svelte` with the new stock-pattern button using the canonical data value already emitted by Python.
6. Fix any existing `Always` / `Always Available` mismatch in the smallest safe way so stock-pattern filtering is internally consistent.
7. Update fixture data and browser tests to include at least one `Newly Observed` breeder row.
8. Add or update visual assertions only if button layout/visibility contracts are explicitly asserted.
9. Re-run client tests, Python website tests, and full E2E.

#### Tests To Add Or Modify First

- `client/src/shared/components/SortableTable.test.ts`
- `tests/website_module/test_interactive.py`
- `tests/e2e/helpers.py`
- `tests/e2e/test_table_interactions.py`
- `client/src/shared/components/SortableTable.visual.test.ts` if visible UI assertions are changed
- Tests must prove:
- the breeder filter list includes `Newly Observed`,
- row counts include the new pattern,
- selecting the filter shows only matching rows,
- combined signal + stock-pattern filters still use AND logic,
- dealer pages still do not expose stock-pattern filters.

#### Validation Steps

1. Run `make test-client-fast` during red/green iteration for `client/src` changes.
2. Run `make test-client` when the client phase is ready.
3. Run `make test-visual` if visual-contract tests or visual/UI assertions that depend on real browser style/layout changed.
4. Run `make test` because website-unit JSON payload and templates/tests are also in scope.
5. Run `make test-e2e` because `client/src` and website output changed and browser behavior is phase-blocking.

#### Exit Criteria

- Breeder UI exposes and filters `Newly Observed` correctly.
- No stock-pattern value mismatch remains between payload and UI filter buttons.
- Browser tests prove the feature works end-to-end.

#### Phase Checklist

- Failing client/browser tests written first.
- Client filter list updated.
- Payload assumptions updated.
- E2E fixtures updated.
- `make test-client` green.
- `make test` green.
- `make test-e2e` green.
- `make test-visual` green if used.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize findings, surprises, and repo discoveries from the phase.
- Feed forward any final integration concerns into Phase 6.
- Update later phases if the safest execution path changed.
- Create a separate commit for this phase with a scoped commit message.

### Phase 6: Final Integration And PR Prep

#### Purpose

- Prove the finished branch satisfies the full contract across scrape, website, client, and browser layers.
- This phase exists to catch cross-phase drift, missing feedforward updates, and messy commit boundaries before review.

#### Files in Scope

- All files changed in Phases 1-5.

#### Pre-Phase Checks

- Review all prior phase summaries and confirm any feedforward updates were incorporated.
- Review git history to ensure each phase is isolated in its own commit.

#### Ordered Steps

1. Run the full required validation suite across impacted layers.
2. Re-check coverage for every edited Python module and ensure client coverage gates passed in `make test-client`.
3. Review changed snapshots one final time and confirm every update is intentional.
4. Verify no generated build-output files were edited manually.
5. Review commit boundaries and, if necessary, clean up only with non-destructive git operations that preserve separate phase commits.
6. Confirm the acceptance checklist item by item against the final code and generated behavior.
7. Prepare the branch for review and draft the PR summary.

#### Tests To Add Or Modify First

- None. This is verification and review only.

#### Validation Steps

1. Run `make test`.
2. Run `make test-client`.
3. Run `make test-visual` if any visual-contract file or visual UI behavior changed.
4. Run `make test-e2e`.
5. Run `.venv/bin/python scripts/check_coverage.py --module=shared/history_utils.py`.
6. Run `.venv/bin/python scripts/check_coverage.py --module=scrape/breeder_matrix.py`.
7. Run coverage checks for any other edited Python modules such as `scrape/dealer_matrix.py`, `website/generate_website.py`, and `website/species_detail.py`.

#### Exit Criteria

- All required tests and coverage checks pass.
- Later-phase feedforward updates were incorporated.
- Commit history is clean and phase-scoped.
- Branch is ready for PR review.

#### Phase Checklist

- Full validation suite green.
- All edited-module coverage checks green.
- Snapshot diffs reviewed.
- Commit boundaries verified.
- Acceptance checklist satisfied.
- PR summary drafted.

#### Phase Closeout

- Confirm which checklist items were completed.
- Summarize findings, surprises, and repo discoveries from the phase.
- Confirm no later-phase updates remain outstanding.
- Create a final separate commit only if Phase 6 itself introduced review-prep changes. Otherwise leave prior phase commits intact.

## 8. Data And Behavior Contract

- Qualification rule: classify breeder stock pattern as `Newly Observed` only when the species is present in the current run, appears in no more than the latest 2 consecutive runs, and all earlier runs in the dataset lack that species/size key.
- Exit rule: after 3 observed runs, `Newly Observed` is no longer eligible; evaluate the row using the normal breeder taxonomy.
- No retroactive OOS inference: runs before first observation are ambiguous and must never increment breeder `OOS Runs`, create `Emerging`, or raise dealer absence events as if the species was confirmed out of stock.
- Relationship to OOS, OUT, and OOS Runs: `OOS` still reflects current status (`IN`, `OUT`, `IN/OUT`); `Newly Observed` applies only when current status is `IN`; `OOS Runs` for `Newly Observed` rows remains `0` unless current logic explicitly proves an actual post-observation OUT streak.
- Observation coverage metadata: compute first observed run, latest observed run, observed run count, and total dataset run count from the full run timeline, not bounded carryover windows.
- Breeder signal behavior: `Newly Observed` always maps to `⚠️`; it is a hold-state for uncertainty, not a scarcity or abundance claim.
- Dealer-side behavior: dealer risk classification remains driven by reliability, avg OOS duration, and restock speed; sparse coverage can soften wording or add caution but must not become the primary risk driver.
- Sorting behavior: breeder order remains signal-first; within the `⚠️` bucket, evidence-backed `Emerging` and `Cyclical` rows sort above `Newly Observed`; `Newly Observed` rows still sort above `❌` rows.
- Recommendation text behavior: breeder `Newly Observed` text should mention limited history and observed X/Y runs; dealer sparse-history text should mention limited history only when confidence is thin; first-observed explanation belongs primarily on the species detail page.

## 9. Test Matrix

| Phase | Layer | What behavior it protects | When it must be run | Phase-blocking |
|---|---|---|---|---|
| 1 | Python unit | Shared full-history observation coverage contract | During Phase 1 red/green and final Phase 1 validation | Yes |
| 1 | Client unit | None | Not required | No |
| 1 | Visual | None | Not required | No |
| 1 | E2E | None | Not required | No |
| 1 | Snapshot | None unless a shared helper indirectly changes covered output | Only if an existing snapshot test fails | Conditional |
| 2 | Python unit | Breeder qualification, exit rule, no retroactive OOS inference, sort order | During Phase 2 red/green and final Phase 2 validation | Yes |
| 2 | Client unit | None | Not required | No |
| 2 | Visual | None | Not required | No |
| 2 | E2E | None yet | Defer to Phase 5/6 | No |
| 2 | Snapshot | Integrated scrape/legend outputs if breeder table text changes | Only after reviewing intentional diffs | Conditional |
| 3 | Python unit | Dealer sparse-history wording, summary tooltip text generation, legend/example generation | During Phase 3 and final Phase 3 validation | Yes |
| 3 | Client unit | None | Not required | No |
| 3 | Visual | None unless a visual contract is explicitly changed | Only if touched | Conditional |
| 3 | E2E | Usually not needed if only wording/unit surfaces changed | Defer to Phase 5/6 | No |
| 3 | Snapshot | Legend/example or generated analysis summary content | Run when those outputs change; follow snapshot protocol | Conditional but blocking if touched |
| 4 | Python unit | Species-detail metadata extraction and rendered explanation copy | During Phase 4 red/green and final Phase 4 validation | Yes |
| 4 | Client unit | None | Not required | No |
| 4 | Visual | None unless new browser-backed species-page visual assertions are added | Only if touched | Conditional |
| 4 | E2E | Species page browser-visible metadata, if asserted | If browser-visible behavior is added now or in final integration | Conditional |
| 4 | Snapshot | Species-detail HTML snapshots if present/added | Only if touched | Conditional |
| 5 | Python unit | Breeder JSON payload assumptions and website interactive coverage | During Phase 5 final validation | Yes |
| 5 | Client unit | New stock-pattern button rendering, counts, filter logic | `make test-client-fast` during iteration; `make test-client` before closeout | Yes |
| 5 | Visual | Visible filter button presence/layout/count assertions in real browser | `make test-visual` if visual tests or visible UI contracts changed | Conditional but yes if touched |
| 5 | E2E | Real breeder filter interaction, combined filters, species-page browser checks if added | `make test-e2e` in Phase 5 and Phase 6 | Yes |
| 5 | Snapshot | Only if browser-fixture-backed generated output snapshots changed | Only after review | Conditional |
| 6 | Python unit | Final regression coverage across all Python layers | Final integration | Yes |
| 6 | Client unit | Final client regression and coverage gate | Final integration | Yes |
| 6 | Visual | Final browser-backed UI contract regression if any touched | Final integration | Conditional |
| 6 | E2E | Final end-to-end confidence for breeder/species pages | Final integration | Yes |
| 6 | Snapshot | Any touched snapshots remain intentional and explained | Final integration review | Yes if touched |

## 10. Risk Register

- First appearance late in history: helper logic must scan the full dataset run timeline, not bounded lookback windows.
  - Mitigation: unit test a species first seen near the end of a long history.
- Disappearance after first appearance: once a species has been observed and then goes `OUT`, only post-observation absence counts as OOS.
  - Mitigation: add breeder tests for seen-then-missing behavior after first appearance.
- Sparse history with strong wishlist signals: high wishlist pressure must not escalate `Newly Observed` to `🔥`.
  - Mitigation: explicit breeder test asserting `⚠️` remains fixed.
- Disagreement between breeder and dealer outputs: breeder may show `Newly Observed` while dealer remains low/medium/high reliability.
  - Mitigation: dealer tests should assert taxonomy does not leak into dealer risk class.
- Accidental inference of historical OOS before first observation: easy to introduce if helpers treat all missing runs uniformly.
  - Mitigation: shared helper tests plus breeder classification regression tests.
- UI copy drifting from logic: legend/species-detail/tooltips can remain stale even if tables work.
  - Mitigation: include copy-bearing files in later phases and update affected unit/snapshot tests.
- Canonical value mismatch (`Always` vs `Always Available`): can break filter counts or stock-pattern filtering.
  - Mitigation: settle canonical data value early and align tests/client buttons before final E2E.

## 11. Final Integration Phase

- Run full validation across every impacted layer after all behavior and UI phases land.
- Review commit boundaries so each prior phase remains separately reviewable.
- Confirm that any discoveries from earlier phases were propagated into later phases before final validation.
- Re-check the acceptance contract against the final generated outputs, not just unit tests.
- Prepare the branch in a review-ready state before opening the PR.

## 12. Final Acceptance Checklist

- A species first observed in the current run or latest 2 consecutive runs is no longer mislabeled as breeder `Always`.
- `Newly Observed` appears only when the qualification rule is satisfied.
- After 3 observations, the species exits `Newly Observed` and uses normal breeder taxonomy.
- Pre-first-seen absence never increments breeder `OOS Runs` or creates false scarcity.
- Breeder `Newly Observed` rows always map to `⚠️`.
- Breeder recommendation text for `Newly Observed` rows includes limited-history coverage.
- Dealer risk classification remains supply-first and does not gain a new primary taxonomy.
- Sparse-history dealer wording is cautious where implemented.
- Species detail pages show first observed, latest observed, and observed X/Y runs.
- Species detail copy explains that pre-first-seen absence is ambiguous.
- Breeder sorting places `Newly Observed` below evidence-backed `⚠️` rows and above `❌` rows.
- Breeder UI exposes a `Newly Observed` stock-pattern filter with correct counts.
- Browser tests prove the breeder filter works and dealer pages still omit stock-pattern filters.
- Legend/tooltip/copy surfaces no longer imply the breeder taxonomy has only four values.
- All required tests and coverage checks pass.
- Snapshot updates, if any, were reviewed and justified.
- Each implementation phase was committed separately.

## 13. PR Instructions

- Verify all phases are complete before opening the PR.
- Verify every required test command and module coverage check passed on the final branch.
- Ensure each phase remains committed separately and the branch is clean.
- Prepare a concise PR summary covering: the false-`Always` problem, the `Newly Observed` qualification/exit rules, breeder/dealer/species-page behavior changes, test coverage added, and any confirmed repo-specific decisions such as canonical `Always` filter values.
- Open a pull request only after the final acceptance checklist is fully satisfied.