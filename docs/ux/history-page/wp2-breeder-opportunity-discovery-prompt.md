# WP2 Discovery Prompt — Breeder Opportunity KPIs

> Ready to copy-paste into a new planning-mode chat window.
> Generated from `docs/prompt-templates/MOCK_DISCOVERY_PROMPT_TEMPLATE.md`.

---

You are doing the discovery phase for `History Page — Breeder Opportunity KPIs`.

This work package is `WP2 — Section 2: Breeder Opportunity KPIs`.

Your job in this prompt is to create one artifact only:

1. A discovery memo at `docs/ux/history-page/wp2-breeder-opportunity-discovery.md`

Do not write the spec.
Do not write the executable plan.
Do not implement product code.
Do not write files to disk in the first step.

### Scope

- Intended scope: The Comparison Controls panel and Breeder Opportunity section (Section 2)
  as defined in the mock's `.comparison-panel` and `#breeder-section` elements. Specifically:
  1. Comparison controls panel — focus genus picker, peer set editor, compare mode toggle
     ("Peer average" | "Market baseline"), state badge and copy. This panel is shared with
     WP3 (Bias Control), so component ownership must be decided during this discovery.
  2. Empty/placeholder state for the breeder section when no focus genus is selected.
  3. Four Breeder KPI cards: Focus genus scarcity rate, Median wishlist in-stock, Restock
     cadence, and Opportunity score. The Opportunity score card includes an expandable
     "How this works" panel — richer than the `?` info-popovers in WP1.
  4. Opportunity score bar chart with 3 switchable compare views: `none` (all peers ranked),
     `peer-average`, `market-baseline`.
  5. Opportunity ingredients rank table (per-genus scarcity / demand / restock / read badges;
     highlight row for the focus genus).
  6. A new computation engine (or extension of `market-health-engine.ts`) that derives a
     Breeder Opportunity payload from `MarketHealthRawData`. This must include a formula for
     the Opportunity Score — see Known Constraints below.
  7. Fixture files and Storybook stories following the WP1 pattern.

- Out of scope:
  - Section 3 Bias Control KPIs (WP3)
  - Section 4 Filtered Data Preview (WP4)
  - Replacing `history.html` with `history-insights.html` as the canonical page
  - Global genus selector UI (delivered by WP-Arch — discovery must verify its status)
  - Time window filter UI panel
  - Python-side generator changes

- Known constraints:
  1. **WP-Arch dependency.** The handoff spec (§12 staged delivery model) says WP2 depends
     on WP-Arch being merged. The discovery memo must verify WP-Arch's current status (is it
     merged? does the genus selector exist and wire to `buildMarketHealthPayload`?) and flag
     it as a blocker if not.
  2. **Opportunity Score formula is undefined.** The formula is described only loosely in the
     mock as "scarcity + demand + restock cadence composite". The memo must either propose a
     formula conservative enough to pass the project's market analysis philosophy (see
     copilot-instructions.md § Market Analysis Design Intent — "signal stability over early
     detection", "conservative by default") or flag it as a blocking open question requiring
     human sign-off before planning begins. Do not invent an arbitrary formula.
  3. **Comparison controls are shared with WP3.** Component ownership must be decided in this
     discovery phase — do not defer it to the spec.
  4. **Two selection layers must be clearly separated.** The global genus selector (WP-Arch)
     determines which genera are in scope for the whole page. The comparison controls panel
     (WP2) assigns a focus genus and peer set *within* that scope. The memo must define how
     the two layers interact — specifically, what happens when the global genus selection
     changes after a focus genus has already been assigned.
  5. All Svelte components must use Svelte 5 runes syntax (`$props`, `$state`, `$derived`).
  6. No hardcoded colours; all colours must use design tokens from `templates/common.css`.

### Source material

- Mock: `docs/ux/history-page/history-kpi-concepts-mockup.html`
  Focus elements are `#breeder-section` (the Breeder Opportunity section) and the
  `.comparison-panel` section immediately above it. The mock is a runnable HTML file with
  live JavaScript — open it in a browser or use Chrome DevTools MCP to inspect computed
  styles rather than estimating values from the CSS source alone.

