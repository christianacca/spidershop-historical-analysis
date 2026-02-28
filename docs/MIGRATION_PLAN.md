# TypeScript + Svelte Migration Plan

## How to use this document

Each phase is designed to be executed in a **separate AI conversation** to keep context tight.
Open a new conversation and start with:

> "Read `docs/MIGRATION_PLAN.md`. We are implementing **Phase N**. Begin."

At the end of each phase conversation, ask the AI to update this file — tick off completed steps
and record any decisions that deviated from the plan.

---

## TL;DR

Vite compiles `client/` (never committed to git); `dist/` is built locally via `make build-client`
and in CI before the Python generator runs.

**Phase sequence:**
Vite foundation → TypeScript → feature-slice folders → Svelte tooling →
CSS audit/tokens/BEM → data contract → primitive Svelte components →
`SortableTable` (breeder/dealer/snapshot) → `HistoryTable` → CSV download → dead-code cleanup.

**Testing strategy:** Vitest is the primary component test layer (sub-100ms, optimal for AI
iteration). Playwright E2E is the integration safety net (real browser, Python data shape, URL state).

**CSS strategy:** CSS migrates progressively into Svelte scoped `<style>` blocks. Global CSS
shrinks to chrome, design tokens, and reset only. BEM is applied only to permanent global CSS
during Phase 4a — not before, because most current classes are being deleted into Svelte scopes.

---

## Target client-side structure

```
client/
  package.json
  tsconfig.json
  vite.config.ts
  src/
    test-setup.ts
    global.d.ts             ← window.speciesChartData interface
    shared/
      constants.ts
      dom-utils.ts          ← getElement, setActiveButton, toggleRowVisibility
      sort.ts               ← sortTable
      filter.ts             ← filterByAttribute, filterRows, updateFilterBadge
      components/
        RangeSlider.svelte  ← used by SortableTable + HistoryTable
        SearchInput.svelte
        FilterButton.svelte
        SortableTable.svelte ← breeder, dealer, snapshot pages
    breeder-page/
      index.ts              ← entry point; mounts SortableTable
    dealer-page/
      index.ts
    snapshot-page/
      index.ts
    history-page/
      index.ts              ← entry point; mounts HistoryTable
      HistoryTable.svelte   ← structurally different from SortableTable
      DateFilter.svelte     ← unique to history page
    species-page/
      index.ts              ← entry point; mounts charts
      charts.ts             ← renderLineChart, renderStockStrip (until Phase 5)
      LineChart.svelte      ← Phase 5
      StockStrip.svelte     ← Phase 5
```

---

## CSS conventions

| Layer | Convention |
|---|---|
| `common.css` (global, permanent) | BEM |
| Page-level CSS (static Python-rendered HTML) | BEM |
| CSS custom properties | `--category-name` prefix (e.g. `--color-signal-hot`, `--spacing-sm`) |
| Svelte `<style>` blocks | Simple semantic names (`.header`, `.row`, `.filter-bar`) |
| Svelte state modifiers | `.is-active`, `.is-sorted`, `.is-expanded` |
| Svelte `:global()` escapes | BEM (back in global namespace) |

**Three permanent CSS layers:**
1. `common.css` — browser reset, CSS custom properties (design tokens), base HTML element styles,
   page chrome layout. Grows only when a new token or chrome element is added.
2. Page-level CSS files — only for Python-rendered static HTML not inside a Svelte island.
   Shrinks as islands grow; some may eventually disappear entirely.
3. Svelte `<style>` blocks — all component styles.

---

## Verification gates (apply at every phase boundary)

- `make build-client` — zero TS/Svelte compile errors; expected `dist/*.js` and `dist/*.css` emitted
- `make test` — Python unit tests green, coverage ≥ 80%
- `make test-client` — Vitest green (Phase 3 onwards)
- `make test-e2e` — Playwright green (required for any website-output change)

---

## Phase 0 — Vite + TypeScript foundation

**Goal:** Wire up a build pipeline. Existing JS continues to work identically.

