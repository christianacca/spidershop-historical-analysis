# Agent Prompt — Market Health KPI Section (History Page)

> **How to use this file:** Copy the content of the "Prompt" section below into the
> VS Code Copilot agent-mode chat (or any LLM agent). It is self-contained.

---

## Prompt

You are implementing **Work Package 1 (WP1) of 5** for the redesigned History page of
the spidershop-historical-analysis project.

> **WP1 scope: Section 1 — Market Health KPIs only.**
> The mock shows four sections (Market Health KPIs, Breeder Opportunity KPIs, Bias Control
> KPIs, Filtered Data Preview). This work package covers Section 1 **only**. Sections 2–4
> are future work packages (WP2–WP4). An infrastructure work package (**WP-Arch**) between
> WP1 and WP2 will add the genus selector UI, lazy-load static JSON generator, and Svelte
> fetch hook. Do not implement, scaffold, or stub anything from WP-Arch or WP2–WP4 here.
>
> **New page, not replacement.** WP1 delivers a new `history-insights.html` page alongside
> the existing `history.html`. Do NOT modify or delete `history.html` or
> `templates/history_page.html`. Those files are touched only after all work packages
> (WP1, WP-Arch, WP2–WP4) are merged.

---

### STEP 1 — Read these files BEFORE writing a single line of code

Read all four files in full. Do not start Phase 1 until you have read them.

1. `docs/ux/history-page/market-health-implementation-plan.md` — engineering blueprint;
   nine phases; all task checklists; all housekeeping rules; GATE format
2. `docs/ux/history-page/market-health-handoff-spec.md` — full functional specification;
   component rendering rules; data structures; design decisions
3. `docs/ux/history-page/history-kpi-concepts-mockup.html` — visual reference; open in
   a browser if possible; use it to reconcile component layout and copy strings
4. `templates/common.css` `:root` block — CSS design token definitions; you will need
   these for Phase 1's token mapping table

After reading: verify the four files are consistent and note any discrepancy in the Phase 1
feed-forward log entry. Then start Phase 1.

---

### STEP 2 — Non-negotiable operating rules

These rules override any general coding instinct. Violating them produces a broken
build, wrong artefact paths, and broken CI — not just a style issue.

#### 2a. Make commands only — NEVER bypass

| Task | Command |
|---|---|
| Client unit tests (no coverage) | `make test-client-fast` |
| Client unit tests + coverage | `make test-client` |
| Python unit tests | `make test` |
| E2E Playwright tests | `make test-e2e` |
| Browser-backed visual contracts | `make test-visual` |
| Generate website | `make generate-website` |
| Serve site locally | `make preview` |
| Start Storybook | `make storybook` |

**Never run** `pytest`, `vitest`, `npx vitest`, `python -m pytest`, `python -m website`, or
`node` directly. Make commands set the working directory, artefact paths, and environment
correctly. Bypassing them scatters CSV files, breaks coverage numbers, and fails CI.

**Never generate the website by running Python** (`python src/website/...` or similar).
Always use `make generate-website` or `make preview`.

#### 2b. TDD — tests first, always

Write the failing test before the implementation. Confirm it fails with the expected
error. Then implement. This applies to every new function and every new component.

#### 2c. Storybook stories are first-class deliverables

Each phase that builds a component (Phases 2–5) requires a co-located `*.stories.ts` file.
These stories are not optional documentation — they are the living spec for visual
acceptance. The implementation plan lists the exact story names and the `evaluate_script`
assertions required for each. Treat a failing `evaluate_script` assertion the same as a
failing unit test: stop, fix, then re-run.

#### 2d. Chrome DevTools MCP for style verification

When the plan calls for an `evaluate_script` check, use the Chrome DevTools MCP tool:

1. Ensure Storybook is running: `make storybook`
2. Navigate to the story URL (format: `http://localhost:6006/?path=/story/<story-id>`)
3. Call `evaluate_script` with the script from the plan
4. Compare the returned values against the expected values in the plan
5. If any value differs: fix the component or CSS, then re-run evaluate_script

Do not skip a DevTools MCP check because the unit tests are green. Computed styles can
drift even when logic tests pass.

#### 2e. New page, not replacement — NEVER touch `history.html`

`templates/history_page.html` and `history.html` are out of scope for this work package.
Phase 7 creates a **new** `history-insights.html` page and a **new**
`templates/history_insights_page.html` template. Any edit to the existing history files
is a scope violation.

Do **not** build any genus selector UI, lazy-load JSON infrastructure
(`market-health/genus/` or `market-health/species/` static files), or Svelte fetch hook.
Those belong to WP-Arch and have no spec yet.

---

### STEP 3 — Phase protocol (mandatory for every phase, no exceptions)

The implementation plan defines **five mandatory steps** at the end of every phase.
You must complete all five before starting the next phase. An incomplete phase means
the next phase builds on a broken foundation.

```
[ ] H1 — Mark every task checkbox in the phase as ✅
         Only check off a task after it is actually done, not speculatively.

[ ] H2 — Reflection: scan every new file against the code smell checklist in the plan.
         Fix ALL issues before committing.
         Do NOT commit with a TODO comment intending to fix later.
         This is a real review step, not a checkbox. Take 30–60 seconds per file.

[ ] H3 — Feed-forward: append a dated entry to the Feed-forward Log at the bottom
         of the implementation plan. Required even when there is nothing new to add
         (write "no new findings"). This creates the audit trail for the reviewer.

[ ] H4 — Commit:
           git add -A && git commit -m "Phase N: <one-line summary>"
         Then verify it landed:
           git log --oneline -1
         If the commit is not in the log, something went wrong — do not proceed.

[ ] GATE — Output the phase completion block (format below) in your chat response.
           Every field must contain actual terminal output — no placeholders.
           If any field cannot be filled, the phase is BLOCKED: stop, fix it, then output.
```

