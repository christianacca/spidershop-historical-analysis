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

## Phase 0 — Vite + TypeScript foundation ✅

**Goal:** Wire up a build pipeline. Existing JS continues to work identically.

- [x] 1. Create `client/package.json` with `vite`, `typescript`, `@types/node` as devDeps,
         `"type": "module"`, `"build": "vite build"`.

- [x] 2. Create `client/tsconfig.json`: `ESNext` modules, `DOM` + `DOM.Iterable` lib, `strict: true`,
         `verbatimModuleSyntax: true`, `rootDir: "src"`.

- [x] 3. Create `client/vite.config.ts` with `build.rollupOptions` multi-entry map for the five
         existing files, `preserveModules: true` (see Decisions), `entryFileNames: "[name].js"`,
         `build.outDir: "../templates/scripts/dist"`, `build.emptyOutDir: true`.

- [x] 4. Copy the five existing `.js` files into `client/src/` (see Decisions).
         Built with `npm run build`, verified `dist/*.js` maintains relative imports and is
         functionally identical to the originals.

- [x] 5. Added `templates/scripts/dist/` and `client/node_modules/` to `.gitignore`.

- [x] 6. Added `make build-client` to `Makefile`: `cd client && npm ci && npm run build`.

- [x] 7. Updated `generate_website.py` to copy JS from `templates/scripts/dist/` instead of
         `templates/scripts/`.

- [x] 8. **Updated CI** — in `.github/workflows/deploy-pages.yml`: added `actions/setup-node@v4`
         (Node 22 LTS) with npm cache on `client/package-lock.json`, and `make build-client`
         before the Python generate step.

- [x] 9. **Verified:** `make build-client` succeeds. `make test-e2e` → 106/106 passed.

- [x] Doc: Updated CONTRIBUTING.md — added Node.js 22 install step to all OS setup sections,
         added client-side iterative dev workflow, updated Project Structure diagram,
         updated E2E required list (`client/src/` replaces `templates/scripts/`).
- [x] Doc: Updated copilot-instructions.md — updated E2E required entry: `client/src/` is
         the JS source; `templates/scripts/dist/` is build output only.

---

## Phase 1 — Rename JS → TS, one file at a time

**Goal:** Type-check each file with no `any`. Zero logic changes.

**Important:** After renaming each file from `.js` → `.ts`, update the corresponding
`vite.config.ts` entry in `rollupOptions.input` from `src/<name>.js` → `src/<name>.ts`.
Vite 6 requires the entry path to match the actual file extension.
Import statements inside the files (`import { CSS } from './constants.js'`) do **not**
need changing — `moduleResolution: "bundler"` resolves `.js` → `.ts` transparently.

- [x] 10. Rename `constants.js` → `constants.ts`. Update `vite.config.ts` entry.
          Add explicit property types to the three exported const objects
          (`CHART`, `CSS`, `CONFIG`).

- [x] 11. Rename `utils.js` → `utils.ts`. Update `vite.config.ts` entry.
          Type all exported functions and the `RangeSlider` class:
          - `getElement(id: string): HTMLElement | null`
          - `setActiveButton(button: HTMLElement): void`
          - `toggleRowVisibility(row: HTMLElement, shouldShow: boolean): void`
          - `filterByAttribute(attributeName, filterValue, tableId, button, limit?: number | null): void`
          - `RangeSlider`: constructor config type, `enforceConstraints(event?: Event): void`,
            `getValues(): [number, number]`, `updateDisplay(min: number, max: number): void`.

- [x] 12. Rename `table-interactions.js` → `table-interactions.ts`. Update `vite.config.ts` entry.
          Type all exported functions (`sortTable`, `filterByPrice`, `filterByWishlist`,
          `filterRows`, `toggleAdvancedFilters`, `downloadFilteredCsv`, `updateDateSummary`)
          and private helpers.

- [x] 13. Rename `table-setup.js` → `table-setup.ts`. Update `vite.config.ts` entry.
          Imports from all others — type errors cascade
          here, catching any remaining gaps.

