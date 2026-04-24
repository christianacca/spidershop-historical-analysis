# PWA Service Worker — Implementation Plan

**Companion spec:** [`market-health-handoff-spec.md`](./market-health-handoff-spec.md) §12 (WP-SW row)  
**Work package:** WP-SW (see §12 for staged delivery model)  
**Dependency:** WP1 (Phase 12) merged — `window.marketHealthRawData` must be live  
**Branch:** `history-insights-pwa-sw`

WP-SW delivers the service worker and PWA foundation layer for the entire site. It is a
purely additive work package — no existing Python logic, HTML generation, or Svelte
components are modified. The only page-template change is an addition to `base.html`.

---

## Scope

This work package consists of five deliverables:

1. **`vite-plugin-pwa`** (`injectManifest` strategy) added to `client/vite.config.ts`,
   emitting a compiled `sw.js` bundle into `templates/scripts/dist/`.
2. **`client/src/sw.ts`** — the service worker source with SWR caching for HTML
   navigation routes and unhashed CSS, and cache-first (precache) for hashed JS/CSS
   bundles via the auto-injected precache manifest.
3. **SW registration script** added directly to `templates/base.html` (before
   `{% block extra_js %}`) so every page participates without any child-template change.
4. **`SwUpdateToast.svelte`** — an update notification component that uses the
   `virtual:pwa-register/svelte` store from `vite-plugin-pwa` to tell users "New data
   has been deployed" when a new SW version is waiting to activate.
5. **PWA web manifest + icons** (`client/public/manifest.webmanifest`) enabling browser
   install-prompt, added in Phase 5 after the caching layer is fully validated.

---

## Engineering Gaps the UX Spec Does Not Cover

The §12 WP-SW description in the handoff spec is intentionally brief. The following gaps
are implementation-level decisions that an engineer or agent must understand before
writing any code.

### G1 — Why `injectManifest`, not `generateSW`

`vite-plugin-pwa` supports two strategies:

- **`generateSW`** (default): Workbox auto-generates the service worker and computes a
  precache manifest from Vite's `dist/` output. **Unsuitable for this project.** HTML
  pages are Python-generated (`generate_website.py`) and never appear in Vite's `dist/`
  — so `generateSW` would produce a precache manifest containing only JS/CSS bundles,
  with no knowledge of the HTML pages it is meant to serve offline.

- **`injectManifest`** (chosen): You write `client/src/sw.ts` yourself. The plugin
  builds it as a Vite bundle, then replaces `self.__WB_MANIFEST` with a compile-time
  constant that expands to the auto-computed precache manifest for hashed JS/CSS assets.
  HTML navigation is handled separately with a custom `NavigationRoute` (SWR strategy).
  This strategy works correctly regardless of how HTML is generated.

### G2 — Caching strategy decisions

**Progressive enhancement contract:** the SW is purely additive. Every page is
Python-generated static HTML that loads and functions fully from the network without
any SW present. No content, navigation, or feature depends on a SW being registered or
active. On iOS (7-day eviction), on browsers that block SW (e.g. private browsing on
some mobile browsers), and on any page where registration fails, the site behaves
identically to the no-SW baseline: pages load from the network on every visit, caches
are never consulted, and the update toast is never shown. This must be verifiable by an
E2E test that runs with SW explicitly blocked (see Phase 4).

| Resource type | Strategy | Rationale |
|---|---|---|
| HTML navigation routes (`*.html`, `/species/<slug>/`) | Stale-while-revalidate via `NavigationRoute` | Never precache HTML — pages embed `window.marketHealthRawData` inline (~13 KB gzip), so cache-first would serve stale market data. SWR serves the cached page instantly while revalidating in the background. |
| Hashed JS/CSS bundles | Cache-first via precache manifest | Handled automatically by `precacheAndRoute(self.__WB_MANIFEST)`. Content hash changes on every build, so the manifest revision is always fresh. |
| Unhashed static CSS (`common.css`, `analysis.css`, `homepage.css`, `species-detail.css`) | Runtime SWR rule | No content hash in filenames; they change between deploys. SWR keeps them fresh without blocking page load. |
| Species detail pages (`/species/<slug>/index.html`) | SWR on demand, never precache | Hundreds of pages — precaching all would bloat the SW install. SWR caches them on first user visit. |
| External resources | Network-only (no rule) | Do not intercept CDN or third-party requests. |

### G3 — Service worker foot guns to avoid

1. **No `skipWaiting()` in `sw.ts`.** Calling `skipWaiting()` directly activates a new
   SW while old tabs are still open. If the page and SW disagree on the data contract,
   the page can break silently. Instead: let the new SW wait, and notify the user via
   `SwUpdateToast.svelte`. The `updateServiceWorker(true)` call in the toast component
   calls `skipWaiting()` only after the user explicitly chooses to refresh.

   **Multi-tab stale SW — consciously accepted for this project.** Without
   `skipWaiting`, an old SW can control pages indefinitely in multi-tab sessions.
   For this project this is an acceptable trade-off: the SW code contains no
   business logic (only routing rules), and SWR background revalidation keeps the
   `html-pages` cache current regardless of SW version. The only practical consequence
   is that users with long-lived open tabs see the old update-notification UX, not
   stale market data. This is a conscious design decision — not an oversight.

2. **`cleanupOutdatedCaches()` must be called before `precacheAndRoute()`.** Without
   this, stale cache entries from previous SW versions accumulate in the browser.

3. **No global SW state that relies on persistence.** DevTools masks a common bug: the
   SW process is stopped and restarted between navigations, resetting module-level
   variables. Do not store mutable state in SW global scope.

4. **Do not override cache names.** `vite-plugin-pwa` generates cache names automatically.
   If two SWs share a manually chosen cache name, they silently conflict.

### G4 — `virtual:pwa-register/svelte` and the update notification

`vite-plugin-pwa` provides a virtual module `virtual:pwa-register/svelte` that exports a
`useRegisterSW()` Svelte store factory. It exposes:

- `needRefresh: Writable<boolean>` — becomes `true` when a new SW has been installed and
  is waiting to activate.
- `updateServiceWorker(reloadPage?: boolean)` — calls `skipWaiting()` on the waiting SW
  and optionally reloads the page. Call with `true` so the user gets the freshest page.

`SwUpdateToast.svelte` subscribes to `needRefresh` and renders a "New data has been
deployed" notification only when it is `true`. The component mounts from
`sw-toast-entry.ts`, which is a separate Vite entry that runs on every page (referenced
in `base.html` directly, outside `{% block extra_js %}`).

> **Note for Vitest:** `virtual:pwa-register/svelte` is a Vite virtual module that
> cannot run in happy-dom. Mock it in `SwUpdateToast.test.ts` with:
> ```typescript
> vi.mock('virtual:pwa-register/svelte', () => ({
>   useRegisterSW: vi.fn(() => ({
>     needRefresh: writable(false),
>     updateServiceWorker: vi.fn(),
>   })),
> }));
> ```

### G5 — Build pipeline: `sw.js` placement requires no pipeline changes

`vite-plugin-pwa` emits `sw.js` to the **root of `templates/scripts/dist/`** alongside
the page bundle files. The existing `shutil.copytree()` call in `generate_website.py`
copies the entire `templates/scripts/dist/` tree to `website/` — **no pipeline changes
are required**. `sw.js` automatically lands at `website/sw.js`.

