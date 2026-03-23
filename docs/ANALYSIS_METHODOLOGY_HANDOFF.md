# Analysis Methodology UI Handoff

## Purpose

Implement a high-fidelity methodology UI for the analysis pages that matches the visual and
interaction intent of the mock in `tmp/analysis-methodology-mockup.html`, with one explicit
exception:

- Do **not** implement the mock's combined breeder/dealer page mode switch.
- The real product keeps **separate breeder and dealer pages**.
- Each page should render its **own page-specific methodology panel** using the same layout
  system and interaction model.

This handoff replaces the earlier low-prominence, below-the-table methodology plan. The target
experience is now the mock's information hierarchy: the methodology is a first-class explanatory
surface, not an appendix.

## Scope

This handoff applies to:

- `src/website/generate_website.py`
- `src/website/page_config.py`
- `src/website/analysis_methodology.py`
- `templates/analysis_page.html`
- `templates/macros.html`
- `templates/analysis.css`
- any supporting tests in `tests/website_module/`, `tests/e2e/`, and `tests/visual/` as needed

It does **not** change:

- the underlying breeder/dealer scoring rules
- row-level payloads sent to Svelte islands
- the meaning of legend content
- the existing Drivers tooltip behavior
- the single-page routing model of the mock

## Non-Negotiable Constraints

These constraints still hold even though the UX target has changed.

### 1. Read-only explanatory UI

The methodology panel explains existing Python-driven outputs. It does not recalculate signals,
change thresholds in-browser, or mutate analysis results.

### 2. Python rules remain the source of truth

All thresholds, labels, worked-example logic, and explanatory copy must be derived from the live
Python rule system already used to generate the tables.

Do not invent parallel threshold definitions in JavaScript or hard-code values into templates that
can drift from the analysis engine.

### 3. No new row metadata for methodology rendering

Do not add hidden methodology payloads to each table row. The methodology panel is page-level
content and should be rendered from page-level data.

### 4. Preserve the legend and Drivers tooltip

The legend still matters and must remain on the page. The Drivers tooltip in the analysis table
must remain intact.

### 5. Separate breeder and dealer pages

The mock's breeder/dealer toggle was a prototype convenience for comparing both variants in one
HTML file. The production site keeps separate pages:

- breeder page renders breeder methodology
- dealer page renders dealer methodology

## Final UX Decision

### Methodology becomes the main explanatory block

The methodology panel should appear **above the legend and above the table**, in the prominent,
card-based layout shown in the mock.

Target page order:

1. page title and intro
2. summary/KPI cards
3. instruction or context callout
4. methodology panel
5. legend
6. analysis table

This is a deliberate reversal of the previous handoff. The goal is to let users understand the
classification model before reading the legend or interpreting row-level signals.

### Internal organization matches the mock

The methodology panel should use the mock's richer composition:

- prominent container panel
- clear section header and supporting intro copy
- a compact top-level explanation row or callout
- tabbed or pill-based internal navigation for major views
- card-based content inside each view
- short explanatory asides that explain why signals escalate or do not escalate

The methodology content should feel like a structured briefing, not a long markdown appendix.

### Allowed interaction model

Tabbed internal navigation is allowed and expected.

Examples of acceptable tab labels:

- `Threshold Inventory`
- `Decision Tree`
- `Worked Example`

This interaction is presentational only. Switching tabs must not alter page data or analysis
results; it only swaps visible explanatory content.

## Page-Level UX Structure

Each analysis page should render a methodology panel with the following structure.

### 1. Panel shell

A visually prominent panel, consistent with the mock's `methodology-box` concept.

Required characteristics:

- strong section heading
- short descriptive intro
- clear containment distinct from legend and table
- card-based internal spacing
- responsive layout that collapses cleanly on mobile

### 2. Context callout

A short block near the top of the panel that explains how to read the methodology.

Purpose:

- frame the methodology as a guide to signal interpretation
- explain that supply drives the base signal and demand modifies confidence/urgency
- set user expectations before they inspect tabs/cards

This can be styled as an info bar, note card, or explainer strip, consistent with the mock.

### 3. Tab row / pill row

A compact navigation row inside the methodology panel.

Minimum tabs:

- `Threshold Inventory`
- `Decision Tree`
- `Worked Example`

Optional additional tab:

- `Edge Cases`

If edge-case content fits naturally into the other three tabs, a fourth tab is not required.

### 4. Tab content area

