# Testing Improvements Plan — Agent Feedback Loop

**Repository:** spidershop-historical-analysis  
**Branch:** svelte-migration (PR #104)  
**Date:** 2026-03-08

---

## Objective

Give a coding agent (and devs) faster, more direct, and more comprehensive test feedback —
particularly for visual/CSS regressions that are currently only caught by slow E2E tests (~20s)
or not caught at all. The four objectives:

1. Feedback arrives sooner (tests are faster)
2. Failure messages directly isolate the problem
3. Tests are easier to write and maintain (less flake, less setup)
4. Strong safety net for computed styling / visual regressions

---

## Current State

### Existing test tiers

| Tier | Command | Speed | What it covers |
|---|---|---|---|
| Vitest unit tests (happy-dom) | `make test-client` | ~1s | Component logic, props, events, `$state`/`$derived`, pure utilities |
| Playwright E2E tests | `make test-e2e` | ~20s | Full multi-component integration, sorting/filtering, URL state, some computed styles |

### What the existing tiers cannot do

**happy-dom (Vitest):**
- CSS custom properties (`var(--token)`) are **not resolved** — `getComputedStyle()` returns empty
  strings or token names, not the actual colour values.  So you can't assert a button is blue.
- Has no awareness of whether a Svelte `<style>` block uses design tokens or hardcoded values.

**E2E (Playwright):**
- Requires the full Python website generation pipeline before running.
- Takes ~20s, too slow for the tight feedback loop an agent needs during active CSS work.
- Style assertions are written with hardcoded `rgb(44, 62, 80)` strings that silently break
  when a design token value changes.
- Uses `page.wait_for_timeout(200)` polling which is both slow and fragile.

### What currently has NO test coverage

- Whether a Svelte `<style>` block accidentally hard-codes a colour that should use a token
- Whether a design token value in `templates/common.css` silently drifts
- Accessibility (no Lighthouse or axe-core integration)
- Visual sanity checking during active development without running the full E2E suite

---

## Tech / Architecture Context

### CSS architecture (3-layer model)

| Layer | Files | Scope |
|---|---|---|
| 1 — Global chrome | `templates/common.css` | Browser reset, `:root` tokens, page chrome |
| 2 — Page-level static | `templates/analysis.css`, `homepage.css`, `species-detail.css` | Python-rendered HTML |
| 3 — Svelte component | `client/src/**/*.svelte` `<style>` blocks | Elements owned by a Svelte component |

All design tokens are CSS custom properties in the `:root` block of `templates/common.css`
(e.g. `--color-accent: #3498db`, `--color-signal-hot: #ef4444`). Svelte components reference
them as `color: var(--color-accent)` — no imports needed.

### Svelte components

10 Svelte components across `client/src/`:

- `shared/components/FilterButton.svelte` — signal/stock filter toggle
- `shared/components/SearchInput.svelte` — text search
- `shared/components/RangeSlider.svelte` — dual-handle price/wishlist range slider
- `shared/components/SortableTable.svelte` — core table with sorting, filtering, CSV download
- `shared/components/SparklineBar.svelte` — SVG sparkline from DTO
- `shared/components/ToggleButton.svelte` — generic toggle
- `shared/components/TableStats.svelte` — "Showing X of Y" strip
- `shared/components/FiltersPanel.svelte` — collapsible filter group container
- `history-page/DateFilter.svelte` — multi-date checkbox selector
- `history-page/HistoryTable.svelte` — HistoryTable + DateFilter integration

### Test tooling already in place

- **Vitest** + **@testing-library/svelte** with happy-dom environment
- **Playwright** for E2E (the binary is already installed for the E2E suite)
- **pytest** for Python unit tests
- `templates/common.css` is the single source of truth for all token values

---

## Proposed Feedback Loop — Full Picture

```
agent makes CSS change
       │
       ▼  <100ms
Phase 2: Compliance audit
  ↳ catches hardcoded hex/rgb in Svelte <style> blocks immediately
       │
       ▼  <1s
make test-client
  ↳ logic tests (unchanged) + token value snapshot (Phase 1)
       │
       ▼  ~2-3s
CDP MCP evaluate_script + take_screenshot   [interactive, not a test]
  ↳ agent queries live getComputedStyle() on served site without writing a test
  ↳ visual sanity check via screenshot
       │
       ▼  ~5-10s
make test-visual   [new CI gate]
  ↳ Vitest browser mode: mounts components in real Chromium
  ↳ getComputedStyle() resolves var(--token) → actual rgb value
  ↳ asserts computed colour/spacing matches the token
       │
       ▼  ~20s
make test-e2e
  ↳ multi-component integration, full site smoke tests (unchanged role)
       │
       ▼  ad-hoc
CDP MCP lighthouse_audit
  ↳ accessibility/performance audit on generated pages
```

**Key principle:** CDP MCP is the agent's interactive "inspection REPL" during development.
The test tiers are automated CI gates. They are complementary, not competing.

---

## Phases

### Phase 0 — `make preview` + CDP MCP workflow documentation

**Step 1.** Add `make preview` to `Makefile`:
- Serves `tmp/local-testing/website/` on a fixed port (8080) using Python `http.server`
- Depends on `make generate-website` already having run
- Gives ~2-3s feedback vs ~20s E2E for active CSS inspection

**Agent workflow enabled:**
```
make generate-website   # regenerate static site after CSS or Python change
make preview            # start HTTP server on port 8080 (background)
# then in CDP MCP:
# navigate_page http://localhost:8080/breeder.html
# evaluate_script "getComputedStyle(document.querySelector('.filter-btn.is-active')).backgroundColor"
# take_screenshot
```

**Step 2.** Add an **"## Interactive Inspection"** section to
`.github/copilot-instructions.md` documenting this agent workflow.

---

### Phase 0b — Lighthouse accessibility baseline

**Step 3.** Agent uses CDP MCP `lighthouse_audit` on `breeder.html`, `snapshot.html`,
`history.html` (via `make preview`) to capture current accessibility scores.

**Step 4.** Record baseline scores in `docs/ACCESSIBILITY_BASELINE.md` as a one-time artifact.

**Step 5.** (Future/optional) Formalise as `make test-a11y` once a stable baseline exists.

---

### Phase 1 — Design Token Snapshot *(the trust anchor)*

**Step 6.** Create `client/src/shared/__tests__/token-parser.ts`:
- Shared utility used by both Phase 1 and Phase 2
- Parses the `:root { }` block in `templates/common.css`
- Returns a `Map<string, string>` of `--property-name → value`

**Step 7.** Create `client/src/shared/__tests__/design-tokens.test.ts`:
- Calls `parseTokens()` on `templates/common.css` (via `fs.readFileSync`)
- Uses `toMatchInlineSnapshot()` on the full token map
- Any accidental token value change (e.g. `--color-signal-hot` drifts from `#ef4444`)
  produces an immediate, readable diff
- Runs inside existing `make test-client` — no new make target needed

---

### Phase 2 — CSS Token Compliance Audit *(shift-left prevention)*

**Step 8.** Create `client/src/shared/__tests__/css-token-compliance.test.ts`:
- Globs all `client/src/**/*.svelte` files
- Extracts `<style>…</style>` block from each file
- Rejects bare hex values (`#[0-9a-fA-F]{3,6}`) that match a known token value
- Rejects bare `rgb(…)` / `rgba(…)` strings that match a known token value
- **Allowlist** of legitimate hard-coded values: `#fff`, `#000`, `transparent`, `none`,
  `0`, `50%`, unitless values, opacity decimals
- Error message names the file and suggests the correct token:
  ```
  FilterButton.svelte uses hardcoded #3498db — use var(--color-accent)
  ```
- Runs inside `make test-client` — adds <100ms

---

### Phase 3 — Vitest Browser Mode Setup

**Step 9.** Add `@vitest/browser` to `client/package.json` devDependencies.
The Playwright browser binary is already installed for the E2E suite — reuse it.

**Step 10.** Create `client/vite.browser.config.ts`:
- `test.browser.enabled = true`
- `provider: 'playwright'`, `name: 'chromium'`
- `include: ['**/*.visual.test.ts']` (separate from `*.test.ts`)
- Same `setupFiles` as `vite.config.ts`
- Coverage excluded entirely (visual tests are environment tests, not logic paths)

**Step 11.** Create `client/src/test-utils/token-colors.ts`:
- `getTokenRgb(tokenName: string): string` — reads `templates/common.css` at test-time,
  converts the hex value of `tokenName` to the `rgb(r, g, b)` string that
  `getComputedStyle()` returns
- **This is the auto-sync mechanism** — no hand-maintained TS file needed.
  Any token rename or revalue is immediately reflected in visual test assertions.

**Step 12.** Add `make test-visual` target to `Makefile`:
```makefile
test-visual: .check-venv
	cd client && npx vitest run --config vite.browser.config.ts
```

---

### Phase 4 — Visual Contract Tests (`*.visual.test.ts`) per Component

One file per component. Each test:
1. Mounts the component via `@testing-library/svelte` (same API as existing tests)
2. Queries a DOM element
3. Calls `window.getComputedStyle(el).backgroundColor` (now works — real browser)
4. Compares against `getTokenRgb('--color-accent')` from the auto-synced helper

Priority order (most visual-regression-prone first):

**Step 13.** `client/src/shared/components/FilterButton.visual.test.ts`
- `.is-active` → `backgroundColor` = `getTokenRgb('--color-accent')`
- inactive default → `backgroundColor` = `getTokenRgb('--color-surface')`
- `.is-active` → `borderColor` = `getTokenRgb('--color-accent')`

**Step 14.** `client/src/shared/components/RangeSlider.visual.test.ts`
- `.label` → `color` = `getTokenRgb('--color-primary')`
- `.slider-values` → `color` = `getTokenRgb('--color-text-muted')`
- Note: pseudo-elements (`::-webkit-slider-thumb`) can't be tested via `getComputedStyle()`.
  Phase 2 compliance check is the only automated guard for those rules.

**Step 15.** `client/src/shared/components/TableStats.visual.test.ts`
- stats container → `backgroundColor` = `getTokenRgb('--color-info-bg')`

**Step 16.** `client/src/shared/components/FiltersPanel.visual.test.ts`
- `.filters-panel` → `backgroundColor` = `getTokenRgb('--color-surface')`
- `.filters-panel` → `borderColor` = `getTokenRgb('--color-border-light')`

**Step 17.** `client/src/shared/components/SearchInput.visual.test.ts`
- unfocused → `borderColor` = `getTokenRgb('--color-border')`
- focused (via `fireEvent.focus`) → `borderColor` = `getTokenRgb('--color-accent')`

**Step 18.** `client/src/history-page/DateFilter.visual.test.ts`
- date section → `borderColor` = `getTokenRgb('--color-date-filter')` (`#ffc107`)
- expand button → `backgroundColor` = `getTokenRgb('--color-date-filter')`
- Once this passes, remove the `getComputedStyle` assertions that currently duplicate
  this in `tests/e2e/test_history_date_filter.py`.

---

### Phase 5 — E2E Style Assertion Cleanup

**Step 19.** Create `tests/e2e/css_tokens.py`:
- Python mirror of the `token-colors.ts` helper
- Parses `templates/common.css`
- Returns `dict[str, str]` mapping `--name → rgb(r, g, b)` (hex converted, matches
  what `window.getComputedStyle()` returns in a browser)

**Step 20.** Replace all hardcoded rgb strings in E2E tests with `css_tokens` lookups:
- `tests/e2e/test_navigation_and_page_loads.py` — header bg/color (`rgb(44, 62, 80)`, `rgb(255, 255, 255)`)
- `tests/e2e/test_snapshot_filters.py` — download button bg, stats strip bg
- `tests/e2e/test_history_date_filter.py` — date section border and button bg (`rgb(255, 193, 7)`)

**Step 21.** Replace `page.wait_for_timeout(100/200)` with `wait_for_selector()` or
`wait_for_function()` where observable state is available. Where unavoidable (e.g. slider
animation), add a comment explaining why.

---

## File Inventory

### New files

| File | Phase | Purpose |
|---|---|---|
| `client/src/shared/__tests__/token-parser.ts` | 1 | Shared CSS token parser utility |
| `client/src/shared/__tests__/design-tokens.test.ts` | 1 | Token value snapshot (trust anchor) |
| `client/src/shared/__tests__/css-token-compliance.test.ts` | 2 | Static compliance audit of Svelte styles |
| `client/vite.browser.config.ts` | 3 | Vitest browser mode config |
| `client/src/test-utils/token-colors.ts` | 3 | Auto-synced `getTokenRgb()` helper |
| `client/src/shared/components/FilterButton.visual.test.ts` | 4 | Visual contract for FilterButton |
| `client/src/shared/components/RangeSlider.visual.test.ts` | 4 | Visual contract for RangeSlider |
| `client/src/shared/components/TableStats.visual.test.ts` | 4 | Visual contract for TableStats |
| `client/src/shared/components/FiltersPanel.visual.test.ts` | 4 | Visual contract for FiltersPanel |
| `client/src/shared/components/SearchInput.visual.test.ts` | 4 | Visual contract for SearchInput |
| `client/src/history-page/DateFilter.visual.test.ts` | 4 | Visual contract for DateFilter |
| `tests/e2e/css_tokens.py` | 5 | Python token → rgb helper for E2E tests |
| `docs/ACCESSIBILITY_BASELINE.md` | 0b | One-time Lighthouse score record |

### Modified files

| File | Phase | Change |
|---|---|---|
| `Makefile` | 0, 3 | Add `make preview` and `make test-visual` targets |
| `.github/copilot-instructions.md` | 0 | Add "Interactive Inspection" section for CDP MCP workflow |
| `client/package.json` | 3 | Add `@vitest/browser` devDependency |
| `client/vite.config.ts` | 3 | Add `**/*.visual.test.ts` to `coverage.exclude` |
| `tests/e2e/test_navigation_and_page_loads.py` | 5 | Replace hardcoded rgb strings |
| `tests/e2e/test_snapshot_filters.py` | 5 | Replace hardcoded rgb strings |
| `tests/e2e/test_history_date_filter.py` | 5 | Replace hardcoded rgb strings; remove duplicate style assertions once Phase 4 DateFilter test exists |

---

## What Each Layer Catches

| Regression type | Phase 2 compliance | Phase 1 snapshot | Phase 4 visual | E2E |
|---|---|---|---|---|
| Hardcoded `#3498db` in Svelte style | ✅ immediate | ❌ | ❌ (code still uses token syntax) | ❌ |
| `var(--color-accent)` → `var(--color-danger)` (wrong token) | ❌ (valid syntax) | ❌ | ✅ rendered colour wrong | ✅ (if tested) |
| Token value drifts in `common.css` | ❌ | ✅ snapshot diff | ✅ wrong rgb | ✅ (if tested) |
| Component logic / prop regression | ❌ | ❌ | ❌ | ✅ |
| Multi-component interaction regression | ❌ | ❌ | ❌ | ✅ |
| Accessibility regression | ❌ | ❌ | ❌ | ❌ (CDP MCP ad-hoc) |

---

## CDP MCP vs Automated Tests — Role Clarity

Chrome DevTools MCP (`chrome-devtools-mcp`) is an **MCP server** that gives an AI agent
live access to Chrome DevTools. Key tools relevant here:

| Tool | Use in this workflow |
|---|---|
| `evaluate_script` | Run `getComputedStyle()` REPL queries on the live served site |
| `take_screenshot` | Visual sanity check — "does this look right?" — without writing a test |
| `lighthouse_audit` | Accessibility/performance audit on generated pages |
| `navigate_page` | Direct the browser to the page under inspection |

**CDP MCP is NOT a replacement for automated tests.** It fills the "agent's eyes" role:
- Used during active development, not in CI
- No assertion code to write or maintain
- Gives ~2-3s feedback for CSS work vs ~20s for E2E
- Can inspect things that are hard to assert in tests (e.g. hover states, pseudo-elements,
  visual layout of many elements at once)
- The `lighthouse_audit` capability covers accessibility — a gap none of the test tiers fills today

---

## Verification / Acceptance Criteria

1. **`make preview`** starts a server; CDP MCP can navigate to `http://localhost:8080/breeder.html`
   and `evaluate_script "getComputedStyle(document.querySelector('.filter-btn.is-active')).backgroundColor"`
   returns the expected accent token rgb value.

2. **`make test-client`** still passes and completes in <2s (Phases 1+2 add <200ms total).

3. **`make test-visual`** exits 0 on a clean codebase and completes in ~5-10s.

4. **Regression demo A** — hardcoded value:
   - Replace `var(--color-accent)` with `#3498db` in `FilterButton.svelte`
   - Phase 2 compliance test should fail immediately with a message naming the file and suggesting the token

5. **Regression demo B** — wrong token:
   - Replace `var(--color-accent)` with `var(--color-danger)` in `FilterButton.svelte`
   - Phase 2 should pass (valid token syntax used)
   - Phase 4 `FilterButton.visual.test.ts` should fail (rendered colour is red, not blue)

6. **Token drift demo:**
   - Change `--color-signal-hot` value in `templates/common.css`
   - Phase 1 design-tokens snapshot should fail with an inline snapshot diff showing the changed value

7. **`make test-e2e`** still passes after Phase 5 cleanup (purely non-functional refactoring).

---

## Key Decisions

- **`make test-client` is additive only** — existing happy-dom tests are unchanged; Phases 1+2
  add new test files that run in the same suite.
- **`make test-visual` is a separate target** — keeps `make test-client` at ~1s while giving
  a `~5-10s` tier for computed-style contracts.
- **Token values are auto-synced** — both JS (`token-colors.ts`) and Python (`css_tokens.py`)
  helpers read `templates/common.css` at test-time. No hand-maintained constant files.
- **E2E tests are NOT removed** — they remain the authoritative gate for multi-component
  integration, URL state, and full-site smoke tests.
- **Phase 5 is maintenance only** — no new E2E coverage, just making existing assertions
  resilient to token changes and faster to fail.
- **CDP MCP is documented, not automated** — `make preview` gives agents something to point the
  browser at; CDP MCP tool calls are made by the agent on demand, not scripted.

---

## Out of Scope

- Pixel-diff screenshot testing (too brittle, too expensive to maintain)
- Axe-core accessibility assertions (natural follow-on, separate concern)
- Layer 2 CSS (`analysis.css`, `homepage.css`, `species-detail.css`) —
  that CSS is on Python-rendered HTML and is not inside any Svelte island
- Formalising `make test-a11y` (deferred until a Lighthouse baseline is stable)

---

## Further Considerations

### Pseudo-elements
`::-webkit-slider-thumb` and similar pseudo-elements in `RangeSlider.svelte` cannot be
inspected via `getComputedStyle()`. The Phase 2 compliance test (token-use enforcement) is
the only automated guard for those rules. This is an acceptable trade-off.

### CI Playwright binary caching
`@vitest/browser` with Playwright provider needs the Chromium binary. The E2E suite already
downloads it. Confirm that `make test-visual` in CI reuses the same cached Playwright install
(same `PLAYWRIGHT_BROWSERS_PATH` env var) to avoid downloading browsers twice.

### Coverage exclusion
`*.visual.test.ts` files are environment tests, not logic coverage. Add
`'**/*.visual.test.ts'` to the `coverage.exclude` array in `client/vite.config.ts` so they
don't inflate or distort the logic coverage report.