- Relevant code paths:
  - `client/src/history-page/` — all existing WP1 components and engine; read every file
  - `client/src/history-page/types.ts` — payload type contracts; WP2 will extend these
  - `client/src/history-page/market-health-engine.ts` — existing computation engine; WP2
    must decide whether to extend this file or add a sibling engine
  - `client/src/history-page/index.ts` — page entry point and mount logic
  - `client/src/history-page/MarketHealthSection.svelte` — section shell pattern to follow
  - `client/src/history-page/MarketKpiCard.svelte` — KPI card pattern; WP2 cards may reuse
    or need a variant
  - `client/src/history-page/__fixtures__/` — existing WP1 fixture files
  - `client/src/history-page/MarketHealthSection.stories.ts` — Storybook story pattern
  - `src/website/generate_website.py` — specifically `generate_history_insights_page()`
    to understand what raw data is already injected into the page
  - `templates/history_insights_page.html` — Jinja template for the insights page
  - `templates/common.css` — all design tokens (the `:root` block)

- Supporting docs:
  - `docs/ux/history-page/market-health-handoff-spec.md` — read §7 (component boundaries
    and payload type contracts), §12 (staged delivery model and WP dependency table), and
    the WP-Arch note about genus selector wiring
  - `docs/ux/history-page/implementation-extensions.md` — engineering decisions made during
    WP1 that are not in the mock (e.g. run dates in sparkline readout)
  - `docs/ux/history-page/market-health-implementation-plan.md` — WP1 implementation plan;
    understand which phases are complete and what patterns were established
  - `docs/MIGRATION_PLAN.md` — current stable client architecture reference
  - `docs/SIZE_VARIANT_IDENTITY_REQUIREMENTS.md` — Decision 4 (max-variant dedup for
    wishlist/price) and Decision 2 (size-transition detection), both referenced in WP1 spec
  - `.github/copilot-instructions.md` — CSS conventions, Svelte 5 runes authoring rules,
    testing pyramid, market analysis design philosophy

- Storybook mode: `forced-on`
  WP1 established Storybook stories as the verification harness for this page section.
  WP2 must follow the same pattern. Storybook is not optional for this work package.

- Browser tooling available: Chrome DevTools MCP (`mcp_chrome-devtoo_*` tools in VS Code).
  Use it to inspect the mock's computed styles for the comparison controls panel, KPI cards,
  bar chart, and ingredients table. Capture `background-color`, `border-radius`, `color`,
  `padding`, `display`, and `grid-template-columns` for each major block.

### Operating rules

#### 0. Use plan-then-write

This workflow always uses planning-mode first:

- first build the discovery memo in memory only
- do not write files to disk in the first step
- output a compact continuity block that the next same-chat step can use
- wait for the explicit follow-up instruction to write
  `docs/ux/history-page/wp2-breeder-opportunity-discovery.md`

Before finalizing the discovery memo, re-ground on primary sources.

#### 1. Read before concluding

Before writing the discovery memo, read the mock and the relevant code/docs in full.

You must understand:

- current architecture and feature boundaries
- existing component and template patterns
- shared CSS token source and styling conventions
- global selectors or layout rules that could collide with planned markup
- test and preview workflow
- data dependencies, payload shapes, and server/client boundaries where relevant

If the mock is inspectable HTML and browser tooling is available, inspect it in a browser.
Do not rely on screenshots alone if computed styles can be read directly.
Inspect the repo first and use the canonical commands you find in places like `Makefile`,
`package.json`, task configs, and existing docs. Do not ask the human to provide or
override those commands. If Storybook is used, use the repo-defined Storybook command.
Only ask follow-up questions if the repo is genuinely ambiguous.

#### 2. Inspect the mock as a real artifact

Build an internal inventory of the mock covering:

- major sections or blocks
- visible states and variants (especially the 3 compare-view states in the bar chart, the
  empty/placeholder state, and the focus/peer-set pill states in the comparison controls)
- copy and hierarchy
- layout model per block
- card, panel, badge, pill, and emphasis treatments
- interactions visible in the mock
- responsive clues

