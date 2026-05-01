#!/usr/bin/env python3
"""E2E tests for the PWA service worker (WP-SW).

Scope:
- SW registration on all pages (via base.html) produces no errors
- SW activates and becomes the controller after initial page loads
- Precache manifest covers at least one hashed JS bundle
- HTML navigation routes land in the `html-pages` SWR cache
- CSS files land in the `css-runtime` SWR cache
- SW registration scope covers the whole site (not a narrow per-page scope)
- `#sw-update-toast-root` mount point present on every page
- Update toast is hidden on fresh load (no waiting SW)
- Update toast appears when a new SW version is installed and waiting
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
def test_css_cached_in_css_runtime(e2e_site_minimal) -> None:
    """At least one CSS file is present in the `css-runtime` SWR cache.

    The sw.ts registerRoute for request.destination === 'style' covers the
    unhashed top-level CSS files (common.css, analysis.css, etc.).  This test
    verifies that route is active and that visiting a page actually populates
    the cache — a misconfigured or missing route would leave it empty.
    """
    page, base_url, _ = e2e_site_minimal

    page.goto(f"{base_url}/history-insights.html", wait_until="load")
    page.evaluate("navigator.serviceWorker.ready")

    css_entry_count = page.evaluate("""
        async () => {
            const cache = await caches.open('css-runtime');
            const reqs = await cache.keys();
            return reqs.filter(r => r.url.endsWith('.css')).length;
        }
    """)
    assert css_entry_count > 0, (
        f"Expected at least one .css entry in the 'css-runtime' cache, got {css_entry_count}. "
        "Check that the registerRoute for request.destination === 'style' is active in sw.ts."
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
