#!/usr/bin/env python3
"""E2E tests for the PWA service worker (WP-SW).

Scope:
- SW registration on all pages (via base.html) produces no errors
- SW activates and becomes the controller after initial page loads
- Precache manifest covers at least one hashed JS bundle
- Precache manifest covers at least one CSS file (via additionalManifestEntries)
- Install handler pre-fetches ALL 6 main HTML pages before SW enters waiting state
- html-pages cache is populated by install handler, not only by navigation
- Toast only fires after install handler completes (ordering guarantee)
- HTML navigation routes land in the `html-pages` SWR cache
- SW registration scope covers the whole site (not a narrow per-page scope)
- `#sw-update-toast-root` mount point present on every page
- Update toast is hidden on fresh load (no waiting SW)
- Update toast appears when a new SW version is installed and waiting;
  html-pages cache contains fresh entries at that point
- Refresh button activates new SW and fresh HTML is served on reload
- Pages load and function correctly when SW is blocked (progressive enhancement)

Test isolation:
- SW tests live in their own module so they never contaminate other modules.
- Most tests share one browser context (module-scoped fixture). SW state accumulates
  across tests within this module; this is intentional — each test builds on the SW
  state established by the previous ones.
- The update-toast test and SW-blocked test each create their own browser context to
  isolate their specific SW lifecycle scenarios.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from e2e.fixtures import e2e_site_minimal


@pytest.mark.e2e
def test_sw_toast_root_present_on_all_pages(e2e_site_minimal) -> None:
    """#sw-update-toast-root mount point exists on all main pages (base.html change)."""
    page, base_url, _ = e2e_site_minimal

    pages = ["index.html", "breeder.html", "history-insights.html"]
    for path in pages:
        page.goto(f"{base_url}/{path}", wait_until="domcontentloaded")
        mount_div = page.query_selector("#sw-update-toast-root")
        assert mount_div is not None, (
            f"#sw-update-toast-root not found on {path} — base.html change may not have propagated"
        )


@pytest.mark.e2e
def test_sw_registers_without_console_errors(e2e_site_minimal) -> None:
    """SW registration produces no 'SW registration failed' console warnings."""
    page, base_url, _ = e2e_site_minimal

    sw_warns: list[str] = []

    def on_console(msg):
        if msg.type in ("warning", "error"):
            sw_warns.append(msg.text)

    page.on("console", on_console)
    try:
        page.goto(f"{base_url}/history-insights.html", wait_until="load")
        # Wait for SW to finish registering — navigator.serviceWorker.ready resolves
        # only when an active SW exists. The SW registration script runs on 'load',
        # so waiting until load + SW ready confirms registration was attempted.
        page.evaluate("navigator.serviceWorker.ready")
    finally:
        page.remove_listener("console", on_console)

    failed = [w for w in sw_warns if "SW registration failed" in w]
    assert not failed, f"SW registration emitted failure messages: {failed}"


@pytest.mark.e2e
def test_sw_activates_after_two_navigations(e2e_site_minimal) -> None:
    """SW controller is non-null after two navigations (SW installed and active)."""
    page, base_url, _ = e2e_site_minimal

    # Navigate to a page within scope; preceding tests have already triggered SW
    # installation. This navigation is intercepted by the now-active SW.
    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")

    # navigator.serviceWorker.ready resolves only when an active SW exists.
    # Using this instead of wait_for_timeout() for reliability.
    page.evaluate("navigator.serviceWorker.ready")

    controller_present = page.evaluate("navigator.serviceWorker.controller !== null")
    assert controller_present, (
        "Expected navigator.serviceWorker.controller to be non-null after two navigations "
        "(SW should be active and controlling page)"
    )