For inspectable mocks, capture computed values for the key elements, including:

- `display`
- `flex-direction` or `grid-template-columns`
- `background-color`
- `color`
- `border`
- `border-radius`
- `padding`
- `font-size`

#### 3. Decide whether Storybook is worth using later

Storybook mode is `forced-on` for this work package. Recommend a Storybook-based
verification approach for component states. Remember: Storybook is good for isolated
component states but insufficient for page-level CSS and global integration issues — the
recommendation must cover what goes in Storybook stories and what goes in visual contract
tests or E2E tests instead.

#### 4. Write the discovery memo as a planning input, not a vague summary

Write `docs/ux/history-page/wp2-breeder-opportunity-discovery.md` with these sections:

1. Purpose and scope summary
2. Existing architecture and feature boundaries
3. Candidate implementation approaches
4. Recommended approach and why
5. Reuse opportunities
6. Likely files / modules / templates / components to touch later
7. CSS token and global selector constraints
8. Data / API / DTO / backend implications (payload type extensions, engine additions)
9. Verification harness recommendation
10. Storybook recommendation with rationale
11. Risks and likely drift points
12. Open questions resolved conservatively, or explicitly listed if truly unresolved
13. Recommended work-package boundaries if the feature should be split further
14. Recommended next workflow
15. Handoff inputs for the next stage

For `Candidate implementation approaches`:

- present up to 3 viable approaches, not more
- include the main tradeoff for each
- if there is only one credible approach, state that directly rather than inventing weak
  alternatives

For `Recommended next workflow`:

- choose one of: `PLAN_ONLY`, `MOCK_TO_SPEC_PLAN`, or `stop for human decision`
- explain why that is the correct next step

The final section, `Handoff inputs for the next stage`, must include:

- which downstream workflow the user should run next
- recommended spec path
- recommended plan path
- the must-capture visual requirements that the later spec must spell out explicitly
  (pay special attention to the 3-state bar chart switching, the comparison controls
  panel states, and the `.section-placeholder` / `.section-live` reveal pattern)
- the must-check integration risks that the later plan must include (especially WP-Arch
  dependency and the Opportunity Score formula)

The discovery memo is an input to the next stage, but not the only input.
The later plan-only or spec+plan prompt must still re-read the mock and the key repo files.
Use the discovery memo as an accelerator and decision record, not as a substitute for
primary sources.

#### 5. Required quality bar

The memo must be strong enough that a later spec-and-plan agent can use it as a durable
input.

Do not stop at observations like "looks like a card grid".
Tie observations to the existing repo and likely implementation consequences. In particular:

- For the comparison controls panel: state exactly which file should own it and why.
- For the Opportunity Score: either propose a formula with rationale grounded in the
  market analysis philosophy, or write an explicit blocking open question with the minimum
  information a human needs to decide.
- For the WP-Arch dependency: state clearly whether it is blocked, partially done, or
  fully resolved based on what you find in the repo.

#### 6. End state for this chat step

After building the discovery memo in memory:

- summarize the proposed discovery memo structure
- summarize the candidate approaches and the recommended one
- summarize the top implementation risks
- summarize the recommended next workflow and why
- summarize the Storybook recommendation and why
- output a short instruction block for the next same-chat step:
  `Switch to writing-capable agent mode and write the approved discovery memo to docs/ux/history-page/wp2-breeder-opportunity-discovery.md`
- stop

Do not write files to disk until explicitly asked.

#### 7. Default behavior after writing the file

After writing `docs/ux/history-page/wp2-breeder-opportunity-discovery.md`:

- summarize the top implementation risks
- summarize the recommended next workflow and why
- summarize the Storybook recommendation and why
- stop

Do not begin writing the spec or the executable plan unless I explicitly ask you to
continue.

### Deliverable

Write:

- `docs/ux/history-page/wp2-breeder-opportunity-discovery.md`

Then report:

1. where the file was written
2. whether Storybook was recommended, rejected, or mandated
3. the top 5 findings that the later spec/plan stage must preserve
