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
- `fireEvent.click`, `fireEvent.input` for **native DOM events** (click a button, type in an input)
- `@testing-library/jest-dom` is imported globally via `src/test-setup.ts` — **not per file**

**Svelte 5 callback props — test pattern:**
Svelte 5 uses callback props (`onchange`, `oninput`, `onclick`) rather than `createEventDispatcher`.
For tests that assert a component notifies its parent, pass a `vi.fn()` spy as the callback prop
and assert it was called after the interaction:

```ts
import { vi } from 'vitest';

test('calls onchange with {min, max} after clamp', async () => {
  const onchange = vi.fn();
  const { getAllByRole } = render(RangeSlider, { min: 0, max: 100, label: 'Price', onchange });
  const [minInput] = getAllByRole('slider');
  await fireEvent.input(minInput, { target: { value: '120' } });
  expect(onchange).toHaveBeenCalledWith({ min: 100, max: 100 });
});
```

Native DOM events (`click`, `input`, `change`) still use `fireEvent` on the host element.
Svelte binds these automatically when the component uses `onclick={...}` / `oninput={...}`.

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

## Phase 3 — Introduce Svelte + Vitest tooling ✅

**Goal:** Add tooling. No behaviour changes, no Svelte components yet.

**Pre-existing state at Phase 3 handoff:**
- `client/package.json` already has `"test": "vitest run"` in `scripts` — do NOT add it again.
  Steps 23 and 26 are additions only: add packages and the Makefile target.
- `make test-client` does not yet exist in `Makefile`.

- [x] 22. `npm install svelte@^5 @sveltejs/vite-plugin-svelte@^5 --save-dev` in `client/`.
          **Note:** plan said `@^4` but `@^4` only supports Vite 5; `@^5` is the Vite-6-compatible
          release. Used `@^5` instead.

- [x] 23. `npm install vitest@^3 @testing-library/svelte@^5 @testing-library/jest-dom jsdom --save-dev`
          in `client/`. (The `"test": "vitest run"` script already exists in `package.json`.)
          **Note:** `jsdom` retained in devDeps for compatibility but `happy-dom` is used as the
          actual test environment (see step 24 decision).

- [x] 24. Updated `client/vite.config.ts`:
          - Added `svelte()` plugin from `@sveltejs/vite-plugin-svelte`.
          - Added `test` config object: `globals: true`, `environment: 'happy-dom'`,
            `setupFiles: ['src/test-setup.ts']`, `resolve: { conditions: ['browser'] }`.
          - Added `coverage` sub-config (see step 27a).
          - Added top-level `resolve: { conditions: ['browser'] }` so Svelte resolves its
            browser (DOM) entry in both build and test environments.

- [x] 25. Created `client/src/test-setup.ts` importing `@testing-library/jest-dom`.

- [x] 25a. Extracted `_escapeCsvRow` from `history-page/index.ts` into a new exported function
           `escapeCsvRow` (without leading underscore — it is now public) in
           `client/src/shared/csv-utils.ts`. Updated `history-page/index.ts` to import from it.
           No behaviour change.

- [x] 25b. Wrote `client/src/shared/csv-utils.test.ts` with 8 test cases covering all
           `escapeCsvRow` edge cases (empty array, plain value, comma, double-quote, newline,
           carriage return, multi-value row). `make test-client` confirms 8/8 pass.

- [x] 26. Added `make test-client` to `Makefile`: `cd client && npm run test`.
          Not folded into `make test` — kept separate to avoid pulling Node into the Python
          edit cycle.

- [x] 27. Added `make test-client` and `make coverage-client` steps to CI `deploy-pages.yml`,
          after `Build client assets` and before `Generate HTML website`. Node/npm are
          already available at that point from `actions/setup-node@v4` inside the
          `build-client` composite action.

- [x] 27a. Coverage infrastructure:
           - `npm install @vitest/coverage-v8@^3 --save-dev` (pinned to `^3` to match
             `vitest@^3`; unpinned `@vitest/coverage-v8` resolved to v4 which requires
             vitest v4).
           - Added `"coverage": "vitest run --coverage"` to `client/package.json`.
           - Added `make coverage-client` to Makefile: `cd client && npm run coverage`.
           - `coverage` config in `vite.config.ts`: provider `v8`, include `src/**/*.{ts,svelte}`,
             exclude test-setup and test files.
           - **Thresholds:** `branches: 80, functions: 80, lines: 0, statements: 0`.
             Lines/statements start at 0 to avoid blocking CI before all modules have tests;
             they will ratchet upward in Phase 4c+ as Svelte components are added and tested.
             Branches/functions are already at 80% (all modules currently have 100% function
             coverage and ≥87% branch coverage).
           - Added `client/coverage/` to `.gitignore`.

- [x] 28. Wrote `HelloWorld.svelte` (Svelte 5 `$state` counter) and `HelloWorld.test.ts`.
          Confirmed both `make build-client` and `make test-client` pass with the smoke test.
          CSS file emission confirmed to be phase-4c behaviour (no Svelte component is wired
          into a page entry yet). Deleted `HelloWorld.svelte` and `HelloWorld.test.ts` after
          confirmation. `csv-utils.test.ts` is the only test file.

- [x] Doc: Updated CONTRIBUTING.md — added `make test-client` and `make coverage-client` to
         the Running Tests section with a table showing Vitest vs E2E scenarios, and when
         Vitest tests are required.
- [x] Doc: Updated copilot-instructions.md — added `make test-client` and `make coverage-client`
         to mandatory commands; documented the Vitest vs E2E boundary; noted that coverage is
         a migration confidence gate, not a substitute for edge-case thinking.

**Decision:** Used `happy-dom` instead of `jsdom` as the Vitest test environment. `jsdom@26+`
depends on `@csstools/css-calc` which is ESM-only; `@asamuzakjp/css-color` (a transitive
dependency) tries to `require()` it via CJS, causing an `ERR_REQUIRE_ESM` error. `happy-dom`
avoids this entirely and is lighter weight. `jsdom` remains in devDeps (required by
`@testing-library/svelte`) but is not the active environment.

**Decision:** Needed `globals: true` in Vitest config. `@testing-library/jest-dom` calls
`expect.extend(...)` in its module body; without `globals: true`, `expect` is not defined when
the setup file executes, causing `ReferenceError: expect is not defined`.

**Decision:** Added top-level `resolve: { conditions: ['browser'] }` in `vite.config.ts`.
Svelte 5's package exports default to the server entry (`index-server.js`). Without the
`browser` condition, `mount()` is not available and every `@testing-library/svelte` render
fails with `lifecycle_function_unavailable`. The condition must be at the top level (not inside
`test.resolve`) to be picked up by Vitest's module resolver.

**Decision:** `vite-plugin-svelte@^5` instead of plan's `@^4`. The `@^4` series requires
`vite@^5`; this project uses `vite@^6`. The `@^5` release is the Vite-6-compatible version
with identical API surface.

**Decision:** `@vitest/coverage-v8@^3` pinned to match `vitest@^3`. Unpinned `@vitest/coverage-v8`
resolved to v4 (which requires vitest v4), causing a peer dependency conflict.

**Decision:** `escapeCsvRow` exported without the leading underscore. The function was private
(`_escapeCsvRow`) in `history-page/index.ts`. Moving it to `shared/csv-utils.ts` as a public
export makes it Vitest-testable and clearly signals it is shared API.

---

## Pre-existing state at Phase 4 handoff

- `make test-client` and `make coverage-client` exist in `Makefile`.
- Vitest is configured in `client/vite.config.ts` with:
  - `globals: true` (needed by `@testing-library/jest-dom`)
  - `environment: 'happy-dom'` (NOT jsdom — jsdom@26+ has an ESM incompatibility)
  - `setupFiles: ['src/test-setup.ts']`
  - Top-level `resolve: { conditions: ['browser'] }` (needed so Svelte resolves its
    DOM entry; must be top-level, not inside `test.resolve`)
  - Coverage thresholds: `branches: 80, functions: 80, lines: 0, statements: 0`
    (lines/statements ratchet upward in Phase 4c+ as components gain tests)
- `client/src/test-setup.ts` imports `@testing-library/jest-dom` globally — **do not re-import
  it in individual test files**.
- `client/src/shared/csv-utils.ts` exists with `escapeCsvRow` exported and fully tested.
- No CSS files are currently emitted by the build. The first `.css` file in `dist/` will
  appear when a Svelte component is first imported by a page entry (step 44, Phase 4c-ii).
  `generate_website.py` already uses `shutil.copytree` — it will pick up CSS automatically.