- [ ] 1. Create `client/package.json` with `vite`, `typescript`, `@types/node` as devDeps,
         `"type": "module"`, `"build": "vite build"`.

- [ ] 2. Create `client/tsconfig.json`: `ESNext` modules, `DOM` + `DOM.Iterable` lib, `strict: true`,
         `verbatimModuleSyntax: true`, `rootDir: "src"`.

- [ ] 3. Create `client/vite.config.ts` with `build.lib` multi-entry map for the five existing files,
         `entryFileNames: "[name].js"` (no content hashes),
         `build.outDir: "../templates/scripts/dist"`, `build.emptyOutDir: true`.

- [ ] 4. Mirror the five existing `.js` files as pass-through re-exports in `client/src/`.
         Run `npm run build`, verify `dist/*.js` output is functionally identical to the originals.

- [ ] 5. Add `templates/scripts/dist/` to `.gitignore`.

- [ ] 6. Add `make build-client` to `Makefile`: `cd client && npm ci && npm run build`.

- [ ] 7. Update `generate_website.py` to copy JS from `templates/scripts/dist/` instead of
         `templates/scripts/`.

- [ ] 8. **Update CI** — in `.github/workflows/deploy-pages.yml`: add `actions/setup-node@v4`
         (Node 22 LTS) and run `make build-client` before the Python generate step.
         The scrape workflow is unaffected.

- [ ] 9. **Verify:** `make build-client && make generate-website && make test-e2e` all green.
         Confirm CI passes.

---

## Phase 1 — Rename JS → TS, one file at a time

**Goal:** Type-check each file with no `any`. Zero logic changes.

- [ ] 10. Rename `constants.js` → `constants.ts`. Add explicit property types to the three
          exported const objects.

- [ ] 11. Rename `utils.js` → `utils.ts`. Type `RangeSlider` class fully (constructor params,
          method signatures, return types). Type `filterByAttribute` parameters.

- [ ] 12. Rename `table-interactions.js` → `table-interactions.ts`. Type all exported functions.

- [ ] 13. Rename `table-setup.js` → `table-setup.ts`. Imports from all others — type errors cascade
          here, catching any remaining gaps.

- [ ] 14. Rename `species-detail.js` → `species-detail.ts`. Type `renderLineChart` options object.
          Declare `window.speciesChartData` interface in `client/src/global.d.ts`.

- [ ] 15. After each rename: `make build-client` must emit zero type errors.
          Run `make test-e2e` after the final file.

---

## Phase 2 — Reorganise into feature-slice folders

**Goal:** Move from flat `client/src/*.ts` to page-oriented slices. No logic changes.

- [ ] 16. Extract shared utilities from `table-interactions.ts` and `utils.ts` into
          `shared/dom-utils.ts`, `shared/range-slider.ts`, `shared/sort.ts`, `shared/filter.ts`.
          Move `constants.ts` to `shared/constants.ts`.

- [ ] 17. Create each feature-slice folder with an `index.ts` that imports from `shared/` and
          wires event handlers for that page only. `history-page/index.ts` owns the date-filter
          logic (currently buried in `table-setup.ts`). `species-page/index.ts` + `charts.ts`
          own the former `species-detail.ts` content.

- [ ] 18. Update `vite.config.ts` entry map — one entry per slice:
          `{ "breeder-page": "src/breeder-page/index.ts", "dealer-page": ...,
          "snapshot-page": ..., "history-page": ..., "species-page": ... }`.
          No more `table-setup.js` / `table-interactions.js` as output files.

- [ ] 19. Update page templates to load the correct slice script per page.
          Update `templates/base.html` so JS is no longer loaded globally —
          each page template declares its own script.

- [ ] 20. Update `generate_website.py` asset-copy logic to copy the new output filenames.

- [ ] 21. Run `make build-client && make test-e2e`.

---

## Phase 3 — Introduce Svelte + Vitest tooling

**Goal:** Add tooling. No behaviour changes, no Svelte components yet.