**GATE format — fill every field with real output and post it in your response:**

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE N COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of: make test-client-fast  or  make test]
║  Commit:   [paste output of: git log --oneline -1]
║  Stories:  [StoryName → evaluate_script passed]  or  [N/A — no stories this phase]
║  Blockers: none  /  [name any deferred item with a short reason]
╚══════════════════════════════════════════════════════════════╝
```

**The GATE block in your response is the ONLY acceptable evidence that the phase is done.**  
Its absence means the phase is not complete and you must not start the next phase.

---

### STEP 4 — Phase execution order

Execute phases strictly in order. Do not skip, merge, or reorder.

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9
```

| Phase | Summary |
|---|---|
| 1 | Foundation — TypeScript types, test fixtures, CSS token map, Storybook install |
| 2 | `MarketSparkline` SVG component + story + DevTools MCP assertions |
| 3 | `MarketKpiCard` component + story + DevTools MCP assertions |
| 4 | `MarketEventsCard` component + story + DevTools MCP assertions |
| 5 | `MarketHealthSection` island (assembly + state) + story + DevTools MCP assertions |
| 6 | Python `market_health_dto` module + unit tests |
| 7 | Create `history-insights.html` (new page, `history.html` untouched) — new template, new nav entry, payload injection, E2E green |
| 8 | Visual acceptance — full DevTools MCP sweep across all stories + preview site |
| 9 | Push branch, open PR, output review handoff prompt |

Each phase has a detailed task list in the implementation plan. Follow it exactly —
do not reorder tasks within a phase, and do not add tasks that are not in the plan
without noting the addition in the feed-forward log.

---

### STEP 5 — Phase 9 deliverable: review handoff prompt

After creating the PR in Phase 9, run `gh pr view --json url,number` to get the PR
number and URL. Then output the following block in your response, **with all three
placeholders replaced by real values from your Phase 8 feed-forward log**. The user
will paste this into a new chat session to initiate a spec-conformance review.

---

**REVIEW HANDOFF PROMPT — paste into a new chat session:**

> Review PR #[PR_NUMBER] (`history-page-market-health`) against the spec and plan for
> the Market Health KPI section.
>
> PR: [PR_URL]
>
> Before reviewing any code, read these files in full:
> 1. `docs/ux/history-page/market-health-handoff-spec.md`
> 2. `docs/ux/history-page/market-health-implementation-plan.md`
> 3. `docs/ux/history-page/history-kpi-concepts-mockup.html`
>
> Then diff the PR and systematically verify each area:
>
> **TypeScript:** `types.ts` interfaces match spec §7.2 exactly (field names, types,
> optional/required) · Fixtures match §8.2 (currentQuarter) and §8.3 (allTime) ·
> No `any` types · No TODO/FIXME
>
> **Components:** `MarketSparkline` rendering matches spec §4.1 (opacity values, baseline
> axis, run-axis labels) and §4.2 (run-selection, `.is-subdued` opacity) ·
> `MarketKpiCard` delta CSS classes and copy strings match spec §3 exactly ·
> `MarketEventsCard` copy and value formats match spec §5 · `MarketHealthSection`
> sparkline support row matches §4.3–§4.5, state wiring correct · No hardcoded colours
> in any `<style>` block — all values must be `var(--token)`
>
> **Python:** `market_health_dto.py` computation matches Phase 6 rules in the plan ·
> Species-level deduplication applied per SIZE_VARIANT_IDENTITY_REQUIREMENTS Decision 4 ·
> Size transitions NOT counted as drop+add · Events are species-level · Coverage ≥ 80% ·
> All required test cases from the Phase 6 checklist are present
>
> **Integration:** `window.marketHealthPayloads` injected as all-windows
> `Record<WindowId, MarketHealthPayload>` · Island mount guarded (element AND payloads
> both present) · Dev-mode payload validation present · E2E test covers: section
> renders, 4 KPI cards populated, no console errors
>
> **Deferred items from Phase 8 (assess whether any are spec violations):**
> [DEFERRED_ITEMS]
>
> For each item found, report: **PASS** / **FAIL** (spec violation — quote the spec §,
> quote the code, suggest a fix) / **CONCERN** (not a violation but worth noting).

---

### STEP 6 — If you get stuck

- A failing test is not a reason to skip the phase. Fix the test or the code.
- A failing `evaluate_script` assertion is not a blocker to defer — it is a failing test.
  Fix the CSS or component before outputting the GATE block.
- If a task in the plan is genuinely ambiguous, resolve it by re-reading the spec and the
  mock. If still ambiguous, make the more conservative choice and record your reasoning
  in the feed-forward log.
- Never push a WIP commit as "Phase N complete". The GATE block must reflect real green
  test output.

---

### Quick reference

```bash
# Start here (one-time setup, already done if repo is cloned):
make e2e-install          # install Playwright browser binary

# During development:
make test-client-fast     # fast Vitest run (no coverage) — use during active iteration
make test-client          # Vitest + coverage — required before GATE on any client phase
make test                 # Python unit tests — required before GATE on any Python phase
make test-e2e             # Playwright E2E — required for Phase 7 GATE and Phase 9 pre-flight
make test-visual          # browser-backed visual contracts — required when style blocks change
make storybook            # start Storybook at http://localhost:6006
make preview              # generate site + serve at http://localhost:8000
```
