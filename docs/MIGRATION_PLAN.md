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
Vitest coverage (≥ 80%) is enforced in CI as a migration confidence gate and long-term feature integrity check.

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
- `make coverage-client` — Vitest coverage ≥ 80% branches/functions/lines for all `client/src/` modules (Phase 3 onwards)
- `make test-e2e` — Playwright green (required for any website-output change)

---

## Client-side testing conventions

### Test file location

All Vitest test files are co-located with the module they test. `foo.test.ts` lives in the
same directory as `foo.ts` or `Foo.svelte`. Examples:

- `shared/csv-utils.test.ts` tests `shared/csv-utils.ts`
- `shared/components/RangeSlider.test.ts` tests `RangeSlider.svelte`
- `species-page/charts.test.ts` tests `species-page/charts.ts`

### Vitest import pattern

```ts
import { render, fireEvent } from '@testing-library/svelte';
import '@testing-library/jest-dom';
import MyComponent from './MyComponent.svelte';

test('applies .is-active when active prop is true', async () => {
  const { getByRole } = render(MyComponent, { label: 'Hot', value: '🔥', active: true });
  expect(getByRole('button')).toHaveClass('is-active');
});
```

Key points:
- `render(Component, propsObject)` — no `{ props: … }` wrapper (that is Testing Library v4 syntax)
- `fireEvent.click`, `fireEvent.input` for interactions
- Svelte 5 component events dispatched via `fireEvent` on the host element
- `@testing-library/jest-dom` is imported globally via `src/test-setup.ts` — **not per file**

### When to write Vitest vs E2E

| Scenario | Vitest | E2E |
|---|---|---|
| Pure function (no DOM) | ✅ only | ❌ |
| Svelte component render, props, events | ✅ primary | ❌ |
| Filter / sort logic in `$derived` state | ✅ primary | Smoke test only |
| URL `pushState` / `?view=` param reads | ❌ | ✅ only |
| CSS computed styles, visual layout | ❌ | ✅ only |
| Blob download (OS file system) | ❌ | ✅ only |
| Asset 404 / missing CSS or JS files | ❌ | ✅ only |
| Real data shape from Python generator | ❌ | ✅ only |

E2E tests are **kept in full** throughout and after the migration — they cover real browser
behaviour and Python data shape that Vitest cannot replicate. Vitest and E2E test different layers;
they are not interchangeable. Once Svelte components own filter/sort logic, Vitest covers that logic
at the unit level and E2E remains the integration safety net for DOM-contract and browser behaviour.

### Coverage as a feedback loop

Client-side coverage serves two purposes:

1. **Migration confidence** — as TypeScript is replaced by Svelte components, coverage confirms
   the equivalent logic is tested by Vitest. A coverage drop after migrating a module to Svelte
   means the component's tests are incomplete — not that the code is safe.
2. **Future feature integrity** — new components added after migration must maintain the threshold.
   Coverage is a first-pass signal that logic paths have been exercised; it does not replace
   thinking about edge cases.

Coverage is enforced on all `client/src/**/*.{ts,svelte}` files, excluding `test-setup.ts`,
`global.d.ts`, and `*.test.ts` files. Run `make coverage-client` locally to see the report.
The same command runs in CI after `make test-client`.

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

- [ ] 25a. Extract `_escapeCsvRow` from `history-page/index.ts` into a new exported function
           in `client/src/shared/csv-utils.ts`. Update `history-page/index.ts` to import from it.
           No behaviour change — this is a pure refactor to make the first real Vitest target
           accessible and to establish `shared/csv-utils.ts` as the home for future CSV logic
           (including the Phase 4d component-state-based download).

- [ ] 25b. Write `client/src/shared/csv-utils.test.ts` — the first permanent Vitest test file,
           establishing the co-located convention. Test cases:
           - Empty array → `""`
           - Single plain value → no quoting
           - Value containing a comma → wrapped in double-quotes
           - Value containing a double-quote → double-quoted; inner quote doubled (`""`)
           - Value containing a newline → wrapped in double-quotes
           - Multiple values in one row combining all edge cases
           Run `make test-client` to confirm Vitest discovers and passes. This is the point
           the runner is validated against real (non-smoke) test logic.

- [ ] 26. Add `make test-client` to `Makefile`: `cd client && npm run test` (Vitest run mode).
          **Do NOT fold into `make test`.**  `make test` is the fast Python-only loop (≤1s,
          no Node required); merging would add a Node dependency to every Python edit cycle.
          The verification gates already list `make test` and `make test-client` separately.
          Update `copilot-instructions.md` instead: add `make test-client` as the mandatory
          command for any edit in `client/src/`.