- [x] 14. Rename `species-detail.js` → `species-detail.ts`. Update `vite.config.ts` entry.
          Created `client/src/global.d.ts` declaring `window.speciesChartData`:
          ```ts
          interface SpeciesRun { observed: boolean; price: string; wishlist: string; }
          interface SpeciesChartData { runs: SpeciesRun[]; }
          interface Window { speciesChartData?: SpeciesChartData; }
          ```
          Typed the `renderLineChart` options as `LineChartConfig` interface;
          `Point = [number, number, number, number]` and `ChartLayout` types added.

- [x] 15. After each rename: `make build-client` emits zero type errors.
          `make test-e2e` → 106/106 passed.

- [x] Doc: Updated copilot-instructions.md — `client/src/` is now pure TypeScript source.

---

## Phase 2 — Reorganise into feature-slice folders ✅

**Goal:** Move from flat `client/src/*.ts` to page-oriented slices. No logic changes.

- [x] 16. Extract shared utilities from `table-interactions.ts` and `utils.ts` into:
          - `shared/constants.ts` ← move `constants.ts` here
          - `shared/dom-utils.ts` ← `getElement`, `setActiveButton`, `toggleRowVisibility` (from `utils.ts`)
          - `shared/range-slider.ts` ← `RangeSlider` class + `RangeSliderConfig` interface (from `utils.ts`)
          - `shared/sort.ts` ← `sortTable` (from `table-interactions.ts`)
          - `shared/filter.ts` ← `filterByAttribute` (from `utils.ts`), `filterRows`, `updateFilterBadge`, `updateVisibleCount`, `toggleAdvancedFilters` (from `table-interactions.ts`)

          ⚠️ **Do NOT put `filterByPrice` / `filterByWishlist` into `shared/filter.ts`.**
          These functions reference page-specific DOM IDs (`priceMin`, `priceMax`,
          `wishlistMin`, `wishlistMax`) and depend on module-level singletons
          (`priceSlider: RangeSlider | null`, `wishlistSlider: RangeSlider | null`).
          They are page-specific and must move into each page-slice `index.ts`
          (breeder, dealer, snapshot) alongside their slider singletons.

- [x] 17. Create each feature-slice folder with an `index.ts` that imports from `shared/` and
          wires event handlers for that page only:
          - `breeder-page/index.ts` — sorting, filtering, signal/stock-pattern filters, price/wishlist sliders
          - `dealer-page/index.ts` — same as breeder (different table ID)
          - `snapshot-page/index.ts` — sorting, filtering, price/wishlist sliders
          - `history-page/index.ts` — all of the above plus:
            - Date-filter logic (`initDateFilter`, currently in `table-setup.ts`)
            - `downloadFilteredCsv` and `updateDateSummary` (currently in `table-interactions.ts`;
              these are history-page-only — not called from any other page)
          - `species-page/index.ts` + `species-page/charts.ts` — former `species-detail.ts` content

          After this step, `table-setup.ts` and `table-interactions.ts` should be
          fully dissolved (all code redistributed) and can be deleted.

- [x] 18. Update `vite.config.ts` entry map — one entry per slice:
          `{ "breeder-page": "src/breeder-page/index.ts", "dealer-page": ...,
          "snapshot-page": ..., "history-page": ..., "species-page": ... }`.
          Delete the source files `table-setup.ts` and `table-interactions.ts`
          (fully dissolved in step 17). Also deleted `constants.ts`, `utils.ts`, `species-detail.ts`.
          Vite output will no longer emit `table-setup.js` or `table-interactions.js`.

- [x] 19. Update page templates to load the correct slice script per page.
          Removed both global `<script>` tags from `base.html`. Added `{% block extra_js %}` block
          to `base.html`. Each page template overrides this block:
          - `analysis_page.html` — `{{ page_script }}` variable (set by Python to `breeder-page.js` / `dealer-page.js`)
          - `snapshot_page.html` — loads `snapshot-page.js`
          - `history_page.html` — loads `history-page.js`
          - `species_detail.html` — changed to load `species-page.js`