@pytest.mark.e2e
def test_precache_contains_hashed_js_bundle(e2e_site_minimal) -> None:
    """Workbox precache contains at least one hashed JS bundle entry."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    precache_entry_count = page.evaluate("""
        async () => {
            const keys = await caches.keys();
            const precache = keys.find(k => k.startsWith('workbox-precache-v2-'));
            if (!precache) return 0;
            const cache = await caches.open(precache);
            const reqs = await cache.keys();
            // URLs may include ?__WB_REVISION__=... query params for unversioned files,
            // so use includes() not endsWith().
            return reqs.filter(r => r.url.includes('.js')).length;
        }
    """)
    assert precache_entry_count > 0, (
        f"Expected at least one hashed JS entry in workbox-precache-v2-* cache, got {precache_entry_count}"
    )


@pytest.mark.e2e
def test_html_page_cached_in_html_pages(e2e_site_minimal) -> None:
    """A navigated HTML page is present in the `html-pages` SWR cache."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    cached = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.some(r => r.url.includes('history-insights.html'));
        }
    """)
    assert cached is True, (
        "Expected history-insights.html to be cached in the 'html-pages' SWR cache"
    )


@pytest.mark.e2e
def test_install_prefetches_all_main_pages(e2e_site_minimal) -> None:
    """Install handler pre-fetches all 6 main HTML pages before SW enters waiting.

    This verifies the race-condition fix: by the time any toast fires, fresh HTML
    is already in html-pages for every main page — not just pages the user navigated
    to.  We prove this by checking for pages that were never explicitly navigated to
    in this test context.

    The module-scoped fixture starts fresh; the tests that precede this one navigated
    only to history-insights.html and index.html — NOT to breeder.html, dealer.html,
    snapshot.html, or history.html.  Finding those pages in html-pages proves they
    were put there by the install handler, not by navigation.
    """
    page, base_url, _ = e2e_site_minimal

    # Navigate to any page and wait for SW to be active.
    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    # These pages were NEVER explicitly navigated to in this test module.
    # If they appear in html-pages it can only be because the install handler fetched them.
    never_navigated = ["breeder.html", "dealer.html", "snapshot.html", "history.html"]

    cached_pages = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)

    missing = [p for p in never_navigated if not any(p in url for url in cached_pages)]
    assert not missing, (
        f"The following main pages were NOT found in html-pages cache, "
        f"meaning the install-time pre-fetch did not run or failed for them: {missing}.\n"
        f"Cached URLs: {cached_pages}"
    )


@pytest.mark.e2e
def test_css_cached_in_precache(e2e_site_minimal) -> None:
    """At least one CSS file is present in the Workbox precache.

    The unhashed top-level CSS files (common.css, analysis.css, etc.) are added
    to the precache manifest via additionalManifestEntries in vite.config.ts with
    a content-derived revision.  They are therefore served cache-first and swapped
    atomically with JS bundles when a new SW activates — no separate css-runtime
    cache is needed.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")

    css_entry_count = page.evaluate("""
        async () => {
            const keys = await caches.keys();
            const precacheName = keys.find(k => k.startsWith('workbox-precache-v2-'));
            if (!precacheName) return 0;
            const cache = await caches.open(precacheName);
            const reqs = await cache.keys();
            return reqs.filter(r => r.url.includes('.css')).length;
        }
    """)
    assert css_entry_count > 0, (
        f"Expected at least one .css entry in the workbox-precache-v2-* cache, got {css_entry_count}. "
        "Check that additionalManifestEntries in vite.config.ts includes the unhashed CSS files."
    )

    no_runtime_cache = page.evaluate("""
        async () => {
            const keys = await caches.keys();
            return !keys.includes('css-runtime');
        }
    """)
    assert no_runtime_cache is True, (
        "Found a 'css-runtime' cache — it should no longer exist. "
        "CSS is now handled by the precache, not a runtime route."
    )