- [ ] 27. Add `make test-client` and `make coverage-client` steps to the CI `deploy-pages.yml`
          workflow, run after `make build-client` and before `make test`. Node/npm are already
          available at that point (installed by `actions/setup-node@v4` + `npm ci` inside
          `make build-client`). `coverage-client` enforces the threshold; the build fails if
          coverage drops below 80%.

- [ ] 27a. Set up Vitest coverage infrastructure:
           - `npm install @vitest/coverage-v8 --save-dev` in `client/`.
           - Add `"coverage": "vitest run --coverage"` script to `client/package.json`.
           - Add `make coverage-client` to Makefile: `cd client && npm run coverage`.
           - In `vite.config.ts` (inside the `test` config object), add:
             ```ts
             coverage: {
               provider: 'v8',
               include: ['src/**/*.{ts,svelte}'],
               exclude: ['src/test-setup.ts', 'src/global.d.ts', 'src/**/*.test.ts'],
               thresholds: { branches: 80, functions: 80, lines: 80, statements: 80 },
             }
             ```
           - Add `client/coverage/` to `.gitignore`.
           - Run `make coverage-client` — it will show 100% for `csv-utils.ts` (only file
             with tests so far) and 0% for everything else; thresholds apply per-file or
             globally depending on Vitest version — verify thresholds pass at this stage
             before they become a blocker in later phases.
             **Note:** configure thresholds to apply globally (not per-file) so they ratchet
             upward as coverage is added, not block the build before all modules have tests.

- [ ] 28. Write a trivial `HelloWorld.svelte` smoke test using a `$state` counter.
          Confirm Vitest and `make build-client` both pass and that a `.css` file is emitted
          alongside the `.js` output in `templates/scripts/dist/`. Then delete `HelloWorld.svelte`
          and its test. After deletion, `csv-utils.test.ts` (step 25b) is the only test file.
          This ordering is intentional: the smoke test proves the toolchain works, and 25b
          provides the first real test — not the other way around.

- [ ] Doc: Update CONTRIBUTING.md — add `make test-client` and `make coverage-client` to
         the Running Tests section. Document when Vitest tests are required (all new Svelte
         components and shared utilities); note that test files are co-located with the
         module they test.
- [ ] Doc: Update copilot-instructions.md — add `make test-client` and `make coverage-client`
         to the mandatory test commands. Document that Vitest covers component logic and pure
         functions; E2E covers browser interactions and real data shape; coverage is a migration
         confidence gate, not a substitute for thinking about edge cases.

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

- [ ] 39. For each primitive: write Vitest tests co-located with each component file.
          Run `make test-client && make coverage-client` after all three.

          **`RangeSlider.svelte` — `RangeSlider.test.ts`:**
          - Renders two range inputs with `min`/`max`/`value` attributes matching props
          - Display text shows formatted `minProp – maxProp` initially
          - Setting the min input above the current max → max auto-clamps up
          - Setting the max input below the current min → min auto-clamps down
          - After constraint is enforced, a `change` event fires with `{ min, max }` payload

          **`FilterButton.svelte` — `FilterButton.test.ts`:**
          - Renders a button with the correct `label` text
          - `active: true` → element has `.is-active` class
          - `active: false` → `.is-active` class absent
          - Click fires a `click` event

          **`SearchInput.svelte` — `SearchInput.test.ts`:**
          - Renders an `<input>` with the `placeholder` prop as its placeholder attribute
          - Typing a value fires an `input` event with that value as the payload

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

- [ ] 42a. **E2E DOM-contract audit.** Before any Svelte HTML is written, audit
           `tests/e2e/test_table_interactions.py` for every DOM attribute and class name it
           depends on. Produce an explicit mapping and resolve each as a Decisions entry:
           - `data-sort-direction` attr on `<th>` — Svelte must emit this or 15+ E2E assertions break
           - `.hidden` class on `<tr>` — E2E counts hidden rows via this class
           - `.active` class on filter buttons — must remain `.active` (not `.is-active`) unless
             the E2E tests are updated at the same time
           - `data-original-index` on `<tr>` — required by the top-10 limit logic in `filterByAttribute`
           Resolve each: either `SortableTable.svelte` emits the existing attribute/class, or
           update the E2E tests alongside the component. Record the decision before writing any
           Svelte HTML. This prevents silent E2E churn during rollout.