- [x] 20. Update `generate_website.py` asset-copy logic.
          Added `page_script` variable to `generate_analysis_page` template render call.
          Replaced named-file JS copy with `shutil.copytree` to recursively copy the entire
          `dist/` tree (including `shared/` and `species-page/` subdirectories).

- [x] 21. `make build-client` — zero type errors. `make test-e2e` — 106/106 passed.
          `make test` — 620 passed, 95.50% coverage.

- [x] Doc: Update CONTRIBUTING.md project structure — show the feature-slice folder layout
         (`breeder-page/`, `history-page/`, etc.) replacing the flat `client/src/*.ts` listing.
- [x] Doc: Update copilot-instructions.md — document the feature-slice entry-point structure;
         note that Vite entry names now map to page-slice folders, not individual TS files.

**Decision:** `filterRows` in `shared/filter.ts` was changed to accept optional `priceSlider`
and `wishlistSlider` parameters rather than closing over module-level singletons. This keeps
the shared function pure with respect to external state while each page slice owns its singletons.

**Decision:** JS asset copy changed from a named-file list (`_copy_files`) to `shutil.copytree`
of the entire `dist/` directory tree. With `preserveModules: true`, shared/ subdirectories are
generated alongside the entry files and must all be served. `copytree` is simpler and self-maintaining
as new shared modules are added in future phases.

---

## Phase 3 — Introduce Svelte + Vitest tooling

**Goal:** Add tooling. No behaviour changes, no Svelte components yet.

**Pre-existing state at Phase 3 handoff:**
- `client/package.json` already has `"test": "vitest run"` in `scripts` — do NOT add it again.
  Steps 23 and 26 are additions only: add packages and the Makefile target.
- `make test-client` does not yet exist in `Makefile`.

- [ ] 22. `npm install svelte@^5 @sveltejs/vite-plugin-svelte@^4 --save-dev` in `client/`.

- [ ] 23. `npm install vitest@^3 @testing-library/svelte@^5 @testing-library/jest-dom jsdom --save-dev`
          in `client/`. (The `"test": "vitest run"` script already exists in `package.json`.)

- [ ] 24. Update `client/vite.config.ts` to add `svelte()` plugin and Vitest config
          (`environment: "jsdom"`, `setupFiles: ["src/test-setup.ts"]`).
          Note: this project uses `rollupOptions` + `preserveModules: true`, NOT `build.lib` mode.
          With that setup + the Svelte plugin, Vite emits one aggregate `.css` file per page-slice
          entry (e.g. `breeder-page.css`) containing all Svelte component styles compiled for
          that entry — not one `.css` per module file. The smoke test in step 28 must confirm
          a `.css` file is emitted by checking `templates/scripts/dist/` after build.

- [ ] 25. Create `client/src/test-setup.ts` importing `@testing-library/jest-dom`.

- [ ] 26. Add `make test-client` to `Makefile`: `cd client && npm run test` (Vitest run mode).
          **Do NOT fold into `make test`.**  `make test` is the fast Python-only loop (≤1s,
          no Node required); merging would add a Node dependency to every Python edit cycle.
          The verification gates already list `make test` and `make test-client` separately.
          Update `copilot-instructions.md` instead: add `make test-client` as the mandatory
          command for any edit in `client/src/`.

- [ ] 27. Add a `make test-client` step to the CI `deploy-pages.yml` workflow, run after
          `make build-client` and before `make test`. Node/npm are already available at that
          point (installed by `actions/setup-node@v4` + `npm ci` inside `make build-client`).

- [ ] 28. Write a trivial `HelloWorld.svelte` smoke test using a `$state` counter.
          Confirm Vitest and `make build-client` both pass and that a `.css` file is emitted
          alongside the `.js` output. Delete it.

- [ ] Doc: Update CONTRIBUTING.md — add `make test-client` to the Running Tests section.
         Document when Vitest tests are required (new Svelte components, shared utilities).