@pytest.mark.e2e
def test_sw_registration_scope_covers_site(e2e_site_minimal) -> None:
    """The SW registration scope covers the whole site, not a narrow per-page scope.

    The scope must end with '/' (i.e. a directory scope) so that all pages
    under the deployment root are controlled by a single registration.  A
    per-page scope (e.g. ending in '.html') would mean each page creates its
    own registration, causing unpredictable behaviour between navigations.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")
    page.evaluate("navigator.serviceWorker.ready")

    scope = page.evaluate("""
        async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            return reg ? reg.scope : null;
        }
    """)
    assert scope is not None, "Expected a SW registration to exist"
    assert scope.endswith("/"), (
        f"Expected SW scope to end with '/' (directory scope covering the whole site), got: {scope!r}. "
        "A scope ending in a filename means only that exact URL is controlled."
    )
    # The scope must be a prefix of the page URL, confirming this registration
    # actually covers the page we navigated to.
    assert base_url.rstrip("/") + "/" in scope or scope in base_url + "/", (
        f"SW scope {scope!r} does not appear to cover the test server origin {base_url!r}"
    )


@pytest.mark.e2e
def test_update_toast_hidden_on_fresh_load(e2e_site_minimal) -> None:
    """The SW update toast is not visible on a fresh load (no waiting SW)."""
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/index.html", wait_until="domcontentloaded")

    toast = page.query_selector(".sw-update-toast")
    assert toast is None, (
        "Expected .sw-update-toast to be absent from DOM on fresh load (no update pending)"
    )


@pytest.mark.e2e
def test_page_loads_with_sw_blocked(e2e_site_minimal) -> None:
    """Pages load and function correctly when SW is blocked (progressive enhancement)."""
    page, base_url, _ = e2e_site_minimal

    # Create a new browser context with service workers blocked.
    # We reuse the existing browser instance from the fixture (via page.context.browser)
    # to avoid starting a new sync_playwright() session inside the fixture's asyncio loop.
    ctx = page.context.browser.new_context(service_workers="block")
    try:
        blocked_page = ctx.new_page()
        blocked_page.set_default_timeout(5_000)
        blocked_page.goto(f"{base_url}/history-insights.html", wait_until="domcontentloaded")

        # Page should still render core content without SW
        title = blocked_page.title()
        assert title != "", "Expected page to have a title even with SW blocked"

        # SW guard in sw-toast-entry.ts must prevent mounting
        toast = blocked_page.query_selector(".sw-update-toast")
        assert toast is None, "Expected .sw-update-toast to be absent when SW is blocked"

        # SW must not be controlling the page
        controller = blocked_page.evaluate("navigator.serviceWorker.controller")
        assert controller is None, "Expected no SW controller when service workers are blocked"
    finally:
        ctx.close()


@pytest.fixture()
def _e2e_sw_update_context(e2e_site_minimal):
    """Fresh browser context + isolated server for the SW update-toast test.

    Reuses the module-scoped browser (no new sync_playwright session needed) but
    creates an isolated browser context (clean SW state) and a private copy of the
    output directory so patching sw.js mid-test does not affect the module fixture's
    server or other tests in this module.

    Yields:
        tuple: (page, base_url, output_dir)
    """
    import shutil

    page_module, _, _ = e2e_site_minimal
    browser = page_module.context.browser

    from website.generate_website import OUTPUT_DIR
    from e2e.helpers import test_server

    cwd = Path.cwd()
    src_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    private_dir = cwd / "tmp_sw_update_test"

    if private_dir.exists():
        shutil.rmtree(str(private_dir))
    shutil.copytree(str(src_dir), str(private_dir))

    with test_server(private_dir) as base_url:
        context = browser.new_context()
        page = context.new_page()
        try:
            yield page, base_url, private_dir
        finally:
            context.close()
            if private_dir.exists():
                shutil.rmtree(str(private_dir))


@pytest.mark.e2e
def test_update_toast_appears_when_new_sw_waiting(_e2e_sw_update_context) -> None:
    """Update toast appears when a new SW version is installed and waiting to activate.

    Simulates a deployment by patching sw.js on disk after SW V1 is active.
    Workbox's byte-change detection treats any modification as a new version and
    installs the changed SW into the 'waiting' state, which flips needRefresh=true
    inside useRegisterSW() and renders the toast.
    """
    page, base_url, output_dir = _e2e_sw_update_context

    # Step 1: Two navigations to install and activate SW V1.
    # Navigate to the root URL (trailing slash) so that location.href ends in '/',
    # which makes new URL('', location.href) resolve to the site root.  This is
    # critical: the manual SW registration in base.html uses
    #   scope = new URL(path_prefix, location.href).href
    # For path_prefix='' that evaluates to location.href itself.  When location.href
    # ends in '/' both the manual registration and the Workbox registration
    # (new Workbox('/sw.js', { scope: '/' })) share the same scope and therefore
    # share the SAME ServiceWorkerRegistration object.  If we navigate to
    # /index.html instead, location.href is '.../index.html', the manual registration
    # gets scope '.../index.html', the Workbox registration gets scope '/', and
    # getRegistration() below returns the more-specific manual one — meaning
    # reg.update() fires updatefound on a registration Workbox isn't watching.
    #
    # First visit: SW installs and activates (state: installing → activated).
    # We must wait for navigator.serviceWorker.ready before the second navigation so
    # the SW is fully active and can control the next page load.
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")
    # Second visit: SW is now active and claims control of this navigation.
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")

    assert page.evaluate("navigator.serviceWorker.controller !== null"), (
        "Expected SW to be controlling the page after two navigations"
    )
    assert page.query_selector(".sw-update-toast") is None, (
        "Expected no toast before any update is pending"
    )

    # Step 2: Simulate a new deployment by appending a comment to sw.js.
    # Any byte change to sw.js triggers Workbox's update detection; a trailing
    # comment is the least invasive modification.
    sw_path = output_dir / "sw.js"
    sw_path.write_text(
        sw_path.read_text(encoding="utf-8") + "\n// update-test-marker",
        encoding="utf-8",
    )

    # Step 3: Give Workbox's async init time to complete, then trigger the update.
    #
    # Workbox adds its 'updatefound' listener inside wb.register(), which requires
    # a dynamic import of workbox-window to complete first (~5-50 ms on a local
    # server).  A 500 ms pause is conservative but reliable, ensuring the listener
    # is in place before reg.update() fires 'updatefound' — otherwise Workbox
    # misses the event and the 'waiting' event is never dispatched.
    #
    # No page reload is needed: while this tab is open, V2 stays in 'waiting'
    # state and Workbox fires its 'waiting' event on the current page.

    # Capture console messages for debugging.
    console_msgs: list[str] = []
    page.on("console", lambda msg: console_msgs.append(f"{msg.type}: {msg.text}"))

    update_state = page.evaluate("""
        async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            if (!reg) throw new Error('No SW registration found');
            // Allow Workbox's dynamic import + wb.register() to complete before
            // calling update().
            await new Promise(resolve => setTimeout(resolve, 500));

            // Listen for updatefound before calling update() to verify it fires.
            let updateFoundFired = false;
            reg.addEventListener('updatefound', () => { updateFoundFired = true; });

            await reg.update();
            // Wait for the new SW to finish installing (state → 'installed').
            await new Promise((resolve, reject) => {
                const deadline = setTimeout(
                    () => reject(new Error('Timed out waiting for SW waiting state')),
                    8_000
                );
                const poll = () => {
                    if (reg.waiting) { clearTimeout(deadline); resolve(); return; }
                    if (reg.installing) {
                        reg.installing.addEventListener('statechange', poll, { once: true });
                    } else {
                        setTimeout(poll, 50);
                    }
                };
                poll();
            });
            return {
                updateFoundFired,
                waiting: reg.waiting?.scriptURL || null,
                controller: navigator.serviceWorker.controller?.scriptURL || null,
            };
        }
    """)

    assert update_state.get("updateFoundFired"), (
        f"Expected updatefound event to have fired. State: {update_state}"
    )
    assert update_state.get("waiting") is not None, (
        f"Expected registration.waiting to be set. State: {update_state}"
    )

    # Step 4: Wait for the toast.  Workbox fires its 'waiting' event once the new
    # SW is in the 'installed' (waiting) state, which calls onNeedRefresh() →
    # needRefresh.set(true) → Svelte re-renders the {#if $needRefresh} block.
    try:
        toast = page.wait_for_selector(".sw-update-toast", timeout=30_000)
    except Exception as exc:
        # Include recent console output to aid diagnosis.
        recent_console = "\n".join(console_msgs[-30:]) if console_msgs else "(none)"
        raise AssertionError(
            f"Toast did not appear within 30s.\nConsole output:\n{recent_console}"
        ) from exc
    assert toast.is_visible(), (
        "Expected .sw-update-toast to be visible when a new SW is waiting to activate"
    )

    # Step 5: Assert the ordering guarantee — html-pages cache must already contain
    # ALL main pages at the point the toast fires.  This proves the install handler
    # completed its pre-fetch BEFORE the SW entered waiting state (and therefore
    # before the toast could appear).  Clicking Refresh at this point is guaranteed
    # to serve fresh HTML with no race condition.
    main_pages = [
        "index.html", "breeder.html", "dealer.html",
        "snapshot.html", "history.html", "history-insights.html",
    ]
    cached_urls = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)
    missing_from_cache = [p for p in main_pages if not any(p in u for u in cached_urls)]
    assert not missing_from_cache, (
        f"Toast appeared but html-pages cache is MISSING these main pages: {missing_from_cache}.\n"
        f"This means the install pre-fetch did not complete before the SW entered waiting.\n"
        f"Cached: {cached_urls}"
    )


@pytest.mark.e2e
def test_refresh_button_activates_new_sw(_e2e_sw_update_context) -> None:
    """Clicking Refresh in the update toast activates the waiting SW and reloads.

    This test verifies the full Refresh path end-to-end:
      1. V1 is active and controlling the page
      2. sw.js is patched (simulating a deployment)
      3. V2 installs and enters 'waiting' — toast appears
      4. User clicks Refresh
      5. V2 calls self.skipWaiting() (requires the SKIP_WAITING message listener in sw.ts)
      6. V2 becomes the active controller
      7. Page reloads — toast is gone, no SW is left waiting

    A missing `self.addEventListener('message', ...)` handler in sw.ts would cause
    step 5 to silently fail: the toast would never disappear and reg.waiting would
    remain non-null indefinitely.
    """
    page, base_url, output_dir = _e2e_sw_update_context

    # --- Install and activate SW V1 ---
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")

    assert page.evaluate("navigator.serviceWorker.controller !== null"), (
        "SW V1 must be controlling the page before simulating an update"
    )

    # --- Simulate a new deployment ---
    sw_path = output_dir / "sw.js"
    sw_path.write_text(
        sw_path.read_text(encoding="utf-8") + "\n// refresh-test-marker",
        encoding="utf-8",
    )

    # --- Trigger update check and wait for toast ---
    console_msgs: list[str] = []
    page.on("console", lambda msg: console_msgs.append(f"{msg.type}: {msg.text}"))

    page.evaluate("""
        async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            await new Promise(resolve => setTimeout(resolve, 500));
            await reg.update();
            await new Promise((resolve, reject) => {
                const deadline = setTimeout(
                    () => reject(new Error('Timed out waiting for waiting state')), 8_000
                );
                const poll = () => {
                    if (reg.waiting) { clearTimeout(deadline); resolve(); return; }
                    setTimeout(poll, 50);
                };
                poll();
            });
        }
    """)

    try:
        page.wait_for_selector(".sw-update-toast", timeout=30_000)
    except Exception as exc:
        recent_console = "\n".join(console_msgs[-30:]) if console_msgs else "(none)"
        raise AssertionError(
            f"Toast did not appear — cannot test Refresh.\nConsole:\n{recent_console}"
        ) from exc

    # --- Click Refresh and wait for the page to reload ---
    with page.expect_navigation(wait_until="load", timeout=15_000):
        page.click(".sw-update-toast button:has-text('Refresh')")

    # --- After reload: V2 must be the active controller, nothing waiting ---
    page.evaluate("navigator.serviceWorker.ready")

    post_state = page.evaluate("""
        async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            return {
                waiting: reg?.waiting?.state ?? null,
                activeState: reg?.active?.state ?? null,
                controller: navigator.serviceWorker.controller !== null,
            };
        }
    """)

    assert post_state["waiting"] is None, (
        f"Expected reg.waiting to be null after Refresh — skipWaiting() was not called. "
        f"Full state: {post_state}. "
        f"Check that sw.ts has a 'message' event listener for {{type: 'SKIP_WAITING'}}."
    )
    assert post_state["activeState"] == "activated", (
        f"Expected new SW to be activated after Refresh, got: {post_state['activeState']}"
    )
    assert post_state["controller"] is True, (
        "Expected SW to be controlling the page after reload"
    )
    assert page.query_selector(".sw-update-toast") is None, (
        "Expected toast to be gone after successful SW update"
    )

    # Verify html-pages cache still contains all main pages after reload.
    # The new SW's install handler pre-fetched them, cleanupOutdatedCaches removed old
    # entries, and the SWR route on the Refresh reload re-populated the navigated page.
    main_pages = [
        "index.html", "breeder.html", "dealer.html",
        "snapshot.html", "history.html", "history-insights.html",
    ]
    cached_urls_after = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)
    missing_after = [p for p in main_pages if not any(p in u for u in cached_urls_after)]
    assert not missing_after, (
        f"After Refresh, html-pages cache is missing: {missing_after}.\n"
        f"Cached: {cached_urls_after}"
    )


@pytest.mark.e2e
def test_install_does_not_cache_species_pages(e2e_site_minimal) -> None:
    """The install handler must NOT pre-cache species detail pages.

    Species pages contain an inline pagereveal script baked at HTML-generation time.
    Pre-caching them during install would mean stale HTML with an outdated script
    is served after a deploy until the user explicitly navigates to that species.
    Keeping species pages out of the install cache ensures the activate handler can
    evict any previous copy that was lazily cached, so the first post-update visit
    always fetches fresh HTML.

    Mutation targets:
    - Add species pages to the install handler's `mainPages` array → species URLs
      appear in html-pages immediately after install, test fails.
    - Add a separate `caches.open('html-pages').then(cache => cache.put(speciesUrl, ...))` 
      in the install handler → same failure.
    """
    page, base_url, _ = e2e_site_minimal

    # Navigate once to activate the SW (do NOT visit any species page).
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")

    # Read all keys currently in the html-pages cache.
    cached_urls: list[str] = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)

    species_in_cache = [u for u in cached_urls if "/species/" in u]
    assert species_in_cache == [], (
        f"The install handler must NOT pre-cache species detail pages, "
        f"but found these species URLs in html-pages immediately after install: {species_in_cache}. "
        "Species pages contain an inline pagereveal script baked at HTML-generation time; "
        "pre-caching them would serve stale scripts after a deploy."
    )


@pytest.mark.e2e
def test_species_page_in_cache_after_navigation(e2e_site_minimal) -> None:
    """A species page IS lazily cached after the user navigates to it (SWR route).

    This is the complementary proof to test_install_does_not_cache_species_pages:
    species pages are intentionally absent from the install cache but ARE added to
    html-pages via the StaleWhileRevalidate NavigationRoute on first visit.  The
    activate handler's job is to evict these lazily-cached entries on the NEXT SW
    update, not prevent them from being cached at all.
    """
    page, base_url, _ = e2e_site_minimal

    # Navigate to a species page — the SWR route should cache it.
    page.goto(f"{base_url}/species/aphonopelma-seemanni.html", wait_until="domcontentloaded")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")
    # Give the SWR background-fetch a moment to write to the cache.
    page.wait_for_timeout(500)

    cached_urls: list[str] = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)

    species_cached = any("/species/" in u for u in cached_urls)
    assert species_cached, (
        "Expected at least one species page URL in html-pages after navigation. "
        "The StaleWhileRevalidate NavigationRoute should have cached it. "
        "If this fails, check that the NavigationRoute is still registered in sw.ts."
    )


@pytest.mark.e2e
def test_activate_evicts_previously_cached_species_page(_e2e_sw_update_context) -> None:
    """SW activate handler evicts stale species HTML from html-pages on every SW update.

    Root cause of the bug this tests:
    Species pages contain an inline pagereveal script baked at HTML-generation time.
    After a deploy the old HTML (with the outdated script) was served from cache,
    silently breaking view-transition direction detection.

    This test:
    1. Installs SW V1 and navigates to a species page → caches it via SWR.
    2. Patches sw.js on disk (simulates a deploy).
    3. Triggers SW V2 install + activation.
    4. Confirms the species URL is gone from html-pages (evicted by activate handler).
    5. Confirms all six main pages are still present (install pre-fetched them).

    Mutation targets:
    - Remove the `activate` event listener from sw.ts → species URL survives,
      test fails: 'species page was NOT evicted'.
    - Change the `activate` filter from `!mainPages.has` to `mainPages.has` →
      main pages are evicted instead, subsequent assertion fails.
    - Remove `history-insights.html` from the mainPages Set in sw-activate.ts →
      history-insights is evicted, retained-main-pages assertion fails.
    """
    page, base_url, output_dir = _e2e_sw_update_context

    # ── Step 1: Install and activate SW V1 ───────────────────────────────────
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")

    # ── Step 2: Navigate to a species page → SWR caches it ───────────────────
    page.goto(f"{base_url}/species/aphonopelma-seemanni.html", wait_until="domcontentloaded")
    page.wait_for_timeout(600)  # Allow SWR background fetch to complete

    before_urls: list[str] = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)
    species_present_before = any("/species/" in u for u in before_urls)
    assert species_present_before, (
        "Precondition failed: species page was not cached by SWR. "
        "Cannot test eviction without a cached species entry."
    )

    # ── Step 3: Patch sw.js on disk to trigger SW V2 install ─────────────────
    sw_path = output_dir / "sw.js"
    original_sw = sw_path.read_text(encoding="utf-8")
    patched_sw = original_sw + "\n/* v2-patch */"
    sw_path.write_text(patched_sw, encoding="utf-8")

    # Navigate twice: first visit starts V2 install (V1 still controlling),
    # second visit the new SW takes over after skipWaiting/activate.
    # The toast triggers skipWaiting automatically in the test context, but
    # we also inject the message manually to be deterministic.
    page.goto(f"{base_url}/breeder.html", wait_until="domcontentloaded")
    page.wait_for_timeout(800)

    # Force skip-waiting so V2 activates immediately
    page.evaluate("""
        async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            if (reg?.waiting) {
                reg.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
        }
    """)
    page.wait_for_timeout(400)

    # Reload to let V2 take control
    page.reload(wait_until="domcontentloaded")
    page.evaluate("async () => { await navigator.serviceWorker.ready; }")
    page.wait_for_timeout(400)

    # ── Step 4: Verify species page was evicted ───────────────────────────────
    after_urls: list[str] = page.evaluate("""
        async () => {
            const cache = await caches.open('html-pages');
            const keys = await cache.keys();
            return keys.map(r => r.url);
        }
    """)

    species_after_update = [u for u in after_urls if "/species/" in u]
    assert species_after_update == [], (
        f"Species page was NOT evicted from html-pages after SW update. "
        f"Found: {species_after_update}. "
        "The SW activate handler must evict all non-main-page entries so stale "
        "species HTML (with outdated inline scripts) is not served after a deploy."
    )

    # ── Step 5: Verify main pages are still present ───────────────────────────
    main_pages = [
        "index.html", "breeder.html", "dealer.html",
        "snapshot.html", "history.html", "history-insights.html",
    ]
    missing_main = [p for p in main_pages if not any(p in u for u in after_urls)]
    assert missing_main == [], (
        f"After SW update and eviction, these main pages are missing from html-pages: {missing_main}. "
        "The activate handler must only evict non-main-page entries; "
        "main pages were pre-fetched by the install handler and must be retained."
    )