- [ ] 22. `npm install svelte@^5 @sveltejs/vite-plugin-svelte@^4 --save-dev` in `client/`.

- [ ] 23. `npm install vitest@^3 @testing-library/svelte@^5 @testing-library/jest-dom jsdom --save-dev`
          in `client/`.

- [ ] 24. Update `client/vite.config.ts` to add `svelte()` plugin and Vitest config
          (`environment: "jsdom"`, `setupFiles: ["src/test-setup.ts"]`).
          Confirm `build.cssCodeSplit: true` is set (Vite default for lib mode) — verify it
          emits per-entry `.css` files alongside `.js`.

- [ ] 25. Create `client/src/test-setup.ts` importing `@testing-library/jest-dom`.

- [ ] 26. Add `make test-client` to `Makefile`: `cd client && npm run test` (Vitest run mode).
          Fold it into the `make test` target so it runs as part of the standard suite.

- [ ] 27. Add a `make test-client` step to the CI `deploy-pages.yml` workflow, run after
          `make build-client` and before `make test`.

- [ ] 28. Write a trivial `HelloWorld.svelte` smoke test using a `$state` counter.
          Confirm Vitest and `make build-client` both pass and that a `.css` file is emitted
          alongside the `.js` output. Delete it.

---

## Phase 4a — CSS audit: tokens, BEM, and permanent scope

**Goal:** Establish the permanent CSS architecture before any component styles are written.
Apply BEM only to what permanently stays global. Extract design tokens so Svelte components
can reference `var(--color-signal-hot)` without importing anything.

- [ ] 29. **Audit all stylesheets** (`common.css`, `analysis.css`, `homepage.css`, `history.css`,
          `species-detail.css`). For each rule, classify it as:
          - **Permanent global** — browser reset, page chrome, base HTML element styles.
          - **Static page HTML** — styles for Python-rendered HTML not inside a future Svelte island.
          - **Component-bound** — styles for elements that will become Svelte islands.
            Do not rename or BEM these — they are being deleted, not kept.

- [ ] 30. **Extract CSS custom properties** into `:root` in `common.css`. Every repeated colour,
          spacing, and type-scale value becomes a token. Replace every hard-coded usage across
          all stylesheets with the corresponding token.
          Naming: `--category-name` (e.g. `--color-*`, `--spacing-*`, `--font-*`).

- [ ] 31. **Apply BEM to permanent global CSS only** — rules classified as "permanent global"
          and "static page HTML" in step 29. Update class attributes in Jinja2 templates and
          class-name constants in `shared/constants.ts` at the same time.
          Do not BEM component-bound rules — they are going away.

- [ ] 32. Run `make test-e2e` to confirm no visual regressions.

---

## Phase 4b — Python data contract + mount points

**Goal:** Prepare server-rendered HTML for Svelte takeover.

- [ ] 33. In `src/website/` (likely `page_config.py` or a new `table_data_helpers.py`), add a
          serialiser converting each page's table row data into a JSON-serialisable list of dicts
          keyed by column name. Write Python unit tests for this serialiser.

- [ ] 34. Update `templates/table.html`: replace the `{%- for row in rows %}` tbody loop with
          `<div id="{{ table_id }}-root"></div>`. Add
          `<script>window.{{ table_id }}Data = {{ rows | tojson }};</script>`
          before the slice script tag.

- [ ] 35. **Snapshot update:** run `make test`, review every snapshot diff — confirm each change
          is exactly the mount div + data script replacing row HTML. Update snapshots only after
          verifying this. Snapshots become minimal; expected and correct.

---

## Phase 4c-i — Primitive Svelte components

**Goal:** Build shared UI atoms that both `SortableTable` and `HistoryTable` compose from.
Tight Vitest feedback — tested in isolation before assembly.

- [ ] 36. Create `client/src/shared/components/RangeSlider.svelte`. Replaces `shared/range-slider.ts`.
          Props: `min`, `max`, `label`. Emits `change` with `{min, max}`.
          `<style>` block uses design tokens; class names are simple and semantic
          (`.track`, `.thumb`, `.label`).