- [ ] Doc: Update copilot-instructions.md — add `make test-client` to the mandatory test
         commands. Document that Vitest covers component logic; E2E covers browser
         interactions and real data shape.

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

- [ ] Doc: Update copilot-instructions.md — document the 3-layer CSS architecture
         (`common.css` global BEM, page-level BEM, Svelte scoped). Note BEM naming
         conventions and design token prefix (`--category-name`).

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

- [ ] Doc: Update copilot-instructions.md — add Svelte 5 component authoring guidelines:
         use runes (`$state`, `$derived`, `$props`), semantic class names in `<style>` blocks,
         write Vitest tests for props/events, E2E for browser interactions.

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

- [ ] Doc: Update CONTRIBUTING.md project structure — reflect the final feature-slice layout
         with Svelte components and page-entry points. Remove stale references.
- [ ] Doc: Update copilot-instructions.md — update CI test commands to include
         `make test-client`. Update E2E required triggers for the final project structure.

---

## Phase 5 — Species-page charts (future)

**Goal:** Migrate imperative SVG chart rendering into Svelte components.

- [ ] 60. Create `client/src/species-page/LineChart.svelte` and `StockStrip.svelte` using
          Svelte 5, consuming the existing `window.speciesChartData` global.
          `<style>` blocks use semantic names; remove equivalent rules from `species-detail.css`.

- [ ] 61. Update `species-page/index.ts` to mount both components.
          Remove imperative `renderLineChart`/`renderStockStrip` from `charts.ts`.

- [ ] 62. Write Vitest tests. Run `make test-client && make test-e2e`.

- [ ] Doc: Update CONTRIBUTING.md project structure — add `LineChart.svelte`,
         `StockStrip.svelte` under `species-page/` in the diagram.

---

## Decisions log

| Decision | Rationale |
|---|---|
| **`build.rollupOptions` + `preserveModules` instead of `build.lib`** (Phase 0) | `build.lib` bundles inter-entry dependencies together, which would break the `priceSlider`/`wishlistSlider` singletons shared between `table-interactions.js` and `table-setup.js` when both are loaded on the same page. `preserveModules: true` keeps each module as a separate file with relative imports intact — output is structurally identical to source. Required `preserveEntrySignatures: 'allow-extension'` to override Vite 6's default `false` (incompatible with `preserveModules`). |
| **Copy files into `client/src/` instead of re-exports** (Phase 0) | Re-exporting from `../../templates/scripts/*.js` would create cross-directory relative paths in the dist output that would break deployment (only `dist/` files are copied to the website output — `templates/scripts/` is not). Copying makes `client/src/` the self-contained source. |
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
| **Arrow functions in `table-setup.ts` event listeners** (Phase 1) | Event callbacks in `table-setup.ts` used `function()` + `this` in the original JS. TypeScript strict mode would require `this: HTMLElement` parameters, which conflicts with the `EventListener` interface (`this: EventTarget`). Instead, generic `querySelectorAll<HTMLElement>()` was used and inner callbacks were converted to arrow functions closing over the typed element. No logic change — behavior is identical. |
| **`window.event` for `enforceConstraints`** (Phase 1) | `filterByPrice` / `filterByWishlist` used the deprecated global `event` to pass to `enforceConstraints`. Replaced with `window.event` (typed `Event \| undefined` in the DOM lib). The `enforceConstraints` parameter changed from `event: Event` to `event?: Event` (optional). No behavior change — the `?.target` optional chain already handled undefined. |
| **No snapshot purge** | Table-page snapshots shrink to mount-div + data-script in Phase 4b — still guard against server-rendered scaffold regressions. Update, don't delete. |
| **Phase 4 split into 4a–4e + c-i/ii/iii** | Separates CSS audit/BEM (4a), data contract (4b), primitive foundations (4c-i), `SortableTable` (4c-ii), `HistoryTable` (4c-iii), CSV (4d), cleanup (4e). |