Each tab should render one or more cards. The content should use short labels, small lists,
compact narrative, and visually distinct result callouts, similar to the mock.

## Tab Specifications

### Threshold Inventory tab

This tab should present the page's core rule inputs as scannable cards rather than one long list.

For breeder, include cards or grouped blocks covering at minimum:

- supply pattern / out-of-stock persistence
- price trend interpretation
- wishlist pressure meaning
- wishlist delta meaning
- escalation rules and non-escalation rules

For dealer, include cards or grouped blocks covering at minimum:

- stock reliability bands
- average out-of-stock duration / restock speed
- price pressure interpretation
- wishlist pressure meaning
- wishlist delta meaning
- escalation rules and non-escalation rules

Expectations:

- thresholds shown here must come from live constants or live rule functions where possible
- labels should be concise and product-facing
- cards can include small "what this means" notes
- the layout should visually resemble the mock's threshold cards and side-asides

### Decision Tree tab

This tab should explain the order of evaluation in a compact, card-based flow.

It should not be a literal code dump. It should answer:

- what is evaluated first
- what can reinforce a signal
- what cannot override a stronger supply-based conclusion
- why neutral decisions are preferred when evidence is weak

Structure guidance:

- step cards, decision cards, or a short flow stack
- each step has a title and one or two lines of explanatory copy
- include explicit "does not override" notes where important

Breeder emphasis:

- supply pattern determines the base classification
- price trend can reinforce or soften borderline cases
- wishlist metrics can escalate emerging opportunities only when the rule allows it
- sustained scarcity must never be downgraded

Dealer emphasis:

- stock reliability and restock speed determine the base risk view
- price pressure and wishlist behavior can reinforce urgency
- healthy supply must not be overridden by demand alone

### Worked Example tab

This tab should show a concrete example row and explain how the page's rules classify it.

Format guidance:

- species card or result card at the top
- short list of observed facts from local demo data
- step-by-step reasoning bullets
- final result badge or callout
- short note explaining why nearby alternative outcomes did not apply

Requirements:

- use realistic species/examples from local demo data for both breeder and dealer pages
- the example should map directly to current generated demo content where possible
- copy must remain aligned with live rules

This tab should feel very close to the mock's worked-example presentation.

### Edge Cases handling

Edge cases still need to be explained, but they no longer need to exist as a separate stacked
section below everything else.

Acceptable placements:

- an `Edge Cases` tab
- a dedicated edge-case card within `Decision Tree`
- short aside cards inside `Threshold Inventory`
- a compact note card at the bottom of the methodology panel

At minimum, cover:

- newly observed species / limited history
- carryover bounds for out-of-stock wishlist handling
- bounded lookback for previous comparable observations
- why ambiguous cases remain neutral instead of being forced upward

## Visual Fidelity Requirements

The target should be recognizably close to the mock's visual hierarchy and composition.

### Required visual traits

- methodology panel is visually stronger than the legend block
- cards are used deliberately, not as plain text wrappers
- the tab row is clearly interactive and current state is obvious
- result outcomes are visually highlighted
- supporting asides help users understand "why" and "why not"
- spacing, borders, and grouping create a dashboard-like explanatory surface

### Avoid

- a plain markdown article below the table
- a single long vertical stack of generic paragraphs
- burying the methodology after the legend and table
- reducing the mock to only content parity without layout parity

### Responsive expectations

On desktop:

- tab row remains easy to scan
- cards can appear in 2-column layouts where appropriate
- worked example may use a main card with supporting side card

On mobile:

- tab row may wrap or collapse cleanly
- cards stack vertically
- no horizontal overflow from threshold or tree cards

## Data and Rendering Architecture

### Page-level data model

Continue using a page-level methodology object generated from Python.

Suggested structure:

- `title`
- `intro`
- `callout`
- `tabs`
- each tab contains structured cards, notes, badges, and small lists

A tab may contain card types such as:

- threshold cards
- aside cards
- decision steps
- example facts
- example reasoning
- result callout
- edge-case notes

Do not flatten everything into pre-rendered HTML too early. The template needs structured data so it
can faithfully reproduce the mock-style composition.

### Templating approach

Use Jinja macros to render the panel and its substructures. The goal is a maintainable component-like
server-rendered layout, not string-built HTML fragments.

Recommended macro responsibilities:

- methodology shell
- tab navigation
- threshold cards
- decision tree steps
- worked example result block
- supporting note/aside cards

### Client-side behavior

Minimal client-side behavior is acceptable for switching tabs or expanding/collapsing methodology
subsections, provided that:

- no analysis logic runs in the browser
- no thresholds are recalculated in the browser
- page still renders meaningful default content without needing data-fetching

If tabs are implemented progressively, keep the behavior lightweight and scoped to presentation.

## Content Requirements By Page

### Breeder page

The methodology content must reflect the breeder opportunity philosophy:

- supply pattern is primary
- price trend confirms or weakens borderline opportunity signals
- wishlist pressure and wishlist delta can amplify emerging signals but do not create signals alone
- always-available species remain negative despite demand noise
- sustained scarcity remains strong and is not downgraded

### Dealer page

The methodology content must reflect the dealer risk philosophy:

- stock reliability and restock speed are primary
- price pressure and wishlist behavior adjust urgency, not the base truth of supply health
- high demand can reinforce low reliability risk
- healthy supply should not be pushed into strong risk by demand alone

## Implementation Notes

### Templates

Update `templates/analysis_page.html` so the methodology panel renders before the legend and table.

Expected order inside the analysis content region:

1. summary/stat cards
2. instruction/context box
3. methodology panel
4. legend
5. table

Update `templates/macros.html` to support the richer methodology component structure required by the
mock.

### Styling

Update `templates/analysis.css` to support:

- prominent methodology shell styling
- tab row / pill row states
- threshold card grid
- decision tree cards
- worked example cards and result callouts
- aside/note cards
- responsive adaptations

Use existing design tokens from `templates/common.css`. Do not hard-code unrelated one-off values if
existing tokens already express the needed color, spacing, radius, or type scale.

### Page config and generation

Continue injecting methodology at page-config/render time. Keep breeder and dealer methodology built
explicitly from Python-side helpers.

The generation path should make it obvious which page receives which methodology object.

## Testing Requirements

This is UI-heavy work and must be validated at the correct layers.

### Unit / integration tests

Add or update tests to assert at minimum:

- breeder and dealer methodology render above the legend and table
- expected tabs render for each page
- worked-example content uses the intended demo data
- live threshold constants appear in the rendered methodology where appropriate
- legend and Drivers tooltip remain present

### Visual tests

Browser-backed visual tests are required for:

- tab active state
- methodology panel layout and card rendering
- result callout styling
- responsive stacking behavior where practical

### E2E tests

Use Playwright to verify:

- methodology panel appears before the legend and table in the real page
- tab switching works if tabs are interactive
- breeder page shows breeder-specific methodology only
- dealer page shows dealer-specific methodology only
- table interactions still work after the layout change

## Acceptance Criteria

This work is complete when all of the following are true.

### Functional

- breeder and dealer pages each have a page-specific methodology panel
- the methodology panel sits above the legend and analysis table
- the panel uses mock-faithful internal organization with tabs/pills and card-based content
- no combined breeder/dealer page switch is introduced into production
- no browser-side analysis recalculation exists

### Content

- methodology copy remains grounded in live Python rules
- breeder and dealer content reflect their distinct analysis philosophies
- worked examples align with available demo data
- edge cases are explained clearly somewhere in the panel

### UX / visual

- the result is recognizably close to the mock's hierarchy and composition
- methodology feels like a primary explanatory feature, not an appendix
- legend remains present but visually secondary to the methodology panel
- mobile layout remains readable and non-fragile

### Quality

- relevant tests pass
- visual checks pass
- E2E checks pass when required by the touched files

## Out of Scope

Do not implement the following as part of this handoff unless separately requested:

- the mock's single-page breeder/dealer switch
- editable thresholds
- per-row methodology drawers or expanded metadata payloads
- client-side recomputation of classifications
- replacing the legend entirely

## Build Sequence

Recommended implementation order:

1. restructure the methodology data model so it can express mock-style tabs/cards
2. move methodology rendering above the legend and table in the template
3. implement the new Jinja macros for shell, tabs, cards, and result blocks
4. add the required CSS for high-fidelity composition
5. add or update tests for order, content, and interaction
6. run `make test`
7. run `make test-visual`
8. run `make test-e2e`

## Summary

The target is no longer a conservative documentation appendix below the table. The target is the
mock's richer explanatory product surface, adapted to the real site's separate breeder and dealer
pages.

In short:

- keep the real site's separate page model
- keep the methodology static and Python-sourced
- keep the legend and Drivers tooltip
- move the methodology up
- make it visually prominent
- use tabs/cards/decision views like the mock
- ship a recognizably high-fidelity version of the prototype UI