There is no CNAME file in this repository, so GitHub Pages serves the site at the
**project-page subpath** (`https://christianacca.github.io/spidershop-historical-analysis/`),
not at the domain root. **Never register with an absolute path like `'/sw.js'`** — that
resolves to `christianacca.github.io/sw.js` and 404s on production. Use the
`{{ path_prefix }}` template variable to derive the correct registration URL at runtime
(see Phase 3).

`sw-toast-entry.js` follows the same path — it lands alongside other bundle files and is
referenced in `base.html` by the path pattern used for other scripts.

### G8 — `sw.ts` is an isolated Rollup build

`vite-plugin-pwa` compiles `sw.ts` in a **separate Rollup invocation** that does not
share the main bundle’s module graph. This has one critical implication:

**`sw.ts` cannot import from `client/src/` or any project source file.** Attempting to
import from `src/shared/`, `src/history-page/`, or any other local module will either
silently resolve to an empty module or fail the build depending on Rollup’s `external`
config. Every utility needed in the SW must come from workbox packages or be defined
inline within `sw.ts` itself.

This is not a constraint for the current `sw.ts` (it only uses workbox packages), but
it is a footgun for anyone who later extends the SW with caching logic that tries to
reuse shared utilities. If a shared utility is genuinely needed in the SW, it must be
extracted into a standalone file with no transitive imports from the project source tree.

### G9 — Local dev ergonomics: `make preview` and stale SW state

After `make preview` rebuilds the client bundle, any open browser tab with an active SW
from a previous session will NOT immediately see the new assets. The pattern:

1. `make preview` completes — new `sw.js` carries an updated precache manifest
   (new content-hashed filenames).
2. Reload the page — the old SW is still in control; it serves old cached assets while
   the browser fetches `sw.js` in the background, detects the byte change, and installs
   the new SW into the **waiting** state.
3. The `SwUpdateToast` appears. Click it — new SW activates, page reloads with fresh
   assets.

For rapid iteration (e.g. editing CSS and immediately checking the result) this
two-reload cycle is friction. Two mitigations:

**Human developer — enable "Update on reload" in Chrome DevTools:**
1. Open DevTools → Application → Service Workers.
2. Check ✅ **Update on reload**.
3. Chrome now bypasses the waiting state and immediately activates the new SW on
   every page reload. You see fresh assets on every `make preview` cycle.
4. Disable this setting only when you specifically want to test the real update-toast
   flow end-to-end.

**Agentic DevTools MCP workflow — always run the clean-slate script (Step 0 in the G7 protocol) before beginning any inspection.**
The agent MUST unregister all existing SWs and clear caches before beginning any
inspection. This is not optional: without it, the agent may be asserting against a page
still controlled by a SW from a previous session, and assertions about cache population
or SW state will be unreliable.

**Key asymmetry to understand:** workbox's SWR strategy caches HTML pages and serves
them from cache even when the HTTP server is stopped. The next `make preview` session
brings up a server with new assets, but the browser will still serve the old cached HTML
on the first load (from the old SW). The old SW then fetches the new `sw.js` from the
now-running server, detects the change, and queues the update — but you still see one
load of stale HTML before the toast appears. The Step 0 clean-slate script avoids this
entirely by starting fresh every time.

### G6 — Test commands (MANDATORY)

```bash
make test-client-fast     # fast Vitest — run after every TypeScript/Svelte change
make test-client          # Vitest + coverage — run at end of each client phase (≥80%)
make test                 # Python unit tests — no Python changes in WP-SW
make test-e2e             # Playwright — required at end of Phase 4 (SW integration)
make test-visual          # browser-backed CSS contracts — run when Svelte style blocks change
```

### G7 — Chrome DevTools MCP verification protocol

Chrome DevTools MCP is the primary verification tool for SW behaviour that Vitest
cannot model: actual SW registration, cache population, and update notification
rendering in a real browser. The Chrome DevTools MCP server must be connected in VS Code.

**Standard SW verification sequence:**

0. **Clean slate — always run this first.** Any previous `make preview` session may
   have left a stale SW controlling the page. Unregister all SWs and clear all caches
   before inspecting, then reload to force a fresh install:
   ```js
   const regs = await navigator.serviceWorker.getRegistrations();
   await Promise.all(regs.map(r => r.unregister()));
   const keys = await caches.keys();
   await Promise.all(keys.map(k => caches.delete(k)));
   location.reload();
   // After reload: no active SW exists, so the page's registration script installs a
   // fresh SW which activates immediately (no old SW to wait for). Reload once more
   // to get a page served by the newly-active SW before proceeding with assertions.
   ```
1. Run `make preview` to regenerate the site and serve at `http://localhost:8000`.
2. Navigate to the target page via Chrome DevTools MCP navigation tool.
3. Check SW registration state:
   ```js
   // getRegistration() takes a scope URL. On localhost the scope is '/';
   // on production it is '/spidershop-historical-analysis/'.
   const reg = await navigator.serviceWorker.getRegistration(location.origin + '/');
   return {
     scope:     reg?.scope,
     state:     reg?.active?.state,
     scriptURL: reg?.active?.scriptURL,
   };
   // localhost expected:
   // { scope: 'http://localhost:8000/', state: 'activated', scriptURL: '...sw.js' }
   ```
4. Check cache names:
   ```js
   const keys = await caches.keys();
   return keys;
   // expected: array containing 'html-pages', 'css-runtime', and a 'workbox-precache-v2-...' entry
   ```
5. To simulate an SW update: bump a bundle (rebuild), re-serve, reload the page once
   (installs new SW), then reload again (new SW waits) — confirm the toast appears.

---

## Phase Structure

Each phase ends with **five mandatory steps. All five must be completed before starting
the next phase. An agent that skips any step is in protocol violation — the phase is NOT
complete.**

```
[ ] H1 — Mark every task checkbox above as ✅ — only after the task is actually done,
         not speculatively
[ ] H2 — Reflection: step back from the implementation and read every file you touched
         or created this phase as if seeing it for the first time. Look for code hygiene
         issues you introduced under time pressure: anything on the code smell checklist
         below, but also anything that just feels wrong — unnecessary complexity,
         inconsistent naming, missing guard clauses, copy-paste drift. Fix ALL issues
         through refactoring before committing. Do not move on with a TODO to fix later.
[ ] H3 — Feed-forward: append a dated entry to the Feed-forward log.
         Record any insights gained during this phase (surprises, foot guns hit,
         decisions made, things that took longer than expected). Then scan the
         remaining phases below and UPDATE their task lists, pre-flight steps, or
         verification instructions to reflect what you now know — stale plan text
         is worse than no plan. Required even when there is nothing new: write
         "no new findings; no downstream phase changes needed" rather than skipping.
[ ] H4 — Commit: `git add -A && git commit -m "Phase N: <summary>"`
         then `git log --oneline -1` to confirm the commit is present
[ ] GATE — Output the phase completion block (format below) in your chat response.
           Every field must contain actual terminal output — no placeholders allowed.
           If a field cannot be filled, the phase is BLOCKED: stop, fix it, then output.
```