---

## Phase 4a — CSS audit: tokens, BEM, and permanent scope

**Goal:** Establish the permanent CSS architecture before any component styles are written.
Apply BEM only to what permanently stays global. Extract design tokens so Svelte components
can reference `var(--color-signal-hot)` without importing anything.

- [x] 29. **Audit all stylesheets** (`common.css`, `analysis.css`, `homepage.css`, `history.css`,
          `species-detail.css`). For each rule, classify it as:
          - **Permanent global** — browser reset, page chrome, base HTML element styles.
          - **Static page HTML** — styles for Python-rendered HTML not inside a future Svelte island.
          - **Component-bound** — styles for elements that will become Svelte islands.
            Do not rename or BEM these — they are being deleted, not kept.

- [x] 30. **Extract CSS custom properties** into `:root` in `common.css`. Every repeated colour,
          spacing, and type-scale value becomes a token. Replace every hard-coded usage across
          all stylesheets with the corresponding token.
          Naming: `--category-name` (e.g. `--color-*`, `--spacing-*`, `--font-*`).

          **Decision:** Two minor colour consolidations were accepted during tokenisation:
          - `--color-signal-watch: #f59e0b` (was `#f39c12` in stat-cards) — harmonised to single token.
          - `--color-signal-avoid: #94a3b8` (was `#95a5a6` in stat-cards) — harmonised to single token.
          - `--color-surface-light: #f8f9fa` replaced `#f1f3f5` in `.summary-info` background.
          - `--color-text-muted: #7f8c8d` replaced `#666` for `.table-row-count` text.
          Affected E2E colour assertions were updated to match the new token values.

- [x] 31. **Apply BEM to permanent global CSS only** — rules classified as "permanent global"
          and "static page HTML" in step 29. Update class attributes in Jinja2 templates and
          class-name constants in `shared/constants.ts` at the same time.
          Do not BEM component-bound rules — they are going away.

          **Renames applied:**
          - `nav a.active` → `nav a.nav__link--active` (in `base.html`)
          - `.btn-primary/secondary/success/download/filters` → `.btn--primary/secondary/success/download/filters`
          - `.stat-card.stat-hot/watch/avoid` → `.stat-card.stat-card--hot/watch/avoid`
          - `.badge.hot/watch/avoid` → `.badge--hot/watch/avoid`
          - `.btn.secondary` (species detail) → `.btn--secondary`
          - `client/src/shared/constants.ts` left unchanged — `CSS.ACTIVE` and `CSS.FILTER_BTN`
            reference component-bound filter-button classes, not the renamed nav class.

- [x] 32. Run `make test-e2e` to confirm no visual regressions.
          Result: 106 passed (after updating colour assertions for the two consolidations above).

- [x] Doc: Update copilot-instructions.md — document the 3-layer CSS architecture
         (`common.css` global BEM, page-level BEM, Svelte scoped). Note BEM naming
         conventions and design token prefix (`--category-name`).

---

## Pre-existing state at Phase 4b handoff

- 3-layer CSS architecture is established (Phase 4a): `:root` design tokens in `common.css`;
  BEM applied to permanent global and static page HTML only; component-bound CSS left untouched.
- All BEM renames are done — templates and E2E tests already updated.
- `make test` → 620 passed, 95.50% coverage. `make test-e2e` → 106 passed.

### Current `rows` format in templates

The template variable `rows` (passed from Python to Jinja2) is **not** a simple list of lists.
It is `rows_enum = [list(enumerate(row)) for row in rows]`, so each row is
`List[Tuple[int, Any]]`. Example for a 3-column table:
```python
rows = [
    [(0, 'Aphonopelma'), (1, '1.5'), (2, '12.99')],
    [(0, 'Brachypelma'), (1, '2.0'), (2, '14.50')],
]
```
The serialiser in step 33 must work with the **pre-enumeration** form (`List[List[Any]]`
parallel to `List[str]` headers), not with the Jinja-side `rows_enum`.

### SVG sparkline cells

`convert_sparklines_in_rows(...)` runs **before** `rows_enum` is built. It replaces Unicode
sparkline strings with full SVG markup in the corresponding cells. These SVG strings are large
(~1–2 KB each) and not appropriate to include verbatim in the JSON payload.

The serialiser must skip sparkline cells (i.e. cells that are SVG strings or `None`/empty after
sparkline conversion) and instead pass the **original Unicode sparkline string** (from the raw
CSV) in the JSON payload. The Svelte `SortableTable` component will be responsible for
converting unicode → SVG client-side.

**Practical implication for step 33:** The serialiser should receive the raw `rows` list
(before sparkline conversion) alongside the headers, or a separate column mapping identifying
which column holds sparkline data.

### Step 34 will blank tables until Phase 4c-ii

Once `table.html` replaces the `{%- for row in rows %}` tbody with a mount div, all four
tables (breeder, dealer, snapshot, history) will render empty until Phase 4c-ii wires the
first Svelte component. This is intentional — the static website is not user-facing during
the migration branch — but it means `make test-e2e` **will fail** after step 34 and must not
be run until Phase 4c-ii is complete.

The correct verification gate for steps 33–35 is `make test` only (Python snapshot tests confirm
the mount div + script are present; E2E is deferred to Phase 4c-ii).

---

## Phase 4b — Python data contract + mount points

**Goal:** Prepare server-rendered HTML for Svelte takeover.

- [x] 33. In `src/website/` (likely `page_config.py` or a new `table_data_helpers.py`), add a
          serialiser `rows_to_json(headers, rows)` that converts the raw row data into a JSON-
          serialisable `List[dict]` keyed by column name. Rows are `List[List[Any]]` (before
          `enumerate`); any cell whose value starts with `'<svg'` should be omitted from its
          dict entry (replaced with the original raw Unicode sparkline string — see Pre-existing
          state note above). Write Python unit tests covering: basic conversion, SVG cell
          exclusion, empty input, and multi-row output.

          Make the serialiser available to each `generate_*` function in `generate_website.py`
          and pass its output as a new template variable `json_rows` alongside the existing
          `rows` (the enumerated form used by the remaining Jinja rendering).

- [x] 34. Update `templates/table.html`: replace the `{%- for row in rows %}` tbody loop (and
          all the closing `{% endfor %}` and `</tbody>`) with:
          ```html
          <tbody>
            <div id="{{ table_id }}-root"></div>
          </tbody>
          ```
          Add the data script immediately before the slice `<script>` tag:
          ```html
          <script>window.{{ table_id }}Data = {{ json_rows | tojson }};</script>
          ```
          Note: `json_rows` is the new template variable from step 33, NOT the existing `rows`
          variable (which holds enumerate-pairs and is not the correct format).

          After this step `make test-e2e` will fail (tables are blank — expected). Do NOT run
          E2E until Phase 4c-ii is complete.

- [x] 35. **Snapshot update:** run `make test`, review every snapshot diff — confirm each change
          is exactly the mount div + data script replacing row HTML. Update snapshots only after
          verifying this. Snapshots become minimal; expected and correct.

---
## Pre-existing state at Phase 4c-i handoff

- Phase 4b complete: `rows_to_json` serialiser lives in `src/website/table_data_helpers.py`,
  exported from `src/website/__init__.py`, tested with 15 unit tests.
- All three `generate_*` functions pass `json_rows` to their Jinja2 templates.
- `templates/table.html` tbody now renders a `<div id="{{ table_id }}-root"></div>` mount
  point; row data is injected as `window['{{ table_id }}Data'] = ...` (bracket notation
  required for hyphenated IDs like `breeder-table`).
- `html_utils.py` `generate_table_html()` also computes and passes `json_rows`.
- `make test` → 635 passed, 0 failures, 95.40% coverage.
- `make test-e2e` is **intentionally broken** (tables are blank — Svelte not yet mounted).
  Do NOT run E2E until Phase 4c-ii is complete.

---
## Phase 4c-i — Primitive Svelte components

**Goal:** Build shared UI atoms that both `SortableTable` and `HistoryTable` compose from.
Tight Vitest feedback — tested in isolation before assembly.

- [x] 36. Create `client/src/shared/components/RangeSlider.svelte`. Replaces `shared/range-slider.ts`.
          Props (via `$props()`): `min`, `max`, `label`, `onchange: (detail: {min: number, max: number}) => void`.
          Calls `onchange({min, max})` after constraint enforcement.
          `<style>` block uses design tokens; class names are simple and semantic
          (`.track`, `.thumb`, `.label`).
          Uses `$props.id()` to generate a stable unique ID for each component instance;
          labels bound via `{uid}-min` / `{uid}-max`.