- [ ] 42. Create `client/src/shared/components/SortableTable.svelte`. Svelte 5 runes
          (`$props()`, `$state()`, `$derived()`). Accepts `rows`, `columns`, `filterConfig`
          as props. Composes `RangeSlider`, `SearchInput`, `FilterButton` primitives.
          Renders sortable `<th>` headers + filtered tbody rows.
          Sort state and active filters in `$state`. Visible rows in `$derived`.
          `<style>` block uses semantic names (`.table`, `.header`, `.row`, `.filter-bar`)
          and `.is-sorted`, `.is-ascending`, `.is-hidden` modifiers.
          Remove equivalent rules from page-level CSS files.

- [ ] 43. Write `SortableTable.test.ts` co-located with the component.
          Run `make test-client && make coverage-client`.

          Test cases:
          - Initial render: all `rows` prop items visible, correct column headers present
          - Click column 0 header → rows reorder ascending; target `<th>` has `data-sort-direction="asc"`
          - Click same header again → `data-sort-direction="desc"`, rows reversed
          - Numeric column detected correctly (numbers sort numerically, not lexicographically)
          - Signal filter button click → only rows with matching signal visible; others hidden
          - Search input text → only rows whose text contains the search string visible
          - Signal filter + search simultaneously → AND logic: only rows matching both
          - Visible row count element reflects correct number after each filter change
          - "Show All" resets to all rows visible and deactivates the filter button
          - "Top 10" limit → at most 10 rows visible in original CSV order regardless of current sort

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

- [ ] 49. Write `DateFilter.test.ts` and `HistoryTable.test.ts` co-located with each component.
          Run `make test-client && make coverage-client`.

          **`DateFilter.svelte` — `DateFilter.test.ts`:**
          - Renders one checkbox per unique date in the `dates` prop
          - Unchecking a date fires a `change` event with that date excluded from the payload
          - "Last N Runs" quick-select fires `change` with exactly the N most recent dates
          - "Show All" fires `change` with all dates checked

          **`HistoryTable.svelte` — `HistoryTable.test.ts`:**
          - Deselecting a date → rows for that date hidden
          - Search text → only matching rows visible
          - Date + search AND logic: only rows matching both date selection and search text
          - Price slider below a row's price → that row hidden
          - Wishlist slider above a row's count → that row hidden
          - Combined: date + search + price → intersection of all three filters applied

- [ ] 50. Update `history-page/index.ts` to mount `HistoryTable`.
          Run `make build-client && make test-client && make test-e2e`.

- [ ] 51. Audit `history.css` — remove rules now covered by scoped component styles.

---

## Phase 4d — CSV download in Svelte

**Goal:** Replace DOM-scraping `downloadFilteredCsv` with component-state-based export.

- [ ] 52. Add download logic to `SortableTable.svelte` and `HistoryTable.svelte`. Both components
          already hold all visible row data in `$derived` state — build CSV from that directly.
          No `data-raw` attribute scraping needed.

- [ ] 53. Write Vitest tests for the download logic in `SortableTable.test.ts` and
          `HistoryTable.test.ts`. Import the exported `escapeCsvRow` from
          `shared/csv-utils.ts` to build expected strings independently.
          Run `make test-client && make coverage-client`.

          Test cases (apply to both `SortableTable` and `HistoryTable`):
          - Render with 5 rows, apply a filter leaving 3 visible; assert the `$derived` CSV
            value has a header row + exactly 3 data rows
          - Assert no hidden row's data appears in the CSV string
          - Assert the URL column maps to the raw href value, not anchor HTML
          - Assert CSV is RFC-4180 compliant: values containing commas or quotes are quoted;
            reuse the `escapeCsvRow` unit tests in `csv-utils.test.ts` as a reference
          No browser interaction needed — assert the derived state string directly.

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

- [ ] 59. Run `make test && make test-client && make coverage-client && make test-e2e`.
          Full green required. Coverage must meet ≥ 80% threshold — if not, add tests for
          any gaps before merging. This is the migration completion gate.

- [ ] Doc: Update CONTRIBUTING.md project structure — reflect the final feature-slice layout
         with Svelte components and page-entry points. Remove stale references.
- [ ] Doc: Update copilot-instructions.md — update CI test commands to include
         `make test-client`. Update E2E required triggers for the final project structure.

---

## Phase 4e→ 5 bridge: export and test `charts.ts` pure helpers

**Goal:** Establish a Vitest safety net for the most complex TypeScript in the codebase
before rewriting it as Svelte components. Run once, at the start of the Phase 5 conversation.