- [ ] 37. Create `client/src/shared/components/SearchInput.svelte`.
          Props: `placeholder`, `tableId`. Emits `input` with current value.
          `<style>` block with semantic names.

- [ ] 38. Create `client/src/shared/components/FilterButton.svelte`.
          Props: `label`, `value`, `active`. Emits `click`.
          Uses `.is-active` modifier class for active state.

- [ ] 39. For each primitive: write Vitest tests covering render, props, and emitted events.
          Run `make test-client`.

- [ ] 40. Update `generate_website.py` to copy `dist/*.css` files to the website output directory
          alongside `dist/*.js`.

- [ ] 41. Update page templates to include
          `<link rel="stylesheet" href="{{ path_prefix }}<slice-name>.css">`
          alongside each slice `<script>` tag.
          Confirm empty CSS links cause no E2E errors.

---

## Phase 4c-ii — `SortableTable.svelte` (breeder, dealer, snapshot)

**Goal:** Svelte owns full table rendering for three pages.

- [ ] 42. Create `client/src/shared/components/SortableTable.svelte`. Svelte 5 runes
          (`$props()`, `$state()`, `$derived()`). Accepts `rows`, `columns`, `filterConfig`
          as props. Composes `RangeSlider`, `SearchInput`, `FilterButton` primitives.
          Renders sortable `<th>` headers + filtered tbody rows.
          Sort state and active filters in `$state`.
          `<style>` block uses semantic names (`.table`, `.header`, `.row`, `.filter-bar`)
          and `.is-sorted`, `.is-ascending`, `.is-hidden` modifiers.
          Remove equivalent rules from page-level CSS files.

- [ ] 43. Write Vitest tests for `SortableTable`: initial render, column sort asc/desc,
          signal filter, search filter, combined filters, row count.

- [ ] 44. Update `breeder-page/index.ts`, `dealer-page/index.ts`, `snapshot-page/index.ts`
          to `mount()` `SortableTable` with the correct column/filter config.
          Remove the old DOM-wiring event handler code from each `index.ts`.

- [ ] 45. Run `make build-client && make generate-website && make test-e2e`.
          Fix any DOM-contract breakages following the snapshot update protocol.

- [ ] 46. Audit `analysis.css` — remove rules now covered by `SortableTable`'s scoped styles.

---

## Phase 4c-iii — `HistoryTable.svelte` (history page)

**Goal:** Svelte owns history table with its own distinct filter composition.

- [ ] 47. Create `client/src/history-page/DateFilter.svelte`. Svelte 5 runes.
          Owns checkbox date picker, "Last N Runs" quick-select, "Show All".
          Emits `change` with selected dates array.
          `<style>` block with semantic names (`.date-list`, `.date-item`, `.quick-select`).

- [ ] 48. Create `client/src/history-page/HistoryTable.svelte`. Composes `RangeSlider`,
          `SearchInput`, and `DateFilter` in its own arrangement (not `SortableTable`).
          Accepts `rows` and `columns` props. Sort and filter state in `$state`.
          `<style>` block with semantic names; remove equivalent rules from `history.css`.

- [ ] 49. Write Vitest tests for `HistoryTable` and `DateFilter`: date checkbox selection,
          "Last N" quick-select, price/wishlist slider, search, combined filters.

- [ ] 50. Update `history-page/index.ts` to mount `HistoryTable`.
          Run `make build-client && make test-client && make test-e2e`.

- [ ] 51. Audit `history.css` — remove rules now covered by scoped component styles.

---

## Phase 4d — CSV download in Svelte

**Goal:** Replace DOM-scraping `downloadFilteredCsv` with component-state-based export.

- [ ] 52. Add download logic to `SortableTable.svelte` and `HistoryTable.svelte`. Both components
          already hold all visible row data in `$derived` state — build CSV from that directly.
          No `data-raw` attribute scraping needed.

- [ ] 53. Write Vitest tests: render component, apply filter, trigger download action,
          assert CSV string content matches visible rows only.

- [ ] 54. Run `make test-client && make test-e2e`.