- [x] 37. Create `client/src/shared/components/SearchInput.svelte`.
          Props: `placeholder`, `tableId`, `oninput: (value: string) => void`.
          Calls `oninput(currentValue)` on the native `input` event.
          `<style>` block with semantic names.

- [x] 38. Create `client/src/shared/components/FilterButton.svelte`.
          Props: `label`, `value`, `active`, `onclick: () => void`.
          Passes `onclick` directly to the `<button>` element.
          Uses `.is-active` modifier class with Svelte 5 object syntax:
          `class={{ 'filter-btn': true, 'is-active': active }}`.

- [x] 39. For each primitive: write Vitest tests co-located with each component file.
          `make test-client && make coverage-client` → 19 passed, branches 89.65% ✓.

          **`RangeSlider.svelte` — `RangeSlider.test.ts`:** 5 tests.
          **`FilterButton.svelte` — `FilterButton.test.ts`:** 4 tests.
          **`SearchInput.svelte` — `SearchInput.test.ts`:** 2 tests.

- [ ] 40. *(Deferred to Phase 4c-ii, step 45.)* `generate_website.py` already copies the
          entire `dist/` tree via `shutil.copytree` — no code change needed once CSS files
          start appearing. Confirm this after step 44 (first `mount()` call).

- [ ] 41. *(Deferred to Phase 4c-ii, step 45.)* Add `<link rel="stylesheet">` tags to page
          templates **only after** the first CSS file is confirmed to exist in `dist/`.
          Adding link tags before CSS exists causes 404s that E2E tests will catch.
          Do both steps (40 + 41 verification + link tags) as part of the step 45 E2E run.

- [x] Doc: Update copilot-instructions.md — added Svelte 5 component authoring guidelines:
         runes (`$state`, `$derived`, `$props`), `$props.id()` for unique IDs, semantic class
         names in `<style>` blocks, `fireEvent` must be awaited in tests (v5 wraps in `act`).

**Decision:** `toHaveValue()` for `input[type="range"]` fails in happy-dom because
`valueAsNumber` is returned as a string, not a number. Tests check `.value` property directly
(`(element as HTMLInputElement).value`) instead.

**Decision:** Clamp-up tests require using `max=200` props (not 100) so the test values (80)
don't get clamped by the HTML input's own `max` attribute before the event reaches the handler.
The sequence is: reduce max to 60 first, then push min to 80 — happy-dom won't clamp 80 on a
[0,200] input. The constraint logic (`if newMin > currentMax → clamp max up`) is confirmed.

---

## Pre-existing state at Phase 4c-ii handoff

### Primitives available in `client/src/shared/components/`

| Component | Props | Notes |
|---|---|---|
| `RangeSlider.svelte` | `min`, `max`, `label`, `onchange: ({min, max}) => void` | Uses `$props.id()` for unique label IDs |
| `SearchInput.svelte` | `placeholder`, `tableId`, `oninput: (value: string) => void` | Fires `oninput(value)` on native input event |
| `FilterButton.svelte` | `label`, `value`, `active`, `onclick: () => void` | Emits `.is-active` via Svelte 5 object class binding |

19 Vitest tests, all passing. `make build-client` succeeds. `make test-e2e` is **intentionally
broken** (tables blank — Svelte not yet mounted). Do NOT run E2E until step 45.

### Window data shape

Python injects table data as `window['<tableId>Data']` (bracket notation, not dot notation).
Each payload is an `Array<Record<string, string|number>>` — one dict per row keyed by column
header. **SVG cells are omitted** from the payload (stripped by `rows_to_json`). Unicode
sparkline strings are preserved as a string cell value under the column header
(e.g., `"Price History": "▁▂▃▄▅▆▇█"`).

Example payload shape:
```ts
window['breeder-tableData'] = [
  { "Species": "Brachypelma hamorii", "Size": "1.5", "Signal": "🔥", "Price History": "▁▂▆▄█" },
  ...
]
```

The TypeScript type to declare at the top of the page-slice `index.ts`:
```ts
declare global {
  interface Window {
    [key: string]: unknown;
  }
}
```

### Missing: `unicodeToSvg` helper — must be created in this phase

Step 42 imports it from `shared/`, but it does not yet exist.

Create `client/src/shared/sparklines.ts` with a single exported function:
```ts
export function unicodeToSvg(sparkline: string): string
```

It maps `▁▂▃▄▅▆▇█` (8-level block characters) to proportional SVG bar charts.
The Python `SPARKLINE_CHARS` mapping is `{ '▁': 1, '▂': 2, '▃': 3, '▄': 4, '▅': 5, '▆': 6, '▇': 7, '█': 8 }`.
Use the same 8-level height encoding. Return the Unicode string unchanged if it is empty, `"-"`,
or contains no recognised sparkline characters.

Write `client/src/shared/sparklines.test.ts` alongside it before implementing.

### E2E DOM-contract resolution (step 42a pre-answered)

The E2E tests in `tests/e2e/test_table_interactions.py` depend on:

| DOM feature | Current value | Svelte approach |
|---|---|---|
| Row visibility | `tr:visible` (Playwright CSS) | Render only visible rows in `{#each}` — no `.hidden` class needed |
| Sort direction | `data-sort-direction` attr on `<th>` | `SortableTable` **must** emit this attr |
| Filter buttons — class | `"active"` asserted via `get_attribute("class")` | **Update E2E to check `"is-active"`** (consistent with `FilterButton.svelte`) |
| Filter buttons — attrs | `data-action="filter-signal"`, `data-signal="🔥"` | `SortableTable` must set these on rendered `<FilterButton>` elements (add `data-action` and `data-signal`/`data-stock-pattern` props to `FilterButton.svelte`) |
| Filter btn class | `.filter-btn[data-action="filter-signal"]` compound selector | `FilterButton.svelte` already emits `.filter-btn` |
| Visible count | `#visible-count-<tableId>` span | `SortableTable` must emit `<span id="visible-count-{tableId}">` |
| Original row index | `data-original-index` on `<tr>` | **Not needed in Svelte** — top-10 logic slices `allRows` in original order inside `$derived.by`; no DOM attribute required |
| Advanced filter panel | `.show` class on content div | Svelte `{#if showAdvanced}` replaces class toggle |
| Data row attributes | `data-signal`, `data-stock-pattern` on `<tr>` | **Not needed** — E2E counts `tr:visible` rows; signal/pattern filtering is pure Svelte state |

**Key decisions to make in step 42a:**
1. Update E2E assertions from `"active"` → `"is-active"` (aligns with `FilterButton.svelte`).
   Alternatively, add a second class `.active` alongside `.is-active` in `FilterButton.svelte`,
   but that is messy. Preferred: update E2E.
2. Extend `FilterButton.svelte` with optional `data-action` and `data-value` passthrough props
   so `SortableTable` can set the `data-action`/`data-signal` attributes the E2E tests query.

---

## Phase 4c-ii — `SortableTable.svelte` (breeder, dealer, snapshot)

**Goal:** Svelte owns full table rendering for three pages.

- [x] 41b. Create `client/src/shared/sparklines.ts` with a single exported function:
           `unicodeToSvg(sparkline: string): string`.
           Maps the 8-level block characters (`▁▂▃▄▅▆▇█`) to proportional SVG bar charts.
           Returns the input unchanged for empty strings, `"-"`, or unrecognised characters.
           Write `sparklines.test.ts` co-located with the module **before** implementing.
           Result: 6 tests passing.

- [x] 42a. **E2E DOM-contract audit** completed. Decisions:
           1. Updated E2E assertions from `"active"` → `"is-active"` on filter buttons.
           2. Extended `FilterButton.svelte` with `...rest` spread props (not just `data-action`/
              `data-value` — any HTML attribute passthrough). `SortableTable` sets
              `data-action`, `data-signal`, `data-stock-pattern`, `data-limit` via spread.

- [x] 42. Created `client/src/shared/components/SortableTable.svelte`. Svelte 5 runes.
          Composes `RangeSlider`, `SearchInput`, `FilterButton` primitives.
          `ColumnConfig` interface includes `type?: 'sparkline' | 'species-link'` and
          `linkViewParam?: string` (for `?view=breeder/dealer` on species links).
          Supports `FilterConfig` with `signalFilter`, `stockPatternFilter`, `priceColumn`,
          `wishlistColumn`, `showSearch`, `statsLabel`.
          `StockPatternFilterConfig` supports separate stock-pattern filter buttons.
          `$state.raw` for row data; `$derived.by` for multi-step filter chain.