- [ ] 59a. Export the currently private pure helper functions from
           `client/src/species-page/charts.ts` as named exports and write
           `client/src/species-page/charts.test.ts` co-located alongside them.

           Functions to export and test:
           - `calculateLayout()`
             Assert key output properties (total width/height, usable inner dimensions, margin values)
             match what `CHART` constants produce. This is a deterministic pure function.
           - `mapPointsToCoordinates(series, yMin, yMax, layout)`
             Edge cases: `yMin === yMax` (div-by-zero guard — all points map to mid-y, not NaN),
             single-element series, a `null` value in the series passes through as `null`.
           - `buildPolylineSegments(points)`
             Edge cases: all-null input → empty array; single-point segment (length < 2)
             → excluded (a line needs ≥ 2 points); normal multi-segment split on nulls.
           - `createCircleElements(points, formatValue)`
             Assert returned array length matches non-null point count;
             assert formatted value string appears in each element's output.
           - `createPolylines(segments, stroke)`
             Assert stroke attribute is present in each element; assert point count is
             reflected in the `points=` attribute.

           Run `make test-client && make coverage-client` after.

---

## Phase 5 — Species-page charts (future)

**Goal:** Migrate imperative SVG chart rendering into Svelte components.

- [ ] 60. Create `client/src/species-page/LineChart.svelte` and `StockStrip.svelte` using
          Svelte 5, consuming the existing `window.speciesChartData` global.
          `<style>` blocks use semantic names; remove equivalent rules from `species-detail.css`.

- [ ] 61. Update `species-page/index.ts` to mount both components.
          Remove imperative `renderLineChart`/`renderStockStrip` from `charts.ts`.

- [ ] 62. Write Vitest tests for `LineChart.svelte` and `StockStrip.svelte`.
          Run `make test-client && make coverage-client && make test-e2e`.

          **`LineChart.svelte` — `LineChart.test.ts`:**
          - Renders an `<svg>` element with the expected width/height from CHART constants
          - With valid data: emits the correct number of `<circle>` elements (one per non-null run)
          - With valid data: emits at least one `<polyline>` element
          - With a single data point: renders one circle and no polyline (no segment of ≥ 2 points)
          - With all identical prices (`yMin === yMax`): renders without NaN in any attribute

          **`StockStrip.svelte` — `StockStrip.test.ts`:**
          - Renders one block per run in the input data
          - Observed runs have a visually distinct class/fill compared to not-observed runs
          - Total block count matches `chartData.runs.length`

          Delegate pixel-math edge cases to `charts.test.ts` (added in step 59a) —
          component tests cover structure and rendering, not arithmetic.

- [ ] Doc: Update CONTRIBUTING.md project structure — add `LineChart.svelte`,
         `StockStrip.svelte` under `species-page/` in the diagram.

---

## Decisions log

| Decision | Rationale |
|---|---|
| **Test files co-located, not in `__tests__/`** | Standard Vite/Vitest convention; `foo.test.ts` lives next to `foo.ts` or `Foo.svelte`, making it trivial to find the test for any file without mirroring a directory tree. |
| **`_escapeCsvRow` extracted to `shared/csv-utils.ts` in Phase 3** | Provides the first real (non-smoke) Vitest example immediately — establishes the co-located pattern and validates the runner before any Svelte components exist. The function is the highest-value immediate Vitest target: pure string logic, RFC-4180 edge cases, zero DOM. |
| **Chart pure helpers exported in step 59a (Phase 4e→5 bridge), not earlier** | The helpers are private implementation details of `charts.ts` today. Exporting them before the Phase 5 rewrite adds churn if the API changes. Exporting them at the bridge step gives a safety net exactly when it's needed — just before the Svelte rewrite — without premature exposure. |
| **E2E tests kept in full after Svelte migration** | Vitest and E2E test different layers. Vitest covers `$derived` filter/sort logic; E2E covers DOM contracts, real browser APIs (`pushState`, blob download), asset loading, Python data shape, and CSS computed styles. Trimming E2E to happy-path after Svelte migration would lose coverage of DOM-contract regressions. |
| **DOM-contract audit (step 42a) before `SortableTable.svelte`** | The E2E suite depends on specific attributes (`data-sort-direction`, `.hidden`, `.active`, `data-original-index`). Resolving whether Svelte emits the same attribute names — or whether E2E tests update in sync — must be a deliberate decision, not an accidental breakage discovered mid-rollout. |
| **Coverage threshold global, not per-file** | Per-file thresholds would block the build before any tests exist for a given module. Global thresholds ratchet upward as coverage accumulates across phases — they enforce the migration being tracked without becoming a blocker on the first day a new file is added. |
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
