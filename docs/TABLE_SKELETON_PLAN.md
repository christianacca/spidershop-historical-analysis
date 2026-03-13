# Table Skeleton Plan

## Purpose

Reduce the visible blank gap and breeder-page layout shift that occur between initial server render and client-side Svelte table mount.

The chosen approach is a **server-rendered table skeleton** that appears in the HTML before JavaScript runs, reserves space for the eventual table, and is removed only after the real Svelte table mounts successfully.

This document is intended to be reusable context for future implementation work.

## Problem Summary

- The current table pages render an empty mount target in the server HTML.
- The real table appears only after the relevant Svelte entry point loads and mounts.
- On the deployed site, the bundling improvement reduced request fan-out substantially, but breeder-page CLS remained high.
- The remaining issue is primarily **layout instability**, not server latency or bundle fan-out.

## Current Findings

### Performance observations

- Production request fan-out was reduced successfully by the Vite bundling change.
- Breeder page LCP is already acceptable on a fast desktop connection.
- Breeder page CLS remains poor because content below the table area is pushed downward when the table appears.
- History page is much less affected, but may still benefit from a consistent first-paint skeleton pattern.

### Architectural conclusion

- A **Svelte skeleton component** is the wrong tool for this first-paint problem.
- If the skeleton is client-rendered, it appears too late to solve the blank-gap/CLS issue.
- The skeleton must live in the **server-rendered template layer**.

## Decision

### Use a server-rendered skeleton, not a Svelte skeleton

The skeleton should be emitted by the existing Jinja template flow and styled in the static CSS layers.

### Reuse one shared skeleton system with simple page variants

Reuse is desirable, but it should happen in the **template layer**, not through a shared Svelte loading component.

The shared system should support:

- analysis-table variant for breeder and dealer
- snapshot-table variant for snapshot
- history-table variant for history

History should use the same skeleton system for consistency, but without introducing any new shared client abstraction into the transitional history slice.

## Scope

### Included

- server-rendered skeleton markup before the mount root
- reserved vertical space to reduce CLS
- subtle loading presentation that feels table-shaped rather than blank
- minimal client-side handoff to remove or hide the skeleton after mount
- shared template-level reuse across breeder, dealer, snapshot, and history

### Excluded

- server-rendering real interactive rows
- SSR or true Svelte hydration
- virtualization
- pagination redesign
- history-page architecture changes beyond minimal mount handoff
- species-page changes

## Implementation Strategy

### 1. Add reusable server-rendered skeleton markup

Create a shared skeleton macro or partial in the template layer.

Preferred locations:

- `templates/macros.html`
- `templates/table.html`

The skeleton should accept simple parameters such as:

- column count
- row count
- variant name

### 2. Insert the skeleton in the shared table include

Update `templates/table.html` so that:

- the no-data branch remains unchanged
- the normal branch emits the skeleton before the mount root
- the JSON data script remains unchanged
- the mount root stays stable for current page entry points

Conceptually:

1. render skeleton
2. render mount root
3. inject `window['...Data']`

### 3. Pass lightweight variant metadata from wrapper templates

Update wrapper templates only as needed:

- `templates/analysis_page.html`
- `templates/snapshot_page.html`
- `templates/history_page.html`

Use only lightweight metadata such as variant or row-count. Do not add new history-specific client abstractions.

### 4. Style the skeleton in static CSS layers

Primary CSS location:

- `templates/common.css`

Optional page-specific refinements only if necessary:

- `templates/analysis.css`

Styling requirements:

- reserve realistic table height
- include a header row and several body rows
- use existing design tokens only
- avoid hard-coded colors
- avoid overly noisy shimmer
- avoid visual mismatch with the real table layout

### 5. Add minimal client-side handoff

The skeleton should be hidden or removed only after the real table mounts successfully.

Likely client touch points:

- `client/src/shared/page-init.ts`
- `client/src/history-page/index.ts`

The handoff should be minimal:

- no reusable Svelte skeleton component
- no heavy new state model
- no change to the table component architecture itself unless required