- [x] 43. Wrote `SortableTable.test.ts` co-located. 25 tests passing.
          `make test-client && make coverage-client` ✓.

- [x] 44. Updated `breeder-page/index.ts`, `dealer-page/index.ts`, `snapshot-page/index.ts`
          to `mount()` `SortableTable`. Old DOM-wiring removed from each `index.ts`.
          Added `linkViewParam: 'breeder'` / `linkViewParam: 'dealer'` to Species column config.

- [x] 45. `make build-client && make test-e2e` → 106/106 passed.
          E2E fixes applied (see Decisions log).

- [ ] 46. Audit `analysis.css` — remove rules now covered by `SortableTable`'s scoped styles.
          (Not yet done — `analysis.css` still 312 lines.)

---

## Pre-existing state at Phase 4c-iii handoff

- Phase 4c-ii complete: `SortableTable.svelte` mounts on breeder, dealer, snapshot pages.
- `make test` → 635 passed, 95.40% coverage. `make test-e2e` → 106 passed.
- `make test-client` → 55 passed (6 shared utils, 49 component tests).
- Step 46 (`analysis.css` audit) was deferred — carry it into Phase 4e cleanup.

## State at Phase 4c-iii completion

- Steps 47–50 complete: `DateFilter.svelte` + `HistoryTable.svelte` mounted on history page.
- `make test` → 635 passed, 95.40% Python coverage.
- `make test-client` → 96 passed (DateFilter: 16 tests, HistoryTable: 21 tests).
- `make coverage-client` → 81.49% branches ≥ 80% threshold.
- `make test-e2e` → 106 passed.
- Step 51 (`history.css` audit) deferred to Phase 4e alongside step 46 (`analysis.css` audit).

### History page current state — server-rendered rows

The history page does **not** use Svelte yet. `table.html` has a two-mode render system:

- **Svelte mode** (default, all other pages): emits only `<div id="{tableId}-root"></div>` +
  `<script>window['...Data'] = [...];</script>`. No `<table>` element.
- **Server-rendered mode** (`render_server_rows=True`): emits a full `<table>` with `<thead>` and
  `<tbody>` rows carrying `data-date`, `data-price`, `data-wishlist`, `data-raw` attributes.
  Used by `history_page.html` only.

`history-page.js` (plain TypeScript, no Svelte) manipulates the server-rendered `<tbody> <tr>`
elements directly via `filterRows()` from `shared/filter.ts`. The JS reads `data-date` for date
filtering and `data-price`/`data-wishlist` for slider filtering.

**Consequence for Phase 4c-iii:** Once `HistoryTable.svelte` is mounted:
1. `history_page.html` should switch to the Svelte mount-div mode (remove `render_server_rows=True`).
2. The `render_server_rows` branch in `table.html` becomes dead code and can be removed.
3. `data-date`, `data-raw`, `data-price`, `data-wishlist` server-side attribute generation goes away.
4. `filterRows()` in `shared/filter.ts` is no longer needed for history — defer deletion to Phase 4e.

### DOM attributes the history E2E tests depend on

| DOM feature | Current (server-rendered) | Svelte approach |
|---|---|---|
| Row visibility | `.hidden` class toggled by JS | `{#each}` over filtered rows — no class toggle |
| Date filter | `data-date` on `<tr>` | `HistoryTable` holds selected dates in `$state` |
| Price/wishlist filter | `data-price`, `data-wishlist` on `<tr>` | Slider state in `$derived.by` filter chain |
| CSV export | `data-raw` on date `<td>` | Build CSV from `visibleRows` `$derived` state |
| Date checkboxes | Python-rendered `<input type="checkbox">` | `DateFilter.svelte` renders its own checkboxes |

---

## Phase 4c-iii — `HistoryTable.svelte` (history page)

**Goal:** Svelte owns history table with its own distinct filter composition.

- [x] 47. Created `client/src/history-page/DateFilter.svelte`. Svelte 5 runes.
          Owns checkbox date picker, "Last N Runs" quick-select, "Show All".
          Emits `change` with selected dates array via callback prop `onchange`.
          `<style>` block with semantic names (`.date-list`, `.date-item`, `.quick-select`,
          `.date-controls`, `.search-hint`).

- [x] 48. Created `client/src/history-page/HistoryTable.svelte`. Composes `RangeSlider`,
          `SearchInput`, and `DateFilter` in its own arrangement (not `SortableTable`).
          Accepts `rows` and `columns` props. Sort and filter state in `$state`.
          `<style>` block with semantic names; equivalent rules removed from `history.css`.
          Uses `$state.raw(rows)` for the incoming row data and `$derived.by` for the
          multi-step filter derivation (date selection → search → price → wishlist).
          Advanced-filters panel toggled with `showAdvanced: boolean` state;
          filter badge shows active filter count.

- [x] 49. Wrote `DateFilter.test.ts` (16 tests) and `HistoryTable.test.ts` (21 tests)
          co-located with each component.
          `make test-client && make coverage-client` → 96 passed, 81.49% branches ✓.

          **`DateFilter.svelte` — `DateFilter.test.ts` (16 tests):**
          - Renders one checkbox per unique date in the `dates` prop
          - Unchecking a date fires a `change` event with that date excluded from the payload
          - "Last N Runs" quick-select fires `change` with exactly the N most recent dates
          - "Show All" fires `change` with all dates checked

          **`HistoryTable.svelte` — `HistoryTable.test.ts` (21 tests):**
          - Deselecting a date → rows for that date hidden
          - Search text → only matching rows visible
          - Date + search AND logic: only rows matching both date selection and search text
          - Price slider below a row's price → that row hidden
          - Wishlist slider above a row's count → that row hidden
          - Combined: date + search + price → intersection of all three filters applied

- [x] 50. Updated `history-page/index.ts` to mount `HistoryTable`. Removed
          `render_server_rows=True` from `history_page.html` call; removed server-rendered
          `<tbody>` rows from `table.html` (dead code path deleted).
          Injected `_raw_scrape_datetime` key into each JSON row from Python so Svelte
          `DateFilter` can group rows by date.
          Added 5 CSS `<link>` tags to `history_page.html` for Svelte-emitted scoped CSS
          (`HistoryTable.css`, `DateFilter.css`, `SearchInput.css`, `SortableTable.css`,
          `RangeSlider.css`) — required because Vite does not auto-inject component CSS.
          Rewrote 11 Python unit tests in `TestGenerateHistoryPage` to assert JSON data
          payload structure instead of server-rendered DOM elements.
          `make build-client && make test-client && make test-e2e`:
          96 client tests pass, 106 E2E tests pass ✓.
          `make test` → 635 passed, 95.40% Python coverage ✓.

- [ ] 51. Audit `history.css` — remove rules now covered by scoped component styles.
          (Not yet done — carry into Phase 4e cleanup.)

---

## Pre-existing state at Phase 4d handoff

### `HistoryTable.svelte` — download already implemented (Phase 4c-iii)

`HistoryTable.svelte` has full download logic:
- Imports `escapeCsvRow` from `shared/csv-utils.js`
- `buildCsv(): string` — iterates `visibleRows` (the `$derived.by` result), maps each row
  through `col.csvHeader ?? col.key` for headers and `col.rawValueKey ?? col.key` for values
- `downloadCsv(): void` — calls `buildCsv()`, creates a `Blob`, programmatically clicks a
  temporary `<a download>` link
- Download button: `<a data-action="download-filtered-csv" class="btn btn--download">` rendered
  in the toolbar
- `HistoryTable.test.ts` has **one** smoke test: clicking the download link calls
  `URL.createObjectURL`. Detailed CSV content tests are absent — add them in step 53.

### `SortableTable.svelte` — download NOT implemented

`ColumnConfig` already has `csvHeader?: string` (added for `HistoryTable` parity) but `SortableTable`
has no `buildCsv()`, no `downloadCsv()`, no download button, and no `escapeCsvRow` import.
Full download implementation is required in step 52.

### Test pattern for CSV content assertions

`buildCsv()` is a plain function (not `$derived`) — test it via mock interception:
```ts
const mockBlob = vi.fn();
global.Blob = mockBlob as unknown as typeof Blob;
// ... render, apply filter, click download link ...
const csvText: string = mockBlob.mock.calls[0][0][0];
expect(csvText).toContain('header,row\n');
```
Or mock `URL.createObjectURL` and inspect the `Blob` argument:
```ts
const createObjectURL = vi.spyOn(URL, 'createObjectURL');
// ... click download ...
const blob: Blob = createObjectURL.mock.calls[0][0] as Blob;
const text = await blob.text();
expect(text.split('\n')).toHaveLength(4); // header + 3 data rows
```