---

## Phase 4e — Retire dead code

**Goal:** Remove all replaced TypeScript, stale CSS, and stale script tags.

- [ ] 55. Delete `shared/range-slider.ts`, `shared/filter.ts`, `shared/sort.ts` — replaced by
          Svelte components and primitives. Remove remaining DOM-wiring code from page
          `index.ts` files.

- [ ] 56. Confirm `vite.config.ts` entry map has no stale entries. Verify `dist/` emits exactly
          five page entry points (`.js` + `.css`) and nothing else.

- [ ] 57. Confirm `templates/base.html` and page templates reference only current slice scripts
          and CSS.

- [ ] 58. Review `analysis.css`, `homepage.css`, `history.css`, `species-detail.css` — delete
          any file that is now empty or contains only rules already in `common.css`.

- [ ] 59. Run `make test && make test-client && make test-e2e`. Full green required.

---

## Phase 5 — Species-page charts (future)

**Goal:** Migrate imperative SVG chart rendering into Svelte components.

- [ ] 60. Create `client/src/species-page/LineChart.svelte` and `StockStrip.svelte` using
          Svelte 5, consuming the existing `window.speciesChartData` global.
          `<style>` blocks use semantic names; remove equivalent rules from `species-detail.css`.

- [ ] 61. Update `species-page/index.ts` to mount both components.
          Remove imperative `renderLineChart`/`renderStockStrip` from `charts.ts`.

- [ ] 62. Write Vitest tests. Run `make test-client && make test-e2e`.

---

## Decisions log

| Decision | Rationale |
|---|---|
| **dist/ not committed** | Built via `make build-client` locally; CI wires `setup-node` (Node 22 LTS) + `make build-client` in `deploy-pages.yml` before the Python generate step. Scrape workflow unchanged. |
| **Vite, not webpack** | Zero config, native ES modules, no content hashing needed, first-class Svelte 5 plugin. |
| **Svelte 5 runes throughout** | `$state`, `$derived`, `$props`, snippets — canonical latest API. Not Svelte 4 stores. |
| **Vitest primary, E2E sanity net** | Sub-100ms Vitest feedback per component — optimal for AI iteration. E2E covers real browser, Python data shape, URL state. |
| **Feature-slice entry points** | One Vite entry per page (`breeder-page`, etc.). Each page folder owns its Svelte components unless the component is reused across pages. |
| **`SortableTable` in `shared/components/`** | Breeder, dealer, snapshot are configuration variants of the same component. History is structurally different — `HistoryTable.svelte` lives in `history-page/`, composing the same primitives differently. |
| **Primitive components in `shared/components/`** | `RangeSlider`, `SearchInput`, `FilterButton` are UI atoms reused by both `SortableTable` and `HistoryTable`. Built and tested in isolation before assembly. |
| **window globals for data injection** | Same pattern already used by `window.speciesChartData`. Avoids a fetch roundtrip, keeps the site fully static, no API layer needed. |
| **BEM applied at Phase 4a only, to permanent global CSS only** | Most current CSS classes are being deleted into Svelte scopes — renaming before then is double churn. Applied once, at the audit step, when permanent-vs-migrating is clear. |
| **CSS three-layer architecture** | `common.css` = reset + tokens + chrome; page-level CSS = static Python HTML only; Svelte `<style>` = all component styles. Vite emits per-entry `.css`; Python copies them; page templates link them. |
| **Design tokens before components** | Svelte components reference `var(--color-signal-hot)` natively — tokens must exist before component `<style>` blocks are written (Phase 4a before 4c). |
| **No snapshot purge** | Table-page snapshots shrink to mount-div + data-script in Phase 4b — still guard against server-rendered scaffold regressions. Update, don't delete. |
| **Phase 4 split into 4a–4e + c-i/ii/iii** | Separates CSS audit/BEM (4a), data contract (4b), primitive foundations (4c-i), `SortableTable` (4c-ii), `HistoryTable` (4c-iii), CSV (4d), cleanup (4e). |