## Recommended UX Shape

### Analysis pages

Use a table-shaped skeleton with:

- one placeholder header row
- roughly 8 to 10 placeholder data rows
- reserved height tuned to visible above-the-fold space

### History page

Use the same visual language, but allow a taller variant if needed because history has a denser table and different controls.

### Loading treatment

- Prefer a skeleton, not a spinner
- A spinner may be used as a minor accent, but should not be the primary loading treatment
- The first goal is CLS reduction; the second goal is perceived continuity

## File Inventory

### Primary implementation files

- `templates/table.html`
- `templates/macros.html`
- `templates/analysis_page.html`
- `templates/snapshot_page.html`
- `templates/history_page.html`
- `templates/common.css`
- `templates/analysis.css`
- `client/src/shared/page-init.ts`
- `client/src/history-page/index.ts`

### Primary test files

- `client/src/shared/page-init.test.ts`
- `tests/website_module/` existing page-generation tests
- `tests/e2e/` relevant browser tests for initial load and post-mount behavior

## Testing Plan

### Client tests

- Run `make test-client-fast` during iteration if client files change
- Run `make test-client` for final client verification

### Python/template tests

- Run `make test`

### Visual and browser verification

- Run `make test-visual` if the CSS change needs browser-backed visual assertions
- Run `make test-e2e` because website output and browser load behavior will change

### Chrome DevTools MCP verification

Use Chrome DevTools MCP as part of final verification for both local preview and deployed pages.

Required DevTools MCP checks:

- open breeder and history pages in a real browser
- inspect the initial DOM before mount and confirm the skeleton is present in server-rendered HTML
- verify the skeleton disappears after successful Svelte mount
- capture performance traces and compare LCP, CLS, and request count before and after the change
- inspect network requests to confirm the skeleton does not introduce unexpected blocking assets
- inspect layout behavior during initial load to confirm breeder-page CLS improves materially

DevTools MCP is not a substitute for automated tests, but it is required here because the goal is a real-world improvement in first paint, layout stability, and mount handoff.

### Live validation

After deploy, re-profile:

- breeder page
- history page

Use Chrome DevTools MCP for the live re-test, not just Lighthouse-style summary numbers. The live verification should include:

- performance trace capture on deployed breeder and history pages
- network request inspection
- direct confirmation that the skeleton exists before mount and is gone after mount
- comparison against the current post-bundling baseline metrics

Primary success metric:

- breeder CLS should drop materially from the current post-bundling baseline

Secondary checks:

- skeleton visible before mount
- skeleton removed after mount
- no regression in table functionality
- no regression in no-data states
- no new unexpected render-blocking behavior in DevTools traces

## Risks

### Risk: skeleton removed too early

If hidden before successful mount, users may briefly see an empty gap again.

Mitigation:

- remove or hide only after mount succeeds

### Risk: visual mismatch between skeleton and real table

If the skeleton height or layout is too different from the final table, CLS reduction will be weaker.

Mitigation:

- use realistic table proportions and row counts
- prioritize reserved space over decorative effects

### Risk: over-engineering history

History is a transitional slice and should not become the anchor point for new shared client abstractions.

Mitigation:

- reuse the shared template skeleton only
- keep history-specific client changes minimal

## Non-Goals

- replacing the Svelte migration
- reverting to full server-rendered interactive tables
- introducing virtualization as part of this fix
- redesigning page structure or content hierarchy below the table

## Summary Recommendation

Implement a **shared server-rendered table skeleton system** in the Jinja/static CSS layers, then add a minimal mount-time handoff in the client entry logic.

The implementation should be verified not only by unit, Python, visual, and E2E tests, but also by **Chrome DevTools MCP inspection and tracing** on both preview and deployed pages, because the main success criteria are user-visible performance and layout stability.

This is the smallest approach that directly addresses the current live problem:

- request fan-out is already fixed
- LCP is already acceptable
- breeder CLS is still poor

The next implementation should therefore optimize **first-paint continuity and layout stability**, not client architecture complexity.