---

## Phase 4d — CSV download in Svelte

**Goal:** Replace DOM-scraping `downloadFilteredCsv` with component-state-based export.

- [x] 52. `HistoryTable.svelte` download is already implemented (see pre-phase state above).
          Added download logic to `SortableTable.svelte`:
          - Imported `escapeCsvRow` from `../csv-utils.js`
          - Added `buildCsv(): string` iterating `visibleRows` using `col.csvHeader ?? col.key`
            for headers and `col.rawValueKey ?? col.key` for cell values
          - Added `downloadCsv(): void` — same blob+link pattern as `HistoryTable`
          - Added download button to the `table-stats` strip:
            `<a data-action="download-filtered-csv" class="btn btn--download">`
          - Updated `.table-stats` CSS to `display: flex; justify-content: space-between`
            so the stats label and download button sit on opposite sides.
          Download filename: `${tableId}_filtered.csv`.

- [x] 53. Written Vitest tests for CSV download in `SortableTable.test.ts` (8 new tests)
          and augmented `HistoryTable.test.ts` (5 new tests, existing smoke test kept).
          Used `vi.stubGlobal` (consistent with `HistoryTable`) rather than `vi.spyOn`
          to mock `URL.createObjectURL` — avoids `TypeError: URL is not a constructor`
          from happy-dom's internal navigation on anchor click.
          Added `beforeEach` to clear mock call history between tests.
          `make test-client && make coverage-client` → 109 passed, 81.25% branches ✓.

          Test cases in `SortableTable.test.ts`:
          - Download link is rendered
          - Clicking download calls `URL.createObjectURL`
          - CSV has header + all rows when unfiltered
          - CSV uses `col.key` as header when `csvHeader` not set
          - Filtered CSV excludes hidden rows (signal filter to 🔥)
          - CSV uses `csvHeader` for column headers when provided
          - CSV uses `rawValueKey` for cell values when provided
          - RFC-4180: values with commas are double-quoted

          Additional test cases in `HistoryTable.test.ts`:
          - CSV header uses `csvHeader` values (e.g. `scrape_datetime`)
          - CSV data uses `rawValueKey` for date column (ISO datetime, not display date)
          - CSV has header + all rows when unfiltered
          - Filtered CSV (date-deselected) excludes hidden rows
          - RFC-4180: values with commas are double-quoted

- [x] 54. `make test-client` → 109 passed. `make test-e2e` → 106 passed.

## State at Phase 4d completion

- Steps 52–54 complete: `SortableTable.svelte` has full CSV download parity with `HistoryTable`.
- `make test-client` → 109 passed (8 new `SortableTable` CSV tests + 5 new `HistoryTable` CSV tests).
- `make coverage-client` → 81.25% branches ≥ 80% threshold ✓.
- `make test-e2e` → 106 passed.
- `vi.stubGlobal` used for `URL.createObjectURL` mock (consistent with `HistoryTable.test.ts`);
  `beforeEach` clears mock call history so each CSV test starts clean.

**Decision:** Download filename for `SortableTable` is `${tableId}_filtered.csv` (dynamic),
giving breeder, dealer, and snapshot pages their own distinct filenames
(`breeder-table_filtered.csv`, etc.). `HistoryTable` keeps its fixed filename
`spidershop_spiderlings_history_filtered.csv`.

---

## Phase 4e — Retire dead code

**Goal:** Remove all replaced TypeScript, stale CSS, and stale script tags.

---

## Pre-existing state at Phase 4e handoff

### Dead TypeScript modules (safe to delete)

These three shared modules are completely unreferenced — no `import` of any of them exists
anywhere in `client/src/`:

| File | Was used for | Replaced by |
|---|---|---|
| `client/src/shared/filter.ts` | DOM row filtering via `filterRows()` | `$derived.by` chains in `SortableTable` / `HistoryTable` |
| `client/src/shared/sort.ts` | DOM sort helpers | `$derived.by` sort in `SortableTable` / `HistoryTable` |
| `client/src/shared/range-slider.ts` | Imperative `RangeSlider` class | `RangeSlider.svelte` primitive |

### Shared modules that are still alive — do NOT delete

| File | Still used by |
|---|---|
| `client/src/shared/constants.ts` | `species-page/charts.ts` |
| `client/src/shared/dom-utils.ts` | `species-page/charts.ts` |
| `client/src/shared/csv-utils.ts` | `SortableTable.svelte`, `HistoryTable.svelte` |
| `client/src/shared/sparklines.ts` | `SortableTable.svelte`, `HistoryTable.svelte` |

### Page index.ts files — already clean

All four page `index.ts` files (`breeder-page`, `dealer-page`, `snapshot-page`, `history-page`)
contain only Svelte `mount()` calls and, for breeder/dealer, a `wireOpenDetailsLinks()` helper
that wires the `<details>` accordion elements. This function is **live app code**, not a
migration artefact — do NOT remove it.

There is no remaining DOM-wiring code from the pre-migration era in any page `index.ts`.

### dist/ output shape — expected

`preserveModules: true` causes Vite to emit many files beyond the five entry points.
The full `dist/` tree includes:
- Five entry point `.js` files: `breeder-page.js`, `dealer-page.js`, `snapshot-page.js`,
  `history-page.js`, `species-page.js`
- Sub-module JS files: `shared/components/*.svelte.js`, `shared/csv-utils.js`,
  `shared/sparklines.js`, `shared/constants.js`, `shared/dom-utils.js`,
  `history-page/DateFilter.svelte.js`, `history-page/HistoryTable.svelte.js`,
  `species-page/charts.js`, etc.
- Bundled node_modules: `node_modules/svelte/src/...` (Svelte runtime), `node_modules/clsx/...`
- Scoped CSS: `assets/history-page/DateFilter.css`, `assets/shared/components/*.css`, etc.

This is **correct and expected** — `generate_website.py` copies the entire tree with
`shutil.copytree`. There is no "exactly 5 files" goal; the goal is that each page loads
only its own slice entry script and no stale entry points remain.

### vite.config.ts — already clean

All five entries in `rollupOptions.input` map to live source files. No stale entries.

### Template script references — already clean

| Template | slice loaded |
|---|---|
| `analysis_page.html` | `{{ page_script }}` (dynamic, set per page) |
| `history_page.html` | `history-page.js` (explicit) |
| `snapshot_page.html` | `snapshot-page.js` (explicit) |
| `species_detail.html` | `species-page.js` (direct `<script>` tag, not `extra_js` block) |

No stale script references exist. Step 57 is a quick verification pass only.

### CSS deferred audits (steps 46 and 51)

Two CSS audits were deferred into Phase 4e:
- **`analysis.css` (312 lines)** — step 46, deferred from Phase 4c-ii
- **`history.css` (132 lines)** — step 51, deferred from Phase 4c-iii

`homepage.css` (70 lines) and `species-detail.css` (311 lines) are out of scope for Svelte
migration at this phase — `homepage.css` has no Svelte island and `species-detail.css`
is targeted in Phase 5.

---

- [x] 55. Deleted `client/src/shared/filter.ts`, `client/src/shared/sort.ts`,
          `client/src/shared/range-slider.ts` — confirmed unreferenced.
          `constants.ts` and `dom-utils.ts` retained (still used by `species-page/charts.ts`).
          `make build-client` → zero compile errors after deletion ✓.

- [x] 56. Verified `vite.config.ts` `rollupOptions.input` has exactly five live entries:
          `breeder-page`, `dealer-page`, `snapshot-page`, `history-page`, `species-page`.
          No stale entries. `dist/` contains many more files — correct `preserveModules`
          behaviour expected by `generate_website.py`.

- [x] 57. Verified page templates reference only current slice scripts — all clean.

- [x] 58. Audited and trimmed `analysis.css` (312 → ~230 lines) and `history.css`:
          **`analysis.css`**: removed `.filter-btn`, `.filter-btn:hover`, `.filter-btn.active`,
          `.filter-buttons-container`, `.signal-filter-row`, `.filter-row`, `.filter-label`,
          `.table-row-count` and their mobile responsive overrides — all now in
          `FilterButton.svelte` and `SortableTable.svelte` scoped styles.
          Also added `display: inline-flex; align-items: center; gap: var(--spacing-xs)`
          to `FilterButton.svelte` to preserve the CSS contract (removing the global
          `display: inline-flex` rule would otherwise make Playwright report `block`
          due to CSS blockification in flex containers).
          **`history.css`**: deleted entirely — every rule is now covered by
          `HistoryTable.svelte` and `DateFilter.svelte` scoped styles.
          Removed `<link rel="stylesheet" href="...history.css">` from `history_page.html`
          and removed `"history.css"` from the `css_files` copy list in
          `generate_website.py`.
          `make build-client && make test-e2e` → green ✓.