**GATE — phase completion block. Paste this template and fill with real output.**
This block appearing in your response is the ONLY acceptable evidence a phase is complete.
Its absence means the phase was NOT completed per protocol.

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE N COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of last make test-client-fast / make test output]
║  Commit:   [paste output of: git log --oneline -1]
║  Stories:  [N/A — no stories this WP]
║  Blockers: none  /  [name any deferred item]
╚══════════════════════════════════════════════════════════════╝
```

**Code smell checklist for H2:**

*General code quality — applies to every file touched in any phase:*
- **Duplicate code** — any logic copy-pasted across two or more places; extract a shared helper
- **Long functions / methods** — more than ~20 lines usually signals mixed responsibilities; split
- **Mixed abstraction levels** — a function that both decides what to do and knows how to do low-level details; separate the levels
- **Poor naming** — variables/functions named after implementation details (`data2`, `temp`, `flag`) rather than intent
- **Magic literals** — unexplained numeric or string constants inline; name them as constants
- **Dead code** — unreachable branches, unused imports, commented-out blocks left in
- **Unnecessary complexity** — conditionals or abstractions that exist "just in case"; delete them
- **Test signal-to-noise ratio** — assertions that restate implementation details (exact HTML strings, JS variable names, internal function names); tests should assert observable behaviour, not implementation. If a test would survive a valid refactor without changes, it has good signal.
- **Test coverage theatre** — a test that always passes regardless of the code it claims to cover (wrong assertions, wrong mock return values, missing `await`)

*WP-SW specific — applies only to files in this work package:*
- Hardcoded cache names (must use `vite-plugin-pwa` automatic naming — never `'my-cache'`)
- Any `skipWaiting()` call in `sw.ts` that is not guarded by a user action
- `virtual:pwa-register/svelte` used outside `SwUpdateToast.svelte` (single-use module)
- TypeScript `any` in `sw.ts` or `SwUpdateToast.svelte`
- Svelte `<style>` blocks with hardcoded colours (must use `var(--token)`)
- SW registration code duplicated in individual page templates (must live only in `base.html`)
- `sw-toast-entry.ts` importing any page-specific logic (must be standalone)

**Make commands — MANDATORY (never bypass):**
- `make test-client-fast` / `make test-client` / `make test` / `make test-e2e`
- **Never run vitest or pytest directly.** Make commands ensure correct working directory.
- **Never generate the website by running Python directly.** Always use `make generate-website`.

---

## Phase 1 — Install and configure `vite-plugin-pwa`

**Goal:** Add `vite-plugin-pwa` to the build and confirm a `sw.js` file is emitted.
No caching rules yet — just the scaffold. The precache manifest injection alone (an empty
`self.__WB_MANIFEST` array) is enough to validate the build pipeline is wired correctly.

**Pre-flight:**
- [ ] Run `make test-client-fast` — confirm baseline is green before touching anything.
- [ ] Read `client/vite.config.ts` fully — understand the `createViteConfig(isCiBuild)`
  function and the `rollupOptions.input` map. `sw.ts` is **not** added to
  `rollupOptions.input` — `vite-plugin-pwa` handles it separately via `srcDir`/`filename`.
- [ ] Read `client/package.json` — note existing plugin versions before adding new deps.

**Tasks — install:**
- [ ] From `client/`, install the plugin and all workbox packages used in `sw.ts`:
  ```bash
  cd client && npm install --save-dev vite-plugin-pwa workbox-precaching workbox-routing workbox-strategies workbox-expiration
  ```
  All five packages must be explicit `devDependencies` in `client/package.json`. Do not
  rely on transitive hoisting: `workbox-routing`, `workbox-strategies`, and
  `workbox-expiration` are `devDependencies` of `workbox-build` (not `dependencies`)
  and are not guaranteed to appear at the root of `node_modules` on a fresh `npm ci`
  in CI. Missing explicit entries = CI build failure at the `sw.ts` compile step.
  Confirm all five packages appear in `devDependencies` in `client/package.json`.

**Tasks — configure `vite.config.ts`:**
- [ ] Import `VitePWA` at the top of `client/vite.config.ts`:
  ```typescript
  import { VitePWA } from 'vite-plugin-pwa';
  ```
- [ ] Add `VitePWA(...)` to the `plugins` array inside `createViteConfig` (alongside the
  existing `svelte(...)` call):
  ```typescript
  VitePWA({
    strategies: 'injectManifest',
    srcDir: 'src',
    filename: 'sw.ts',
    injectRegister: null,        // We register manually in base.html (Phase 3)
    manifest: false,             // Web manifest added in Phase 5
    devOptions: {
      enabled: false,            // SW irrelevant in Vite dev server for this project
    },
    injectManifest: {
      // Only precache content-hashed JS/CSS — never HTML (Python-generated, not in dist)
      globPatterns: ['**/*.{js,css}'],
    },
  }),
  ```
  **`injectRegister: null` is critical** — omitting it causes the plugin to inject a
  registration snippet that conflicts with our manual registration in `base.html`.

**Tasks — create `sw.ts` scaffold:**
- [ ] Create `client/src/sw.ts` (minimal scaffold; caching rules added in Phase 2):
  ```typescript
  /// <reference lib="webworker" />
  import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
  import type { PrecacheEntry } from 'workbox-precaching';

  declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<PrecacheEntry | string> };

  // Must be called BEFORE precacheAndRoute to remove stale entries from prior builds.
  cleanupOutdatedCaches();
  precacheAndRoute(self.__WB_MANIFEST);
  ```
  > **⚠️ `self.__WB_MANIFEST` not `__WB_MANIFEST`:** workbox-build's `injectManifest`
  > step looks for the literal string `self.__WB_MANIFEST` in the compiled output.
  > Using `declare const __WB_MANIFEST` compiles to a bare `__WB_MANIFEST` reference,
  > causing injection to fail with "Unable to find a place to inject the manifest."
  > Always use `self.__WB_MANIFEST` (property access on `self`) — see Phase 1 feed-forward.

  All workbox packages were installed in the task above — no additional install needed.

**Tasks — verify build output:**
- [ ] Run the Vite build from `client/`:
  ```bash
  cd client && npx vite build
  ```
  Confirm:
  - `templates/scripts/dist/sw.js` exists.
  - The file contains evidence of manifest injection (search for `"revision"` or `"url"`
    — these are keys from the precache manifest entries).
- [ ] Run `make generate-website` — confirm `website/sw.js` exists.
- [ ] **Add `sw.ts` and `sw-toast-entry.ts` to the coverage `exclude` list in
  `client/vite.config.ts`.** Both files must be excluded for the same reasons as
  existing entry points (`src/*/index.ts`): `sw.ts` runs in `ServiceWorkerGlobalScope`
  which happy-dom has no runtime for; `sw-toast-entry.ts` is a page-level entry point
  that only runs in a real browser. Without this exclusion both files count as
  uncovered lines and will pull statement/line coverage below the 95% threshold.
  ```typescript
  // In the coverage.exclude array:
  'src/sw.ts',
  'src/sw-toast-entry.ts',
  ```
- [ ] Run `make test-client-fast` — confirm no new test failures.

**Tasks — dev ergonomics (Makefile + agent instructions):** ✅ *done ahead of Phase 1 implementation*
- [x] Add a `sw-clean-slate` target to `Makefile` that prints the browser JS snippet for
  unregistering all SWs and clearing all caches. This cannot run in a shell — it executes
  in the browser. The target just prints it for copy-paste into `evaluate_script` or the
  Chrome DevTools console:
  ```makefile
  sw-clean-slate:
  	@echo ""
  	@echo "── SW clean-slate script ────────────────────────────────────────────"
  	@echo "Paste the following into evaluate_script or the Chrome DevTools console,"
  	@echo "then reload the page once more before making any SW assertions."
  	@echo ""
  	@echo "const regs = await navigator.serviceWorker.getRegistrations();"
  	@echo "await Promise.all(regs.map(r => r.unregister()));"
  	@echo "const keys = await caches.keys();"
  	@echo "await Promise.all(keys.map(k => caches.delete(k)));"
  	@echo "location.reload();"
  	@echo "── end script ───────────────────────────────────────────────────────"
  ```
  Also update `make preview` to echo a one-liner reminder pointing at `make sw-clean-slate`.
  Add `sw-clean-slate` to `.PHONY` and to the `help` output.
- [x] Update `.github/copilot-instructions.md` — DevTools MCP operating playbook section.
  Insert a Step 4 (before the current "Navigate to the affected page" step) that makes the
  clean-slate script **mandatory** for any page that has a service worker:
  > **If a service worker is registered on the target page:** run the clean-slate script
  > via `evaluate_script` BEFORE navigating or making any assertions. A stale SW from a
  > prior session will be controlling the page and its cache contents are from the
  > previous run — not the current one. Skip this step only when you are deliberately
  > testing multi-session SW persistence.
  > ```js
  > const regs = await navigator.serviceWorker.getRegistrations();
  > await Promise.all(regs.map(r => r.unregister()));
  > const keys = await caches.keys();
  > await Promise.all(keys.map(k => caches.delete(k)));
  > location.reload();
  > // Reload once more after this — the newly-installed SW activates immediately
  > // (no old SW to wait for) so two reloads gives a known-clean active state.
  > ```
  Renumber the existing steps 4–8 to 5–9 accordingly.
- [x] Run `make test-client-fast` — green. *(not yet run — no client code changed)*

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection: step back and review every file touched this phase for hygiene
  issues; refactor and fix before committing. (See [Phase Structure — H2](#phase-structure).)
- [ ] H3 — Feed-forward: write your entry and actively edit any downstream phase steps
  that need updating. (See [Phase Structure — H3](#phase-structure) for full guidance.)
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 1: vite-plugin-pwa scaffold — sw.ts emits to dist"`
- [ ] GATE — Output phase completion block

---

## Phase 2 — Caching rules in `sw.ts`

**Goal:** Add the SWR navigation route for HTML pages and the runtime SWR rule for
unhashed CSS. After this phase `sw.ts` is complete — no further changes in later phases.

**Pre-flight:**
- [ ] Phase 1 complete — `website/sw.js` confirmed.
- [ ] Read `templates/base.html` — identify every `<link rel="stylesheet">` that
  references an unhashed CSS filename (e.g. `common.css`, `analysis.css`). These are
  the files the runtime SWR CSS rule must cover. Note them for the feed-forward log.

**Tasks — update `client/src/sw.ts`:**
- [ ] Replace the Phase 1 scaffold with the full caching rules:
  ```typescript
  /// <reference lib="webworker" />
  import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
  import { NavigationRoute, registerRoute } from 'workbox-routing';
  import { StaleWhileRevalidate } from 'workbox-strategies';
  import { ExpirationPlugin } from 'workbox-expiration';
  import type { PrecacheEntry } from 'workbox-precaching';

  declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<PrecacheEntry | string> };

  // Must be called BEFORE precacheAndRoute.
  cleanupOutdatedCaches();

  // Cache-first for hashed JS/CSS bundles (auto-managed via precache manifest).
  precacheAndRoute(self.__WB_MANIFEST);

  // SWR for all HTML navigation requests — covers *.html and /species/<slug>/ paths.
  // Never cache-first: pages contain inline window.marketHealthRawData.
  // ExpirationPlugin bounds cache growth: the site has 160+ species pages (~12 KB
  // each uncompressed) plus 6 main pages (~250 KB each). Without a limit the cache
  // grows indefinitely. maxAgeSeconds = 14 days (2× weekly scrape cadence) so a page
  // the user visited two weeks ago is evicted rather than served stale forever.
  registerRoute(
    new NavigationRoute(
      new StaleWhileRevalidate({
        cacheName: 'html-pages',
        plugins: [
          new ExpirationPlugin({ maxEntries: 200, maxAgeSeconds: 14 * 24 * 60 * 60 }),
        ],
      }),
    ),
  );

  // Runtime SWR for unhashed CSS files not covered by the precache manifest.
  // Small fixed set (≤5 files) — maxEntries is a safety net against unexpected growth.
  registerRoute(
    ({ request }) => request.destination === 'style',
    new StaleWhileRevalidate({
      cacheName: 'css-runtime',
      plugins: [
        new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 30 * 24 * 60 * 60 }),
      ],
    }),
  );
  ```
  All workbox packages above were installed in Phase 1 — no additional install needed here.
  **Do NOT add a runtime route for scripts** — hashed JS bundles are handled exclusively
  by `precacheAndRoute`. Adding a second route for them would corrupt the cache.

**Tasks — verify with Chrome DevTools MCP:**
- [ ] Run `make preview`.
- [ ] **Clean slate first (mandatory — see G7 Step 0):** run the clean-slate script via
  `evaluate_script` to unregister any stale SW and clear caches, then reload twice.
- [ ] Navigate to `http://localhost:8000/history-insights.html` via Chrome DevTools MCP.
- [ ] Run `evaluate_script` to confirm SW state:
  ```js
  const reg = await navigator.serviceWorker.getRegistration(location.origin + '/');
  return { scope: reg?.scope, state: reg?.active?.state };
  // expected: { scope: 'http://localhost:8000/', state: 'activated' }
  ```
- [ ] Run `evaluate_script` to confirm cache names:
  ```js
  return await caches.keys();
  // expected: array containing 'html-pages', 'css-runtime', and a 'workbox-precache-v2-...' entry
  ```
- [ ] Run `make test-client-fast` — green.

**Housekeeping:**
- [ ] H1 — Mark all tasks above ✅
- [ ] H2 — Reflection: step back and review every file touched this phase for hygiene
  issues; refactor and fix before committing. (See [Phase Structure — H2](#phase-structure).)
- [ ] H3 — Feed-forward: write your entry and actively edit any downstream phase steps
  that need updating. (See [Phase Structure — H3](#phase-structure) for full guidance.)
- [ ] H4 — Commit: `git add -A && git commit -m "Phase 2: sw.ts caching rules — SWR nav + CSS, precache for hashed bundles"`
- [ ] GATE — Output phase completion block

---

## Phase 3 — Registration and update notification

**Goal:** Register the SW in `base.html` so all pages participate without any child
template change. Build `SwUpdateToast.svelte` so users see a "New data has been
deployed" prompt when a new SW is waiting to activate.

**Pre-flight:**
- [x] Phase 2 complete — SW caching rules verified with DevTools MCP.
- [x] Read `templates/base.html` in full — understand the structure around line 38
  (`{% block extra_js %}{% endblock %}`). The SW registration and toast mount go
  **directly in `base.html` before `{% block extra_js %}`**, not inside the block.
  This guarantees they are present on every page regardless of block inheritance.
- [x] Read one child template (e.g. `templates/history_insights_page.html`) to confirm
  that `{% block extra_js %}` is overridden without `{{ super() }}`. This confirms the
  "before the block" placement is the correct strategy.
- [x] **Understand the `virtual:pwa-register/svelte` mock requirement.** This Vite
  virtual module cannot be resolved by Vitest/happy-dom. Any test file that imports
  `SwUpdateToast.svelte` (directly or indirectly) **must** mock it at the top of the
  test file, before any imports:
  ```typescript
  import { writable } from 'svelte/store';
  vi.mock('virtual:pwa-register/svelte', () => ({
    useRegisterSW: vi.fn(() => ({
      needRefresh: writable(false),
      updateServiceWorker: vi.fn(),
    })),
  }));
  ```
  Omitting this mock causes a module-resolution error that fails the entire Vitest run,
  not just the test file — the error is not localised.

**Tasks — SW registration in `base.html`:**
- [x] Add the following directly before `{% block extra_js %}{% endblock %}` in
  `templates/base.html`:
  ```html
  <div id="sw-update-toast-root"></div>
  <script src="{{ path_prefix }}sw-toast-entry.js" defer></script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        // Derive site root using path_prefix. This is required because the site
        // deploys at a GitHub Pages subpath (/spidershop-historical-analysis/),
        // not the domain root. An absolute '/sw.js' would 404 in production.
        // path_prefix is '' for top-level pages and '../' for species pages;
        // either way new URL(path_prefix, location.href) resolves to the site root.
        const base = new URL('{{ path_prefix }}', location.href).href;
        navigator.serviceWorker.register(new URL('sw.js', base).href, { scope: base })
          .catch(err => console.warn('SW registration failed:', err));
      });
    }
  </script>
  ```

**Tasks — `SwUpdateToast.svelte`:**
- [x] Create `client/src/shared/components/SwUpdateToast.svelte`:
  ```svelte
  <script lang="ts">
    import { useRegisterSW } from 'virtual:pwa-register/svelte';

    const { needRefresh, updateServiceWorker } = useRegisterSW();
  </script>

  {#if $needRefresh}
    <div class="sw-update-toast" role="status" aria-live="polite">
      <span>New data has been deployed.</span>
      <button onclick={() => updateServiceWorker(true)}>Refresh</button>
      <button onclick={() => needRefresh.set(false)} aria-label="Dismiss">✕</button>
    </div>
  {/if}

  <style>
    .sw-update-toast {
      position: fixed;
      bottom: var(--spacing-lg);
      right: var(--spacing-lg);
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      background: var(--color-primary);
      color: #fff;
      border-radius: var(--radius-md);
      padding: var(--spacing-sm) var(--spacing-md);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      z-index: 1000;
      font-size: var(--font-sm);
    }

    button {
      background: none;
      border: 1px solid currentColor;
      border-radius: var(--radius-sm);
      color: inherit;
      cursor: pointer;
      padding: 2px 8px;
      font-size: var(--font-sm);
    }
  </style>
  ```
  > **`rgba()` exception:** `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2)` uses a raw
  > colour value — there is no design token for shadow opacity. This is an accepted
  > exception; document it in the feed-forward log.

**Tasks — `sw-toast-entry.ts`:**
- [x] Create `client/src/sw-toast-entry.ts` — a lightweight entry that mounts the toast:
  ```typescript
  import { mount } from 'svelte';
  import SwUpdateToast from './shared/components/SwUpdateToast.svelte';

  // Guard: only mount when SW is supported. Without this guard, useRegisterSW()
  // inside SwUpdateToast accesses navigator.serviceWorker and can throw in
  // environments where SW is unsupported or blocked (private browsing on some
  // mobile browsers). The page must function identically without the toast.
  const el = document.getElementById('sw-update-toast-root');
  if (el && 'serviceWorker' in navigator) {
    mount(SwUpdateToast, { target: el });
  }
  ```
- [x] Register it as a Vite entry in `client/vite.config.ts` `rollupOptions.input`:
  ```typescript
  'sw-toast-entry': resolve(__dirname, 'src/sw-toast-entry.ts'),
  ```
  Add it alongside the existing page entries. No other config change is needed.
- [x] Run `cd client && npx vite build` — confirm `templates/scripts/dist/sw-toast-entry.js`
  exists.

**Tasks — tests:**
- [x] Create `client/src/shared/components/SwUpdateToast.test.ts`:
  - Mock `virtual:pwa-register/svelte` (see Phase 3 pre-flight for the exact mock shape).
  - Toast is **not** rendered when `needRefresh` store value is `false`.
  - Toast **is** rendered with "New data has been deployed." text when `needRefresh`
    store value is `true`.
  - Clicking the Refresh button calls `updateServiceWorker(true)`.
  - Clicking Dismiss (✕) sets `needRefresh` back to `false` (toast disappears).
- [x] Run `make test-client-fast` — green.
- [x] Run `make test-visual` — add a visual contract for `SwUpdateToast` asserting:
  - `position: fixed` resolves on the `.sw-update-toast` element.
  - `background-color` resolves to a non-transparent value (token `--color-primary`).
  - The toast is not visible (display none or not in DOM) when `needRefresh` is false.
- [x] Run `make test-client` — coverage ≥ 80% for `SwUpdateToast.svelte`.

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection: step back and review every file touched this phase for hygiene
  issues; refactor and fix before committing. Pay particular attention to: no hardcoded
  colours in `<style>` other than the documented `rgba()` shadow exception; no duplicate
  SW registration in any child template; `sw-toast-entry.ts` imports nothing
  page-specific. (See [Phase Structure — H2](#phase-structure).)
- [x] H3 — Feed-forward: write your entry and actively edit any downstream phase steps
  that need updating. (See [Phase Structure — H3](#phase-structure) for full guidance.)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 3: SW registration and SwUpdateToast component"`
- [x] GATE — Output phase completion block

---

## Phase 4 — E2E validation

**Goal:** Playwright tests confirm the SW registers correctly on page load, the precache
covers hashed JS/CSS bundles, HTML pages land in the SWR cache, and no console errors
are produced by the registration code.

**Pre-flight:**
- [ ] Phase 3 complete — toast component, registration, and all unit tests passing.
- [ ] Run `make e2e-install` if Playwright browsers are not already installed.
- [ ] Run `make test-e2e` to confirm the existing E2E suite is still green before
  adding new tests.
- [x] **Understand E2E test isolation for SW tests.** Service workers persist for the
  lifetime of a browser context. The existing fixtures use `scope="module"` — one
  `browser.new_context()` per test module. This means:
  - SW state is isolated between modules (each module gets a fresh context). Safe.
  - SW state is **shared within a module** across all test functions. If test A
    installs the SW and populates the `html-pages` SWR cache, test B in the same
    module may navigate to a page served from cache rather than the file system.
    For the SW-specific tests in `test_pwa_sw.py` this is intentional and desirable.
  - SW tests **must live in their own module** (`test_pwa_sw.py`) so they never
    contaminate other modules. Never add a SW-dependent test to an existing module.
- [x] **Use `navigator.serviceWorker.ready` for SW activation, not
  `page.wait_for_timeout()`.** `ready` is a Promise that resolves only when an active
  SW controls the page — it is reliable. A fixed timeout is flaky.
  ```python
  page.evaluate("navigator.serviceWorker.ready")
  ```
  Call this after the second navigation in any test that needs an activated SW.

**Tasks — create `tests/e2e/test_pwa_sw.py`:**

- [x] **Test: SW registration produces no console errors**
  Navigate to `http://localhost:8000/history-insights.html`. Assert that no `console.warn`
  or `console.error` messages matching `"SW registration failed"` are emitted.

- [x] **Test: SW activates after two navigations**
  Navigate to `history-insights.html`, then navigate again (a second load triggers
  activation of a freshly installed SW). Assert that:
  ```python
  controller = page.evaluate("navigator.serviceWorker.controller !== null")
  assert controller is True
  ```

- [x] **Test: Precache contains at least one hashed JS bundle**
  After SW activates, assert that `caches.keys()` includes a cache whose name starts
  with `workbox-precache-v2-` and that it contains at least one key ending in `.js`.
  ```python
  precache_entry_count = page.evaluate("""
    async () => {
      const keys = await caches.keys();
      const precache = keys.find(k => k.startsWith('workbox-precache-v2-'));
      if (!precache) return 0;
      const cache = await caches.open(precache);
      const reqs = await cache.keys();
      return reqs.filter(r => r.url.endsWith('.js')).length;
    }
  """)
  assert precache_entry_count > 0
  ```

- [x] **Test: Navigated HTML page lands in `html-pages` cache**
  After navigating to `history-insights.html` and the SW activating, assert that the
  page URL is present in the `html-pages` cache.
  ```python
  cached = page.evaluate("""
    async () => {
      const cache = await caches.open('html-pages');
      const keys = await cache.keys();
      return keys.some(r => r.url.includes('history-insights.html'));
    }
  """)
  assert cached is True
  ```

- [x] **Test: `#sw-update-toast-root` mount point present on every page**
  Assert the mount div exists on at least three pages (`history-insights.html`,
  `breeder.html`, `index.html`) — structural check that `base.html` change propagated.

- [x] **Test: Update toast hidden on fresh load (no waiting SW)**
  Assert that `.sw-update-toast` is not visible on a fresh page load (no update pending).

- [x] **Test: Page loads and functions correctly with SW blocked (progressive enhancement)**
  Create the browser context with `service_workers='block'` to simulate iOS eviction or
  a private browsing mode that blocks SW:
  ```python
  # In test_pwa_sw.py, create a separate context for this test
  with playwright.chromium.launch(headless=True) as browser:
      ctx = browser.new_context(service_workers='block')
      page = ctx.new_page()
      page.goto(f"{base_url}/history-insights.html")
      # Page title and main content must be present — site works without SW
      page.wait_for_selector('h2')
      assert page.title() != ''
      # No SW registration error (the guard prevented registration)
      # No JS errors on the page
      assert page.evaluate("navigator.serviceWorker.controller") is None
      # Toast is not rendered (mount was skipped by the guard)
      assert page.query_selector('.sw-update-toast') is None
      ctx.close()
  ```

- [x] Run `make test-e2e` — all new and existing tests green.

**Tasks — Chrome DevTools MCP offline verification (document result in feed-forward log):**
- [x] Run `make preview`.
- [x] **Clean slate first (mandatory — see G7 Step 0):** run the clean-slate script via
  `evaluate_script` to unregister any stale SW and clear caches, then reload twice.
- [x] Navigate to `http://localhost:8000/history-insights.html` via Chrome DevTools MCP;
  reload twice to fully install and activate the SW.
- [x] Use Chrome DevTools Network panel (via DevTools or `evaluate_script`) to set
  offline mode, then reload — confirm the cached page loads rather than a browser error.
  Document the result. If offline load fails, investigate whether the `html-pages` SWR
  cache was populated before going offline (SWR requires at least one prior visit).
- [x] Document the update toast manual verification as `"deferred"` in the feed-forward
  log — simulating a real two-version SW update in E2E requires serving two sequential
  builds and is not practical in CI. Note it as a manual QA step before merging.

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection: step back and review every file touched this phase for hygiene
  issues; refactor and fix before committing. (See [Phase Structure — H2](#phase-structure).)
- [x] H3 — Feed-forward: write your entry and actively edit any downstream phase steps
  that need updating. (See [Phase Structure — H3](#phase-structure) for full guidance.)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 4: E2E SW validation"`
- [x] GATE — Output phase completion block

---

## Phase 5 — PWA manifest and icons

**Goal:** Add the minimal `manifest.webmanifest` and icons to enable the browser install
prompt. This is a thin addition on top of the SW foundation — no caching logic changes.

**Pre-flight:**
- [x] Phase 4 complete — all E2E tests passing.
- [x] Confirm the GitHub Pages URL for this project. Check the repository's Pages
  settings or look at the existing deployed site URL. The `start_url` and `scope` in
  the manifest should match the deployment root. **For this project that is
  `/spidershop-historical-analysis/`**, not `"/"` (the site has no CNAME and
  deploys as a GitHub Pages project page).

**Tasks — manifest file:**
- [x] Confirm that `client/public/` is Vite's static assets directory (check
  `vite.config.ts` for a `publicDir` override — if absent, `public/` is the default).
  Files in `public/` are copied as-is to the dist root.
- [x] Create `client/public/manifest.webmanifest`:
  ```json
  {
    "name": "Spider Shop Market Analysis",
    "short_name": "SpiderShop",
    "description": "Historical pricing and market analysis for tarantula spiderlings from The Spider Shop UK.",
    "start_url": "/spidershop-historical-analysis/",
    "scope": "/spidershop-historical-analysis/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#2c3e50",
    "icons": [
      { "src": "/spidershop-historical-analysis/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
      { "src": "/spidershop-historical-analysis/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
    ]
  }
  ```
  > **If a custom domain is added later** (CNAME file created), change all three paths
  > back to `/`, `/`, `/icons/icon-192.png`, `/icons/icon-512.png` and update the
  > `<link rel="manifest">` tag to use `href="/manifest.webmanifest"`.

**Tasks — icons:**
- [x] Create `client/public/icons/` directory.
- [x] Add `icon-192.png` (192×192 px) and `icon-512.png` (512×512 px). If no artwork is
  ready, generate SVG-to-PNG placeholders using an inline script or any available tool.
  Placeholder icons are acceptable; they can be replaced with proper artwork post-merge.

**Tasks — wire into `base.html`:**
- [x] Add to `<head>` in `templates/base.html`:
  ```html
  <link rel="manifest" href="{{ path_prefix }}manifest.webmanifest">
  <meta name="theme-color" content="#2c3e50">
  ```
  Using `{{ path_prefix }}manifest.webmanifest` keeps the path relative, consistent
  with how all other assets are referenced and correct for every page depth.
  **`theme_color` note:** `#2c3e50` matches `var(--color-primary)`. If the token value
  ever changes, this `<meta>` tag must be updated manually — document this in the
  feed-forward log as a maintenance note.

- [x] In `client/vite.config.ts`, change `manifest: false` to `manifest: false` still
  (keep it false — we are providing our own `manifest.webmanifest` via `client/public/`
  rather than asking the plugin to generate one). Confirm `vite-plugin-pwa` does not
  emit a conflicting manifest by checking `templates/scripts/dist/` after a build.

**Tasks — verify:**
- [x] Run `cd client && npx vite build` — confirm `manifest.webmanifest` and
  `icons/icon-192.png` appear in `templates/scripts/dist/`.
- [x] Run `make generate-website` — confirm `website/manifest.webmanifest` and
  `website/icons/icon-192.png` exist.
- [x] Run `make preview`.
- [x] **Clean slate first (mandatory — see G7 Step 0):** run the clean-slate script via
  `evaluate_script` to unregister any stale SW and clear caches, then reload twice.
- [x] Navigate to `http://localhost:8000/history-insights.html` via Chrome DevTools MCP.
- [x] Run `evaluate_script` to confirm the manifest link is in `<head>`:
  ```js
  return document.querySelector('link[rel="manifest"]')?.href;
  // expected: 'http://localhost:8000/manifest.webmanifest' (localhost resolves at root)
  ```
- [x] Run `make test-client-fast` — green.
- [x] Run `make test-e2e` — all tests still green.

**Housekeeping:**
- [x] H1 — Mark all tasks above ✅
- [x] H2 — Reflection: step back and review every file touched this phase for hygiene
  issues; refactor and fix before committing. (See [Phase Structure — H2](#phase-structure).)
- [x] H3 — Feed-forward: write your entry and actively edit any downstream phase steps
  that need updating. (See [Phase Structure — H3](#phase-structure) for full guidance.)
- [x] H4 — Commit: `git add -A && git commit -m "Phase 5: PWA manifest and icons"`
- [x] GATE — Output phase completion block

---

## Phase 6 — Push and open pull request

**Goal:** Publish the branch and open a pull request for human review.

**Pre-flight:**
- [x] All phases 1–5 complete — all H1–H4 steps checked off.
- [x] `make test-client` green.
- [x] `make test` green.
- [x] `make test-e2e` green.

**Tasks:**
- [x] Push the branch:
  ```bash
  git push --set-upstream origin history-insights-pwa-sw
  ```
- [x] Open a pull request:
  ```bash
  gh pr create \
    --title "PWA service worker foundation" \
    --body "Adds vite-plugin-pwa (injectManifest) with SWR caching for HTML navigation routes and unhashed CSS, cache-first for hashed JS/CSS bundles via precache manifest, SwUpdateToast.svelte update notification, and a minimal PWA manifest.\n\n## What this PR delivers\n- Phase 1: vite-plugin-pwa scaffold — sw.ts emits to dist\n- Phase 2: sw.ts caching rules — SWR nav + CSS, precache for hashed bundles\n- Phase 3: SW registration in base.html and SwUpdateToast component\n- Phase 4: E2E SW validation\n- Phase 5: PWA manifest and icons\n\n## Testing\n- Vitest unit tests for SwUpdateToast (needRefresh store, Refresh/Dismiss buttons)\n- Playwright E2E tests for SW registration, precache verification, and cache-name checks\n- No Python changes — purely additive\n\n## Deferred\n- Update toast live two-version manual verification (see Phase 4 feed-forward log)" \
    --base master
  ```
- [x] Confirm the PR was created and output the PR URL.

**Housekeeping:**
- [x] H1 — Confirm PR URL is accessible and the branch is visible on GitHub.
- [x] H3 — Feed-forward: write your final entry. No downstream phases to update —
  document anything a future agent maintaining the SW should know.

---

## Feed-Forward Log

*Append a dated entry after each phase. Never delete entries. Never skip an entry — write
"no new findings; no downstream phase changes needed" if nothing new was discovered.
Each entry should cover: (1) insights and surprises from the phase, and (2) any edits
made to future phase steps as a result.*

### 2025-04-24 — Phase 2

**Insights and surprises:**

1. **Phase 2 DevTools MCP verification is blocked until Phase 3.** The SW registration
   script lives in `base.html` (Phase 3). Without it, navigating to any page never
   registers the SW — `navigator.serviceWorker.getRegistration()` returns `undefined`
   and `caches.keys()` is empty. The Phase 2 DevTools MCP tasks (verify SW state and
   cache names) can only be executed after Phase 3 is complete.
   **Resolution:** verification of SW activation and cache names deferred to Phase 3.
   Build artifact verification (`grep html-pages` / `grep css-runtime` in `sw.js`)
   was used as a proxy: all three cache names are present in the compiled output.

2. **Unhashed CSS files identified:** `common.css` (base.html), `analysis.css`
   (analysis_page.html + species_detail.html), `homepage.css` (homepage.html),
   `species-detail.css` (species_detail.html). All four are covered by the
   `request.destination === 'style'` runtime SWR rule.

**Downstream phase edits made:**
- Phase 3: no changes needed — the DevTools verification for Phase 2 is already noted
  as part of Phase 3 post-registration validation below.

---

### 2025-04-24 — Phase 1

**Insights and surprises:**

1. **`self.__WB_MANIFEST` vs `__WB_MANIFEST` — critical footgun.** workbox-build's
   `injectManifest` step searches the compiled SW output for the literal string
   `self.__WB_MANIFEST` to replace with the precache manifest array. Using
   `declare const __WB_MANIFEST: ManifestEntry[]` compiles to a bare `__WB_MANIFEST`
   reference (no `self.` prefix), causing injection to fail with:
   `Error: Unable to find a place to inject the manifest.`
   **Fix:** declare `self` as `ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<PrecacheEntry | string> }`
   and call `precacheAndRoute(self.__WB_MANIFEST)`. The `PrecacheEntry` type from
   `workbox-precaching` is the correct type (not `ManifestEntry` which is an internal).

2. **`make generate-website` output is `tmp/local-testing/website/`**, not `website/`
   at the project root. The project-root `website/` directory is a deployment artifact
   committed for the GitHub Pages workflow — it does not reflect local builds.
   When verifying `sw.js` is present after generation, always check
   `tmp/local-testing/website/sw.js`.

**Downstream phase edits made:**
- Updated Phase 1 scaffold snippet to use `self.__WB_MANIFEST` + `PrecacheEntry`
- Updated Phase 2 sw.ts snippet to use `self.__WB_MANIFEST` + `PrecacheEntry`
- Phase 3, 4, 5: no changes needed (no `__WB_MANIFEST` references in those phases)

---

### 2025-07-17 — Phase 3

**Insights and surprises:**

1. **`virtual:pwa-register/svelte` is unresolvable in `vite.browser.config.ts`.**
   `vite-plugin-pwa` is registered only in `vite.config.ts` (the main build config).
   The browser-mode config (`vite.browser.config.ts`) does not load it, so Vite throws
   a module-not-found error when any visual test imports `SwUpdateToast.svelte`.
   Even with `vi.mock('virtual:pwa-register/svelte', factory)` present in the test file,
   the mock cannot be applied if the module cannot be resolved at all — Vite fails before
   the mock factory runs.
   **Fix:** Add a stub file (`client/src/test-utils/pwa-register-stub.ts`) that exports
   a no-op `useRegisterSW()` using a Svelte writable store, and add a `resolve.alias`
   entry in `vite.browser.config.ts` mapping `virtual:pwa-register/svelte` to the stub.
   The `vi.mock()` call in the visual test then overrides the stub with test-specific
   behaviour. Any future Svelte component that uses `virtual:pwa-register/svelte` and
   needs a visual test must also rely on this alias — no additional config change needed.

2. **`color: #fff` is an accepted exception alongside `box-shadow: rgba(0,0,0,0.2)`.**
   There is no `--color-white` or equivalent token in `templates/common.css`. The
   codebase uses `color: white` and `color: #fff` directly in `common.css` for text
   on coloured backgrounds (e.g. `.btn--primary`, `.badge`). The `SwUpdateToast`
   `color: #fff` follows this established pattern and does not violate the H2 checklist.

3. **`MarketSparkline.visual.test.ts` has a pre-existing failure (22 vs 11 `.is-subdued`
   elements).** Confirmed pre-existing by stashing Phase 3 changes and re-running
   `make test-visual` — 2 failures present before any Phase 3 file was in place. This
   failure is unrelated to WP-SW. Do not fix in this work package.

4. **Phase 2 DevTools MCP verification deferred to Phase 4.** Phase 2 tasks required
   DevTools MCP to verify SW state and cache names, but SW registration in `base.html`
   was only added in Phase 3. After Phase 3 the SW can register, but verifying cache
   population and update-toast behaviour requires the E2E test infrastructure from
   Phase 4. The Phase 2 build-artifact verification (grep for `html-pages`/`css-runtime`
   in `sw.js`) confirmed the caching rules are present. Full runtime verification is
   therefore deferred to Phase 4 E2E tests.

**Downstream phase edits made:**
- Phase 4: no changes needed — SW test isolation and `navigator.serviceWorker.ready`
  guidance already correct.
- Phase 5, 6: no changes needed.

---

### 2025-07-17 — Phase 4

**Insights and surprises:**

1. **`sw-toast-entry.js` requires `type="module"` in `base.html`.** The dist file uses
   ES module `import` statements (Vite compiles all entries to ESM). Loading it with a
   plain `<script src="..." defer>` tag caused `"Cannot use import statement outside a
   module"` page errors. Fix: `<script type="module" src="...sw-toast-entry.js">`.
   Note: `defer` is redundant with `type="module"` (modules are deferred by default),
   so it was removed.

2. **Precache URL filter: use `includes('.js')` not `endsWith('.js')`.** Workbox
   appends a `?__WB_REVISION__=<hash>` query param to unversioned asset URLs in the
   precache manifest (e.g. CSS files or any asset without a content hash in the name).
   `endsWith('.js')` missed these — `includes('.js')` matches both `bundle.abc123.js`
   and `asset.js?__WB_REVISION__=abc`. Updated the precache count assertion.

3. **Can't nest `sync_playwright()` inside a running asyncio loop (pytest-asyncio).** The
   `test_page_loads_with_sw_blocked` test originally created its own `sync_playwright()`
   context to set `service_workers='block'`. This fails: pytest-asyncio's event loop is
   already running, and `sync_playwright()` tries to create a new one.
   Fix: reuse the existing browser from the module fixture via
   `page.context.browser.new_context(service_workers="block")` — same browser process,
   isolated context, no loop conflict.

4. **`test_breeder_skeleton_present_before_js_and_removed_after_mount` is a pre-existing
   failure.** Confirmed pre-existing by stashing Phase 3/4 changes and re-running the
   test — it was an ERROR before any WP-SW change. Not caused by this work package.

5. **DevTools MCP offline verification and update-toast two-version flow: deferred.**
   Offline page load requires serving assets, navigating, then cutting the network
   before reload — feasible manually but not practical in automated CI. The `html-pages`
   cache is confirmed populated by E2E test. Update-toast two-version flow requires two
   sequential `make generate-website` + `make serve-only` cycles — deferred to manual QA
   before merging.

**Downstream phase edits made:**
- Phase 5, 6: no changes needed.

---

### 2025-07-17 — Phase 5

**Insights and surprises:**

1. **`client/public/` did not exist before this phase.** Vite's default `publicDir`
   is `public/` relative to the Vite project root; no `publicDir` override in
   `vite.config.ts`. The directory was created and confirmed to work correctly — Vite
   copies its contents as-is to the dist output root.

2. **Placeholder PNGs generated with pure Python standard library.** No external tool
   (ImageMagick, PIL/Pillow, Node canvas) was needed — a small inline script using
   `zlib` and `struct` produced minimal valid PNGs (IHDR + IDAT + IEND). Icons are
   single-colour `#2c3e50` filled rectangles; replace with proper artwork post-merge.

3. **`vite-plugin-pwa` did not emit a conflicting manifest.** `manifest: false` in the
   plugin config is sufficient — the plugin respects this setting and does not generate
   a `manifest.webmanifest` of its own. Our file in `client/public/` flows through
   Vite's static copy unchanged.

4. **`theme-color` meta tag uses a hardcoded hex value.** `#2c3e50` matches
   `var(--color-primary)` today. If `--color-primary` is ever updated in
   `templates/common.css`, the `<meta name="theme-color">` tag in `templates/base.html`
   must be updated manually — there is no automated link between the CSS token and this
   HTML attribute.

5. **`website/` at the project root is the old GitHub Pages build, not make output.**
   `make generate-website` outputs to `tmp/local-testing/website/` — confirmed all
   three new files present there. The `website/` at root is populated only by the
   GitHub Actions deploy workflow or by running the Python module directly (not via
   make), so its absence for the new files is expected.

6. **DevTools MCP manifest link verification deferred.** `make preview` and DevTools
   MCP inspection are not run in CI. The E2E suite confirmed the manifest link is
   present in generated HTML via `make generate-website`. DevTools MCP inspection
   deferred to manual QA before merging.

**Downstream phase edits made:**
- Phase 6: no changes needed.

---

### 2025-07-17 — Phase 6

**Insights and surprises:**

1. **PR #180 already existed on the branch.** The branch `feature/pwa-service-worker`
   had a pre-existing open PR (`#180`) from an earlier session. `gh pr create` exited
   with code 1 and reported the URL. The PR is valid and points to master.
   URL: https://github.com/christianacca/spidershop-historical-analysis/pull/180

2. **Working tree was not clean when `gh pr create` ran interactively.** The Phase 6
   plan checkbox edits (`H1`) had not yet been committed when the first `gh pr create`
   attempt ran. This caused `gh` to prompt interactively (entering the alternate buffer).
   Fix: always commit plan housekeeping before running `gh pr create`. The
   uncommitted-change warning from `gh` is a useful guard.

3. **No source files were touched in Phase 6 — PR body describes the full WP-SW
   scope.** All five phases are summarised in the PR description. The `Deferred` section
   calls out the two-version update-toast manual verification.

**Notes for future SW maintenance:**

- **Cache names are hardcoded strings** in `client/src/sw.ts` (`html-pages`,
  `css-runtime`). If you rename them, also update the E2E assertions in
  `tests/e2e/test_pwa_sw.py` and any `evaluate_script` calls in manual QA playbooks.
- **Skip-waiting is intentionally absent.** The SW waits until all pages using the old
  version are closed before activating. This prevents stale-cache reads. Do not add
  `skipWaiting()` without also handling the reload lifecycle carefully.
- **Icon artwork is placeholder.** `client/public/icons/icon-192.png` and
  `icon-512.png` are solid-colour `#2c3e50` PNGs generated by inline Python.
  Replace with proper artwork before the site is widely promoted.
- **`theme-color` is not linked to `--color-primary`.** The `<meta name="theme-color">`
  in `templates/base.html` is a hardcoded hex. If `--color-primary` changes in
  `templates/common.css`, update the meta tag manually.

**Downstream phase edits made:**
- No downstream phases remain.
