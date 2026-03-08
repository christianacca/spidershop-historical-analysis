# Testing Improvements Plan — Revised Agent Feedback Loop

**Repository:** spidershop-historical-analysis  
**Branch:** svelte-migration (PR #104)  
**Date:** 2026-03-08

---

## How to use this document

Each phase is designed to be executed in a separate AI conversation so the agent can stay
focused on one layer of the feedback loop at a time.

Start a phase with:

> Read `docs/TESTING_IMPROVEMENTS_PLAN_REVISED.md`. We are implementing **Phase N**. Begin.

At the end of each phase conversation, update this file:

- Tick completed checklist items
- Record decisions made during the phase
- Record any findings that change the assumptions of later phases
- Adjust later phases if implementation reality differs from the initial plan

This plan is intended to be a living document. The goal is not to follow it rigidly if the repo
teaches us something better during execution. The goal is to keep the next step explicit,
defensible, and easy for an agent to continue.

---

## Objective

Improve the agent feedback loop for client-side and website-facing changes so that:

1. Feedback arrives sooner
2. Failures point directly at the broken layer and state
3. Tests are easier to write and maintain
4. Visual and computed-style regressions have a real safety net

This revised plan keeps the strongest parts of the existing
`docs/TESTING_IMPROVEMENTS_PLAN.md` proposal, but changes the order of work and broadens the
scope beyond token-colour assertions so the result is faster and more maintainable in practice.

---

## Core principles

### 1. Shortest valid loop wins

The first feedback mechanism an agent should use is the cheapest one that can actually catch the
target regression.

- Pure logic should fail in tiny Vitest tests
- Component render and callback wiring should fail in ordinary Svelte Vitest tests
- Computed style and layout invariants should fail in browser-backed component tests
- Full-site assembly, URL state, downloads, and Python-generated HTML shape should fail in E2E

### 2. DevTools MCP is diagnosis, not enforcement

Chrome DevTools MCP gives the agent eyes inside a real browser. It is useful during development,
during debugging, and when designing better assertions. It is not the CI gate.

### 3. Reduce breadth in the slowest layer

The slowest tests should be the narrowest. E2E should prove assembly and browser integration, not
re-test every component state already covered below it.

### 4. Convert discoveries into durable assertions

If the agent finds a useful visual or styling invariant through DevTools MCP or debugging, that
invariant should be promoted into the lowest stable automated layer that can express it.

### 5. Reuse existing repo flows

Where the repo already has a valid generation or preview workflow, extend or alias it rather than
introducing a parallel path that will drift.

---

## Current state summary

### Existing automated layers

| Tier | Command | Approx speed | Current role |
| --- | --- | ---: | --- |
| Client Vitest with coverage | `make test-client` | ~1s | Svelte component behavior, pure utilities, coverage gate |
| Python unit tests | `make test` | ~1s | Python logic and website-generation support code |
| Playwright E2E | `make test-e2e` | ~10-20s | Full-site interaction, integration, URL state, asset load, some style checks |

### Existing interactive browser path

The repo already has a local generation and serving path:

- `make generate-website`
- `make serve-only`
- `scripts/test_website_locally.py`

That means the plan does **not** need a separate preview stack. If a new `make preview` command is
added, it should be a thin alias over existing behavior, not a new code path.

### What is still weak today

- `make test-client` is coverage-enforcing by default, which is not the fastest local iteration loop
- Large component tests still carry a lot of setup and duplicated helpers
- `happy-dom` cannot reliably validate computed styles based on CSS custom properties
- E2E still contains style assertions that are too low-level for a full-site test and uses avoidable timeout polling
- There is no static guardrail against hardcoded token-equivalent values in Svelte style blocks
- There is no formal browser-backed component test layer between happy-dom and full E2E
- DevTools-style interactive inspection is not yet documented as an explicit agent workflow

---

## Proposed feedback loop

```text
agent changes code or CSS
       |
       |  <100ms
       v
Phase 2 static guardrails
  - token drift check
  - Svelte CSS token-compliance audit
       |
       |  <1s
       v
make test-client-fast
  - no coverage
  - pure logic + component behavior + small harness tests
       |
       |  ~1-2s
       v
make test-client
  - existing coverage gate retained
       |
       |  ~2-3s interactive
       v
DevTools MCP inspection against locally served site
  - evaluate_script
  - computed styles
  - layout metrics
  - screenshots
       |
       |  ~5-10s
       v
make test-visual
  - browser-backed component visual contracts
       |
       |  ~10-20s
       v
make test-e2e
  - true page assembly and browser integration only
       |
       |  ad hoc / non-blocking initially
       v
DevTools MCP lighthouse_audit
  - accessibility/performance baseline
```

---

## Target layer responsibilities

| Layer | Purpose | What belongs here | What does not belong here |
| --- | --- | --- | --- |
| Static guardrails | Prevent obvious CSS/system mistakes | Token drift, hardcoded token-equivalent colours in Svelte styles | Runtime behavior, DOM interactions |
| Fast Vitest | Tight local iteration | Pure functions, state transforms, render output, callback props, DOM state changes that `happy-dom` can model | Computed styles, sticky positioning, real layout |
| Browser-backed component tests | Real browser contracts without full site assembly | Computed colours, borders, spacing, focus states, overflow, sticky/header behavior, responsive component states | Full navigation, downloads, Python-generated HTML shape |
| E2E | End-to-end assembly and integration | Generated site, page navigation, URL state, downloads, real browser orchestration across layers | Re-testing local component styling in isolation |
| DevTools MCP | Interactive diagnosis and discovery | Live browser inspection, debugging, screenshot sanity checks, Lighthouse audits | Repeatable CI enforcement |

---

## Phase 0 — Inventory and ownership map

**Goal:** Build the move-down map before adding new layers.

- [ ] 1. Audit the current assertions in:
      - `client/src/shared/components/SortableTable.test.ts`
      - `client/src/history-page/HistoryTable.test.ts`
      - `tests/e2e/test_visual_contracts.py`
      - `tests/e2e/test_navigation_and_page_loads.py`
      - `tests/e2e/test_snapshot_filters.py`
      - `tests/e2e/test_history_date_filter.py`

- [ ] 2. Tag each assertion as one of:
      - pure logic
      - component behavior
      - browser-style contract
      - full integration

- [ ] 3. Produce a move-down table that records:
      - keep in place
      - move to fast Vitest
      - move to browser-backed component tests
      - keep in E2E because it depends on full-site assembly

- [ ] 4. Identify the top three client test files with the highest setup friction and the top three E2E tests with the most duplicated waits or style assertions.

- [ ] 5. Record the baseline timings for:
      - `make test-client`
      - `make test-e2e`
      - one representative client test file
      - one representative E2E file

### Phase 0 Outputs

- An ownership map for current assertions
- A ranked list of pain points by speed, setup cost, and flake risk
- Baseline timings to compare future phases against

### Phase 0 Verification

- No code changes required unless minor instrumentation is needed
- The output of this phase is complete only if later phases can point to a specific assertion inventory

### Phase 0 Decisions To Record

- Which current tests are the first candidates for move-down
- Whether any existing E2E files are already thin enough to leave alone
- Which client tests need helper extraction first

---

## Phase 1 — Fast loop first

**Goal:** Improve the default local iteration path before adding heavier tooling.

- [ ] 6. Add a fast client test command in `Makefile` that runs the client suite without coverage.
      Suggested shape:
      - `make test-client-fast`
      - or a clearly named equivalent

- [ ] 7. Keep `make test-client` as the coverage-enforcing command so existing instructions and CI guarantees remain intact.

- [ ] 8. Add a watch-mode client command for active component work.
      Suggested shape:
      - `make test-client-watch`
      - or `npm run test:watch` wired through `Makefile`

- [ ] 9. Update the intended local order of operations in docs and agent instructions:
      - fast tests first
      - coverage second
      - visual/browser tests when CSS or layout changes are involved
      - E2E last

- [ ] 10. Verify that the fast command is materially faster than the current `make test-client` path and becomes the recommended default for active iteration.

### Phase 1 Outputs

- A clearly defined fast local loop
- No regression to existing coverage enforcement

### Phase 1 Verification

- `make test-client-fast` passes
- `make test-client` still passes
- Timing delta is documented

### Phase 1 Decisions To Record

- Final command names
- Whether watch mode is practical enough to recommend by default

---

## Phase 2 — Test helper extraction and smaller seams

**Goal:** Reduce setup friction and improve failure locality in ordinary client tests.

- [ ] 11. Create shared client test helpers for repeated setup patterns.
      Candidate responsibilities:
      - URL/download mocks
      - table render harnesses
      - shared row and column fixtures
      - domain-level selectors or convenience assertions

- [ ] 12. Refactor `client/src/shared/components/SortableTable.test.ts` to use shared helpers and remove duplicated setup.

- [ ] 13. Refactor `client/src/history-page/HistoryTable.test.ts` to use the same shared infrastructure where possible.

- [ ] 14. Extract high-churn table logic into smaller pure TypeScript seams where practical.
      Prioritise:
      - filter state derivation
      - visible-row computation
      - summary/count logic
      - download row selection logic if it can be separated cleanly

- [ ] 15. Add small parametrized tests for any extracted pure helpers.

- [ ] 16. Confirm that failure messages now point more often at a specific helper or component state instead of a large DOM-heavy test body.

### Phase 2 Outputs

- Shared client-side test kit
- Smaller test seams for high-complexity components
- Reduced duplication across component tests

### Phase 2 Verification

- Existing component tests remain green
- Extracted helper tests remain sub-second
- No behavior drift in the affected components

### Phase 2 Decisions To Record

- Which helper patterns worked well and should be reused
- Which component logic was not worth extracting because the seam was artificial

---

## Phase 3 — Static token guardrails

**Goal:** Shift obvious style-system failures to the cheapest possible layer.

- [ ] 17. Create a shared token parser utility for `templates/common.css`.
      It should parse the `:root` block into a stable token map.

- [ ] 18. Add a design-token assertion test to the ordinary client suite.
      Preferred behavior:
      - readable diff when a token changes
      - stable ordering
      - easy snapshot review or structured map comparison

- [ ] 19. Add a Svelte CSS compliance audit that scans `client/src/**/*.svelte` style blocks and rejects hardcoded values that duplicate known design tokens.

- [ ] 20. Keep the compliance rule intentionally narrow at first:
      - only Svelte component styles
      - only hardcoded values that match known tokens
      - clear allowlist for legitimate values like `transparent`, `none`, `0`, and other obvious non-token cases

- [ ] 21. Make failure messages prescriptive.
      Example format:
      - `FilterButton.svelte uses hardcoded #3498db; use var(--color-accent)`

- [ ] 22. Run these checks as part of the fast client loop only if they stay cheap enough.
      If they meaningfully slow down the loop, keep them in `make test-client` but document the tradeoff.

### Phase 3 Outputs

- Token drift guardrail
- Preventive Svelte style compliance rule

### Phase 3 Verification

- A deliberate hardcoded token-equivalent value fails with a file-specific message
- A deliberate token drift change produces a readable diff

### Phase 3 Decisions To Record

- Whether snapshot or structured token assertion is the clearer maintenance model
- Whether the compliance rule is low-noise enough to keep broad or needs tighter scoping

---

## Phase 4 — DevTools MCP workflow and preview ergonomics

**Goal:** Make real-browser interactive inspection an explicit part of the agent workflow.

- [ ] 23. Review the existing preview path in `scripts/test_website_locally.py` and `Makefile`.

- [ ] 24. Decide whether a new `make preview` command is needed.
      Preferred outcome:
      - it is a thin alias over existing behavior
      - it does not create a parallel serving implementation

- [ ] 25. Document the interactive inspection workflow in `.github/copilot-instructions.md`.
      Include:
      - how to generate the site
      - how to serve the site
      - how to inspect target pages through Chrome DevTools MCP
      - when to use this workflow instead of immediately writing or running E2E

- [ ] 26. Add a DevTools MCP operating playbook.
      It should define:
      - trigger conditions
      - inspection order
      - safe browser profile guidance
      - expectation that useful discoveries become automated assertions

- [ ] 27. Validate the workflow against at least one representative style question.
      Example:
      - inspect the computed background colour of an active filter button on a served page

### Phase 4 Outputs

- A documented interactive browser inspection path
- No duplicate preview stack

### Phase 4 Verification

- The agent can inspect a locally served page in a real browser without running the full E2E suite

### Phase 4 Decisions To Record

- Whether `make preview` is worth keeping as an alias
- Whether the current serve path needs port configurability or other small ergonomics improvements

---

## Phase 5 — Browser-backed visual contract foundation

**Goal:** Add the missing middle layer for computed styles and layout contracts.

- [ ] 28. Add browser-backed client test support.
      Preferred first choice:
      - Vitest Browser Mode
      Fallback if needed:
      - Playwright component tests

- [ ] 29. Create a dedicated browser-test configuration separate from the existing `client/vite.config.ts` suite.

- [ ] 30. Keep browser-visual tests separate from logic coverage.
      They should not distort or inflate normal logic coverage reporting.

- [ ] 31. Add token-aware helpers that read `templates/common.css` and convert token values into the browser-comparable format used by `getComputedStyle()`.

- [ ] 32. Confirm that global CSS tokens from `templates/common.css` are reliably loaded in the browser-backed component environment.

- [ ] 33. Add a dedicated command in `Makefile`.
      Suggested shape:
      - `make test-visual`

- [ ] 34. Record baseline runtime and failure output quality for the new browser-backed layer.

### Phase 5 Outputs

- Browser-backed component test runner
- Token-aware style assertion helpers
- Dedicated visual test command

### Phase 5 Verification

- Browser-backed test environment runs successfully in CI and locally
- Computed style assertions resolve CSS custom properties to actual rendered values

### Phase 5 Decisions To Record

- Final runner choice: Vitest Browser Mode or Playwright component tests
- Any limitations in pseudo-elements, isolation, or CSS loading

---

## Phase 6 — Visual contract rollout

**Goal:** Cover the most valuable visual regressions first, not every possible style.

### Initial contract matrix

- [ ] 35. Add `FilterButton` visual contracts:
      - active background
      - active border
      - inactive background
      - active/inactive state semantics

- [ ] 36. Add `SearchInput` visual contracts:
      - unfocused border
      - focused border
      - focus state stability

- [ ] 37. Add `FiltersPanel` visual contracts:
      - background
      - border
      - visible/collapsed state if meaningful in the component layer

- [ ] 38. Add `RangeSlider` visual contracts for inspectable elements:
      - labels
      - value text
      - any container styling that is stable and meaningful

- [ ] 39. Add `TableStats` visual contracts:
      - info-strip background
      - visible count strip styling

- [ ] 40. Add `DateFilter` visual contracts:
      - section border
      - expand button styling
      - open/closed state chrome if stable enough

- [ ] 41. Add one table-level contract for sticky header or other behavior that is hard to trust in `happy-dom` but stable in a component or narrow browser harness.

- [ ] 42. Add one responsive layout contract for a high-risk surface, such as the filter bar or filter panel arrangement.

### Contract scope rules

- [ ] 43. Keep contracts semantic and stable.
      Test what matters to the product:
      - signal state is visually distinct
      - active controls look active
      - focus states are visible
      - panels and headers retain expected chrome
      - responsive layout does not collapse incorrectly

- [ ] 44. Avoid turning browser-backed tests into screenshot diffs or giant all-style snapshots.

### Phase 6 Outputs

- A small, defensible visual contract suite
- Coverage focused on the regressions agents are most likely to introduce

### Phase 6 Verification

- Deliberately wrong token usage fails here before E2E is needed
- At least one layout-oriented contract exists, not just colour contracts

### Phase 6 Decisions To Record

- Which contracts were high-value
- Which proposed contracts were too brittle and should be removed or moved upward/downward

---

## Phase 7 — E2E cleanup and narrowing

**Goal:** Remove low-level style burden from E2E and improve signal quality in the tests that remain.

- [ ] 45. Add a Python token helper for E2E so remaining style assertions do not hardcode rgb literals.

- [ ] 46. Replace hardcoded colour values in:
      - `tests/e2e/test_navigation_and_page_loads.py`
      - `tests/e2e/test_snapshot_filters.py`
      - `tests/e2e/test_history_date_filter.py`

- [ ] 47. Remove duplicated style assertions from E2E once equivalent browser-component contracts exist.

- [ ] 48. Replace avoidable `page.wait_for_timeout(...)` calls with `wait_for_selector()` or `wait_for_function()` where observable state exists.

- [ ] 49. Improve helper-level diagnostics in E2E so failures say:
      - what state was expected
      - what selector or element was checked
      - what visible count or computed value actually occurred

- [ ] 50. Keep E2E coverage focused on:
      - generated page loads
      - navigation
      - URL state
      - downloads
      - multi-layer integration
      - asset and data-shape correctness

### Phase 7 Outputs

- Thinner, more maintainable E2E suite
- Less brittle style coupling in full-site tests

### Phase 7 Verification

- `make test-e2e` remains green
- E2E runtime and setup noise decrease or at least do not worsen

### Phase 7 Decisions To Record

- Which E2E style assertions remained because they genuinely test page-level composition
- Which waits could not be removed and why

---

## Phase 8 — CI ordering and workflow guidance

**Goal:** Ensure CI surfaces the fastest, most localising failure first.

- [ ] 51. Reorder `.github/workflows/test.yml` so failure order is:
      - fast client guardrails and fast client tests
      - browser-backed visual contracts
      - Python tests
      - conditional E2E

- [ ] 52. Cache Node dependencies and Playwright browser binaries so browser-backed visual tests do not introduce avoidable CI cost.

- [ ] 53. Update `docs/MIGRATION_PLAN.md` with the revised testing pyramid once the new layers are stable enough to document as authoritative.

- [ ] 54. Update `.github/copilot-instructions.md` so future agents know:
      - the intended local command order
      - when DevTools MCP should be used
      - when browser-backed visual tests are required
      - when E2E is required versus unnecessary

- [ ] 55. Run a controlled failure-order test by introducing one deliberate failure in each layer and confirming that CI fails first at the cheapest valid layer.

### Phase 8 Outputs

- CI workflow aligned with the revised pyramid
- Agent-facing docs aligned with actual practice

### Phase 8 Verification

- CI ordering behaves as intended
- Documentation and commands match reality

### Phase 8 Decisions To Record

- Whether any browser-backed visual suite is too expensive for the main workflow and should be conditionally triggered

---

## Phase 9 — Accessibility baseline (optional after core loop lands)

**Goal:** Capture accessibility and page-quality signals without delaying the core redesign.

- [ ] 56. Use DevTools MCP `lighthouse_audit` on representative pages:
      - `breeder.html`
      - `snapshot.html`
      - `history.html`

- [ ] 57. Record baseline results in a dedicated markdown document.

- [ ] 58. Decide whether a future `make test-a11y` or other formal gate is justified once the baseline is stable and the false-positive rate is understood.

### Phase 9 Outputs

- Accessibility/performance baseline document

### Phase 9 Verification

- None required for the main delivery path; this phase is intentionally non-blocking

### Phase 9 Decisions To Record

- Whether accessibility should become a formal gate later

---

## File inventory

### Likely new files

| File | Purpose |
| --- | --- |
| `docs/TESTING_IMPROVEMENTS_PLAN_REVISED.md` | This revised phase plan |
| `client/src/shared/__tests__/token-parser.ts` or equivalent | Parse design tokens from `templates/common.css` |
| `client/src/shared/__tests__/design-tokens.test.ts` or equivalent | Token drift guardrail |
| `client/src/shared/__tests__/css-token-compliance.test.ts` or equivalent | Svelte style compliance audit |
| `client/vite.browser.config.ts` or equivalent | Browser-backed visual test configuration |
| `client/src/test-utils/token-colors.ts` or equivalent | Token-aware browser assertion helper |
| `tests/e2e/css_tokens.py` or equivalent | Python token-aware style helper for E2E |
| Additional `*.visual.test.ts` files | Component visual contracts |
| Optional accessibility baseline document | Lighthouse audit record |

### Likely modified files

| File | Purpose |
| --- | --- |
| `Makefile` | Add fast client, watch, visual, and optional preview alias commands |
| `client/package.json` | Add scripts and browser-backed test dependencies |
| `client/vite.config.ts` | Coverage exclusions and shared test behavior updates |
| `.github/copilot-instructions.md` | Document the revised agent workflow |
| `docs/MIGRATION_PLAN.md` | Record the updated test pyramid once stabilized |
| `tests/e2e/test_navigation_and_page_loads.py` | Token-aware style assertions or moved-down checks |
| `tests/e2e/test_snapshot_filters.py` | Timeout cleanup and E2E narrowing |
| `tests/e2e/test_history_date_filter.py` | Timeout cleanup and moved-down style duplication |

---

## Acceptance criteria

1. The repo has a fast client command that is the recommended first loop for active work.
2. Design-token drift and hardcoded token-equivalent values are caught before E2E.
3. Browser-backed component tests catch at least one deliberately introduced computed-style regression before E2E is needed.
4. E2E becomes narrower and more integration-focused, not broader.
5. DevTools MCP is documented as an agent workflow and used as a bridge from diagnosis to durable tests.
6. CI failure ordering reflects the cheapest valid test layer first.

---

## Key decisions

- The revised plan keeps the strongest parts of `docs/TESTING_IMPROVEMENTS_PLAN.md`, especially:
  - token-aware style assertions
  - browser-backed visual contracts
  - E2E style cleanup
  - DevTools MCP as a complementary workflow

- The revised plan changes the order of work to prioritize:
  - fast local feedback
  - test-helper extraction
  - smaller seams in large component tests
  - reuse of existing preview infrastructure
  - broader visual contracts beyond colour-only checks

- DevTools MCP remains non-blocking and interactive.

- E2E remains required for page-level and full-site behavior.

---

## Further considerations

### Runner choice

Start with Vitest Browser Mode because it fits the current Vite and Testing Library setup.
If CSS loading, isolation, or debugging quality is materially worse than Playwright component
tests, switch early rather than forcing a poor fit.

### Pseudo-elements

Pseudo-elements like slider thumbs remain hard to validate through ordinary computed-style
assertions. Static compliance rules plus limited interactive inspection are acceptable guards for
those cases.

### Keep the contract matrix small

The purpose of browser-backed visual tests is not to mirror the entire CSS layer. The purpose is
to protect the highest-value regressions with direct, explainable failures.

### This document must evolve

After each phase, update the next phases based on what was learned. If a phase reveals a better
runner, a better helper shape, or a better division between browser-backed tests and E2E, the plan
should reflect that immediately rather than preserving outdated assumptions.