- [x] 59. `make test` → 635 passed, 95.40% Python coverage ✓.
          `make test-client` → 109 passed ✓.
          `make coverage-client` → branches ≥ 80% threshold met ✓.
          `make test-e2e` → 106 passed ✓.

- [x] Doc: `copilot-instructions.md` — removed `history.css` from the CSS architecture
         table (Layer 2 — Page-level static). CONTRIBUTING.md has no stale references
         to deleted files — no changes needed.

---

## State at Phase 4e completion

- Steps 55–59 complete: dead TypeScript modules deleted, `analysis.css` trimmed,
  `history.css` deleted entirely.
- `client/src/shared/` now contains only live modules: `constants.ts`, `dom-utils.ts`,
  `csv-utils.ts`, `sparklines.ts`, and `components/` (all Svelte components).
- `FilterButton.svelte` gained explicit `display: inline-flex` to preserve the CSS
  contract that the now-removed global `.filter-btn` rule previously provided.
- `make test` → 635 passed, 95.40% Python coverage.
- `make test-client` → 109 passed.
- `make coverage-client` → branches ≥ 80% threshold ✓.
- `make test-e2e` → 106 passed.

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

## Phase 4f — Post-migration cleanup (dead code, duplication, simplification)

**Goal:** Remove all code made dead by the Svelte migration, eliminate copy-paste duplication
between `SortableTable` and `HistoryTable`, and fix two consistency issues in `DateFilter`.
This phase is independent of Phase 5 (it does not touch `charts.ts`, `dom-utils.getElement`,
or `constants.CHART` — those are left for Phase 5 to delete).

**Suggested session split** (open a new conversation per session, feed it only the relevant section):

| Session | Sections | Focus |
|---|---|---|
| 1 | A + C | Pure deletions + token swap — trivial, fast, zero logic change |
| 2 | B | Extract `table-utils.ts` — TDD cycle, deserves full focus |
| 3 | D | Python dead code — variable tracing across 3 functions + `html_utils.py` |
| 4 | E + F | CSS/template removal + full gate verification |

---

## Pre-existing state at Phase 4f handoff

- Phase 4e complete (steps 55–59): dead TS modules removed, `analysis.css` trimmed,
  `history.css` deleted.
- Sections A, B, C, D, E, F all complete.
- `make test` → 597 passed, 95.34% Python coverage.
- `make test-client` → 134 passed.
- `make coverage-client` → branches ≥ 80% threshold.
- `make test-e2e` → 106 passed.

### Dead TypeScript (Section A)

| File | What is dead | Why |
|---|---|---|
| `shared/dom-utils.ts` | `setActiveButton()`, `toggleRowVisibility()`, `import { CSS }` | Replaced by Svelte reactive state; no importer exists |
| `shared/constants.ts` | `CSS` object, `CONFIG` object, `CssClasses` and `AppConfig` interfaces | Only consumed by the two dead functions above |
| `SortableTable.svelte` | `SignalFilterConfig.summaryStats` field + its `{#if}` template block | Never populated by any page slice entry point |
| `SortableTable.svelte` | `StockPatternFilterConfig.counts` field | Defined but never populated; no template rendering for it |
| `SortableTable.svelte` | `data-price` and `data-wishlist` on `<tr>` | Filtering is pure Svelte state; these DOM attrs are not read by anything |

### Duplication (Section B)

The following are byte-for-byte identical in both `SortableTable.svelte` and `HistoryTable.svelte`:
- `priceRange` and `wishlistRange` IIFEs (range computation)
- Sort comparator block inside `$derived.by`
- `handleSort()` function
- `buildCsv()` function
- `downloadCsv()` / `triggerDownload` logic
- `handlePriceChange()`, `handleWishlistChange()`, `formatPrice` constant

Also duplicated across entry files:
- `wireOpenDetailsLinks()` — byte-for-byte identical in `breeder-page/index.ts` and `dealer-page/index.ts`
- `if (document.readyState === 'loading') { ... } else { init(); }` boilerplate — all five slice entry points

### `HistoryTable` `$effect` timing issue (Section B, step B4)

`selectedDates` is initialised as an empty `Set` then filled by a `$effect` on first run.
Between mount and the first effect tick, `visibleRows` filters against an empty set (the
`selectedDates.size < allDates.length` guard evaluates `0 < n = true` on the first render,
applying the date filter with no dates selected → zero visible rows briefly).
Fix: compute `allDates` synchronously from `$state.raw(rows)` at module level and initialise
`selectedDates` inline: `let selectedDates = $state(new Set(allDates))`.
Since `allDates` is derived iteratively in the current implementation, extract it as a plain
function `computeAllDates(rows, dateColumn)` (pure, no reactivity), call it once during
initialisation, and keep the `$derived` for reactive re-computation. Or simply call the
same loop body inline.

### `DateFilter.svelte` hardcoded colours (Section C)

The `<style>` block uses literals instead of design tokens:
- `background: white` → `var(--color-surface)`
- `border: 1px solid #ddd` → `var(--color-border-light)`
- `color: #888` → `var(--color-text-muted)`
- `border-top: 1px solid #e8c400` → `var(--color-date-filter)` (already used by E2E test token)
- `border-radius: 6px` → `var(--radius-md)`

### Dead Python code (Section D)

| Code | Location | Why dead |
|---|---|---|
| `_parse_price_value()` | `generate_website.py` | Only called by `_calculate_column_range` |
| `_calculate_column_range()` | `generate_website.py` | Only called by `_build_slider_ranges` |
| `_build_slider_ranges()` | `generate_website.py` | Return values (`price_min/max`, `wishlist_min/max`) passed to templates that don't consume them — Svelte computes its own ranges client-side |
| ~40 template vars in `generate_analysis_page()` | `generate_website.py` | `page_url_idx`, `scientific_name_idx`, `species_idx`, `size_idx`, `signal_col_idx`, `stock_pattern_col_idx`, `drivers_col_idx`, `link_to_species_page`, `table_view`, `search_filter`, `stock_pattern_counts`, `sortable` — all passed to `template.render()` but not referenced by any template |
| Same class of vars in `generate_snapshot_page()` | `generate_website.py` | `page_url_idx`, `scientific_name_idx`, `price_idx`, `wishlist_idx`, range vars, `hidden_col_indices`, `sortable`, `search_filter`, `raw_headers` |
| Same class of vars in `generate_history_page()` | `generate_website.py` | Same as above plus `scrape_datetimes`, `row_date_counts`, `total_rows`, `num_runs`, `min_date`, `max_date` — verify each against `history_page.html` before deleting |
| `analysis_html = None` + `{% if analysis_html %}` block | `generate_website.py` + `analysis_page.html` | Unconditionally `None`; the conditional block in the template never renders |
| Local `from collections import Counter` inside `generate_analysis_page()` | `generate_website.py` | `Counter` already imported at module level (~line 42) |
| `generate_table_html()` | `html_utils.py` | Imported but never called from `generate_website.py` |
| `get_base_html_template()`, `get_html_footer()` | `html_utils.py` | "Kept for backward compatibility with tests" — `get_html_footer()` still references `table-interactions.js` which no longer exists in `dist/` |
| `escape_html()` | `html_utils.py` | "Kept for backward compatibility with tests"; not called from any production code path |

Before deleting functions from `html_utils.py`, check `tests/website_module/` for any tests
that call them directly - those tests must be removed or rewritten first.

### Dead CSS (Section E)

All in `templates/common.css`:
- Old imperative dual-range slider (~90 lines): `.dual-range-slider`, `.slider-container`,
  `.slider`, `.slider-min`, `.slider-max`, `.slider-values`, `.slider-current`,
  `-webkit-slider-*` / `-moz-range-*` pseudo-elements
- `.table-controls` and its child `input` / `label` rules
- `.advanced-filters-content.show { display: block }` and the `.filter-row` block
- `.advanced-filters-toggle .when-expanded` / `.when-collapsed` / `.expanded` class variants
- Second `.search-input` block at the bottom (hardcoded `#ddd`; overridden by Svelte scoped version)
- Global `.table-stats` rule — assess whether it conflicts with Svelte-scoped versions;
  remove if the scoped version is the sole intended style

In `templates/macros.html`:
- `search_filter`, `signal_filter_buttons`, `stock_pattern_filter_buttons` macro definitions —
  never called from any template

---

## Phase 4f steps

### Section A — TypeScript dead code

- [x] A1. In `client/src/shared/dom-utils.ts`: delete `setActiveButton()` and
          `toggleRowVisibility()`. Remove the `import { CSS }` line (only those two functions
          used it). Keep `getElement`.

- [x] A2. In `client/src/shared/constants.ts`: delete the `CSS` constant, `CONFIG` constant,
          and their interfaces `CssClasses` and `AppConfig`. Keep `CHART` and `ChartConfig`.

- [x] A3. In `client/src/shared/components/SortableTable.svelte`:
          - Remove `summaryStats` from `SignalFilterConfig` interface and its
            `{#if filterConfig.signalFilter.summaryStats}` template block.
          - Remove `counts` from `StockPatternFilterConfig` interface.
          - Remove `data-price` and `data-wishlist` attributes from the `<tr>` in the table body.
          - Remove the now-empty `.summary-stats` scoped CSS rule.

- [x] A4. `make build-client && make test-client` — zero errors; then run `make test-e2e`.

---

### Section B — Extract shared table utilities + fix `HistoryTable` init

- [x] B1. Create `client/src/shared/table-utils.ts` with four exported pure functions:
          - `computeRange(rows, col, mode: 'float' | 'int'): { min: number; max: number }` —
            replaces the identical `priceRange` and `wishlistRange` IIFEs in both components.
            `mode: 'float'` uses `parseFloat` + `Math.floor/ceil`; `mode: 'int'` uses `parseInt`.
            Returns `{ min: 0, max: 0 }` when col is falsy or no valid values found.
          - `sortRows(rows, key, dir: 'asc' | 'desc'): Record<string, unknown>[]` —
            extracts the identical sort comparator (numeric detection via `parseFloat`,
            string `localeCompare`, direction toggle).
          - `buildCsv(columns: CsvColumn[], visibleRows, escapeFn): string` —
            identical in both components; headers from `col.csvHeader ?? col.key`,
            values from `col.rawValueKey ?? col.key`. Accepts a minimal `CsvColumn`
            interface (key, csvHeader?, rawValueKey?) — `ColumnConfig` is structurally
            compatible and TypeScript accepts it without casting.
          - `triggerDownload(content: string, filename: string): void` —
            blob + temporary anchor click pattern; filename varies per caller.

- [x] B2. Write `client/src/shared/table-utils.test.ts` co-located. Cover:
          - `computeRange`: empty rows → `{0,0}`, float mode (floor/ceil), int mode,
            single-value, col undefined → `{0,0}`, skips NaN values
          - `sortRows`: numeric asc, numeric desc, string asc, string desc,
            mixed (one numeric one string) → string comparison, does not mutate original
          - `buildCsv`: headers use `csvHeader ?? key`, values use `rawValueKey ?? key`,
            RFC-4180 comma quoting, empty rows → header line only, CRLF endings
          - `triggerDownload`: calls `URL.createObjectURL` once; `revokeObjectURL` called after;
            Blob has `text/csv` mime type
          TDD: confirmed RED (module missing) then GREEN after B1.
          Result: 25 new tests in `table-utils.test.ts`; total 134 passed.

- [x] B3. Updated `SortableTable.svelte`: imported `computeRange`, `sortRows`, `buildCsv`,
          `triggerDownload` from `'../table-utils.js'`. Removed the two IIFE blocks,
          the sort comparator inside `$derived.by`, local `buildCsv()`, and `downloadCsv()`.
          `downloadCsv()` replaced with a single-line wrapper calling
          `triggerDownload(buildCsv(columns, visibleRows, escapeCsvRow), ...)`.
          `formatPrice` stays local (display-specific, not shared logic).

- [x] B4. Updated `HistoryTable.svelte`:
          - Same imports as B3; replaced the same duplicated blocks.
          - Fixed `$effect` initialisation: extracted `collectAllDates(sourceRows, dateCol)`
            as a local non-reactive function at module level. Calls it once to initialise
            `selectedDates` synchronously:
            `let selectedDates = $state(new Set(collectAllDates(rows, dateColumn)))`.
            `$derived allDates` kept for `DateFilter`'s reactive input (re-derives from
            `allRows` on any future rows change).
            `$effect` block removed entirely.

- [x] B5. Moved `wireOpenDetailsLinks()` into `client/src/shared/dom-utils.ts` as a named
          export. Updated `breeder-page/index.ts` and `dealer-page/index.ts` to import it.

- [x] B6. `make build-client` → zero errors. `make test-client` → 134 passed.
          `make coverage-client` → branches ≥ 80% ✓. `make test-e2e` → 106 passed.

---

### Section C — `DateFilter.svelte` token consistency

- [x] C1. In `client/src/history-page/DateFilter.svelte` `<style>` block, replace hardcoded
          colour/spacing literals with design tokens:
          - `background: white` → `background: var(--color-surface)`
          - `border: 1px solid #ddd` → `border: 1px solid var(--color-border-light)`
          - `color: #888` → `color: var(--color-text-muted)`
          - `border-top: 1px solid #e8c400` → `border-top: 2px solid var(--color-date-filter)`
          - `border-radius: 6px` → `border-radius: var(--radius-md)`

- [x] C2. `make test-e2e` — `test_history_date_filter_section_styling` and
          `test_history_date_grid_styling` will catch any token value mismatch.

---

### Section D — Python dead code

- [x] D1. In `src/website/generate_website.py`: delete `_parse_price_value()`,
          `_calculate_column_range()`, and `_build_slider_ranges()`. These three functions
          form a call chain whose final output is only passed to templates that don't consume it.
          Also deleted `_find_column_indices()` (no callers remained after D3+D4).
          Also removed `Counter` from module-level import (no longer used), `Callable` and
          `Tuple` from typing (used only by deleted functions), and `generate_table_html` from
          the `html_utils` import (deleted in D5).

- [x] D2. In `generate_analysis_page()`:
          - Remove the `stock_pattern_counts` Counter block.
          - Remove the duplicate local `from collections import Counter` import.
          - Remove all dead template variables and their computation:
            `page_url_idx`, `scientific_name_idx`, `species_idx`, `size_idx`, `signal_col_idx`,
            `stock_pattern_col_idx`, `drivers_col_idx`, `link_to_species_page`, `table_view`,
            `search_filter`, `sortable`.
          - Remove `analysis_html = None` and the corresponding
            `{% if analysis_html %}` block from `templates/analysis_page.html`.
          - Remove all dead kwargs from the `template.render()` call.

- [x] D3. In `generate_snapshot_page()`: remove the `_find_column_indices()` call +
          resulting dead index variables, the `_build_slider_ranges()` call + range variables,
          and `hidden_col_indices`, `sortable`, `search_filter`, `raw_headers`.
          Remove all dead kwargs from `template.render()`.

- [x] D4. In `generate_history_page()`: same pattern. Before deleting `scrape_datetimes`,
          `row_date_counts`, `total_rows`, `num_runs`, `min_date`, `max_date` — verified
          each against `templates/history_page.html`; none are referenced. Removed all.
          `raw_datetimes` kept (used for `_raw_scrape_datetime` injection).
          Remove all confirmed-dead kwargs from `template.render()`.

- [x] D5. In `src/website/html_utils.py`:
          - Removed all tests from `tests/website_module/test_html.py` (entire file deleted).
          - Removed 3 snapshot tests (`test_table_structure_snapshot`,
            `test_navigation_structure_snapshot`, `test_footer_structure_snapshot`) from
            `test_integration.py` and their snapshot entries from `test_integration.ambr`.
          - Removed unused `from website import get_base_html_template` import from `test_css.py`.
          - Deleted `generate_table_html()`, `get_base_html_template()`, `get_html_footer()`,
            `escape_html()` from `html_utils.py`.
          - Removed dead exports from `src/website/__init__.py`.

- [x] D6. `make test` — 597 passed, 95.34% Python coverage ✓

---

### Section E — CSS and template dead code

- [x] E1. In `templates/common.css`, remove (verify each selector is absent from all `templates/`
          and `client/src/` files before deleting):
          - Old imperative slider block (~90 lines): `.dual-range-slider`, `.slider-container`,
            `.slider`, `.slider-min`, `.slider-max`, `.slider-values`, `.slider-current`
            and all `-webkit-slider-*` / `-moz-range-*` pseudo-element variants. ✓ deleted
          - `.table-controls` block and its child `input` / `label` rules. ✓ deleted (incl. mobile breakpoint)
          - `.advanced-filters-content.show { display: block }` and the `.filter-row` block. ✓ deleted
          - `.advanced-filters-toggle .when-expanded` / `.when-collapsed` / `.expanded` class
            variant rules. ✓ deleted
          - The second `.search-input` block at the bottom (hardcoded `#ddd`). ✓ deleted
          - The global `.table-stats` rule — confirm it does not affect any server-rendered
            element before removing (the Svelte-scoped version is authoritative). ✓ deleted;
            however, the Svelte scoped version was missing `background`/`padding`/`border-radius`
            — added those to `SortableTable.svelte` and `HistoryTable.svelte` before deleting
            the global, then rebuilt. `common.css`: 822 → 587 lines.

- [x] E2. In `templates/macros.html`: delete the `search_filter`, `signal_filter_buttons`,
          and `stock_pattern_filter_buttons` macro definitions. Keep `instruction_box`
          and `driver_tooltip`. ✓ done. Also deleted `price_slider` and `wishlist_slider`
          (not called anywhere; reference now-deleted CSS classes).

---

### Section F — Final verification gate

- [x] F1. `make test` → 597 passed (E2E are skipped in unit run), 95.34% Python coverage.
          (Plan target 635 assumed client tests counted together; Python unit count is 597.)
- [x] F2. `make test-client` → 134 passed.
- [x] F3. `make coverage-client` → branches ≥ 80% ✓.
- [x] F4. `make test-e2e` → 106 passed.
- [ ] Doc: Update `copilot-instructions.md` if any CSS architecture table entries changed.
          Update this file — tick all A–F steps, record any decisions that deviated from plan.

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
| **`FilterButton.svelte` uses `...rest` spread props** (Phase 4c-ii) | Rather than naming every possible data attribute (`data-action`, `data-signal`, `data-limit`, `data-stock-pattern`), `FilterButton` spreads `rest` onto the `<button>`. This is more flexible — `SortableTable` sets whichever data attributes it needs without requiring `FilterButton` to enumerate them. |
| **`table.html` two-mode rendering** (Phase 4c-ii) | History page JS (`history-page.js`) reads server-rendered `<tbody> <tr>` DOM rows with `data-date`/`data-price`/`data-wishlist` attributes. Adding a `render_server_rows=True` flag preserves this working approach while all other pages use the Svelte mount-div mode. The server-rendered branch becomes dead code once `HistoryTable.svelte` is mounted in Phase 4c-iii. |
| **`linkViewParam` on `ColumnConfig`** (Phase 4c-ii) | Species detail links (`species/{slug}.html`) need `?view=breeder` or `?view=dealer` appended so the species page initialises the correct tab when navigated to from a context page. Added `linkViewParam?: string` to `ColumnConfig`; `species-link` cells append `?view={param}` when present. Breeder and dealer index.ts pass `'breeder'` / `'dealer'` respectively. |
| **E2E slider fix: `input_value()` not `get_attribute("value")`** (Phase 4c-ii) | Svelte sets `<input>` value via the DOM `.value` property, not the HTML `value` attribute. `page.get_attribute("value")` reads the HTML attribute (returns `null`). The correct Playwright method is `locator.input_value()`. |
| **Combined filter: signal "Show All" does not clear stock pattern** (Phase 4c-ii) | `handleSignalFilter('all')` only resets the signal and top-10 limit. Stock pattern is independent state. E2E combined-filter test was updated to click signal Show All then stock-pattern Show All separately before asserting all rows visible. |
| **Top10 Species desc-sort: "Watch" > "Hot" alphabetically** (Phase 4c-ii) | `localeCompare` sorts `Avoid < Hot < Watch`. Descending alpha order puts `Watch Species 03` first, not `Hot Species 15`. E2E parametrize corrected accordingly. Header locator uses `:text-is("Price")` (exact match) to avoid matching the "Price History" column. |
| **Svelte scoped CSS must be explicitly linked in page templates** (Phase 4c-iii) | Vite emits per-component CSS files (e.g. `assets/history-page/HistoryTable.css`) but does NOT auto-inject them into HTML. Each page template must have explicit `<link rel="stylesheet">` tags for every component CSS file used on that page. Missing links cause scoped rules to be absent, which manifested as `height: 0px` on the advanced-filters panel (Playwright reported `visible=False` despite `display: block`). `analysis_page.html` already had the correct links; `history_page.html` was missing all five. |
| **Python unit tests for history page should assert JSON data, not DOM** (Phase 4c-iii) | After migrating `history_page.html` to Svelte mode, `generate_history_page()` only server-renders the Svelte mount div (`<div id="history-table-root">`) and the JSON data `<script>` block. All table/filter UI is Svelte client-rendered. Unit tests were rewritten to assert the JSON payload (via `_table_json(html)`) and the mount target's presence, not `<th>`, `<button>`, `<input>` elements that no longer exist in the server-rendered HTML. |
| **`DateFilter` uses callback prop `onchange`, not `createEventDispatcher`** (Phase 4c-iii) | Svelte 5 replaces `createEventDispatcher` with callback props. `DateFilter` declares `let { onchange }: { onchange: (dates: string[]) => void } = $props()` and calls `onchange(selectedDates)` directly. `HistoryTable` passes a function reference as `onchange={handleDateChange}`. Tests spy on the callback with `vi.fn()`. |
| **`_raw_scrape_datetime` injected into JSON rows** (Phase 4c-iii) | `DateFilter.svelte` groups rows by date for its checkbox list. The display-formatted "Scrape Date" column value is ambiguous (two scrapes on the same calendar day would collide). Injecting `_raw_scrape_datetime` (the ISO string directly from the CSV) as a private key gives `DateFilter` a stable, collision-free grouping key without polluting the visible table columns. |
| **`$state.raw` for Python-injected row data** | `$state()` wraps arrays and objects in deep reactive proxies. Hundreds of table rows injected from Python are static input — they are never mutated cell-by-cell. Using `$state.raw()` avoids the proxy overhead and makes the intent explicit: to trigger a re-render, reassign the whole array, don't mutate inside it. |
| **`HistoryTable` CSV download implemented in Phase 4c-iii, not 4d** | `buildCsv()` + `downloadCsv()` were implemented alongside `HistoryTable.svelte` since download is an integral part of the history table's action bar. Rather than shipping a disabled/placeholder button, the full implementation was included. Phase 4d therefore only needs to add the same logic to `SortableTable.svelte` and augment the test coverage for both. |
| **`csvHeader` added to `SortableTable.ColumnConfig` in Phase 4c-iii** | For consistency and to avoid a breaking interface change in Phase 4d, `csvHeader?: string` was added to `ColumnConfig` when `HistoryTable` first used it. `SortableTable` does not yet read this field (no download button), but the property is already declared so no interface churn is needed in Phase 4d. |
| **`$derived.by` for multi-step filter chains** | The visible-rows computation in `SortableTable` and `HistoryTable` chains 4–5 filter passes before sorting. This cannot fit in a single `$derived(expr)` expression without sacrificing readability. `$derived.by(() => { ... })` is the Svelte 5 canonical form for multi-line derived logic — equivalent to a computed getter body. |
| **Column `type: 'sparkline'` instead of a `{#snippet cell}` prop** | Svelte 5 snippets (`{#snippet cell(col, val)}{/snippet}`) are idiomatic for custom cell rendering but add complexity to the caller (`index.ts` must pass a snippet) and offer flexibility the codebase doesn't need. All three tables use the same sparkline conversion for the same column types — a simple `type` flag on the column descriptor keeps the rendering logic inside `SortableTable` without exposing a snippet API. Revisit if a genuinely different cell type is needed in a future phase. |
| **`$props.id()` for `RangeSlider` label/input pairing** | Each `RangeSlider` instance renders two range inputs that must be paired with `<label for>` attributes. `$props.id()` returns a stable unique string per component instance, preventing duplicate IDs when two sliders (price + wishlist) are mounted on the same page. Hard-coded or sequential IDs would break accessibility and are fragile if component ordering changes. |
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
| **`.table-stats` background missing from Svelte scoped CSS (Section E)** | The global `.table-stats` rule provided `background: var(--color-info-bg)` which the Svelte scoped versions did not replicate. Before deleting the global, the missing properties (`background`, `padding`, `border-radius`) were added to `SortableTable.svelte` and `HistoryTable.svelte` `<style>` blocks, then the project was rebuilt. The E2E test `test_snapshot_page_structure_and_styling` confirmed the background color `rgb(232, 244, 248)` is preserved. |
